# syntax=docker/dockerfile:1
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# ComfyUI-focused Omni development image.
#
# The default image intentionally excludes Xinference, SGLang/SGLDiffusion,
# and the disabled media/3D node bundle. Raylight's xDiT-based multi-XPU
# ComfyUI integration is not part of this image; this image targets one XPU.

ARG BASE_IMAGE=intel/omix:0.3.0-devel-ubuntu24.04@sha256:53e2c4503beeea4aff906dea180933be672449bcf04eb38df3d89622a1cd0967
ARG PYTHON_VERSION=3.12
ARG TORCH_VERSION=2.13.0+xpu
ARG TORCHVISION_VERSION=0.28.0+xpu
ARG TORCHAUDIO_VERSION=2.11.0+xpu
ARG ONEDNN_VERSION=2026.0.0
ARG ONEDNN_SOURCE_REPOSITORY=https://github.com/uxlfoundation/oneDNN.git
ARG ONEDNN_SOURCE_COMMIT=03c022d3ffdcee958cfacbe720048e725fdf644c
ARG ONEDNN_PATCH_SHA256=0a7afff4134f115b4bc53f46301ca3d62b1c11dc02e32c64635c469769fcdaeb
ARG XPU_TARGET=bmg
ARG MAX_JOBS=8
ARG IMAGE_TAG

ARG SYCL_TLA_REPOSITORY=https://github.com/intel/sycl-tla.git
ARG SYCL_TLA_COMMIT=2fc09973bfdf15755090fcb0e3b6ad236408a992

# ======== Stable OS/toolchain base ========
# Keep device, image-version, Kitchen, and local-source arguments out of this
# stage. Changes to those inputs must not invalidate apt or Python setup.
FROM ${BASE_IMAGE} AS os-base

ARG PYTHON_VERSION

ENV DEBIAN_FRONTEND=noninteractive

SHELL ["bash", "-c"]

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update -y && \
    apt-get install -y --no-install-recommends --fix-missing \
        ca-certificates curl ffmpeg git patch \
        python${PYTHON_VERSION}-dev python${PYTHON_VERSION}-venv python3-pip \
        build-essential ninja-build cmake pkg-config \
        libsndfile1 libsm6 libxext6 libgl1 \
        lsb-release numactl wget vim linux-libc-dev \
        libopengl0 libglx0 libxrender1 libxfixes3 libx11-dev \
        libxi6 libxxf86vm1 libxcursor1 libxrandr2 libxinerama1 \
        libxkbcommon0

# ======== Stable Python/Torch base ========
# This stage is shared by the ComfyUI dependency, Kitchen, and kernel branches.
# It changes only when the base Python/Torch/oneDNN environment changes.
FROM os-base AS python-base

ARG PYTHON_VERSION
ARG TORCH_VERSION
ARG TORCHVISION_VERSION
ARG TORCHAUDIO_VERSION
ARG ONEDNN_VERSION
ARG ONEDNN_SOURCE_REPOSITORY
ARG ONEDNN_SOURCE_COMMIT
ARG ONEDNN_PATCH_SHA256
ARG MAX_JOBS

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:/opt/intel/oneapi/compiler/latest/bin:${PATH}" \
    PIP_EXTRA_INDEX_URL="https://download.pytorch.org/whl/xpu" \
    PIP_DISABLE_PIP_VERSION_CHECK=1

ENV LD_LIBRARY_PATH="/opt/venv/lib:/opt/venv/lib/python${PYTHON_VERSION}/site-packages/torch/lib:/opt/intel/oneapi/compiler/latest/lib:/opt/intel/oneapi/dnnl/latest/lib:/opt/intel/oneapi/mkl/latest/lib:/opt/intel/oneapi/tbb/latest/lib:/opt/intel/oneapi/mpi/latest/lib"

RUN python${PYTHON_VERSION} -m venv ${VIRTUAL_ENV} && \
    pip install --upgrade pip setuptools wheel

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install \
        torch==${TORCH_VERSION} \
        torchvision==${TORCHVISION_VERSION} \
        torchaudio==${TORCHAUDIO_VERSION} \
        --index-url https://download.pytorch.org/whl/xpu && \
    pip install \
        pytest \
        onednn==${ONEDNN_VERSION} \
        onednn-devel==${ONEDNN_VERSION} && \
    pip check

COPY owl/packaging/container/onednn-v3.11.2-enable-bf16-int4-dequantization.patch \
    /llm/patches/onednn-v3.11.2-enable-bf16-int4-dequantization.patch

