#!/usr/bin/bash

set -e

echo "run autoflake"

./bin/dev.sh uv run -- autoflake --check --quiet ./depmesh

echo "run flake8"

./bin/dev.sh uv run -- flake8 ./depmesh

echo "run mypy"

./bin/dev.sh uv run -- mypy --show-traceback ./depmesh
