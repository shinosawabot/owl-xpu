# Windows Lunar Lake integration

This `dev` branch records the first OWL assembly for the local Windows 11
Lunar Lake machine (Arc 130V / `lnl`, Torch 2.13.0+xpu, Python 3.13).

## Component contract

The component branches are target-specific and must be installed together:

1. `omni_xpu_kernels` reports `__xpu_target__ == "lnl"` and builds the core,
   LGRF and optional CUTE sidecars with the LNL AOT target.
2. `comfy-kitchen` and `comfy-aimdo` provider wheel manifests accept `lnl` and
   retain the Windows platform contract (`win32`).
3. `ComfyUI_OmniXPU` activates a provider only when its manifest lists `lnl`;
   target checking remains fail-closed.
4. ComfyUI stays on the official host branch. The OWL custom node is layered
   through the provider bootstrap and does not replace the host package.

## Local build

The profile is an experimental recipe, not a published bundle:

```powershell
python packaging/build.py check
python packaging/build.py plan --profile packaging/profiles/lnl-windows-torch213.json
python packaging/build.py build `
  --profile packaging/profiles/lnl-windows-torch213.json `
  --sycl-tla C:\path\to\sycl-tla-2fc09973bfdf15755090fcb0e3b6ad236408a992 `
  --output dist\lnl-windows-torch213
```

The host must provide oneAPI 2026, oneDNN 2026.0.0, the Windows SDK, MSVC,
Level Zero headers, and (for AIMDO) Detours.  The AIMDO step calls
`scripts\build-windows-xpu.cmd`; it does not enable AIMDO in ComfyUI by
itself.

## Validation boundary

The local session already passed LNL native ConvRot correctness and standalone
CUTE correctness checks.  A Qwen Image 2.1 INT8 run should start with Torch
attention and then compare CUTE under the same cold-machine conditions.  The
Qwen attention shape is outside the currently routed CUTE contract, so a CUTE
wheel alone must not be reported as an end-to-end CUTE acceleration.

AIMDO remains opt-in.  The local Windows experiments found unstable VBAR map
failures and no repeatable end-to-end advantage; the ordinary no-AIMDO path is
the baseline for driver, thermal and memory comparisons.
