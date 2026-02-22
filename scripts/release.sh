#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/release.sh [patch|minor|major|X.Y.Z]

Examples:
  scripts/release.sh patch
  scripts/release.sh minor
  scripts/release.sh 1.2.3

The script will:
1. Bump version in pyproject.toml
2. Commit and push the release commit
3. Create and push an annotated git tag (vX.Y.Z)
4. Create a GitHub release using gh with generated notes
USAGE
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -ne 1 ]]; then
  usage
  exit 1
fi

bump_arg="$1"

require_cmd git
require_cmd gh

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree is not clean. Commit or stash changes before releasing." >&2
  exit 1
fi

current_pyproject_version="$(sed -nE 's/^version = "([0-9]+\.[0-9]+\.[0-9]+)"$/\1/p' pyproject.toml)"

if [[ -z "$current_pyproject_version" ]]; then
  echo "Unable to read current version from pyproject.toml." >&2
  exit 1
fi

current_version="$current_pyproject_version"

if [[ "$bump_arg" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  new_version="$bump_arg"
else
  IFS='.' read -r major minor patch <<<"$current_version"
  case "$bump_arg" in
    patch)
      patch=$((patch + 1))
      ;;
    minor)
      minor=$((minor + 1))
      patch=0
      ;;
    major)
      major=$((major + 1))
      minor=0
      patch=0
      ;;
    *)
      echo "Invalid bump type: $bump_arg" >&2
      usage
      exit 1
      ;;
  esac
  new_version="${major}.${minor}.${patch}"
fi

if [[ "$new_version" == "$current_version" ]]; then
  echo "New version is the same as current version ($current_version)." >&2
  exit 1
fi

tag="v${new_version}"

if git rev-parse "$tag" >/dev/null 2>&1; then
  echo "Tag already exists locally: $tag" >&2
  exit 1
fi

if git ls-remote --exit-code --tags origin "refs/tags/$tag" >/dev/null 2>&1; then
  echo "Tag already exists on origin: $tag" >&2
  exit 1
fi

if gh release view "$tag" >/dev/null 2>&1; then
  echo "GitHub release already exists: $tag" >&2
  exit 1
fi

branch="$(git rev-parse --abbrev-ref HEAD)"

sed -E -i "s/^version = \"[0-9]+\.[0-9]+\.[0-9]+\"$/version = \"${new_version}\"/" pyproject.toml

uv run poe check

git add pyproject.toml uv.lock
git commit -m "release: ${tag}"
git push origin "$branch"

git tag -a "$tag" -m "$tag"
git push origin "$tag"

gh release create "$tag" --generate-notes --verify-tag

echo "Release complete: $tag"
