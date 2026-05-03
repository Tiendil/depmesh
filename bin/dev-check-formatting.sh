#!/usr/bin/bash

set -e

echo "run isort"

./bin/dev.sh uv run -- isort --check-only ./depmesh

echo "run black"

./bin/dev.sh uv run -- black --check ./depmesh
