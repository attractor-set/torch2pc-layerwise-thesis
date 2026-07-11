#!/usr/bin/env bash
set -euo pipefail

. /etc/os-release
if [[ "${ID:-}" != "ubuntu" ]]; then
  echo "Установщик предназначен для Ubuntu." >&2
  exit 1
fi

sudo apt-get update
sudo apt-get install -y \
  ca-certificates curl git jq make python3 python3-venv \
  pciutils procps numactl

if ! command -v docker >/dev/null 2>&1; then
  sudo install -m 0755 -d /etc/apt/keyrings
  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    -o /etc/apt/keyrings/docker.asc
  sudo chmod a+r /etc/apt/keyrings/docker.asc
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${UBUNTU_CODENAME:-$VERSION_CODENAME} stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo apt-get update
  sudo apt-get install -y \
    docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin
  sudo usermod -aG docker "$USER"
  echo "Docker установлен. Выйдите из сеанса и войдите снова для работы без sudo."
fi
