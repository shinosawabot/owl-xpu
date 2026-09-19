# Official ComfyUI 0.35.0 enhancement validation

This records the earlier prepared-development-image method. For the complete
installation and compilation from an OMIX base, use
[the current container recipe](omix-container.md). Official ComfyUI is now also
pinned as a fifth submodule for that complete image.

This recipe installs OWL's four pinned components into an **external, official
ComfyUI checkout**. ComfyUI itself is a test fixture, not vendored into OWL or
included in the enhancement ZIP. Runtime source ownership remains in submodules.

## Reproduce in the local development container

Use `omni-local:kernel-dev`, image ID
`sha256:0aeabe95ff3d2168e2f31dc4609db977bb549f7d70aac89542e8c24a6739b833`.
It provides Ubuntu 24.04, Python 3.12, Torch `2.13.0+xpu`, oneAPI 2026.1,
the patched oneDNN runtime, and the pinned `/llm/sycl-tla` checkout. This is a
locally built prerequisite image, not a published OWL release image.

Prepare a clean OWL checkout with its four direct submodules and clone
`https://github.com/Comfy-Org/ComfyUI.git` at tag `v0.35.0`. Verify that the latter
resolves to `40c4fcdf513a4523e39d54a9d391908af8df8171`.
Mount both checkouts and a writable artifact directory into dedicated containers.
Pass the host's proxy environment only when dependency downloads need it.

In the build container, from the clean OWL checkout:

```bash
python -m pip install setuptools-scm
# Required explicitly by the original OWL recipe; the updated packager detects it.
export UR_INCLUDE_DIR=/opt/intel/oneapi/compiler/latest/include/unified-runtime
MAX_JOBS=8 python packaging/build.py build \
  --sycl-tla /llm/sycl-tla --output /artifacts/bundle
```

In a separate runtime container based on the same image, from official ComfyUI:

```bash
python -m pip freeze > /artifacts/base-constraints.txt
python -m pip install -c /artifacts/base-constraints.txt -r requirements.txt
python -m pip install --no-deps --force-reinstall \
  /artifacts/bundle/wheels/kernels/*.whl \
  /artifacts/bundle/wheels/kitchen/*.whl \
  /artifacts/bundle/wheels/aimdo/*.whl
python -m pip check
python -m zipfile -e /artifacts/bundle/ComfyUI_OmniXPU.zip custom_nodes
python -m pip freeze > /artifacts/runtime-freeze.txt
```

Verify artifact SHA256 values against `bundle/manifest.json` before installing.
Keep official `comfy-kitchen==0.2.33` and `comfy-aimdo==0.5.3`; never install the
canonical XPU wheels from `intermediate/`. The separate provider distributions
own their private runtime files and are selected during prestartup.

## Device and startup checks

Expose `/dev/dri` only to the runtime container. For this host,
`ZE_AFFINITY_MASK=0` selects the Arc B580 at PCI `0000:03:00.0`. Verify physical
identity and device idleness first. The current OWL
[verification procedure](omix-container.md#run-and-verify-on-this-b580-host)
automates these checks using `packaging/container/device_check.py`. Run `xpu-smi`
**without** `ZE_AFFINITY_MASK`: the masked Sysman enumeration on this host
incorrectly reports the integrated GPU. Torch's masked identity must match the
unmasked physical-device mapping. This mapping is host-specific.

Run the following from ComfyUI in a fresh process. Native-hook preload must be
prepared before importing Torch:

```bash
export ZE_AFFINITY_MASK=0
export OMNI_IMAGE_XPU_TARGET=bmg
export OMNIXPU_PROVIDER_BOOTSTRAP=required
preload=$(python custom_nodes/ComfyUI_OmniXPU/runtime_bootstrap.py --allocator-preload-path)
test -n "$preload"
export AIMDO_XPU_ALLOCATOR_MODE=native_hook
export LD_PRELOAD="$preload${LD_PRELOAD:+:$LD_PRELOAD}"
python main.py --listen 127.0.0.1 --port 8188 \
  --enable-dynamic-vram --disable-api-nodes
```

From another process in the same container/network namespace:

```bash
python /owl/packaging/smoke_comfyui.py \
  --require-aimdo --output /artifacts/dynamic-vram-smoke
```

The check saves system versions, node registration, the submitted graph,
execution history and OmniXPU diagnostics. It requires both providers active,
Kitchen XPU available, the native kernel version present, and successful
execution of `OmniXPUStatus -> PreviewAny`.

For the DynamicVRAM-disabled comparison, start a **new** process with
`AIMDO_XPU_ALLOCATOR_MODE` and the AIMDO `LD_PRELOAD` unset,
`OMNIXPU_PROVIDER_BOOTSTRAP=auto`, and `--disable-dynamic-vram`. Run the same
smoke check without `--require-aimdo` into a new output directory. Kitchen should
remain active and AIMDO should report that DynamicVRAM is disabled.

These checks do not establish model-inference correctness, throughput gains,
memory savings, compatibility with additional custom nodes, or other GPU support.
