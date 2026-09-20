# Z Image Turbo INT8 OWL status

This record runs one OWL-focused Z Image Turbo INT8 API graph on the three
currently validated Linux targets. The workflow, prompt, model files and
measurement protocol are shared; only the target image and the memory mode
needed by the device are different.

## Workflow and prompt

- Workflow: [`zimage-turbo-int8-owl-api.json`](../workflows/zimage-turbo-int8-owl-api.json)
- Workflow SHA256: `27e651c61e8f9773c1337118e67d1b188d80a2830d4a06a585ab7d24e4d7b604`
- Resolution: 1024×1024, batch 1
- Sampler: `res_multistep`, 8 steps, CFG 1
- Models: `z_image_turbo_int8_convrot.safetensors`, `qwen_3_4b.safetensors` and `ae.safetensors`

The exact prompt is:

> A high-detail editorial illustration of an OWL-XPU optimization laboratory: a wise white owl perched on a glowing Intel XPU board, surrounded by holographic ComfyUI workflow nodes, kernel traces, and a clean open-source engineering notebook, blue and gold light, precise technical atmosphere, cinematic composition

The model files were the same on all three hosts:

| File | Size | SHA256 |
| --- | ---: | --- |
| `z_image_turbo_int8_convrot.safetensors` | 6,201,001,296 bytes | `be517ebd47c912a5626a588e1aeea43e6be4a43c0cdcd2b48a2a780d9f358635` |
| `qwen_3_4b.safetensors` | 8,044,982,048 bytes | `6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a` |
| `ae.safetensors` | 335,304,388 bytes | `afc8e28272cd15db3919bacdb6918ce9c1ed22e96cb12c4d5ed0fba823529e38` |

The package assembly used ComfyUI v0.35.0 and the pinned OWL component commits
listed in the root support matrix. Each run used the same container command
shape and `--disable-api-nodes`; target-specific device mappings are omitted
from the abbreviated command below:

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
| B580 / `bmg` | `owl-xpu:comfyui-0.35.0-bmg`<br>`sha256:63bff5fa9816c993ccbaaaeeb480aae44e8082b2e39b5b6bb7677abfe7603a15` | `--disable-dynamic-vram --lowvram --cpu-vae` | **13.775 s** | `d3d96a571c012c56d01211cfb8dcfdd4cd1f45cd25aa36597a99882a65d7f797` | [PNG](assets/zimage-turbo-int8-owl-b580.png) | CUTE attention and INT8 FFN paths completed. The default DynamicVRAM attempt hit an AIMDO `vbar_fault`; the low-memory, DynamicVRAM-off path completed. |
| A770 / `dg2` | `owl-xpu:comfyui-0.35.0-dg2-current`<br>`sha256:a1242bb72c1275bd24905a0673420a61b2b4b23eed3f0361c58fbc283ea4aac9` | `--disable-dynamic-vram` | **7.810 s** | `f8713de8c83f69da063d95c82df6e97afc1a2bddcab39d21ca54ea48a6901aed` | [PNG](assets/zimage-turbo-int8-owl-dg2.png) | Current canonical DG2 core-only image. CuTe/LGRF is absent by design, so attention uses PyTorch SDPA; the INT8 FFN adapter completed. |
| PTL-H / Arc B390 | `owl-xpu:comfyui-0.35.0-ptl-h`<br>`sha256:951b8b14b47cc0e621dedd68836b71f3bd84df3f99e45821fbaff5a4b3703adb` | `--disable-dynamic-vram` | **12.412 s** | `9a10a6b318e86e6841af8c3519849317b3edd3059dab5199b7832f3f3c231db9` | [PNG](assets/zimage-turbo-int8-owl-ptl-h.png) | Resident weights, CUTE attention and fused INT8 FFN adapters completed without an execution error. |

These are functional warm-execution records, not a cross-device performance
benchmark. B580 used ComfyUI low-memory mode because its full-resident path was
not reliable in this workflow; the target packages also intentionally select
different attention backends.

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
workflow on the target device. The B580 result is a concrete reason to keep this
choice per workflow and per target: its default DynamicVRAM attempt failed with
an AIMDO VBAR fault, while the explicit low-memory path succeeded.
