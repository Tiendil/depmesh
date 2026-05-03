#!/usr/bin/bash

set -e

./bin/dev-build-package.sh

PACKAGE="./dist/depmesh-$(./bin/dev.sh uv version --short)-py3-none-any.whl"

echo "check that CLI works from built package"

./bin/dev.sh uvx --from "$PACKAGE" depmesh --help

echo "check that package reports version"

./bin/dev.sh uvx --from "$PACKAGE" depmesh version
