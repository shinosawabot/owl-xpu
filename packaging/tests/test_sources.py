"""Offline source-admission tests; no network, Torch or device required."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("owl_packaging", Path(__file__).parents[1] / "build.py")
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True, stderr=subprocess.STDOUT).strip()


def init(root):
    root.mkdir()
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Packaging fixture")
    git(root, "config", "user.email", "fixture@example.invalid")


class SourceAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.root = base / "owl"
        init(self.root)
        (self.root / "README.md").write_text("fixture\n")
        (self.root / ".gitignore").write_text("dist/\n")
        for name in BUILD.SOURCES.values():
            source = base / name
            init(source)
            (source / "runtime.txt").write_text(name + "\n")
            git(source, "add", ".")
            git(source, "commit", "-m", "fixture")
            git(self.root, "-c", "protocol.file.allow=always", "submodule", "add", str(source), "components/" + name)
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "pin components")

    def test_exact_pins_and_ignored_outputs_are_accepted(self):
        (self.root / "dist").mkdir()
        (self.root / "dist" / "old.whl").write_text("ignored output")
        receipt = BUILD.inspect_sources(self.root)
        self.assertEqual(set(receipt["components"]), set(BUILD.SOURCES))
        for item in receipt["components"].values():
            self.assertEqual(item["revision"], git(self.root / item["path"], "rev-parse", "HEAD"))

    def test_missing_checkout_is_rejected(self):
        git(self.root, "submodule", "deinit", "-f", "components/comfy-aimdo")
        with self.assertRaisesRegex(RuntimeError, "Uninitialized"):
            BUILD.inspect_sources(self.root)

    def test_modified_runtime_is_rejected(self):
        (self.root / "components/comfy-kitchen/runtime.txt").write_text("changed")
        with self.assertRaisesRegex(RuntimeError, "dirty"):
            BUILD.inspect_sources(self.root)

    def test_untracked_runtime_is_rejected(self):
        (self.root / "components/comfy-kitchen/untracked.py").write_text("pass\n")
        with self.assertRaisesRegex(RuntimeError, "dirty"):
            BUILD.inspect_sources(self.root)

    def test_staged_pin_does_not_replace_committed_authority(self):
        module = self.root / "components/comfy-aimdo"
        git(module, "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "commit", "--allow-empty", "-m", "new revision")
        git(self.root, "add", "components/comfy-aimdo")
        with self.assertRaisesRegex(RuntimeError, "dirty"):
            BUILD.inspect_sources(self.root)

    def test_committed_runtime_outside_submodule_is_rejected(self):
        (self.root / "runtime.py").write_text("pass\n")
        git(self.root, "add", "runtime.py")
        git(self.root, "commit", "-m", "invalid placement")
        with self.assertRaisesRegex(RuntimeError, "ownership violation"):
            BUILD.inspect_sources(self.root)

    def test_workflow_and_blog_assets_are_accepted(self):
        (self.root / "workflows").mkdir()
        (self.root / "workflows/example.json").write_text("{}\n")
        (self.root / "blogs").mkdir()
        (self.root / "blogs/example.md").write_text("# Example\n")
        git(self.root, "add", "workflows", "blogs")
        git(self.root, "commit", "-m", "add validation assets")
        BUILD.inspect_sources(self.root)


if __name__ == "__main__":
    unittest.main()
