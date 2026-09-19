# OWL-XPU

**Omni Workload Layer Runtime for Intel XPU**

OWL-XPU records compatible source combinations and packaging methods for Intel
XPU components used with ComfyUI. Each runtime is maintained in its own
repository and integrated here as a Git submodule. The
[architecture document](docs/architecture.md) defines component responsibilities.

This repository contains **documentation and packaging only**. Native kernels,
operator dispatch, allocator implementations and ComfyUI adapters belong in
the component repositories. Gitlinks pin exact commits; no build follows a
moving branch or downloads an unpinned replacement implementation.

| Submodule | Responsibility |
| --- | --- |
| [components/ComfyUI](https://github.com/Comfy-Org/ComfyUI) | Official ComfyUI host, pinned to v0.35.0 |
| [components/omni_xpu_kernels](https://github.com/shinosawabot/omni_xpu_kernels) | Native Intel XPU kernels, Torch bindings and target capabilities |
| [components/comfy-kitchen](https://github.com/shinosawabot/comfy-kitchen) | Operator APIs, XPU dispatch, input constraints and fallback |
| [components/comfy-aimdo](https://github.com/shinosawabot/comfy-aimdo) | Memory management and allocator lifecycle |
| [components/ComfyUI_OmniXPU](https://github.com/shinosawabot/ComfyUI_OmniXPU) | Provider selection and thin ComfyUI call-site adapters |

## Support and validation

Ubuntu uses the OMIX image build. The planned Windows route enhances the
upstream Intel portable; an OWL Windows installer is not yet available.
**Only Ubuntu + B580 with ComfyUI 0.35.0 has passed OWL device validation.**
The table describes the current committed component pins (updated 2026-09-19).

Legend:

- **V**: OWL device checks passed, limited to the scope in the linked receipt.
- **C**: component code/build path exists; this OS/device combination is unvalidated.
- **G**: provider metadata admits the target; this alone does not prove functionality.
- **B**: missing target support in the current pins blocks the complete enhancement.

| OS | GPU / target | omni_xpu_kernels | Kitchen XPU provider | AIMDO XPU provider | ComfyUI_OmniXPU adapters | OWL package / combined validation |
| --- | --- | --- | --- | --- | --- | --- |
| Ubuntu | B580 / `bmg` | **V**, focused native cases; B580 policy remains experimental | **V**, 40 capabilities registered; INT8 reference case tested | **V**, native hook and VBAR lifecycle | **V**, registration and diagnostic graph; conditional adapters can skip | **V**, OMIX build and both DynamicVRAM modes |
| Ubuntu | A770 / `dg2` | **B**, no `dg2` build target in current kernel pin | **G**, `dg2` accepted but requires a matching companion kernel | **G**, `dg2` manifest eligibility; device untested | **C**, generic XPU discovery; incomplete companion stack | Blocked on DG2 kernel path; no profile or receipt |
| Ubuntu | PTL / `ptl-h` only | **C**, explicit `ptl-h` build path | **G**, `ptl-h` accepted | **G**, `ptl-h` accepted | **C**, target-dependent routes; device untested | No PTL OWL profile or receipt |
| Ubuntu | LNL | **B**, no `lnl` build target | **B**, no `lnl` provider target | **B**, no `lnl` provider target | **C**, generic XPU discovery is not LNL acceptance | Blocked on target integration; no receipt |
| Windows | B580 / `bmg` | **C**, Windows BMG build path; existing build guide is scoped to B70, not B580 acceptance | **G**, Windows + `bmg` manifest support | **C/G**, Windows native-hook/Detours code and `bmg` eligibility | **C**, Windows bootstrap path | Intel portable enhancement planned; no B580 Windows receipt |
| Windows | A770 / `dg2` | **B**, no `dg2` build target | **G**, Windows + `dg2`; matching kernel missing | **C/G**, Windows hook code and `dg2` eligibility | **C**, incomplete companion stack | Blocked on DG2 kernel path; no receipt |
| Windows | PTL / `ptl-h` only | **C**, core target path; Windows CuTe explicitly restricted to `bmg` | **G**, Windows + `ptl-h` | **C/G**, Windows hook code and `ptl-h` eligibility | **C**, device untested | Partial source path; no complete portable bundle or receipt |
| Windows | LNL | **B**, no `lnl` build target | **B**, no `lnl` provider target | **B**, no `lnl` provider target | **C**, generic XPU discovery is not LNL acceptance | Blocked on target integration; no receipt |


PTL covers only `ptl-h`. B580 kernel policy remains experimental; the validated
scope is focused numerical checks and model-free integration, not complete
model inference or performance acceptance. Windows BMG build code is not a
B580 Windows validation result.

See [component evidence and deployment details](docs/platform-validation.md),
the [Ubuntu/B580 validation report](docs/omix-validation.md), and the
[ComfyUI upgrade contract](docs/windows-portable.md#upgrade-acceptance-contract).

## Checkout

The OWL superproject and four enhancement repositories are private; the
authenticated account needs read access to them. Official ComfyUI is public.

```bash
git clone https://github.com/shinosawabot/owl-xpu.git
cd owl-xpu
git submodule update --init
python3 packaging/build.py check
python3 packaging/build.py plan
```

Initialization covers the five direct submodules. Kitchen retains
optional upstream CUDA third-party submodules, which its XPU-only packaging path
does not use. There is no need to download those for this recipe.

## Package

In a prepared Linux development environment with matching Torch XPU, oneAPI,
oneDNN and pinned sycl-tla headers:

```bash
python packaging/build.py build \
  --sycl-tla /path/to/pinned/sycl-tla \
  --output dist/bmg-torch213
```

The result contains the native kernel wheel, separately packaged Kitchen/AIMDO
XPU provider wheels, a ComfyUI custom-node ZIP and a SHA256 manifest. Native builds
run in fresh source copies under the ignored output directory; the submodule
working trees remain unchanged. The command never uploads or publishes artifacts.

See [packaging instructions](docs/packaging.md),
[architecture](docs/architecture.md), and [updating components](docs/development.md).

## Build from clean OMIX

The current scripts target **Ubuntu x86-64**: the container uses Ubuntu 24.04,
and the validated host runs Ubuntu 24.10. Other host distributions, Windows and
macOS have not been validated with this recipe.

No preinstalled Omni kernel or existing development image is required. With
Docker and Python 3 on the host, from a clean checkout with all five direct submodules initialized:

```bash
python3 packaging/container/build_image.py \
  --no-cache --work-dir /absolute/path/to/new-build-directory
python3 packaging/container/verify_image.py \
  --pci 0000:03:00.0 --ze-affinity 0 \
  --output /absolute/path/to/new-validation-directory
```

The device arguments above describe the tested local B580; confirm them for your
host. See [the complete OMIX recipe](docs/omix-container.md) for prerequisites,
build stages and launch/export commands. The [clean-build validation report](docs/omix-validation.md) records the tested image, checks and limits.

## Status

See the [Ubuntu/Windows device and component matrix](docs/platform-validation.md)
for B580, A770, PTL and LNL. Ubuntu uses the OMIX build; the planned Windows
route enhances the official Intel portable. The
[upgrade contract](docs/windows-portable.md#upgrade-acceptance-contract) requires
compatible ComfyUI upgrades to preserve adapter and component behavior.

This is a submodule-based assembly and a BMG/Torch 2.13 development packaging
recipe. Packaging and model-free smoke checks do not establish model inference
correctness, workflow benefit or support for another device.
DG2/A770 and LNL remain future target directions;
each requires its own implementation and device validation.

Build and verification evidence is described in the
[validation report](docs/omix-validation.md).
Component licenses and attribution remain in each submodule; the root
Apache-2.0 license covers this assembly's new
documentation and packaging code.
