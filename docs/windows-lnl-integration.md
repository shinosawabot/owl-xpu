# Windows Lunar Lake integration

This document records the experimental Windows LNL package profile for the
local Intel Arc 130V / `lnl` path. The root keeps every submodule's default
branch at `main` and pins exact component commits through gitlinks. A target
profile or component PR does not by itself establish device acceptance.

## Component contract

The components must be installed as one exact source combination:

1. `omni_xpu_kernels` reports `__xpu_target__ == "lnl"`, builds the LNL core
   AOT image and selects the LNL LGRF/CuTe configurations. DG2 remains a
   separate core-only path because its CuTe/LGRF compiler path is unsupported.
2. `comfy-kitchen` and `comfy-aimdo` provider wheel manifests accept `lnl`
   while retaining their Windows platform contracts.
3. `ComfyUI_OmniXPU` activates a provider only when its manifest lists `lnl`;
   the installed Omni wheel and core AOT marker must also report `lnl`.
4. ComfyUI stays on the official host branch. The OWL custom node is layered
   through the provider bootstrap and does not replace the host package.

## Local build

The profile is an experimental recipe, not a published bundle:

```powershell
python packaging/build.py check
python packaging/build.py plan --profile packaging/profiles/lnl-windows-torch213.json
python packaging/build.py build `
  --profile packaging/profiles/lnl-windows-torch213.json `
  --sycl-tla C:\path\to\pinned\sycl-tla `
  --output dist\lnl-windows-torch213
```

The host must provide oneAPI 2026, oneDNN 2026.0.0, the Windows SDK, MSVC,
Level Zero headers and (for AIMDO) Detours. The AIMDO step calls
`scripts\build-windows-xpu.cmd`; it does not enable AIMDO in ComfyUI by
itself.

## Validation boundary

The component PRs contain standalone LNL native and shape-contract checks.
Those checks establish implementation boundaries only. The root combination
remains unvalidated until the clean Windows build produces all pinned wheel
artifacts, the provider manifests and hashes are recorded, and a ComfyUI
workflow receipt is attached. Qwen Image 2.1 attention must remain on Torch
SDPA for shapes outside the current CuTe contract.

AIMDO remains opt-in. Its Windows allocator path requires target-local
validation before DynamicVRAM is enabled; ordinary resident-weight startup is
the baseline for the experimental profile.
