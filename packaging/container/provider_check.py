import importlib.util
import json
from pathlib import Path
import sys

node = Path('/opt/ComfyUI/custom_nodes/ComfyUI_OmniXPU')
spec = importlib.util.spec_from_file_location('_comfyui_omnixpu_runtime_bootstrap', node / 'runtime_bootstrap.py')
bootstrap = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bootstrap
spec.loader.exec_module(bootstrap)
import comfy_aimdo.control as control
state = bootstrap.bootstrap(dynamic_vram_override=True)
assert all(v['status'] == 'active' for v in state['providers'].values()), state
import torch
import comfy_kitchen as ck
assert control.get_xpu_allocator_mode() == 'native_hook'
assert control.init_devices([0])
torch.manual_seed(35)
a = torch.randint(-16, 16, (32, 128), dtype=torch.int8, device='xpu')
b = torch.randint(-16, 16, (128, 64), dtype=torch.int8, device='xpu')
with ck.use_backend('xpu'):
    actual = ck.mm_int8(a, b)
reference = a.cpu().int() @ b.cpu().int()
torch.testing.assert_close(actual.cpu(), reference, rtol=0, atol=0)
# Exercise the pinned AIMDO regression directly after provider takeover so
# imports resolve to the installed provider, not the source checkout.
test_path = Path('/validation/components/comfy-aimdo/tests/test_xpu_backend.py')
spec = importlib.util.spec_from_file_location('aimdo_pinned_device_test', test_path)
tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tests)
tests.test_vbar_raw_tensor_hit_evict_and_refault_signature()
torch.xpu.synchronize()
receipt = {'status': 'passed', 'bootstrap': state,
           'allocator_mode': control.get_xpu_allocator_mode(),
           'kitchen_mm_int8': 'exact CPU reference match',
           'aimdo_vbar': 'write/read, hit, evict, refault signature passed',
           'aimdo_control_file': control.__file__,
           'kitchen_xpu_file': sys.modules['comfy_kitchen.backends.xpu'].__file__,
           'vmm_stats': control.get_xpu_vmm_stats(),
           'hook_stats': control.get_xpu_ur_hook_stats()}
Path('/evidence/providers.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
del a, b, actual
torch.xpu.empty_cache()
control.deinit()
