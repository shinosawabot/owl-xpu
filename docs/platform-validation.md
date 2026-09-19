# Platform and component validation matrix

Updated 2026-09-19. This matrix describes the **committed OWL component pins**,
not every upstream implementation or Intel GPU supported by PyTorch. Only the
Ubuntu/B580 combination has an OWL device validation receipt. Hardware names
are mapped to build targets, not assumed interchangeable.

## Deployment routes

| OS | Base environment | OWL enhancement route | Current delivery status |
| --- | --- | --- | --- |
| Ubuntu x86-64 | Digest-pinned OMIX Ubuntu 24.04 image | Compile kernels and providers, install official ComfyUI from its gitlink, then install the enhancement bundle | Implemented and validated on an Ubuntu 24.10 host with B580 |
| Windows x64 | Official upstream Intel portable archive | Download and pin the upstream archive, inspect its embedded Python/Torch environment, then install matching Windows wheels and OmniXPU custom node into a separate copy | Planned OWL packaging route; component Windows code exists, but no OWL Windows installer or combined device receipt yet |

The official [ComfyUI README](https://github.com/Comfy-Org/ComfyUI#installing)
links the [Intel portable download](https://github.com/Comfy-Org/ComfyUI/releases/latest/download/ComfyUI_windows_portable_intel.7z).
That moving URL is for discovery. A validated Windows release must record the
release/asset identity, archive SHA256 and actual ComfyUI commit/version; it must
not treat `latest` as a compatibility lock. No Windows archive has yet been
selected or accepted by OWL. See [Windows enhancement and upgrade requirements](windows-portable.md).

## Validation status by OS and device

The canonical OS/device/component support matrix and its status legend are
shown on the [OWL project homepage](../README.md#support-and-validation).
This document provides the deployment details, evidence and upgrade criteria.

Validation outcomes can also be **❌ Validated — not supported**,
**⚠️ Validated — not recommended**, or **🔧 Validated — needs optimization**.
Use these only with a receipt identifying the OS/device, component pins,
environment, test scope and observed results. A confirmed functional blocker
belongs in the first category. A functioning combination with a documented
reason to avoid it belongs in the second. A functioning combination with
measured optimization work remaining belongs in the third; if those gaps also
make it unsuitable for the intended use, use “not recommended” and explain why.
Build-target gaps without a device test remain “missing target support / blocked.”
No existing row is reclassified merely by adding these status definitions.

PTL here means only the explicit `ptl-h` target in the pinned sources; no other
PTL SKU is covered. Do not reuse BMG wheels for LNL or DG2 by renaming or retagging
them. These gaps concern OWL's enhanced stack, not a claim that upstream ComfyUI
or plain Torch XPU cannot run on those devices.

## Evidence and component boundaries

The homepage separates **kernel core (non-CuTe)** from **CuTe / sycl-tla
extensions**. This is a validation boundary, not a new repository or wheel split:
the current kernel wheel contains both. The CuTe column covers
`omni_xpu_kernel.cute.cute_fmha_torch` and its FMHA/Sol-Attn paths; the non-CuTe
column covers the remaining native extensions, with only the stated cases
validated. Core RMSNorm and Kitchen INT8 checks do not validate CuTe attention.

The Ubuntu/B580 build produced a wheel containing the CuTe shared library, but
the linked OWL receipt does not include dedicated CuTe numerical/performance
acceptance. It therefore remains marked as built but device-unvalidated in that
column. Linux has `bmg` and `ptl-h` CuTe AOT paths; neither `dg2` nor `lnl` is
declared. Windows CuTe is opt-in (`OMNI_XPU_REQUIRE_CUTE=1`) and explicitly
restricted to `bmg`; a Windows core target path does not remove that restriction.
These source restrictions are not device-tested “validated — not supported”
outcomes. Changing a CuTe status requires its own target-specific evidence.

- [Kernel target metadata](../components/omni_xpu_kernels/omni_xpu_kernel/_version.py)
  lists `bmg` and `ptl-h`; [setup.py](../components/omni_xpu_kernels/setup.py)
  contains the Windows CuTe restriction. The
  [kernel policy](../components/omni_xpu_kernels/omni_xpu_kernel/policies/kernel-policy-v1.json)
  retains experimental B580 status.
- [Kitchen provider builder](../components/comfy-kitchen/packaging/xpu_runtime_provider/build_wheel.py)
  admits Linux/Windows and `bmg`, `ptl-h`, `dg2`. Capability/shape gates still apply.
- [AIMDO provider builder](../components/comfy-aimdo/packaging/xpu_runtime_provider/build_wheel.py)
  has the same platform/target metadata and defaults to native hook on both OSes.
  [Windows build scripts](../components/comfy-aimdo/scripts/build-windows-xpu.cmd)
  and Detours support are component implementation evidence, not OWL device acceptance.
- [Adapter bootstrap](../components/ComfyUI_OmniXPU/runtime_bootstrap.py) checks
  official package versions, exact Torch XPU version, platform, target and hashes.
  A generic XPU check cannot establish per-device operator support.
- [Ubuntu/B580 receipt](omix-validation.md) records 36 RMSNorm cases, a Kitchen
  INT8 case, AIMDO residency checks and model-free ComfyUI graph execution.

No matrix row establishes complete model inference correctness or performance
improvement. AIMDO's XPU memory compiler is unsupported; tested DynamicVRAM
functionality concerns allocator accounting and model-weight residency. Every
new OS/device row needs its own driver/runtime identity, wheel hashes, numerical
checks, provider diagnostics and upgrade regression results before being marked ✅ Validated.

## ComfyUI upgrade requirement

ComfyUI must be upgradeable independently of the four enhancement repositories.
If the adapter interfaces and component ABI/dependency contracts remain
compatible, retain the existing component pins and wheels. A ComfyUI version
number change alone must not force component source changes or disable them.

Ubuntu upgrades advance only the official ComfyUI gitlink first and build a
candidate image. Packaging reads the version from that pinned source, records
its version-file SHA256, and verifies that identity at installation. API smoke
checks derive their expected version from the selected host instead of fixing
all future builds to 0.35.0. The current *validated* version is still 0.35.0.

Windows upgrades replace the upstream portable base in a separate directory,
then reapply the compatible enhancement bundle. Keep the previous installation
until the candidate passes the upgrade checks. See the
[upgrade acceptance contract](windows-portable.md#upgrade-acceptance-contract)
for both operating systems. No automatic acceptance of arbitrary newer versions
or runtime ABI changes is implied.

### Validation of the version-handling change

On 2026-09-19, eight packaging-control tests passed, including synthetic host
version changes and version-file hashing. A custom-node-only package recorded
the selected host identity. An isolated installer fixture accepted the matching
0.35.0 host and rejected an altered version file before installation. The
updated verifier also passed the existing Ubuntu/B580 image's native/provider
checks and both DynamicVRAM diagnostic workflows.

These are regression checks for the packaging/version-handling change. The
synthetic version fixture is not a newer ComfyUI release test; the native image
was not rebuilt for another ComfyUI version. No additional matrix row becomes
validated as a result. Raw results are retained on the validation machine under
`omni-local/owl-upgrade-validation/`, `omni-local/owl-upgrade-installer/` and
`omni-local/owl-upgrade-node-only/`.
