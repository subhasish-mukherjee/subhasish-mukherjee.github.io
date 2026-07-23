#!/bin/bash
# Re-export the StreetSphere dashboard into this site and commit the update.
#   ./refresh_streetsphere.sh          # export + commit (push manually)
set -euo pipefail
cd "$(dirname "$0")"
~/.juliaup/bin/julia --project="$HOME/StreetSphere" "$HOME/StreetSphere/scripts/export_static.jl" "$PWD/streetsphere"
git add streetsphere
git commit -m "Refresh StreetSphere export" || echo "nothing to commit"
echo "Done — 'git push' to deploy."
