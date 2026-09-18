#!/usr/bin/env bash
set -euo pipefail
cd /opt/ComfyUI
mode=enable
seen=''
for argument in "$@"; do
    case "$argument" in
        --enable-dynamic-vram|--disable-dynamic-vram)
            if [[ -n "$seen" && "$seen" != "$argument" ]]; then
                echo 'Conflicting DynamicVRAM arguments' >&2
                exit 2
            fi
            seen="$argument"
            [[ "$argument" != --disable-dynamic-vram ]] || mode=disable
            ;;
    esac
done
extra=()
[[ -n "$seen" ]] || extra=(--enable-dynamic-vram)
if [[ "$mode" == enable ]]; then
    export OMNIXPU_PROVIDER_BOOTSTRAP=required
    preload=$(python custom_nodes/ComfyUI_OmniXPU/runtime_bootstrap.py --allocator-preload-path)
    [[ -n "$preload" ]] || { echo 'AIMDO preload was not resolved' >&2; exit 1; }
    export AIMDO_XPU_ALLOCATOR_MODE=native_hook
    export LD_PRELOAD="$preload${LD_PRELOAD:+:$LD_PRELOAD}"
else
    [[ "${AIMDO_XPU_ALLOCATOR_MODE:-}" != native_hook ]] || {
        echo 'native_hook requires DynamicVRAM' >&2; exit 2;
    }
    export OMNIXPU_PROVIDER_BOOTSTRAP=auto
fi
exec python main.py "${extra[@]}" "$@"
