"""Container-side physical-device admission and a small numerical smoke check."""
import argparse
import csv
import io
import json
import os
from pathlib import Path
import subprocess
import uuid

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pci', required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
env = dict(os.environ)
env.pop('ZE_AFFINITY_MASK', None)


def smi(name, *arguments):
    result = subprocess.run(['xpu-smi', *arguments], env=env, text=True,
                            capture_output=True, check=True)
    (args.output / name).write_text(result.stdout)
    (args.output / (name + '.stderr')).write_text(result.stderr)
    return result.stdout


inventory = json.loads(smi('discovery.json', 'discovery', '-j'))
matches = [d for d in inventory['device_list'] if d['pci_bdf_address'] == args.pci]
assert len(matches) == 1, matches
device = matches[0]
assert device['pci_device_id'].lower() == '0xe20b', 'This acceptance recipe is B580-only'
index = str(device['device_id'])
processes = json.loads(smi('processes.json', 'ps', '--device', index, '--json'))
assert processes['device_util_by_proc_list'] == [], processes
raw = smi('idle.csv', 'dump', '--device', index, '--metrics', '0,9,17,18',
          '--interval', '1', '--number', '3')
rows = list(csv.DictReader(io.StringIO(raw), skipinitialspace=True))
assert len(rows) == 3, raw
for row in rows:
    normalized = {k.strip().lower(): v.strip() for k, v in row.items()}
    assert float(normalized['memory.used (mib)']) <= 64, row
    for key in ['utilization.gpu (%)', 'eu.active (%)', 'memory.bandwidth.utilization (%)']:
        if normalized.get(key, 'N/A') != 'N/A':
            assert float(normalized[key]) <= 5, row
# Import Torch only after physical idle admission; Sysman ran unmasked above.
import torch
assert torch.xpu.device_count() == 1
prop = torch.xpu.get_device_properties(0)
assert uuid.UUID(str(prop.uuid)).bytes[::-1] == uuid.UUID(device['uuid']).bytes
assert 'B580' in prop.name
from omni_xpu_kernel import norm
import omni_xpu_kernel
cases = 0
for dtype in [torch.float32, torch.float16, torch.bfloat16]:
    for rows_count in [1, 8, 32, 128]:
        for width in [2048, 4096, 8192]:
            x = torch.randn(rows_count, width, device='xpu', dtype=dtype)
            w = torch.randn(width, device='xpu', dtype=dtype)
            actual = norm.rms_norm(w, x, eps=1e-6)
            expected = (x.float() * torch.rsqrt(x.float().square().mean(-1, keepdim=True) + 1e-6) * w.float()).to(dtype)
            tolerance = 1e-4 if dtype == torch.float32 else 1e-2
            torch.testing.assert_close(actual, expected, rtol=tolerance, atol=tolerance)
            cases += 1
torch.xpu.synchronize()
(args.output / 'result.json').write_text(json.dumps({
    'status': 'passed', 'pci': args.pci, 'torch_device': str(prop),
    'kernel_file': omni_xpu_kernel.__file__, 'rms_norm_cases': cases,
    'idle_method': 'three memory samples, available activity counters and empty process inventory',
}, indent=2) + '\n')
print(f'PASS: physical B580 identity, idle admission, {cases} native RMSNorm cases')
