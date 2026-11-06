#!/usr/bin/env bash
# Usage: ./scripts/setup_repo.sh <github-user> [public|private]
# Requires: git and the GitHub CLI (gh auth login)
set -euo pipefail
USER_GH="${1:?github username}"; VIS="${2:-public}"
sed -i "s/YOUR_USER/$USER_GH/g" README.md CITATION.cff manuscript/main.tex
git init -b main
git add . && git commit -m "Initial commit: thesis repository scaffold"
gh repo create "$USER_GH/bsc-thesis-hpop" "--$VIS" --source=. --remote=origin --push
# Basilisk: submodule on YOUR FORK (first: gh repo fork AVSLab/basilisk --clone=false)
git submodule add "https://github.com/$USER_GH/basilisk.git" external/basilisk
git -C external/basilisk checkout feature/bsk-XXX--short-desc || true   # TODO: your fix branch
git add . && git commit -m "Add Basilisk fork as submodule" && git push
echo "Done. Enable the repo at https://zenodo.org/account/settings/github/ then publish a release."
