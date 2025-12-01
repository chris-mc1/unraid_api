#!/usr/bin/env bash

set -e

cd "$(dirname "$0")/.."

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add uv to PATH for this session
    export PATH="$HOME/.local/bin:$PATH"
fi

# Sync dependencies with latest versions
# --frozen: Use the lockfile without updating it
# --group dev: Include dev group (homeassistant, ruff, etc.)
# --group test: Include test group (pytest, coverage, etc.)
echo "Installing dependencies..."
uv sync --frozen --group dev --group test

echo ""
echo "Setup complete! You can now run:"
echo "  ./scripts/develop.sh  - Start Home Assistant for development"
echo "  ./scripts/lint.sh     - Format and lint code"
echo "  uv run pytest         - Run tests"
