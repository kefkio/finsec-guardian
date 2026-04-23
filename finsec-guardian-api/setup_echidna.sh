#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# setup_echidna.sh — Pull the Echidna Docker image and verify it works
#
# Echidna runs inside a Docker container for full isolation — no Haskell
# runtime, no shared-library conflicts with Slither/Mythril.
#
# Prerequisites:
#   • Docker Engine or Docker Desktop (with WSL integration if on Windows)
#   • Current user in the 'docker' group (no sudo needed):
#       sudo usermod -aG docker "$USER" && newgrp docker
#
# Usage:
#   bash setup_echidna.sh              # pull latest known-good image
#   bash setup_echidna.sh 2.2.5        # pull a specific tag
#
# The analyzer invokes Docker at runtime — no local binary to manage.
# ---------------------------------------------------------------------------
set -euo pipefail

DEFAULT_VERSION="2.2.5"
VERSION="${1:-$DEFAULT_VERSION}"
IMAGE="ghcr.io/crytic/echidna/echidna:v${VERSION}"

echo "╔══════════════════════════════════════════════════╗"
echo "║  Echidna Docker Installer — v${VERSION}             ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------

# 1. Docker available?
if ! command -v docker &>/dev/null; then
    echo "❌  'docker' not found on PATH."
    echo ""
    echo "    Install Docker Engine:  https://docs.docker.com/engine/install/"
    echo "    Or enable WSL integration in Docker Desktop settings."
    exit 1
fi

# 2. Docker daemon reachable without sudo?
if ! docker info &>/dev/null 2>&1; then
    echo "❌  Cannot connect to Docker daemon."
    echo ""
    echo "    If you are a non-root user, add yourself to the docker group:"
    echo "      sudo usermod -aG docker \$USER && newgrp docker"
    echo ""
    echo "    Then re-run this script."
    exit 1
fi

echo "  Docker  : $(docker --version)"
echo "  Image   : ${IMAGE}"
echo "  User    : $(id -un) (uid=$(id -u))"
echo ""

# ---------------------------------------------------------------------------
# Pull the image
# ---------------------------------------------------------------------------
echo "⬇  Pulling ${IMAGE} ..."
docker pull "${IMAGE}"

# ---------------------------------------------------------------------------
# Verify: run echidna --version inside the container as current UID
# ---------------------------------------------------------------------------
echo ""
echo "🔍  Verifying image (running as uid=$(id -u)) ..."
ECHIDNA_VER=$(docker run --rm \
    --user "$(id -u):$(id -g)" \
    "${IMAGE}" \
    --version 2>&1 || true)

if [[ -n "$ECHIDNA_VER" ]]; then
    echo "    $ECHIDNA_VER"
    echo ""
    echo "✅  Echidna Docker image ready: ${IMAGE}"
else
    echo "⚠️   Image pulled but 'echidna --version' produced no output."
    echo "    The image may still work for analysis."
fi

# ---------------------------------------------------------------------------
# Django settings reminder
# ---------------------------------------------------------------------------
echo ""
echo "📝  Add the following to config/settings.py:"
echo ""
echo "    ECHIDNA_DOCKER_IMAGE = '${IMAGE}'"
echo "    ECHIDNA_TIMEOUT = 120  # seconds"
echo ""
