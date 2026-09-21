# Verified ComfyUI workflows

This directory contains ComfyUI API-format graphs that have completed an OWL
package validation. They are reusable inputs for device checks and practical
application runs. Model weights, generated media, server logs and machine-local
paths stay outside this directory; small generated examples belong with their
application record under [`blogs/`](../blogs/).

These files are repository assets, not runtime package contents. The OWL wheel,
provider wheels, custom-node ZIP and OMIX runtime image do not copy this
directory. A workflow becomes canonical only after its exact JSON hash, model
identities, package pins, target device and result are recorded in a validation
receipt or in [`blogs/`](../blogs/).

## Catalog

| Workflow | Purpose | Validated targets | Records |
| --- | --- | --- | --- |
| [`zimage-turbo-int8-convrot-api.json`](zimage-turbo-int8-convrot-api.json) | 1024×1024 Z Image Turbo INT8 ConvRot image generation | DG2 core-only and PTL-H | [DG2 receipt](../docs/dg2-validation.md), [PTL-H receipt](../docs/ptl-h-validation.md), [DG2 record](../blogs/2026-09-21-zimage-turbo-int8-dg2.md), [PTL-H record](../blogs/2026-09-21-zimage-turbo-int8-ptl-h.md) |
| [`zimage-turbo-int8-owl-api.json`](zimage-turbo-int8-owl-api.json) | The same 1024×1024 Z Image Turbo INT8 graph with an OWL-XPU engineering prompt | B580, DG2 core-only and PTL-H | [OWL status record](../blogs/2026-09-21-zimage-turbo-int8-owl-status.md) |
| [`qwen-image-2.1-int8-owl-api.json`](qwen-image-2.1-int8-owl-api.json) | 1024×1024 Qwen Image 2.1 INT8 generation with the OWL-XPU engineering prompt | B580, DG2 core-only and PTL-H | [OWL status record](../blogs/2026-09-21-qwen-image-2.1-int8-owl-status.md) |
| [`minimax-h3-vsa-4step-owl-api.json`](minimax-h3-vsa-4step-owl-api.json) | 1344×768 MiniMax H3 VSA 4-step video generation with an OWL-XPU scene prompt | B580 / `bmg` and PTL-H / `ptl-h` | [OWL status record](../blogs/2026-09-21-minimax-h3-vsa-4step-owl-status.md) |

The catalog workflow has SHA256
`7fcd865a3cd5e2819ca7b520fe8c375567eec7d81227825e1984d741a128ac2e` and uses
these model filenames:

- `z_image_turbo_int8_convrot.safetensors`
- `qwen_3_4b.safetensors`
- `ae.safetensors`

The graph fixes a 1024×1024 batch-1 latent, CFG 1, `res_multistep` with 8
steps, seed `123456789`, and a deterministic prompt. The model files are
mounted from a ComfyUI model directory at run time; they are never checked into
this repository.

The OWL-focused variant has SHA256
`7896c25bfade693531e624734c463ed2e643c393f909aabf6bbf6103f609de25`. It uses
the same graph settings and model filenames as the catalog graph; only the text
prompt differs. Its exact prompt, package identities, warm execution method and
sample images are recorded in the [OWL status record](../blogs/2026-09-21-zimage-turbo-int8-owl-status.md).

The Qwen Image 2.1 OWL workflow has SHA256
`c792789fb01f509465c733a99fb8646afb8adf10d821686c4e928edc851d2b97`. It uses
the official INT8 filenames `qwen_image_2.1_int8_convrot.safetensors`,
`qwen3vl_8b_int8_convrot.safetensors` and `qwen_image_2.1_vae_bf16.safetensors`.
The graph fixes a 1024×1024 batch-1 latent, Euler/simple sampling with 25 steps,
CFG 1 and seed `123456789`; the exact prompt, package identities, warm execution
method and sample images are recorded in the [Qwen Image 2.1 status record](../blogs/2026-09-21-qwen-image-2.1-int8-owl-status.md).

The MiniMax H3 VSA 4-step OWL workflow has SHA256
`e90ce64fd8a8d79d2b971ea8f6f7a3f81dabde5ca20c7de121b740f61bca554d`. It fixes a
1344×768, 5-second, 124-frame graph with Euler/simple sampling, four steps,
VSA selection at 10 percent and the H3 video/audio sigma shifts. The graph was
validated on B580 and PTL-H with DynamicVRAM enabled. The PTL-H record includes
the unavailable native segmented H3 RMS and complete Sol VSA routes as explicit
limitations; its exact prompt, model identities, package pins and representative
frames are recorded in the [MiniMax H3 status record](../blogs/2026-09-21-minimax-h3-vsa-4step-owl-status.md).

When changing a graph, preserve the old file when it represents an accepted
contract or add a new filename. Re-run the affected target, calculate the new
SHA256, and update the associated receipt and application record together.
