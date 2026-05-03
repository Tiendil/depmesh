#!/usr/bin/bash

set -euo pipefail

BUMP_VERSION=${1:-}

if [[ "$BUMP_VERSION" != "minor" && "$BUMP_VERSION" != "patch" ]]; then
    echo "usage: ./bin/release-prepare.sh minor|patch"
    exit 1
fi

echo "Bumping version as $BUMP_VERSION"

NEXT_VERSION=$(./bin/dev.sh uv version --bump "$BUMP_VERSION" --short)
NEXT_VERSION_TAG="v$NEXT_VERSION"

echo "New version is $NEXT_VERSION"
echo "New version tag $NEXT_VERSION_TAG"

echo "Building Python package"

./bin/dev-build-package.sh

echo "Commit changes"

git add pyproject.toml uv.lock
git commit -m "Release $NEXT_VERSION"
git push

echo "Create tag"

git tag "$NEXT_VERSION_TAG"
git push origin "$NEXT_VERSION_TAG"
