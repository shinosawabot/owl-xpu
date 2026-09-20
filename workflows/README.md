# Verified ComfyUI workflows

This directory contains ComfyUI API-format graphs that have completed an OWL
package validation. They are reusable inputs for device checks and practical
application runs. Model weights, generated media, server logs and machine-local
paths stay outside the repository.

These files are repository assets, not runtime package contents. The OWL wheel,
provider wheels, custom-node ZIP and OMIX runtime image do not copy this
directory. A workflow becomes canonical only after its exact JSON hash, model
identities, package pins, target device and result are recorded in a validation
receipt or in [`blogs/`](../blogs/).

## Catalog

| Workflow | Purpose | Validated targets | Records |
| --- | --- | --- | --- |
| [`zimage-turbo-int8-convrot-api.json`](zimage-turbo-int8-convrot-api.json) | 1024×1024 Z Image Turbo INT8 ConvRot image generation | DG2 core-only and PTL-H | [DG2 receipt](../docs/dg2-validation.md), [PTL-H receipt](../docs/ptl-h-validation.md), [DG2 record](../blogs/2026-09-21-zimage-turbo-int8-dg2.md), [PTL-H record](../blogs/2026-09-21-zimage-turbo-int8-ptl-h.md) |

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

When changing a graph, preserve the old file when it represents an accepted
contract or add a new filename. Re-run the affected target, calculate the new
SHA256, and update the associated receipt and application record together.
