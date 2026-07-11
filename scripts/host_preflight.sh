#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

fail=0
ok() { printf 'OK: %s\n' "$*"; }
warn() { printf 'WARN: %s\n' "$*"; }
error() { printf 'ERROR: %s\n' "$*"; fail=1; }

. /etc/os-release
printf 'OS: %s\n' "${PRETTY_NAME:-unknown}"
[[ "${ID:-}" == "ubuntu" ]] || warn "Native Ubuntu is required for primary timing results"
[[ "${VERSION_ID:-}" == "24.04" ]] || warn "Check the current AMD support matrix for this Ubuntu version"

command -v docker >/dev/null && ok "Docker found" || error "Docker missing"
docker compose version >/dev/null 2>&1 && ok "Compose plugin found" || error "Compose missing"
[[ -e /dev/kfd ]] && ok "/dev/kfd present" || error "/dev/kfd missing"
[[ -d /dev/dri ]] && ok "/dev/dri present" || error "/dev/dri missing"

lspci -nn | grep -Ei 'AMD.*(VGA|Display)|VGA.*AMD|Display.*AMD' \
  || error "AMD GPU was not found by lspci"

printf '\nCPU topology:\n'
lscpu -e=CPU,CORE,SOCKET,NODE
printf '\nMemory:\n'
free -h
printf '\nDevices:\n'
ls -l /dev/kfd /dev/dri/* 2>/dev/null || true

free_gb=$(df -Pk . | awk 'NR==2 {print int($4/1024/1024)}')
(( free_gb >= 100 )) && ok "Free disk: ${free_gb} GiB" \
  || warn "Recommended free disk is at least 100 GiB; found ${free_gb} GiB"

exit "$fail"
