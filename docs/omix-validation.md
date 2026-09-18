# OMIX clean-build validation — 2026-09-19

**Passed on the local Intel Arc B580.** The image was built with `--no-cache`
from the pinned OMIX base using `packaging/container/build_image.py`, then tested
with `packaging/container/verify_image.py` in network-disabled containers.
No prebuilt Omni development image or previously built enhancement wheel was
used in this build. A direct base-image probe confirmed `/opt/venv` was absent.

- Image: `owl-xpu:comfyui-0.35.0-bmg`
- Image ID: `sha256:63bff5fa9816c993ccbaaaeeb480aae44e8082b2e39b5b6bb7677abfe7603a15`
- Build recipe: `e54284d1c482a746c3b19d287cc4f119315bf3af`
- Verification scripts: `9dcdd18080e656bf4a18f8f3d4ebf840acdb6ecf`
- Official ComfyUI: `40c4fcdf513a4523e39d54a9d391908af8df8171` (`0.35.0`)
- Device: Intel Arc B580, PCI `0000:03:00.0`, device ID `0xe20b`
- Host environment: Ubuntu 24.10 x86-64
- Container environment: Ubuntu 24.04 x86-64 (OMIX development base)

| Check | Result |
| --- | --- |
| Source-admission unit tests | 6 passed |
| Patched oneDNN source build and installed DSO receipt | Passed |
| Four-component source build and SHA256 manifest | Passed |
| Installation alongside official Kitchen 0.2.33 / AIMDO 0.5.3 | Passed |
| `pip check` | No broken requirements |
| Unmasked Sysman identity/idle admission and masked Torch UUID match | Passed |
| Native RMSNorm: FP32, FP16, BF16 over 36 shape/dtype cases | 36 passed |
| Forced Kitchen XPU INT8 matrix multiply | Exact CPU reference match |
| AIMDO native-hook VBAR write/read, hit, eviction, refault signature | Passed |
| DynamicVRAM enabled diagnostic workflow | Kitchen and AIMDO active; Kitchen exposes 40 capabilities |
| DynamicVRAM disabled diagnostic workflow | Kitchen active; AIMDO explicitly skipped |
| Exported artifact SHA256 recheck | All four artifacts matched |

Both app runs executed the real `OmniXPUStatus -> PreviewAny` graph through the
HTTP API and completed successfully. The server logs contained no traceback,
initialization error or failed custom-node import. The LTX rotary adapter skipped
because its target split-half RoPE API is absent; Windows-only and disabled
legacy adapters also skipped as expected. This is not an assertion that every
possible adapter or model workflow is supported.

The build resolves the two issues found during the preceding prepared-image
experiment: AIMDO's UR header directory on oneAPI 2026.1, and provider version
compatibility with the official AIMDO 0.5.3 distribution. No component runtime
source changes were needed.

See the [machine-readable summary](omix-validation.json) for source pins,
artifact hashes and provider state, and [the reproducible procedure](omix-container.md)
for build, run, verify and export commands.

Raw evidence on the validation machine is retained outside Git at
`/home/xiangyu/workspace/omni-local/owl-omix-clean/`:

- `build.log`, `image-inspect.json`, `base-probe.txt`, `packaging-tests.log`
- `bundle/`: three wheels, custom-node ZIP, manifest and Python environment freeze
- `onednn-runtime.env`: exact source, patch and installed DSO hashes
- `validation/`: device admission, numerical checks, API responses, both server
  logs and final `result.json`

The image is local and includes the development toolchain (about 17.8 GB by
Docker's reported size); no registry publication was performed. The tests do not
establish generation quality, model inference correctness, speedups, memory
savings or support for another device. AIMDO's XPU memory compiler is still
unsupported; the tested native-hook functionality concerns allocator accounting
and model-weight residency/offloading. No model weights were downloaded.
