# Initial assembly validation

Date: 2026-09-19. Tested packaging implementation:
`7150f378960882a7089f26337fa487be35a2fe4c`.

- Six offline source-admission tests passed: pinned checkout, missing checkout,
  dirty/untracked component files, staged pin changes and top-level runtime leakage.
- `check` and `plan` resolved all four committed gitlinks successfully.
- Actual Linux packaging with `--components kitchen comfyui` passed in development
  image `sha256:0aeabe95ff3d2168e2f31dc4609db977bb549f7d70aac89542e8c24a6739b833`,
  Torch `2.13.0+xpu`, with networking disabled and no device exposed.
- Kitchen provider namespace ownership, plugin ZIP layout and all artifact hashes
  were checked. Component working trees remained clean.
- The native kernel and AIMDO build phases were not executed in this initialization.
  No GPU, allocator lifecycle, complete ComfyUI image or combined workflow acceptance
  is claimed. Those checks belong to the selected component/target environment.

The packaging smoke run produced:

| Artifact | SHA256 |
| --- | --- |
| `wheels/kitchen/comfy_kitchen_xpu_runtime-0.2.33-py3-none-any.whl` | `d1227c428b1191f797c73e04f2366f90bd5163448e3dd521230c4316781be367` |
| `ComfyUI_OmniXPU.zip` | `d46f22017729a91c3b436b67226a27f08cddc7a86b9db78721fd6145daefbb3c` |
