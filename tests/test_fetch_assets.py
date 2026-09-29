import importlib.util
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile, ZipInfo

script = Path(__file__).resolve().parents[1] / 'scripts/fetch_assets.py'
spec = importlib.util.spec_from_file_location('fetch_assets', script)
fetch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch)


class ArchiveSafety(unittest.TestCase):
    def test_valid_bundle_and_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / 'bundle.zip'
            with ZipFile(archive, 'w') as bundle:
                bundle.writestr('models/example.glb', b'example')
            sha = fetch.sha256(archive)
            fetch.extract_verified(archive, sha, root / 'valid')
            self.assertEqual((root / 'valid/models/example.glb').read_bytes(), b'example')
            archive.write_bytes(archive.read_bytes() + b'changed')
            with self.assertRaises(ValueError):
                fetch.extract_verified(archive, sha, root / 'invalid')
            self.assertFalse((root / 'invalid').exists())

    def test_unsafe_member_rejects_entire_archive_before_writes(self):
        for member in ['../escape', '/absolute', 'nested/../../escape', 'nested\\escape']:
            with self.subTest(member=member), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                archive = root / 'bundle.zip'
                with ZipFile(archive, 'w') as bundle:
                    bundle.writestr('otherwise-valid.txt', b'valid')
                    bundle.writestr(member, b'bad')
                with self.assertRaises(ValueError):
                    fetch.extract_verified(archive, fetch.sha256(archive), root / 'out')
                self.assertFalse((root / 'out').exists())

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / 'bundle.zip'
            entry = ZipInfo('link')
            entry.create_system = 3
            entry.external_attr = 0o120777 << 16
            with ZipFile(archive, 'w') as bundle:
                bundle.writestr(entry, '../outside')
            with self.assertRaises(ValueError):
                fetch.extract_verified(archive, fetch.sha256(archive), root / 'out')


if __name__ == '__main__':
    unittest.main()
