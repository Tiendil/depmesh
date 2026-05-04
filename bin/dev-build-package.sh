#!/usr/bin/bash

set -e

echo "build package distributions"

./bin/dev.sh uv build --sdist --wheel --out-dir dist
