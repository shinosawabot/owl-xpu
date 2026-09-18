# OWL-XPU

**Omni Workload Layer Runtime for Intel XPU**

OWL-XPU records compatible source combinations and packaging methods for Intel
XPU components used with ComfyUI. It follows the component boundaries described
by [xiangyuT/owl-xpu](https://github.com/xiangyuT/owl-xpu), with each runtime
maintained in its own repository and integrated here as a Git submodule.

This repository contains **documentation and packaging only**. Native kernels,
operator dispatch, allocator implementations and ComfyUI adapters belong in
the component repositories. Gitlinks pin exact commits; no build follows a
moving branch or downloads an unpinned replacement implementation.

| Submodule | Responsibility |
| --- | --- |
| [components/omni_xpu_kernels](https://github.com/shinosawabot/omni_xpu_kernels) | Native Intel XPU kernels, Torch bindings and target capabilities |
| [components/comfy-kitchen](https://github.com/shinosawabot/comfy-kitchen) | Operator APIs, XPU dispatch, input constraints and fallback |
| [components/comfy-aimdo](https://github.com/shinosawabot/comfy-aimdo) | Memory management and allocator lifecycle |
| [components/ComfyUI_OmniXPU](https://github.com/shinosawabot/ComfyUI_OmniXPU) | Provider selection and thin ComfyUI call-site adapters |

## Checkout

All five repositories are private; the authenticated account needs read access
to the superproject and all four component repositories.

```bash
git clone https://github.com/shinosawabot/owl-xpu.git
cd owl-xpu
git submodule update --init
python3 packaging/build.py check
python3 packaging/build.py plan
```

Initialization intentionally covers the four direct submodules. Kitchen retains
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

## Status

This is the initial submodule-based assembly and a BMG/Torch 2.13 development
packaging recipe. Packaging success does not establish a validated combined
runtime, installable full ComfyUI image, workflow benefit or support for another
device. DG2/A770 and LNL remain directions inherited from the reference design;
each requires its own implementation and device validation.

Architecture reference: `xiangyuT/owl-xpu@7ecf3402d87381aa7f8fb608840c1c6facd3695d`.
Measurement/evidence reference:
`xiangyuT/omni-xpu-kernel-tuning@c1a22c362e162b69dc3e3a628a02a6494bed9a15`.
The original reference history is retained. Component licenses and attribution
remain in each submodule; the root Apache-2.0 license covers this assembly's new
documentation and packaging code.
