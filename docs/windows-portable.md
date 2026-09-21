# Windows Intel portable enhancement and ComfyUI upgrades

This is the Windows deployment design and acceptance contract. OWL currently
ships Ubuntu build/verification scripts; **a Windows OWL installer and a
Windows device validation receipt are not yet available**. See the
[platform matrix](platform-validation.md) for component-level implementation gaps.

## Portable enhancement flow

1. Obtain the Intel archive from the official
   [ComfyUI releases](https://github.com/Comfy-Org/ComfyUI/releases), not a CUDA
   portable. Record its immutable release/asset identity, archive SHA256 and
   extracted ComfyUI version/commit. Work in a separate extracted directory.
2. Inventory `python_embeded/python.exe`: Python ABI, Torch XPU version, installed
   official Kitchen/AIMDO versions, Windows build, driver, GPU PCI identity and
   available XPU devices. Establish that the unmodified upstream portable starts.
3. Select or build the matching Windows kernel and two provider wheels from
   OWL's component gitlinks. Build native extensions in a separate Windows
   development environment, not inside the portable runtime. The existing
   [kernel Windows guide](../components/omni_xpu_kernels/WHL_BUILD_INSTALL.md)
   describes a Python 3.13/Torch 2.13 BMG contract scoped to B70; it is not proof
   that a newly downloaded portable or B580/PTL/A770/LNL matches that contract.
4. Verify artifact hashes and compatibility before installing with the embedded
   interpreter. Preserve the official Kitchen/AIMDO packages; install the
   separately named XPU providers and extract OmniXPU under `ComfyUI/custom_nodes`.
   Do not use Linux wheels, retag wheels, or silently upgrade/downgrade Torch to
   make an incompatible bundle install.
5. Prepare the Windows AIMDO native-hook/DLL lifecycle using the component's
   Windows implementation and Detours build requirements. The Linux
   `LD_PRELOAD` launcher is not a Windows launcher. Missing hook prerequisites
   must be reported before activating DynamicVRAM.
6. Validate each physical GPU separately: device identity, native numerical
   cases, forced Kitchen dispatch, AIMDO residency and both DynamicVRAM modes,
   adapter status and a diagnostic graph. Record an explicit receipt before
   marking the OS/device combination validated.

Upstream's Intel archive is an environment distribution, not an OWL compatibility
certificate. Its Python, Torch and bundled dependencies can change between
releases. OWL must inventory the actual archive rather than assuming the Ubuntu
Python 3.12 ABI or the Windows component guide's ABI applies to every portable.

## Upgrade acceptance contract

The same contract applies to Ubuntu candidate images and Windows candidate
portable directories:

| Boundary | Compatible upgrade behavior | If the boundary changed |
| --- | --- | --- |
| ComfyUI core version/commit | Update host identity and keep enhancement source pins | Re-run adapter/interface checks; do not infer compatibility from version ordering |
| Adapter call sites, signatures, tensor/layout semantics and prestartup order | Existing adapters and providers continue to work | Fix the owning adapter; do not label an unexpected skip as an upgrade pass |
| Python ABI, Torch XPU, oneDNN/native ABI and GPU AOT target | Reuse matching native wheels | Rebuild matching artifacts and revalidate; never retag old binaries |
| Official Kitchen/AIMDO package versions | Keep official packages and activate matching providers | Validate the new API and publish matching provider compatibility metadata/artifacts; current bootstrap uses exact version gates |
| Provider activation and allocator ownership | Kitchen dispatch and AIMDO lifecycle remain correct | Report the incompatible component; never attempt unsafe rollback after native allocator state becomes live |

A routine ComfyUI core upgrade **with unchanged adapter and component contracts**
should not require changing kernel, Kitchen or AIMDO source. If dependency
requirements themselves change, that is a separate compatibility change even
when the adapter Python code is unchanged. Existing exact-version bootstrap
checks remain in force; do not broaden accepted versions without evidence or
silently replace upstream packages to bypass them.

Required release checks for each upgrade:

- Compare the adapter inventory before/after. Previously applied adapters must
  remain applied; expected conditional skips must stay explicitly documented.
  A successful diagnostic node alone does not prove all adapter call sites work.
- Run affected adapter regression tests and representative numerical/workflow
  cases exercising those call sites, plus kernel/Kitchen/AIMDO checks on the
  target OS and GPU. Include upstream startup without enhancements as a baseline.
- Verify official package files remain independently owned, both DynamicVRAM
  modes behave as expected, and no provider was silently disabled or replaced.
- Record the old/new host identities, environment versions, unchanged or updated
  component pins, artifacts and test results. Promote the candidate only after
  these pass; retain the previous image/portable for rollback.

The existing automated OWL smoke check covers provider registration and the
model-free diagnostic graph. It does not yet automate the complete adapter
inventory comparison or model workflow upgrade suite. The historical 0.35.0/B580
clean-image receipt remains the clean-image baseline; ComfyUI 0.37.0 is covered
by current Linux workflow records, and no Windows portable upgrade has been
accepted.
