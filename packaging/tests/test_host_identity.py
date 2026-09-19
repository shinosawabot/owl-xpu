"""Host version changes must update identity without executing upstream code."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('owl_build', Path(__file__).parents[1] / 'build.py')
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


class HostIdentityTests(unittest.TestCase):
    def test_upgrade_changes_version_and_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'components/ComfyUI/comfyui_version.py'
            source.parent.mkdir(parents=True)
            identities = []
            for version in ['0.35.0', '0.36.0']:
                data = f'raise RuntimeError("must not execute")\n__version__ = "{version}"\n'.encode()
                source.write_bytes(data)
                identity = BUILD.host_identity(root)
                self.assertEqual(identity['host_version'], version)
                self.assertEqual(identity['host_version_file_sha256'], hashlib.sha256(data).hexdigest())
                identities.append(identity)
            self.assertNotEqual(identities[0], identities[1])

    def test_missing_literal_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'components/ComfyUI/comfyui_version.py'
            source.parent.mkdir(parents=True)
            for content in ['other = "0.35.0"', '__version__ = ""', '__version__ = 35']:
                source.write_text(content)
                with self.assertRaises(RuntimeError):
                    BUILD.host_identity(root)


if __name__ == '__main__':
    unittest.main()
