"""Verify the complete bundle before installing it into the official host."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

root = Path('/opt/owl-bundle')
manifest = json.loads((root / 'manifest.json').read_text())
assert manifest['components']['host']['revision'] == '40c4fcdf513a4523e39d54a9d391908af8df8171'
assert set(manifest['selected_components']) == {'kernels', 'kitchen', 'aimdo', 'comfyui'}
for name, digest in manifest['artifacts'].items():
    artifact = (root / name).resolve()
    assert artifact.is_relative_to(root)
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == digest, name
wheels = list((root / 'wheels').rglob('*.whl'))
assert len(wheels) == 3
subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-deps', '--force-reinstall',
                *map(str, wheels)], check=True)
with zipfile.ZipFile(root / 'ComfyUI_OmniXPU.zip') as archive:
    archive.extractall('/opt/ComfyUI/custom_nodes')
subprocess.run([sys.executable, '-m', 'pip', 'check'], check=True)
