# Z Image Turbo INT8 OWL status

This record runs one OWL-focused Z Image Turbo INT8 API graph on the three
currently validated Linux targets. The workflow, prompt, model files and
measurement protocol are shared; only the target image and device mapping are
different.

## Workflow and prompt

- Workflow: [`zimage-turbo-int8-owl-api.json`](../workflows/zimage-turbo-int8-owl-api.json)
- Workflow SHA256: `7896c25bfade693531e624734c463ed2e643c393f909aabf6bbf6103f609de25`
- Resolution: 1024×1024, batch 1
- Sampler: `res_multistep`, 8 steps, CFG 1
- Models: `z_image_turbo_int8_convrot.safetensors`, `qwen_3_4b.safetensors` and `ae.safetensors`

The exact prompt is:

> A square editorial technology poster in a cinematic 3D-rendered style: a white Eurasian eagle-owl stands centered and full-body on a glowing blue Intel XPU development board in a dark modern laboratory. The owl faces the viewer with calm alert eyes; brushed metal traces and cool blue light surround its talons. Across the upper third, a single wide frosted-glass title panel contains the exact uppercase text "OWL-XPU" in large bold white sans-serif letters. Directly below it, the same panel contains the exact uppercase text "Z IMAGE TURBO" in smaller bold white sans-serif letters. On the front-right edge of the board, one compact illuminated badge contains the exact uppercase text "INT8". All other screens and panels are blank or show only simple geometric blue lines with no legible writing. The background is softly defocused, with blue and gold rim light, detailed white feathers, clean negative space around the title, and a balanced centered composition. The overall image is precise, restrained, and suitable for a technical project cover.

The model files were the same on all three hosts:

| File | Size | SHA256 |
| --- | ---: | --- |
| `z_image_turbo_int8_convrot.safetensors` | 6,201,001,296 bytes | `be517ebd47c912a5626a588e1aeea43e6be4a43c0cdcd2b48a2a780d9f358635` |
| `qwen_3_4b.safetensors` | 8,044,982,048 bytes | `6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a` |
| `ae.safetensors` | 335,304,388 bytes | `afc8e28272cd15db3919bacdb6918ce9c1ed22e96cb12c4d5ed0fba823529e38` |

The package assembly used ComfyUI v0.37.0, frontend 1.52.7, workflow templates
0.11.66 and the pinned OWL component commits listed in the root support matrix.
Each run used the same container command
shape, `--disable-dynamic-vram` and `--disable-api-nodes`; target-specific device
mappings are omitted from the abbreviated command below:

```bash
docker run ... OWL_IMAGE \
  --disable-dynamic-vram --listen 0.0.0.0 --port 8188 --disable-api-nodes
```

The API runner then submitted the same graph twice. Seed `123456789` was a
warm-up execution to load and initialize the models. Seed `123456790` was the
timed warm execution. The reported value is the difference between ComfyUI's
`execution_start` and `execution_success` timestamps, so it excludes cold model
loading and does not include the HTTP client's polling overhead.

## Results

| Device | OWL image and identity | Memory mode | Warm generation | Output SHA256 | Sample | Route and notes |
| --- | --- | --- | ---: | --- | --- | --- |
| B580 / `bmg` | `owl-xpu:comfyui-0.37.0-bmg-qwen21`<br>`sha256:a4fbf734c75103463bd460fe5f9361cf29ba44ec75ee407e951acb3eb95aa89f` | `--disable-dynamic-vram` | **4.664 s** | `97e9a51f5dda20f827b745fc44cb0a650f1b97c06108708f00870fd9a77100c3` | [PNG](assets/zimage-turbo-int8-owl-b580.png) | CUTE attention and INT8 FFN paths completed with resident weights. |
| A770 / `dg2` | `owl-xpu:comfyui-0.37.0-dg2-qwen21`<br>`sha256:1762c8745dce5a68a3957d06016886633a155bd8055d564f8428c531f507be20` | `--disable-dynamic-vram` | **7.987 s** | `1b9eb31a84847e65db6a07a99c44bf3d5665c4abf5691bb6fdd13a06370a73f8` | [PNG](assets/zimage-turbo-int8-owl-dg2.png) | Current DG2 core-only profile. CuTe/LGRF is absent by design, so attention uses PyTorch SDPA; the INT8 FFN adapter completed. |
| PTL-H / Arc B390 | `owl-xpu:comfyui-0.37.0-ptl-h-qwen21`<br>`sha256:7e0fd3ad08b35127483ace91fa91db39a1c7a3209ac3d12cf250ebea706e3a07` | `--disable-dynamic-vram` | **12.703 s** | `e2e6d134aa89272c4921bdc4567ed66736dcb551135da9052cd2a85f61030a0f` | [PNG](assets/zimage-turbo-int8-owl-ptl-h.png) | Resident weights, CUTE attention and fused INT8 FFN adapters completed without an execution error. |

These are functional warm-execution records, not a cross-device performance
benchmark. All three runs used resident weights with DynamicVRAM disabled; the
target packages still intentionally select different attention backends.

## Generated examples

### B580

![Z Image Turbo INT8 OWL example on B580](assets/zimage-turbo-int8-owl-b580.png)

### DG2

![Z Image Turbo INT8 OWL example on DG2](assets/zimage-turbo-int8-owl-dg2.png)

### PTL-H

![Z Image Turbo INT8 OWL example on PTL-H](assets/zimage-turbo-int8-owl-ptl-h.png)

## DynamicVRAM policy

The current default recommendation is to keep DynamicVRAM disabled for ordinary
image-generation workflows when the resident model fits. This avoids introducing
allocator/offload behavior into the normal path, and all three examples above
completed with DynamicVRAM disabled. For workflows with materially larger memory
pressure, such as MiniMax H3, enable DynamicVRAM explicitly and validate that
workflow on the target device. The earlier B580 DynamicVRAM attempt in the
0.35.0 validation hit an AIMDO VBAR fault; the current resident,
DynamicVRAM-off path succeeds.
