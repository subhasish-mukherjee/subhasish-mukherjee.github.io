#!/bin/bash
# Re-export the City Streets dashboard into this site and commit the update.
#   ./refresh_city_streets.sh          # export + commit (push manually)
set -euo pipefail
cd "$(dirname "$0")"
~/.juliaup/bin/julia --project="$HOME/StreetSphere" "$HOME/StreetSphere/scripts/export_static.jl" "$PWD/city-streets"
git add city-streets
git commit -m "Refresh City Streets export" || echo "nothing to commit"
echo "Done — 'git push' to deploy."
