import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

# Public repo: tests/ is next to scripts/; development: use the installed skill.
candidate = Path(__file__).resolve().parent.parent / 'scripts'
if not candidate.is_dir():
    raise RuntimeError('Run tests from the repository tests directory.')
sys.path.insert(0, str(candidate))
import temp_workspace as scratch


class ScratchTests(unittest.TestCase):
    def setUp(self):
        self.area = tempfile.TemporaryDirectory()
        self.root = Path(self.area.name).resolve()

    def tearDown(self):
        self.area.cleanup()

    def test_cleanup_removes_only_owned_session(self):
        original = self.root / 'original.pdf'
        original.write_bytes(b'%PDF-original')
        one = scratch.create(self.root)
        two = scratch.create(self.root)
        Path(one['pdf']).write_bytes(original.read_bytes())
        (Path(one['images'])).mkdir()
        (Path(one['images']) / 'page.png').write_bytes(b'image')
        self.assertTrue(scratch.cleanup(one['session'])['removed'])
        self.assertTrue(original.exists())
        self.assertTrue(Path(two['session']).exists())

    def test_repeated_cleanup_is_safe(self):
        created = scratch.create(self.root)
        scratch.cleanup(created['session'])
        self.assertTrue(scratch.cleanup(created['session'])['already_absent'])

    def test_arbitrary_directory_is_refused(self):
        (self.root / 'keep.txt').write_text('keep')
        with self.assertRaises(ValueError):
            scratch.cleanup(self.root)
        self.assertTrue((self.root / 'keep.txt').exists())

    def test_invalid_marker_is_refused(self):
        created = scratch.create(self.root)
        session = Path(created['session'])
        marker = session / scratch.MARKER
        data = json.loads(marker.read_text())
        data['session'] = str(self.root)
        marker.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            scratch.cleanup(session)
        self.assertTrue(session.exists())

    def test_failure_keeps_marker_for_retry(self):
        created = scratch.create(self.root)
        session = Path(created['session'])
        (session / 'images').mkdir()
        with patch.object(scratch.shutil, 'rmtree', side_effect=PermissionError('locked')):
            with self.assertRaises(PermissionError):
                scratch.cleanup(session)
        self.assertTrue((session / scratch.MARKER).exists())
        self.assertTrue(scratch.cleanup(session)['removed'])

    def test_linked_payload_is_refused(self):
        created = scratch.create(self.root)
        session = Path(created['session'])
        external = self.root / 'external'
        external.mkdir()
        try:
            (session / 'link').symlink_to(external, target_is_directory=True)
        except OSError:
            self.skipTest('OS does not allow creating symbolic links')
        with self.assertRaises(ValueError):
            scratch.cleanup(session)
        self.assertTrue(external.exists())
        (session / 'link').unlink()


if __name__ == '__main__':
    unittest.main()
