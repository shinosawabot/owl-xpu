# Build and validate OWL from OMIX

The current installation, compilation and verification scripts target **Ubuntu
x86-64**. The OMIX container is based on **Ubuntu 24.04**; the host used for
validation runs **Ubuntu 24.10**. The recipe uses Ubuntu/Intel apt repositories,
Bash and Linux `/dev/dri` device access. Other Linux distributions, Windows and
macOS are outside the currently validated environment.

This recipe starts with the official OMIX development base, creates its own
Python environment, compiles oneDNN and all OWL native components, and installs
the resulting enhancement bundle into the current official ComfyUI gitlink
(currently v0.37.0). It does not use
`omni-local:kernel-dev` or copy its prebuilt libraries.

The first complete clean-build result, using the earlier v0.35.0 pin, is
recorded in the [historical validation report](omix-validation.md).
For other OS/device combinations and independent ComfyUI upgrades, see the
[platform matrix](platform-validation.md). A new host version is recorded from
its committed submodule source; it is not automatically marked validated.

## Inputs and upstream provenance

The stable dependency stages and oneDNN patch in
`packaging/container/Dockerfile` are adapted from
`intel/llm-scaler@38d9a3dbbfecd3a5293a8acd75efef54f9bb3719`, specifically
`omni/docker/Dockerfile` and
`omni/patches/onednn-v3.11.2-enable-bf16-int4-dequantization.patch`.
The retained files carry upstream Apache-2.0 attribution. Startup follows the
provider preload and DynamicVRAM ordering in `omni/entrypoints/start_comfyui.sh`.

| Input | Pin |
| --- | --- |
| OMIX | `intel/omix:0.3.0-devel-ubuntu24.04@sha256:53e2c4503beeea4aff906dea180933be672449bcf04eb38df3d89622a1cd0967` |
| Python | 3.12 |
| Torch / torchvision / torchaudio | `2.13.0+xpu` / `0.28.0+xpu` / `2.11.0+xpu` |
| oneDNN Python packages | `2026.0.0` |
| oneDNN compiled source | `03c022d3ffdcee958cfacbe720048e725fdf644c` |
| oneDNN patch SHA256 | `0a7afff4134f115b4bc53f46301ca3d62b1c11dc02e32c64635c469769fcdaeb` |
| sycl-tla headers | `2fc09973bfdf15755090fcb0e3b6ad236408a992` |
| Official ComfyUI | current gitlink `73c9bad4d21e7addbe1d13bc92eee0f1431b017d` (`v0.37.0`) |
| Official Kitchen / AIMDO | `0.2.33` / `0.5.3` |
| Enhancement sources | Four committed OWL gitlinks, recorded in the bundle manifest |

System packages and unconstrained transitive Python dependencies still resolve
from their repositories at build time. The image records `runtime-freeze.txt`;
this is a repeatable procedure with pinned principal inputs, **not a claim of
bit-for-bit reproducibility**. Do not upgrade just one ABI-sensitive dependency
without rebuilding and revalidating the combination.

## Host prerequisites and build

Use an Ubuntu x86-64 host, Docker with BuildKit support, Python 3, Git, and network access
to the Ubuntu/Intel repositories, PyPI, PyTorch's XPU index and public GitHub.
Budget substantial disk space (the development toolchain image is large) and
RAM for eight compiler jobs. No host Torch, oneAPI, Python venv or GPU access is
needed during the image build. The host needs a functioning Intel GPU driver
and `/dev/dri` only for runtime verification.

```bash
git clone https://github.com/shinosawabot/owl-xpu.git
cd owl-xpu
git submodule update --init
python3 packaging/build.py check
python3 packaging/container/build_image.py \
  --no-cache --work-dir /absolute/path/to/new-build-directory \
  --tag owl-xpu:comfyui-0.37.0-bmg
```

Commit intended OWL changes before invoking the build: dirty source trees and
uncommitted gitlinks are rejected. The helper clones committed sources locally
into an isolated context; it does not copy `~/.git-credentials`, host venvs,
previous build outputs or global Git configuration. All required submodules must
be initialized on the host first. The Docker build receives no GitHub token.
`http_proxy`, `https_proxy` and `no_proxy`, if present, are forwarded as Docker's
standard proxy build arguments. They are not written as image `ENV` settings.

The new work directory retains `context/`, `build.log`, and, after success,
`image-inspect.json`. Monitor the build with `tail -f <work-dir>/build.log`.
Use a new work directory on each attempt; failed attempts remain inspectable.
Omit `--no-cache` for subsequent incremental builds. Download caches may be reused
even with `--no-cache`; the installation and compilation stages still execute.

