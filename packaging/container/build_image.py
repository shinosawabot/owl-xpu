#!/usr/bin/env python3
"""Build Ubuntu 24.04 OMIX on an Ubuntu x86-64 host from committed gitlinks.

Validated host: Ubuntu 24.10. Other host operating systems are unvalidated.
The build context is a clean, credential-free source snapshot.
"""
import argparse
import importlib.util
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('owl_build', ROOT / 'packaging/build.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def run(*args):
    subprocess.run(list(map(str, args)), check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', help='Default: owl-xpu:comfyui-<pinned host version>-<target>')
    parser.add_argument('--xpu-target', choices=('bmg', 'dg2'), default='bmg')
    parser.add_argument('--work-dir', type=Path, required=True,
                        help='New directory for the isolated build context and logs')
    parser.add_argument('--no-cache', action='store_true')
    args = parser.parse_args()
    plan = module.inspect_sources(ROOT)
    args.tag = args.tag or f"owl-xpu:comfyui-{module.host_identity(ROOT)['host_version']}-{args.xpu_target}"
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=False)
    context = work / 'context'
    context.mkdir()
    clone = context / 'owl'
    run('git', 'clone', '--no-hardlinks', '--no-checkout', ROOT, clone)
    run('git', '-C', clone, 'checkout', '--detach', plan['owl_revision'])
    run('git', '-C', clone, 'submodule', 'init')
    for item in plan['components'].values():
        run('git', '-C', clone, 'config', 'submodule.' + item['path'] + '.url', ROOT / item['path'])
    run('git', '-C', clone, '-c', 'protocol.file.allow=always', 'submodule', 'update', '--init')
    # Clone generates new configs; user/global credential files are never copied.
    shutil.copyfile(ROOT / 'packaging/container/Dockerfile', context / 'Dockerfile')
    command = ['docker', 'build', '--progress=plain', '--tag', args.tag,
               '--build-arg', 'XPU_TARGET=' + args.xpu_target,
               '--build-arg', 'http_proxy', '--build-arg', 'https_proxy', '--build-arg', 'no_proxy']
    if args.no_cache:
        command.append('--no-cache')
    command.append(str(context))
    print('Build log:', work / 'build.log', flush=True)
    with (work / 'build.log').open('w') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    with (work / 'image-inspect.json').open('w') as output:
        subprocess.run(['docker', 'image', 'inspect', args.tag], stdout=output, check=True)
    print('Built:', args.tag)


if __name__ == '__main__':
    main()
