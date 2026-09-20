#!/usr/bin/env python3
"""Package pinned components; no runtime implementations live in this module."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = {
    "kernels": "omni_xpu_kernels",
    "kitchen": "comfy-kitchen",
    "aimdo": "comfy-aimdo",
    "comfyui": "ComfyUI_OmniXPU",
}
SOURCES = {**COMPONENTS, "host": "ComfyUI"}


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def inspect_sources(root: Path = ROOT) -> dict:
    """The committed gitlinks, rather than remote branch heads, own the pins."""
    if git(root, "status", "--porcelain", "--untracked-files=all", "--ignore-submodules=none"):
        raise RuntimeError("OWL or its submodules are dirty; commit/revert the intended inputs first")
    tracked = git(root, "ls-tree", "-r", "HEAD")
    entries = {}
    for line in tracked.splitlines():
        metadata, path = line.split("\t", 1)
        mode, kind, revision = metadata.split()
        entries[path] = (mode, kind, revision)
        if mode == "160000":
            if path not in {"components/" + name for name in SOURCES.values()}:
                raise RuntimeError(f"Unexpected runtime submodule: {path}")
        elif path not in {"README.md", "LICENSE", ".gitignore", ".gitmodules", "AGENTS.md"} and not path.startswith(("docs/", "packaging/")):
            raise RuntimeError(f"Top-level ownership violation: {path}")
    result = {}
    for key, name in SOURCES.items():
        path = "components/" + name
        entry = entries.get(path)
        if not entry or entry[:2] != ("160000", "commit"):
            raise RuntimeError(f"Expected a committed gitlink: {path}")
        module = root / path
        if not (module / ".git").exists():
            raise RuntimeError(f"Uninitialized submodule: {path}; run git submodule update --init")
        if git(module, "rev-parse", "HEAD") != entry[2]:
            raise RuntimeError(f"Checkout differs from committed gitlink: {path}")
        url = git(root, "config", "--file", ".gitmodules", "--get", f"submodule.{path}.url")
        result[key] = {"path": path, "repository": url, "revision": entry[2]}
    return {"owl_revision": git(root, "rev-parse", "HEAD"), "components": result}


def run(argv: list[str], *, cwd: Path, env: dict, log: Path) -> None:
    print("Running: " + " ".join(argv), flush=True)
    with log.open("a") as output:
        output.write(json.dumps({"argv": argv, "cwd": str(cwd)}) + "\n")
        output.flush()
        subprocess.run(argv, cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT, check=True)


def only_wheel(directory: Path) -> Path:
    wheels = list(directory.glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"Expected exactly one wheel in {directory}, got {len(wheels)}")
    return wheels[0]


def aimdo_build_environment(env: dict) -> dict:
    """Resolve toolchain headers before starting any expensive native build."""
    compiler = shutil.which(env.get("CXX", "icpx"), path=env.get("PATH"))
    if compiler is None:
        raise RuntimeError("AIMDO requires the oneAPI C++ compiler (CXX or icpx)")
    include = Path(compiler).resolve().parent.parent / "include"
    candidates = ([Path(env["UR_INCLUDE_DIR"])] if env.get("UR_INCLUDE_DIR") else
                  [include / "unified-runtime", include,
                   Path(sys.prefix) / "include" / "unified-runtime"])
    for candidate in candidates:
        if (candidate / "ur_api.h").is_file():
            return dict(env, UR_INCLUDE_DIR=str(candidate))
    raise RuntimeError("AIMDO requires ur_api.h; set UR_INCLUDE_DIR to its directory")


def host_identity(root: Path = ROOT) -> dict:
    data = (root / "components/ComfyUI/comfyui_version.py").read_bytes()
    for node in ast.parse(data).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets
        ):
            version = ast.literal_eval(node.value)
            if isinstance(version, str) and version:
                return {"host_version": version,
                        "host_version_file_sha256": hashlib.sha256(data).hexdigest()}
    raise RuntimeError("Pinned ComfyUI source does not declare a literal version")


def build(args: argparse.Namespace, plan: dict) -> None:
    profile = plan["profile"]
    if sys.platform != profile["platform"]:
        raise RuntimeError("This recipe currently supports Linux only")
    require_cute = profile.get(
        "require_cute", profile["xpu_target"] not in {"dg2"}
    )
    env = dict(
        os.environ,
        OMNI_XPU_DEVICE=profile["xpu_target"],
        OMNI_XPU_REQUIRE_CUTE="1" if require_cute else "0",
    )
    if "aimdo" in args.components:
        env = aimdo_build_environment(env)
    if set(args.components) != {"comfyui"}:
        probe = subprocess.check_output([sys.executable, "-c", "import torch; print(torch.__version__)"], text=True).strip()
        if probe != profile["torch_version"]:
            raise RuntimeError(f"Torch mismatch: {probe} != {profile['torch_version']}")
    if "kernels" in args.components:
        import importlib.metadata
        if importlib.metadata.version("onednn") != profile["onednn_version"]:
            raise RuntimeError("oneDNN package does not match the selected profile")
        if require_cute:
            if not args.sycl_tla or git(args.sycl_tla, "rev-parse", "HEAD") != profile["sycl_tla_revision"]:
                raise RuntimeError("Pass --sycl-tla pointing to the pinned sycl-tla checkout")
            if git(args.sycl_tla, "status", "--porcelain", "--untracked-files=all"):
                raise RuntimeError("sycl-tla checkout must be clean")
            env["CUTLASS_SYCL_ROOT"] = str(args.sycl_tla.resolve())
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / "build-plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    for key in args.components:
        item = plan["components"][key]
        source = ROOT / item["path"]
        log = output / (key + ".log")
        if key == "comfyui":
            run(["git", "archive", "--format=zip", "--prefix=ComfyUI_OmniXPU/",
                 "--output=" + str(output / "ComfyUI_OmniXPU.zip"), item["revision"]], cwd=source, env=env, log=log)
            continue
        work = output / "sources" / key
        work.parent.mkdir(exist_ok=True)
        # Fresh isolated trees keep native outputs out of the pinned submodules.
        run(["git", "clone", "--no-hardlinks", "--no-checkout", str(source), str(work)], cwd=ROOT, env=env, log=log)
        run(["git", "checkout", "--detach", item["revision"]], cwd=work, env=env, log=log)
        if key == "aimdo":
            run(["bash", "scripts/build-linux-xpu.sh"], cwd=work, env=env, log=log)
        wheel_env = env
        if key == "aimdo":
            # The co-installable provider must accept the official host version.
            # Source identity is independently recorded in its hashed manifest.
            wheel_env = dict(env, SETUPTOOLS_SCM_PRETEND_VERSION=profile["comfy_aimdo_version"])
        wheels = output / ("wheels" if key == "kernels" else "intermediate") / key
        wheels.mkdir(parents=True)
        run([sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "--no-build-isolation",
             "--no-cache-dir", "--wheel-dir", str(wheels)], cwd=work, env=wheel_env, log=log)
        wheel = only_wheel(wheels)
        if key in {"kitchen", "aimdo"}:
            providers = output / "wheels" / key
            run([sys.executable, "packaging/xpu_runtime_provider/build_wheel.py",
                 "--source-wheel", str(wheel), "--output-dir", str(providers),
                 "--source-revision", item["revision"], "--torch-version", profile["torch_version"],
                 "--xpu-target", profile["xpu_target"]], cwd=work, env=env, log=log)
            only_wheel(providers)
    if inspect_sources() != {k: plan[k] for k in ("owl_revision", "components")}:
        raise RuntimeError("Pinned source identity changed during packaging")
    artifacts = sorted((output / "wheels").rglob("*.whl")) if (output / "wheels").exists() else []
    artifacts += list(output.glob("*.zip"))
    receipt = dict(plan, status="packaged", acceptance="not validated on a device or in a ComfyUI workflow",
                   artifacts={str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts})
    (output / "manifest.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(output / "manifest.json")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "plan", "build"))
    parser.add_argument("--profile", type=Path, default=ROOT / "packaging/profiles/bmg-torch213.json")
    parser.add_argument("--components", nargs="+", choices=tuple(COMPONENTS), default=list(COMPONENTS))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--sycl-tla", type=Path)
    args = parser.parse_args()
    if len(set(args.components)) != len(args.components):
        parser.error("components must be unique")
    plan = inspect_sources()
    if args.command != "check":
        plan.update(profile=json.loads(args.profile.read_text()), selected_components=args.components)
        plan.update(host_identity())
    if args.command == "build":
        if args.output is None:
            parser.error("build requires --output pointing to a new directory")
        build(args, plan)
    else:
        print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
