#!/usr/bin/env python3
"""Verify the Ubuntu 24.04 image on an Ubuntu x86-64 host with Intel /dev/dri.

Validated host: Ubuntu 24.10. No models are downloaded or host ports exposed.
Other host operating systems are unvalidated.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', default='owl-xpu:comfyui-0.35.0-bmg')
    parser.add_argument('--pci', required=True)
    parser.add_argument('--ze-affinity', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('owl_build', ROOT / 'packaging/build.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sources = module.inspect_sources(ROOT)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    common = ['--network=none', '--device=/dev/dri',
              '--env', 'ZE_AFFINITY_MASK=' + args.ze_affinity,
              '--volume', str(output) + ':/evidence',
              '--volume', str(ROOT) + ':/validation:ro']

    def run(command, log):
        with (output / log).open('w') as stream:
            subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True)

    run(['docker', 'image', 'inspect', args.image], 'image-inspect.json')
    run(['docker', 'run', '--rm', '--network=none', '--entrypoint=cat', args.image,
         '/opt/owl-bundle/manifest.json'], 'bundle-manifest.json')
    manifest = json.loads((output / 'bundle-manifest.json').read_text())
    assert manifest['components'] == sources['components'], 'Verification source gitlinks differ from image'
    run(['docker', 'run', '--rm', *common, '--entrypoint=python', args.image,
         '/validation/packaging/container/device_check.py', '--pci', args.pci,
         '--output', '/evidence/device'], 'device.log')
    provider_command = (
        'set -euo pipefail; '
        'preload=$(python custom_nodes/ComfyUI_OmniXPU/runtime_bootstrap.py --allocator-preload-path); '
        'test -n "$preload"; '
        'export LD_PRELOAD="$preload" AIMDO_XPU_ALLOCATOR_MODE=native_hook '
        'OMNIXPU_PROVIDER_BOOTSTRAP=required; '
        'exec python /validation/packaging/container/provider_check.py'
    )
    run(['docker', 'run', '--rm', *common, '--entrypoint=bash', args.image,
         '-c', provider_command], 'providers.log')
    for mode in ['enabled', 'disabled']:
        name = 'owl-validation-' + uuid.uuid4().hex[:12]
        try:
            run(['docker', 'run', '-d', '--name', name, *common, args.image,
                 '--listen', '127.0.0.1', '--port', '8188', '--disable-api-nodes',
                 '--' + ('enable' if mode == 'enabled' else 'disable') + '-dynamic-vram'],
                mode + '-container.txt')
            command = ['docker', 'exec', name, 'python', '/opt/owl/smoke_comfyui.py',
                       '--output', '/evidence/' + mode]
            if mode == 'enabled':
                command.append('--require-aimdo')
            run(command, mode + '-smoke.log')
            if mode == 'disabled':
                assert 'comfy_aimdo.xpu: skipped (DynamicVRAM is disabled)' in (output / mode / 'diagnostics.txt').read_text()
        finally:
            with (output / (mode + '-server.log')).open('w') as log:
                subprocess.run(['docker', 'logs', name], stdout=log, stderr=subprocess.STDOUT)
            subprocess.run(['docker', 'rm', '-f', name], check=False, stdout=subprocess.DEVNULL)
    (output / 'result.json').write_text(json.dumps({
        'status': 'passed', 'image': args.image, 'pci': args.pci,
        'verification_revision': sources['owl_revision'],
        'build_revision': manifest['owl_revision'],
        'checks': ['36 native RMSNorm cases', 'DynamicVRAM enabled: both providers active',
                   'Kitchen INT8 exact reference and AIMDO VBAR hit/evict/refault',
                   'DynamicVRAM disabled: Kitchen active, AIMDO skipped',
                   'official ComfyUI 0.35.0 diagnostic workflow in both modes'],
        'scope': 'B580 packaging and model-free integration; no inference/performance claim',
    }, indent=2) + '\n')
    print('PASS:', output / 'result.json')


if __name__ == '__main__':
    main()
