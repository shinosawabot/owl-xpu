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
`27e651c61e8f9773c1337118e67d1b188d80a2830d4a06a585ab7d24e4d7b604`. It uses
the same graph settings and model filenames as the catalog graph; only the text
prompt differs. Its exact prompt, package identities, warm execution method and
sample images are recorded in the [OWL status record](../blogs/2026-09-21-zimage-turbo-int8-owl-status.md).

The Qwen Image 2.1 OWL workflow has SHA256
`df566889cca5a3dd54637a9701e33cc4adeeeedddd8f5ed1e51a89795136e9a0`. It uses
the official INT8 filenames `qwen_image_2.1_int8_convrot.safetensors`,
`qwen3vl_8b_int8_convrot.safetensors` and `qwen_image_2.1_vae_bf16.safetensors`.
The graph fixes a 1024×1024 batch-1 latent, Euler/simple sampling with 25 steps,
CFG 1 and seed `123456789`; the exact prompt, package identities, warm execution
method and sample images are recorded in the [Qwen Image 2.1 status record](../blogs/2026-09-21-qwen-image-2.1-int8-owl-status.md).

When changing a graph, preserve the old file when it represents an accepted
contract or add a new filename. Re-run the affected target, calculate the new
SHA256, and update the associated receipt and application record together.
