# PTL-H validation receipt

Date: 2026-09-21

This receipt covers the explicit `ptl-h` target on an Intel Arc B390 device. It
is a focused native and ComfyUI workflow validation; it is not a performance
acceptance result or a claim of complete model coverage.

The test host was `sas@10.239.141.0`, Ubuntu 24.04.4, kernel
`7.0.0-28-generic`. The GPU was PCI `0000:00:02.0`, device ID `8086:b080`,
using the `xe` driver. Inside the digest-pinned OMIX base,
`sycl-ls --verbose` reported `Intel(R) Arc(TM) B390 GPU` and
`Architecture: intel_gpu_ptl_h` through Level Zero driver
`1.15.38646+7`.

The OWL image was built by `packaging/container/build_image.py
--xpu-target ptl-h` from root revision `0e09318`. Its immutable image ID was
`sha256:951b8b14b47cc0e621dedd68836b71f3bd84df3f99e45821fbaff5a4b3703adb`,
with base image
`intel/omix@sha256:53e2c4503beeea4aff906dea180933be672449bcf04eb38df3d89622a1cd0967`.

| Component | Identity |
| --- | --- |
| Profile | `ptl-h-torch213`, `require_cute=true` |
| Torch | `2.13.0+xpu` |
| oneDNN | `2026.0.0` |
| `omni_xpu_kernel` | `0.2.0b2+torch213.ptlh` |
| kernel source | `7c57b7d4acd6f3d690fcd2985cf45568489d3272` (`shinosawabot/omni_xpu_kernels`) |
| kernel wheel SHA256 | `904c3206d715fdbeb8c45ccbfa173e23c592ac3081787c1305425e1a6ec5de2c` |
| Kitchen | `0.2.33`, PTL-H provider installed |
| AIMDO | `0.5.3`, PTL-H provider installed |
| ComfyUI | `0.35.0`, commit `40c4fcdf513a4523e39d54a9d391908af8df8171` |
| ComfyUI_OmniXPU | `2057f1c9c25ed993e8267ca02ff41aeffd2b9573` |

The wheel contains the PTL-H core `_C`, `cute_fmha_torch`, and the
`lgrf_uni/lgrf_sdp` sidecar. Direct device checks passed with one XPU visible:

- core AOT target: `ptl-h`; Torch reported the B390 as `xpu:0`;
- CUTE BF16 D128 `[1,256,4,128]`: finite output, maximum absolute error
  `0.00390625` against Torch SDPA;
- LGRF BF16 D128 `[1,64,8,128]` through `omni_xpu_kernel.sdp.sdp`: finite
  output, maximum absolute error `0.0078125` against Torch SDPA.

The workflow was the OWL-owned
[`workflows/zimage-turbo-int8-convrot-api.json`](../workflows/zimage-turbo-int8-convrot-api.json), SHA256
`7fcd865a3cd5e2819ca7b520fe8c375567eec7d81227825e1984d741a128ac2e`. It used
1024×1024, batch size 1, CFG 1, 8 `res_multistep` steps and seed
`123456789` with these read-only model files:

| Model | Bytes | SHA256 |
| --- | ---: | --- |
| `z_image_turbo_int8_convrot.safetensors` | 6,201,001,296 | `be517ebd47c912a5626a588e1aeea43e6be4a43c0cdcd2b48a2a780d9f358635` |
| `qwen_3_4b.safetensors` | 8,044,982,048 | `6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a` |
| `ae.safetensors` | 335,304,388 | `afc8e28272cd15db3919bacdb6918ce9c1ed22e96cb12c4d5ed0fba823529e38` |

For the fused INT8 gate, the image ran with `--disable-dynamic-vram` so the
14.5 GB model stayed resident on the XPU. The prompt completed in 17.92
seconds and wrote a 1024×1024 RGB PNG of 1,150,534 bytes with SHA256
`49f3da5de99b6c9a435983c70b64a78e946e84196aa0057d7d3020471c2059b2`.
The debug server log recorded 272 `int8_swiglu_mlp` calls, 272 CUTE attention
calls and zero FeedForward fallback dispatches. Every observed INT8 route was
`shared_up+fused_swiglu+convrot+quant+prequant_down` with
`up_convrot=True` and `down_convrot=True`.

The default DynamicVRAM mode also started successfully and completed the same
graph, but its model-weight offload caused the FFN adapter to report
`w1_offloaded_weight` and use its fallback. That mode is therefore outside the
fused-route gate above; the receipt records the resident-weight mode explicitly
so the result does not imply a DynamicVRAM fused INT8 claim.

This receipt validates the PTL-H package, CUTE/LGRF native paths, PTL-H RMSNorm
and the resident-weight Z-Image Turbo INT8 workflow. It does not establish
performance parity, full DynamicVRAM model coverage, AIMDO memory-compiler
support, or all PTL-H model routes.
