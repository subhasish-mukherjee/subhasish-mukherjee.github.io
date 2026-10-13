#!/bin/bash
# Test the City Streets source and replace this site's generated dashboard with a validated
# static export. This script never commits or pushes implicitly.
#   ./refresh_city_streets.sh
# Override the sibling source checkout only when needed:
#   CITY_STREETS_SOURCE=/path/to/StreetSphere ./refresh_city_streets.sh
set -euo pipefail

SITE_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="${CITY_STREETS_SOURCE:-$SITE_DIR/StreetSpherefull}"
JULIA_CMD="${JULIA_CMD:-$(command -v julia || true)}"

test -f "$SOURCE_DIR/Project.toml" || {
  echo "City Streets source not found at: $SOURCE_DIR" >&2
  exit 1
}
test -n "$JULIA_CMD" || {
  echo "Julia was not found; set JULIA_CMD=/path/to/julia" >&2
  exit 1
}

"$JULIA_CMD" --project="$SOURCE_DIR" -e 'using Pkg; Pkg.test()'
# Commute modal share: importer tests, and the committed dataset must rebuild from its extracts.
python3 -m unittest discover -s "$SOURCE_DIR/scripts/modal_share"
python3 "$SOURCE_DIR/scripts/modal_share/build.py" check
"$JULIA_CMD" --project="$SOURCE_DIR" "$SOURCE_DIR/scripts/export_static.jl" "$SITE_DIR/city-streets"
python3 "$SITE_DIR/scripts/validate_city_streets.py" "$SITE_DIR/city-streets"

git -C "$SITE_DIR" diff --check
echo "City Streets export refreshed and validated. Review the diff, then commit/publish it."
