# Linux development packaging

For installation and compilation starting from a clean OMIX base, use the
[container recipe](omix-container.md) and its [validation report](omix-validation.md).
The instructions below cover enhancement-only builds in an existing toolchain.

The BMG profile is `packaging/profiles/bmg-torch213.json`: Torch
`2.13.0+xpu`, oneDNN packages `2026.0.0`, target `bmg`, and sycl-tla commit
`2fc09973bfdf15755090fcb0e3b6ad236408a992`. The DG2 profile is
`packaging/profiles/dg2-torch213.json`; it selects the same Torch/oneDNN ABI,
sets `xpu_target` to `dg2`, and sets `require_cute` to `false` because DG2 is a
core-only build. The PTL-H profile is
`packaging/profiles/ptl-h-torch213.json`; it selects the same Torch/oneDNN ABI,
sets `xpu_target` to `ptl-h`, and requires CuTe. BMG and PTL-H therefore use
the pinned sycl-tla checkout; DG2 intentionally does not. Use a prepared
oneAPI development environment; the initial deployment used compiler 2026.1.0.
Build inputs include
Python development headers, Git, a C compiler, `icpx`, Level Zero development
libraries, Unified Runtime headers, and Python build tools from the component
`pyproject.toml` files (including `setuptools-scm` for AIMDO).

The packager does not install or change the host toolchain. Source the oneAPI
environment before invoking it, and use the Python interpreter belonging to the
matching Torch XPU environment. Installed runtime packages and driver support
still require their own validation.

```bash
source /opt/intel/oneapi/setvars.sh
python packaging/build.py check
python packaging/build.py plan
python packaging/build.py build \
  --profile packaging/profiles/bmg-torch213.json \
  --sycl-tla /path/to/pinned/sycl-tla \
  --output dist/bmg-torch213
```

DG2 does not require `--sycl-tla` for its core-only build:

```bash
python packaging/build.py build \
  --profile packaging/profiles/dg2-torch213.json \
  --output dist/dg2-torch213
```

PTL-H uses the same explicit profile shape as BMG and requires the pinned
sycl-tla checkout:

```bash
python packaging/build.py build \
  --profile packaging/profiles/ptl-h-torch213.json \
  --sycl-tla /path/to/pinned/sycl-tla \
  --output dist/ptl-h-torch213
```

`--output` must name a new directory. Existing results are never overwritten.
Use `--components kernels kitchen aimdo comfyui` to select the required subset
(all four are the default). A custom-node-only archive needs no Torch:

```bash
python3 packaging/build.py build --components comfyui --output dist/node-only
```

## Build and artifact ownership

1. Read committed component gitlinks; reject dirty or missing inputs.
2. Check the selected Torch version and, for kernels, oneDNN and sycl-tla identity.
3. Create fresh build checkouts of the selected pinned components under `sources/`.
4. Invoke the kernel's existing wheel builder, Kitchen's wheel and provider
   builders, and AIMDO's Linux native, wheel and provider builders as selected.
5. Archive the pinned ComfyUI integration source with its custom-node directory.
6. Recheck source identity and write an artifact SHA256 manifest.

```text
<output>/
  build-plan.json             source pins, selected profile and components
  manifest.json               completed artifacts and SHA256 values
  wheels/kernels/*.whl        installable omni_xpu_kernel wheel
  wheels/kitchen/*.whl        co-installable Kitchen XPU provider
  wheels/aimdo/*.whl          co-installable AIMDO XPU provider
  ComfyUI_OmniXPU.zip         custom-node source archive
  intermediate/              canonical XPU source wheels used by provider builders
  sources/                   isolated build trees; not runtime deliverables
  *.log                      complete command/build output
```

The repository-only `docs/`, `workflows/` and `blogs/` directories are not
artifact inputs. They are used to explain, reproduce and record validation, but
they are excluded from every wheel, provider package, `ComfyUI_OmniXPU.zip`
archive and final OMIX runtime image. The container build stage may read the
committed source snapshot to obtain pins; the runtime stage copies only the
official ComfyUI checkout, generated package artifacts and the required
launcher/check scripts.

Only selected components produce artifacts. `manifest.json` exists only after
all selected phases finish successfully. Failed builds retain their plan and
logs; retry with a new output directory. Packaging does not run GPU kernels or
claim correctness/performance acceptance.

## Installation into an existing ComfyUI environment

Keep ComfyUI's official Kitchen/AIMDO packages installed. Install the matching
native kernel wheel and the provider wheels from `wheels/` with `--no-deps`
after checking their Torch/ABI/target compatibility. Do **not** install the XPU
canonical wheels under `intermediate/` over the official packages.

Extract `ComfyUI_OmniXPU.zip` into ComfyUI's `custom_nodes` directory. The package
is an adapter, not a full ComfyUI application or image. Normal prestartup owns
provider selection. AIMDO native-hook activation has additional explicit
DynamicVRAM/preload prerequisites documented by its submodule; installing wheels
alone does not satisfy those gates.

There is no wheel registry upload, image publication, model download, or automatic
remote update in this packaging command.
