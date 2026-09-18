# Ownership and runtime boundaries

```text
OWL-XPU (documentation, gitlinks, packaging profiles and artifact manifests)
  +-- ComfyUI_OmniXPU: prestartup selection and ComfyUI-specific adapters
  +-- comfy-kitchen: common operator interfaces and per-call dispatch
  +-- comfy-aimdo: allocator and model-weight lifecycle
  +-- omni_xpu_kernels: native operators, bindings and device capabilities
```

ComfyUI uses native kernels through Kitchen or a dedicated adapter. Native
kernels remain independent of ComfyUI, Kitchen and AIMDO. Generic operator
dispatch belongs to Kitchen; memory lifecycle belongs to AIMDO. The integration
node must not duplicate Kitchen registrations or replace workflow semantics.

Official `comfy-kitchen` and `comfy-aimdo` distributions coexist with the optional
`comfy-kitchen-xpu-runtime` and `comfy-aimdo-xpu-runtime` providers. Provider wheels
own private vendor paths rather than overwriting official package files.
ComfyUI prestartup selects one canonical runtime per namespace after compatibility
checks. Kitchen and AIMDO activation remain independent; AIMDO also requires
explicit DynamicVRAM enablement and its allocator-lifecycle admission.

OWL does not implement this behavior. It invokes the component packaging entry
points and records their exact gitlink revisions. The `omni_xpu_kernel` Python
import/distribution name remains unchanged despite the repository's plural name.

The superproject may track only root metadata, `docs/`, `packaging/` and component
gitlinks. It does not vendor runtime source, local wheel/DSO files, models or
machine-specific device ordinals. `packaging/build.py check` enforces this layout.
Gitlinks are the only source-version authority; build manifests derive their
component revisions from them rather than maintaining a second lock file.

The existing ComfyUI host application and compiler/toolchain are prerequisites,
not bundled applications in this initial recipe. If a future package includes
another runtime project, add it as a reviewed, pinned submodule. sycl-tla is an
external build-time header checkout whose required commit is specified in the
packaging profile and verified before a kernel build.

The tuning repository owns measurement contracts and evidence. Reusing a build
target or a package version does not transfer roofline ceilings, numerical
acceptance or workflow support across devices.
