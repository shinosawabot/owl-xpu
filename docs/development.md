# Updating components

Make runtime changes in the owning component repository, run its affected tests,
and push the resulting commit there. OWL only advances the gitlink after that
commit is available to other users.

```bash
git -C components/omni_xpu_kernels fetch origin
git -C components/omni_xpu_kernels checkout --detach <reviewed-full-commit>
git add components/omni_xpu_kernels
git commit -m "Update kernel component to reviewed revision"
python3 packaging/build.py check
python3 packaging/build.py plan
```

Do not use `git submodule update --remote` for builds. On a fresh checkout, use
`git submodule update --init` to restore the commits recorded by the superproject.
Changing a gitlink is a source-combination change, not a combined-runtime pass.
Update packaging profiles only when the toolchain/Torch/target contract changes.

Run the offline packaging-control tests with Python's standard library:

```bash
python3 -m unittest discover -s packaging/tests -v
```

For packaging smoke tests, build `--components kitchen comfyui` in the matching
development environment. Native kernel/AIMDO builds and actual ComfyUI startup,
allocator and workflow checks are separate validation steps.

The superproject checker rejects uninitialized submodules, changed gitlinks,
dirty component trees and runtime files placed outside submodules. Generated
build files belong under ignored `dist/` or an external artifact directory.
