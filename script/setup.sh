#!/usr/bin/env bash

set -e

cd "$(dirname "$0")/.."
python3 -m pip install uv
uv sync --no-install-project --prerelease=allow --group test