# oneDNN 3.11 disabled its optimized BF16 INT4 dequantization path in
# 0d99c32b03614d6943b993974f91d419e3c3a0f6. That changes the observable
# BF16 materialization contract used by Kitchen SVDQuant. Build the exact
# 3.11.2 release with the reviewed two-site restoration instead of downgrading
# the runtime or weakening exact correctness. Keep the Python distribution
# version pinned above and record source, patch, and installed-DSO identities.
RUN set -euo pipefail && \
    echo "${ONEDNN_PATCH_SHA256}  /llm/patches/onednn-v3.11.2-enable-bf16-int4-dequantization.patch" \
        | sha256sum --check - && \
    git clone --filter=blob:none --no-checkout \
        "${ONEDNN_SOURCE_REPOSITORY}" /tmp/onednn-source && \
    git -C /tmp/onednn-source fetch --depth 1 origin \
        "${ONEDNN_SOURCE_COMMIT}" && \
    git -C /tmp/onednn-source checkout --detach FETCH_HEAD && \
    test "$(git -C /tmp/onednn-source rev-parse HEAD)" \
        = "${ONEDNN_SOURCE_COMMIT}" && \
    git -C /tmp/onednn-source apply --check \
        /llm/patches/onednn-v3.11.2-enable-bf16-int4-dequantization.patch && \
    git -C /tmp/onednn-source apply \
        /llm/patches/onednn-v3.11.2-enable-bf16-int4-dequantization.patch && \
    git -C /tmp/onednn-source diff --check && \
    set +u && \
    source /opt/intel/oneapi/setvars.sh --force && \
    set -u && \
    cmake -S /tmp/onednn-source -B /tmp/onednn-build -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX="${VIRTUAL_ENV}" \
        -DCMAKE_C_COMPILER=/opt/intel/oneapi/compiler/2026.1/bin/icx \
        -DCMAKE_CXX_COMPILER=/opt/intel/oneapi/compiler/2026.1/bin/icpx \
        -DDNNL_BUILD_DOC=OFF \
        -DDNNL_BUILD_EXAMPLES=OFF \
        -DDNNL_BUILD_TESTS=OFF \
        -DDNNL_CPU_RUNTIME=NONE \
        -DDNNL_GPU_RUNTIME=SYCL \
        -DDNNL_GPU_VENDOR=INTEL \
        -DONEDNN_BUILD_GRAPH=OFF && \
    cmake --build /tmp/onednn-build --parallel "${MAX_JOBS}" && \
    cmake --install /tmp/onednn-build && \
    test "$(readlink -f "${VIRTUAL_ENV}/lib/libdnnl.so.3")" \
        = "${VIRTUAL_ENV}/lib/libdnnl.so.3.11" && \
    mkdir -p /llm/manifests && \
    library_sha256="$(sha256sum "${VIRTUAL_ENV}/lib/libdnnl.so.3.11" \
        | awk '{print $1}')" && \
    printf '%s\n' \
        "schema_version=1" \
        "package_version=${ONEDNN_VERSION}" \
        "source_repository=${ONEDNN_SOURCE_REPOSITORY}" \
        "source_revision=${ONEDNN_SOURCE_COMMIT}" \
        "patch_sha256=${ONEDNN_PATCH_SHA256}" \
        "library_path=${VIRTUAL_ENV}/lib/libdnnl.so.3.11" \
        "library_sha256=${library_sha256}" \
        > /llm/manifests/onednn-runtime.env && \
    rm -rf /tmp/onednn-source /tmp/onednn-build && \
    pip check

RUN mkdir -p /llm /wheels /llm/patches

# ======== Pinned native headers ========
# Header acquisition is independent of both local native projects. A kernel
# source change reuses this stage; a Kitchen change never reaches it.
FROM python-base AS sycl-tla

ARG SYCL_TLA_REPOSITORY
ARG SYCL_TLA_COMMIT

# Fetch native headers directly. This replaces the old hidden dependency on the
# copy of sycl-tla populated as a side effect of building sgl-kernel-xpu.
RUN cd /llm && \
    git clone --filter=blob:none --no-checkout \
        "${SYCL_TLA_REPOSITORY}" sycl-tla && \
    git -C sycl-tla fetch --depth 1 origin "${SYCL_TLA_COMMIT}" && \
    git -C sycl-tla checkout --detach FETCH_HEAD

# ======== OWL's pinned enhancement bundle ========
FROM sycl-tla AS owl-build
RUN pip install setuptools-scm==10.2.1
COPY owl /owl
ARG MAX_JOBS
ENV MAX_JOBS=${MAX_JOBS} TORCH_XPU_ARCH_LIST=bmg
RUN python /owl/packaging/build.py build \
    --sycl-tla /llm/sycl-tla --output /opt/owl-bundle

# ======== Official ComfyUI plus separately installed OWL providers ========
FROM python-base AS runtime
COPY --from=owl-build /owl/components/ComfyUI /opt/ComfyUI
WORKDIR /opt/ComfyUI
# A submodule .git file is meaningful only in its superproject. The exact source
# revision is retained in the bundle manifest instead.
RUN rm .git && pip freeze > /tmp/base-constraints.txt && \
    pip install -c /tmp/base-constraints.txt -r requirements.txt && pip check
COPY --from=owl-build /opt/owl-bundle/wheels /opt/owl-bundle/wheels
COPY --from=owl-build /opt/owl-bundle/ComfyUI_OmniXPU.zip /opt/owl-bundle/ComfyUI_OmniXPU.zip
COPY --from=owl-build /opt/owl-bundle/manifest.json /opt/owl-bundle/manifest.json
COPY owl/packaging/container/install_bundle.py /opt/owl/install_bundle.py
COPY owl/packaging/container/start.sh /opt/owl/start.sh
COPY owl/packaging/smoke_comfyui.py /opt/owl/smoke_comfyui.py
RUN python /opt/owl/install_bundle.py && \
    pip freeze > /opt/owl-bundle/runtime-freeze.txt
ENV OMNI_IMAGE_XPU_TARGET=bmg
EXPOSE 8188
ENTRYPOINT ["bash", "/opt/owl/start.sh"]
CMD ["--listen", "0.0.0.0", "--port", "8188", "--disable-api-nodes"]
