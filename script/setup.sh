#!/usr/bin/env bash

set -e

cd "$(dirname "$0")/.."

# Install/upgrade uv to latest version
python3 -m pip install --upgrade uv

# Sync dependencies with latest versions
# --upgrade: Upgrade all dependencies to their latest compatible versions
# --no-install-project: Don't install the project itself, just dependencies
# --prerelease=allow: Allow prerelease versions if needed
# --group dev: Include dev group (homeassistant, ruff, etc.)
# --group test: Include test group (pytest, coverage, etc.)
uv sync --upgrade --no-install-project --prerelease=allow --group dev --group test