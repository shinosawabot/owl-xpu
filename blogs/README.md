# OWL-XPU workflow records

This directory holds practical records from running ComfyUI built from an OWL
package. Each record identifies the package profile, component revisions,
workflow hash, model files, device, observed route and known limitations. These
records describe actual application behavior; the support matrix and focused
receipts in [`docs/`](../docs/) remain the authority for validation status.

Blog records are repository documentation and are excluded from wheels,
provider packages, the `ComfyUI_OmniXPU.zip` custom-node archive and the final
OMIX runtime image. A record may include small generated sample images under
`assets/`; it must not contain model weights, credentials or machine-local logs.

## Records

| Date | Workflow | Target | Record |
| --- | --- | --- | --- |
| 2026-09-21 | Z Image Turbo INT8 ConvRot | DG2 / A770 | [Run record](2026-09-21-zimage-turbo-int8-dg2.md) |
| 2026-09-21 | Z Image Turbo INT8 ConvRot | PTL-H / Arc B390 | [Run record](2026-09-21-zimage-turbo-int8-ptl-h.md) |
| 2026-09-21 | Z Image Turbo INT8 OWL prompt | B580, DG2 / A770, PTL-H / Arc B390 | [Status record with sample images](2026-09-21-zimage-turbo-int8-owl-status.md) |
| 2026-09-21 | Qwen Image 2.1 INT8 OWL prompt | B580, DG2 / A770, PTL-H / Arc B390 | [Status record with sample images](2026-09-21-qwen-image-2.1-int8-owl-status.md) |

New records should link to a file under [`workflows/`](../workflows/), include
the exact package and model identities, and state whether DynamicVRAM and
resident weights were used. A workflow record must distinguish successful
execution from a performance or complete-model-support claim.
