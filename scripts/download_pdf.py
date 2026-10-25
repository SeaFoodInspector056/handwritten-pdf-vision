"""Download a connector-provided original PDF; URL is read from stdin."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--expected-bytes', type=int)
    args = parser.parse_args()
    target = Path(args.output).expanduser().resolve()
    created = False
    try:
        if args.expected_bytes is not None and args.expected_bytes <= 0:
            raise ValueError('Expected size must be positive.')
        url = sys.stdin.readline().strip()
        parsed = urlsplit(url)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('An authenticated HTTPS download URL from the connector is required on stdin.')
        if target.exists():
            raise FileExistsError('Output already exists; use a new per-request file path.')
        target.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        total = 0
        with urlopen(Request(url, headers={'User-Agent': 'handwritten-pdf-vision/1'}), timeout=60) as response:
            if urlsplit(response.geturl()).scheme != 'https':
                raise ValueError('Download redirected to a non-HTTPS URL.')
            prefix = response.read(1024)
            if b'%PDF-' not in prefix:
                raise ValueError('Response is not a PDF (missing PDF header).')
            with target.open('xb') as stream:
                created = True
                chunk = prefix
                while chunk:
                    total += len(chunk)
                    if args.expected_bytes is not None and total > args.expected_bytes:
                        raise ValueError('Downloaded size exceeds the connector metadata size.')
                    stream.write(chunk)
                    digest.update(chunk)
                    chunk = response.read(1024 * 1024)
            if args.expected_bytes is not None and total != args.expected_bytes:
                raise ValueError('Downloaded size differs from the connector metadata size.')
        print(json.dumps({'path': str(target), 'bytes': total, 'sha256': digest.hexdigest()}, ensure_ascii=False))
        return 0
    except BaseException as exc:
        if created:
            target.unlink(missing_ok=True)
        if isinstance(exc, (KeyboardInterrupt, EOFError)):
            print('Download cancelled.', file=sys.stderr)
            return 130
        if isinstance(exc, (ValueError, FileExistsError)):
            print(str(exc), file=sys.stderr)
        else:
            # Exception messages can contain signed URLs: report only type/status.
            status = getattr(exc, 'code', None)
            print(f'Download failed: {type(exc).__name__}' + (f' (HTTP {status})' if status else '') + '. Re-fetch the connector reference or check network and file permissions.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
