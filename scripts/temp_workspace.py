"""Create and remove marked, per-request PDF/image scratch directories."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import uuid

BASE = "goodnotes-pdf-vision-tmp"
MARKER = ".goodnotes-pdf-vision-session.json"
PATTERN = re.compile(r"session-[a-f0-9]{32}")


def linked(path):
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def create(work_root):
    base = Path(work_root).expanduser().resolve() / BASE
    base.mkdir(parents=True, exist_ok=True)
    if linked(base):
        raise ValueError("Scratch base must not be a link or junction.")
    session = base / ("session-" + uuid.uuid4().hex)
    session.mkdir()
    data = {"skill": "goodnotes-pdf-vision", "session": str(session.resolve()),
            "created_utc": datetime.now(timezone.utc).isoformat()}
    (session / MARKER).write_text(json.dumps(data), encoding="utf-8")
    return {"session": str(session), "pdf": str(session / "source.pdf"),
            "images": str(session / "images")}


def validate(session):
    path = Path(os.path.abspath(os.path.expanduser(str(session))))
    if path.parent.name != BASE or not PATTERN.fullmatch(path.name):
        raise ValueError("Refusing cleanup outside a named skill scratch session.")
    if path.resolve() != path or (path.parent.exists() and linked(path.parent)):
        raise ValueError("Scratch path must not traverse a link or junction.")
    if not path.exists():
        return path
    if not path.is_dir() or linked(path):
        raise ValueError("Scratch session must be a normal directory.")
    marker = path / MARKER
    if not marker.is_file() or linked(marker):
        raise ValueError("Missing safe session marker; no files were removed.")
    data = json.loads(marker.read_text(encoding="utf-8"))
    if data.get("skill") != "goodnotes-pdf-vision" or data.get("session") != str(path):
        raise ValueError("Session marker does not match this directory.")
    # Check every entry before recursive removal. Never follow links or junctions.
    for current, dirs, files in os.walk(path, followlinks=False):
        for name in dirs + files:
            entry = Path(current) / name
            if linked(entry) or not entry.resolve().is_relative_to(path):
                raise ValueError("Refusing cleanup of a session containing links or junctions.")
    return path


def cleanup(session):
    path = validate(session)
    if not path.exists():
        return {"session": str(path), "removed": True, "already_absent": True}
    # Keep the marker until all payloads are gone so failed cleanup can be retried.
    for child in path.iterdir():
        if child.name == MARKER:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    (path / MARKER).unlink()
    path.rmdir()
    return {"session": str(path), "removed": not path.exists()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("create").add_argument("--work-root", required=True)
    commands.add_parser("cleanup").add_argument("--session", required=True)
    args = parser.parse_args()
    try:
        result = create(args.work_root) if args.action == "create" else cleanup(args.session)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(f"Scratch operation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
