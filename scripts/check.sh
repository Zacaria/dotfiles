#!/bin/bash
set -euo pipefail

repo="$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd -P)"
command -v chezmoi >/dev/null 2>&1 || {
  printf '%s\n' 'Install chezmoi before running checks.' >&2
  exit 1
}
bash -n "$repo/scripts/check.sh"
for config in "$repo/home/dot_zshrc" "$repo/home/dot_zprofile"; do
  zsh -n "$config"
done
ruby -c "$repo/home/dot_Brewfile"
git config --file "$repo/home/dot_gitconfig" --list >/dev/null
python3 -m json.tool "$repo/home/dot_config/zed/settings.json" >/dev/null
python3 -c 'import pathlib, sys, tomllib; tomllib.loads(pathlib.Path(sys.argv[1]).read_text())' "$repo/home/dot_config/mise/config.toml"
python3 -c 'import pathlib, sys, tomllib; tomllib.loads(pathlib.Path(sys.argv[1]).read_text())' "$repo/home/dot_config/uv/uv.toml"
python3 -c 'import pathlib, sys, tomllib; tomllib.loads(pathlib.Path(sys.argv[1]).read_text())' "$repo/home/dot_bunfig.toml"
python3 -m unittest discover -s "$repo/tests" -p 'test_*.py' -v
node --test "$repo/tests/codex-rtk.test.mjs"

# Check the scripts chezmoi actually executes, after template rendering.
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
mkdir -p "$tmpdir/home"
chez=(chezmoi --source "$repo" --destination "$tmpdir/home" --config "$tmpdir/config.toml" --cache "$tmpdir/cache" --persistent-state "$tmpdir/state.boltdb" --no-pager --no-tty)
for template in "$repo"/home/.chezmoiscripts/*.tmpl; do
  rendered="$tmpdir/$(basename "$template" .tmpl)"
  "${chez[@]}" execute-template <"$template" >"$rendered"
  bash -n "$rendered"
  if command -v shellcheck >/dev/null 2>&1; then shellcheck "$rendered"; fi
  if command -v shfmt >/dev/null 2>&1; then shfmt -d -i 2 -ci "$rendered"; fi
done
if command -v shellcheck >/dev/null 2>&1; then shellcheck "$repo/scripts/check.sh"; fi
if command -v shfmt >/dev/null 2>&1; then shfmt -d -i 2 -ci "$repo/scripts/check.sh"; fi