## Build stages and package boundaries

1. Install OS dependencies in the digest-pinned OMIX base.
2. Create `/opt/venv` and install the exact Torch XPU and oneDNN package versions.
3. Verify and apply the upstream oneDNN patch; build its pinned source with
   oneAPI and record the installed DSO hash in `/llm/manifests/onednn-runtime.env`.
4. Fetch the pinned sycl-tla headers.
5. Invoke OWL's existing `packaging/build.py` for all four enhancement components.
   AIMDO's UR headers are resolved before compilation; its intermediate wheel
   uses `SETUPTOOLS_SCM_PRETEND_VERSION=0.5.3` so the provider accepts official
   AIMDO 0.5.3. Exact fork identity remains in the provider's source/hash manifest.
6. Copy official ComfyUI from its gitlink; install its requirements with constraints
   retaining the base Torch stack. Verify every bundle artifact hash, install
   the three enhancement wheels with `--no-deps`, and extract the custom-node ZIP.
7. Run `pip check` and save the resolved Python environment.

The repository's `docs/`, `workflows/` and `blogs/` trees are source-control
assets only. They are available while the build context is prepared so source
identity can be checked, but the final runtime stage does not copy them. The
image contains official ComfyUI, the generated enhancement artifacts, the
bundle manifest and the required runtime/check scripts; model files and
workflow outputs remain host-provided.

The runtime image inherits the development toolchain; slimming it is separate
work. It excludes optional third-party custom nodes, Manager and model weights.
The official Kitchen/AIMDO distributions remain installed alongside the provider
packages. Never install the intermediate canonical XPU wheels over them.

## Run and verify on this B580 host

Confirm physical PCI identity and Torch device mapping before using the example
`0000:03:00.0` / affinity `0` from this machine. The automated check runs Sysman
without `ZE_AFFINITY_MASK`, because masked Sysman enumeration misidentifies this
host's integrated GPU. It requires the B580 PCI ID, an empty device process list,
three idle-memory samples, available activity counters below threshold, and a
matching UUID from Torch under the requested affinity mask.

```bash
python3 packaging/container/verify_image.py \
  --image owl-xpu:comfyui-0.37.0-bmg \
  --pci 0000:03:00.0 --ze-affinity 0 \
  --output /absolute/path/to/new-validation-directory
```

Verification uses temporary containers with `--network=none` and no published
ports. It checks 36 FP32/FP16/BF16 native RMSNorm cases, forced Kitchen XPU INT8
matmul against an exact CPU reference, and AIMDO VBAR write/read, cache hit,
eviction and refault. It then runs official ComfyUI twice and submits the
model-free `OmniXPUStatus -> PreviewAny` graph through its HTTP API:

- DynamicVRAM enabled: Kitchen and AIMDO must both be active, with native-hook
  preload installed before Python startup.
- DynamicVRAM disabled: Kitchen must remain active and AIMDO must explicitly skip.

The output directory retains raw device admission, numerical checks, image
identity, server logs, API responses, diagnostic text and a final `result.json`.
Verification removes its temporary containers; evidence files remain. Files
written by containers may be owned by root on the host.

For interactive local use after validation:

```bash
docker run --rm --name owl-comfyui --device /dev/dri \
  -e ZE_AFFINITY_MASK=0 -p 127.0.0.1:8188:8188 \
  owl-xpu:comfyui-0.37.0-bmg
```

The entrypoint enables DynamicVRAM by default and prepares the verified AIMDO
preload. To disable it, append `--listen 0.0.0.0 --port 8188
--disable-api-nodes --disable-dynamic-vram`. Models, inputs and outputs can be
mounted into the corresponding directories under `/opt/ComfyUI`.

To export the enhancement artifacts and receipts without starting the app:

```bash
container_id=$(docker create owl-xpu:comfyui-0.37.0-bmg)
docker cp "$container_id:/opt/owl-bundle" ./owl-bundle
docker cp "$container_id:/llm/manifests/onednn-runtime.env" ./onednn-runtime.env
docker rm "$container_id"
```

Passing these checks establishes installation, device numerical smoke and
model-free ComfyUI integration on B580. It does not establish model quality,
end-to-end generation correctness, throughput/memory improvements or support
for other GPUs. AIMDO's XPU memory compiler remains unsupported; available
DynamicVRAM support concerns model-weight offloading. Conditional adapters may
skip when the official host lacks their target API.
