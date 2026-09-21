# B580 native-kernel validation receipt

The earlier Ubuntu B580 development-container run passed **39 tests**, including
CuTe attention correctness. The JUnit timestamp is
`2026-09-18T17:16:06.503493+00:00` (2026-09-19 in Asia/Shanghai).
There were zero failures, errors or skipped tests; 240 tests were deselected.

| Implementation family | Executed coverage | Result |
| --- | --- | --- |
| SYCL/ESIMD + oneDNN (`_C` / `lgrf_sdp`) | 36 RMSNorm cases; 2 standalone ESIMD SDP cases (FP16 and BF16) | 38 passed; not every operation in this family was tested |
| CuTe / sycl-tla (`cute_fmha_torch`) | BF16 D128 Z-Image attention shape contract through `cute.sdp` | 1 passed |

The CuTe testcase is
`tests.test_cute_d128_correctness::test_cute_d128_bmg_matches_zimage_workflow_contract`.
It uses random Q/K/V tensors of shape `(1, 4128, 30, 128)` in BLHD layout,
seed `20260726`, and compares against PyTorch scaled-dot-product attention.
It asserts output shape, contiguous layout, finite values and maximum absolute
error at most `0.001953125`. This records a passing assertion, not a separately
logged exact error value. See the
[test source](../components/omni_xpu_kernels/tests/test_cute_d128_correctness.py).

This establishes correctness for that attention contract, not full Z-Image
inference, other CuTe routes, performance gains or Windows support. B580's
experimental runtime policy does not negate this passed correctness test.

## Environment and source identity

- Device: Intel Arc B580, device ID `0xe20b`; unforced `b580-v1` policy.
- Host: Ubuntu 24.10; container: Ubuntu 24.04.
- Development image: `sha256:0aeabe95ff3d2168e2f31dc4609db977bb549f7d70aac89542e8c24a6739b833`.
- Torch: `2.13.0+xpu`; Omni: `0.2.0b2+torch213.bmg`.
- Compiler: oneAPI 2026.1.0; oneDNN Python package: 2026.0.0.
- Original source: `intel/llm-scaler` commit `38d9a3dbbfecd3a5293a8acd75efef54f9bb3719`, directory `omni/omni_xpu_kernel`.
- OWL kernel snapshot: `90356713b5f97d01e1353c8cc95fc830a23d0189`.

The snapshot's provenance records no runtime-file changes. Its `setup.py`, CuTe
wrapper and both attention test files were also compared byte-for-byte against
the original local source when correcting the support table.

This is a separate development-image receipt from the later
[clean OMIX integration validation](omix-validation.md). The latter rebuilt the
components and tested ComfyUI integration but did not run the CuTe testcase.
The support table combines these scoped component and integration results; it
does not claim the two images contain identical binaries.

## Retained evidence

Raw evidence remains outside Git on the validation host. SHA256 values identify
the files reviewed for this receipt:

| File | SHA256 |
| --- | --- |
| `omni-smoke.xml` | `7a654eabbfc636696d9fc66244a9ea8a17f8f2ed6925e980a5e696b219c6be0d` |
| `omni-smoke.log` | `73ca6f5522f0a94e3f572d6e76756ff1abc5725ea0b552cdb88492a5cb10b7ce` |
| `runtime-probe.json` | `61016f8c649e5fb7928ddeb9383a8aa4601cd4d709f6562709252739d08a9c2e` |

The retained `native-sha256.txt` identifies the tested extensions:

| Extension | SHA256 |
| --- | --- |
| `_C.cpython-312-x86_64-linux-gnu.so` | `f0b1c63f79d4294da14131a56451a0dcc27a910321a6b589fd8b4aebf818a3f6` |
| `lgrf_uni/lgrf_sdp.cpython-312-x86_64-linux-gnu.so` | `9e442a0ec72b1b72db4a56a151050b670784065ac3e0bfa3b2c19ffd1790083a` |
| `cute/cute_fmha_torch.cpython-312-x86_64-linux-gnu.so` | `c195494b5dd3deb1e7b161e71683f85a29ad53426a2fa4a16d8b97e3aee04c4b` |
