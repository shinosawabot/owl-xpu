# Running Z Image Turbo INT8 on PTL-H with OWL-XPU

Date: 2026-09-21

This run uses the OWL PTL-H Torch 2.13 package with the canonical
[`Z Image Turbo INT8 ConvRot workflow`](../workflows/zimage-turbo-int8-convrot-api.json)
inside ComfyUI 0.35.0 on an Intel Arc B390. It records both the normal
DynamicVRAM startup behavior and the resident-weight run used for the fused
INT8 route gate.

## Runtime

The image was built from OWL root revision `0e09318` with
`packaging/container/build_image.py --xpu-target ptl-h`:

| Item | Identity |
| --- | --- |
| Device | Intel Arc B390, `intel_gpu_ptl_h`, `xe` driver |
| Profile | `ptl-h-torch213`, `require_cute=true` |
| Image | `sha256:951b8b14b47cc0e621dedd68836b71f3bd84df3f99e45821fbaff5a4b3703adb` |
| Torch | `2.13.0+xpu` |
| oneDNN | `2026.0.0` |
| `omni_xpu_kernel` | `0.2.0b2+torch213.ptlh` |
| Kitchen | `0.2.33`, PTL-H provider installed |
| AIMDO | `0.5.3`, PTL-H provider installed |
| ComfyUI | `0.35.0`, `40c4fcdf513a4523e39d54a9d391908af8df8171` |
| ComfyUI_OmniXPU | `2057f1c9c25ed993e8267ca02ff41aeffd2b9573` |

The exact graph hash is
`7fcd865a3cd5e2819ca7b520fe8c375567eec7d81227825e1984d741a128ac2e`. The
three model files and their hashes are listed in the
[PTL-H validation receipt](../docs/ptl-h-validation.md).

## Native and workflow checks

Before the image run, the PTL-H wheel passed a CUTE BF16 D128 check with a
maximum absolute error of `0.00390625` against Torch SDPA and an LGRF BF16 D128
check with a maximum absolute error of `0.0078125`. ComfyUI startup registered
the CUTE attention, RMSNorm and INT8 FFN adapters.

The graph used 1024×1024 output, batch size 1, CFG 1, 8 `res_multistep` steps
and seed `123456789`. With `--disable-dynamic-vram`, the resident-weight gate
completed in 17.92 seconds and produced a 1024×1024 RGB PNG. The server log
recorded 272 `int8_swiglu_mlp` calls and 272 CUTE attention calls. Every
observed INT8 call used
`shared_up+fused_swiglu+convrot+quant+prequant_down`, with both ConvRot flags
enabled. The output hash was
`49f3da5de99b6c9a435983c70b64a78e946e84196aa0057d7d3020471c2059b2`.

The default DynamicVRAM run also completed the graph and confirmed provider
startup. Its model-weight offload reported `w1_offloaded_weight`, so the FFN
adapter used its fallback instead of the fused resident-weight route. The
default run is therefore recorded as an execution and startup check; the fused
INT8 claim applies only to the explicit resident-weight gate.
