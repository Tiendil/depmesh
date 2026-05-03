#!/usr/bin/bash

set -e

echo "run autoflake"

./bin/dev.sh uv run -- autoflake ./depmesh

echo "run isort"

./bin/dev.sh uv run -- isort ./depmesh

echo "run black"

./bin/dev.sh uv run -- black ./depmesh
