#!/usr/bin/env python3
"""Exercise an already running enhanced ComfyUI through its public HTTP API.

This model-free check validates registration, provider activation and graph
execution. It does not measure model quality, inference speed or memory savings.
"""
import argparse
import json
from pathlib import Path
import time
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8188')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-aimdo', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def request(path, data=None):
        payload = None if data is None else json.dumps(data).encode()
        req = urllib.request.Request(args.url + path, data=payload,
                                     headers={'Content-Type': 'application/json'})
        with opener.open(req, timeout=10) as response:
            return json.load(response)

    def save(name, value):
        (args.output / name).write_text(json.dumps(value, indent=2) + '\n')

    deadline = time.monotonic() + 180
    while True:
        try:
            stats = request('/system_stats')
            break
        except (urllib.error.URLError, TimeoutError):
            if time.monotonic() >= deadline:
                raise
            time.sleep(1)
    save('system_stats.json', stats)
    assert stats['system']['comfyui_version'] == '0.35.0', stats
    assert stats['system']['pytorch_version'] == '2.13.0+xpu', stats
    assert any(d['type'] == 'xpu' for d in stats['devices']), stats
    objects = request('/object_info')
    save('object_info.json', objects)
    assert 'OmniXPUStatus' in objects and 'PreviewAny' in objects
    graph = {'1': {'class_type': 'OmniXPUStatus', 'inputs': {}},
             '2': {'class_type': 'PreviewAny', 'inputs': {'source': ['1', 0]}}}
    save('prompt.json', graph)
    submitted = request('/prompt', {'prompt': graph})
    save('submission.json', submitted)
    prompt_id = submitted['prompt_id']
    deadline = time.monotonic() + 60
    while True:
        history = request('/history/' + prompt_id)
        if prompt_id in history:
            break
        if time.monotonic() >= deadline:
            raise TimeoutError('Diagnostic graph did not finish')
        time.sleep(0.5)
    save('history.json', history)
    result = history[prompt_id]
    assert result['status']['status_str'] == 'success', result
    status = '\n'.join(result['outputs']['2']['text'])
    (args.output / 'diagnostics.txt').write_text(status + '\n')
    assert 'comfy_kitchen.xpu: active' in status, status
    assert 'comfy_kitchen XPU: available' in status, status
    assert 'omni_xpu_kernel: 0.2.0b2' in status, status
    assert '[!!]' not in status and 'rejected:' not in status, status
    if args.require_aimdo:
        assert 'comfy_aimdo.xpu: active' in status, status
    save('result.json', {'status': 'passed', 'require_aimdo': args.require_aimdo,
                         'scope': 'model-free API and provider integration'})
    print(status)
    print('PASS: enhanced ComfyUI 0.35.0 model-free integration')


if __name__ == '__main__':
    main()
