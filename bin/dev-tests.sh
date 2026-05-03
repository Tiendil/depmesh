#!/usr/bin/bash

set -e

echo "run tests"

./bin/dev.sh uv run -- pytest -o cache_dir=/tmp/depmesh-pytest-cache
