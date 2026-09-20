# DG2/A770 focused validation receipt

Date: 2026-09-21

This receipt covers the DG2 core-only profile and one ComfyUI workflow. It is a
focused component-overlay validation in the pinned OMIX runtime; it is not a
clean-image or performance acceptance result.

The test used the DG2 device at PCI address `0000:03:00.0` on Ubuntu 22.04,
inside the existing `intel/omix` image with the following runtime identities:

| Component | Identity |
| --- | --- |
| ComfyUI | `0.35.0`, commit `40c4fcdf513a4523e39d54a9d391908af8df8171` |
| Torch | `2.13.0+xpu` |
| oneDNN | `2026.0.0` |
| omni_xpu_kernel | `0.2.0b2+torch213.dg2` |
| kernel source | `7c57b7d` (`shinosawabot/omni_xpu_kernels`) |
| ComfyUI_OmniXPU | `2057f1c9c25ed993e8267ca02ff41aeffd2b9573` |
| Kitchen | `0.2.33` with the XPU provider active |

The kernel wheel contains the DG2 core extension only. CuTe and LGRF AOT
sidecars are excluded. The ComfyUI startup log reported native INT8 and RMSNorm
capabilities, skipped the unavailable CuTe attention backend, and applied the
INT8 FFN adapter.

The exact graph was
`bmg-image-validation-trace/zimage-int8-convrot-api.json` from the committed
ComfyUI validation template. Its SHA256 is
`7fcd865a3cd5e2819ca7b520fe8c375567eec7d81227825e1984d741a128ac2e`. It used
the following model identities:

| Model | Bytes | SHA256 |
| --- | ---: | --- |
| `z_image_turbo_int8_convrot.safetensors` | 6,201,001,296 | `be517ebd47c912a5626a588e1aeea43e6be4a43c0cdcd2b48a2a780d9f358635` |
| `qwen_3_4b.safetensors` | 8,044,982,048 | `6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a` |
| `ae.safetensors` | 335,304,388 | `afc8e28272cd15db3919bacdb6918ce9c1ed22e96cb12c4d5ed0fba823529e38` |

The graph ran at 1024×1024, batch size 1, CFG 1, 8 `res_multistep` steps and
seed `123456789`. ComfyUI returned `success` in 13.56 seconds and wrote a
1024×1024 RGB PNG. The server log recorded repeated
`int8_swiglu_mlp` calls through the OmniXPU fused ConvRot route with
`up_convrot=True` and `down_convrot=True`; the run completed without an
execution error or kernel fallback.

This receipt validates the supported DG2 core and the INT8 Z-Image workflow.
It does not claim DG2 CuTe/LGRF support, complete model coverage, AIMDO lifecycle
coverage or performance parity with BMG/PTL.
