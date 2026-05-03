#!/usr/bin/bash

set -e

echo "run tests"

./bin/dev.sh uv run -- pytest
