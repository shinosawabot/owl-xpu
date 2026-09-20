# Running Z Image Turbo INT8 on DG2 with OWL-XPU

Date: 2026-09-21

This run uses the OWL DG2 core-only package with the canonical
[`Z Image Turbo INT8 ConvRot workflow`](../workflows/zimage-turbo-int8-convrot-api.json)
inside ComfyUI 0.35.0. The purpose is to exercise a real image-generation graph
through the packaged ComfyUI integration and confirm that the supported DG2
routes remain active.

## Runtime

The run used the `dg2-torch213` profile in the pinned OMIX environment:

| Item | Identity |
| --- | --- |
| Torch | `2.13.0+xpu` |
| oneDNN | `2026.0.0` |
| `omni_xpu_kernel` | `0.2.0b2+torch213.dg2` |
| kernel source | `7c57b7d4acd6f3d690fcd2985cf45568489d3272` |
| Kitchen | `0.2.33`, XPU provider active |
| ComfyUI | `0.35.0`, `40c4fcdf513a4523e39d54a9d391908af8df8171` |
| ComfyUI_OmniXPU | `2057f1c9c25ed993e8267ca02ff41aeffd2b9573` |

The exact graph hash is
`7fcd865a3cd5e2819ca7b520fe8c375567eec7d81227825e1984d741a128ac2e`. The
read-only model files were the INT8 Z Image UNet, Qwen 3 4B text encoder and
`ae.safetensors`; their sizes and hashes are recorded in the
[DG2 validation receipt](../docs/dg2-validation.md).

## Run and result

The graph used 1024×1024 output, batch size 1, CFG 1, 8 `res_multistep` steps
and seed `123456789`. ComfyUI returned success in 13.56 seconds and produced a
1024×1024 RGB PNG.

The DG2 package intentionally contains the core `_C` extension without CUTE or
LGRF AOT sidecars. ComfyUI therefore used PyTorch SDPA for attention while the
OmniXPU INT8 FFN adapter exercised the fused ConvRot route with both
`up_convrot=True` and `down_convrot=True`. The server completed without an
execution error or kernel fallback.

This is a functional workflow record. It does not establish DG2 CUTE/LGRF
support, complete model coverage, AIMDO lifecycle coverage or performance
parity with BMG or PTL-H.
