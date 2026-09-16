# OWL-XPU

**Omni Workload Layer Runtime for Intel XPU**

Enabling and accelerating ComfyUI across Intel GPU architectures with native
kernels, operator dispatch, and memory management.

## Overview

OWL-XPU is being established as an independently maintained home for Intel XPU
runtime development, building on the Omni work in
[Intel's llm-scaler project](https://github.com/intel/llm-scaler/tree/main/omni).

The project is intended to bring native kernels, Kitchen XPU operator dispatch,
AIMDO XPU memory management, and ComfyUI adapters into one repository. Components
will retain distinct responsibilities and independently buildable packages.

## Planned architecture

| Component | Responsibility |
| --- | --- |
| Native kernels | Intel XPU implementations, PyTorch bindings, target capabilities, and kernel selection |
| Kitchen XPU | Common operator interfaces, backend dispatch, input constraints, and fallback |
| AIMDO XPU | Device memory management and allocator lifecycle integration |
| ComfyUI adapters | Runtime initialization and model call-site integration where a Kitchen entry point is unavailable |
| Deployment | Installation tools and compatible component combinations |

ComfyUI calls kernels through Kitchen or a dedicated adapter. Native kernel
packages remain independent of ComfyUI, Kitchen, and AIMDO. Device-specific
implementations share public operator contracts while retaining their own
capability checks and tuning policies.

## Device direction

The initial expansion targets under consideration are:

- **Intel Arc A770 (DG2)**
- **Intel Arc 140V (Lunar Lake / LNL)**

Each target will require its own build, correctness, and workflow validation.
Support will be documented per component and operation; an architecture target
alone does not imply that every kernel or memory-management feature is available.

## Project status

This repository currently contains the initial project documentation. Runtime
code has not yet been migrated, and OWL-XPU does not yet provide installable
packages or validated device support.

The planned migration will preserve upstream attribution and applicable licenses,
and move the required source, build, and deployment tooling into this repository
so future maintenance can proceed independently of llm-scaler.
