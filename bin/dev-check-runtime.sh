#!/usr/bin/bash

set -e

echo "cli works"

./bin/dev.sh uv run -- depmesh --help
