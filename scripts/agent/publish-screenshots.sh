#!/usr/bin/env bash
# Publishes screenshots to the `agent-artifacts` branch and prints a markdown
# image link for each one, for pasting into PR and issue comments.
#
#   scripts/agent/publish-screenshots.sh <dir-with-pngs> <dest-path>
#   scripts/agent/publish-screenshots.sh /tmp/pw_test/shots/run1 issue-123/2026-11-04-verify
#
# GitHub's API can't attach images to comments, so the images live on a branch
# that is never merged, keeping them out of PR diffs. Links use the commit SHA
# rather than the branch name so they keep resolving after later pushes.
set -euo pipefail

src=${1:?usage: publish-screenshots.sh <dir-with-pngs> <dest-path>}
dest=${2:?usage: publish-screenshots.sh <dir-with-pngs> <dest-path>}
branch=agent-artifacts

shopt -s nullglob
shots=("$src"/*.png)
if [ ${#shots[@]} -eq 0 ]; then
  echo "No .png files in $src" >&2
  exit 1
fi

cd "$(git rev-parse --show-toplevel)"
repo=${GITHUB_REPOSITORY:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}
tmp=$(mktemp -d)
cleanup() { git worktree remove --force "$tmp" >/dev/null 2>&1 || rm -rf "$tmp"; }
trap cleanup EXIT

if git ls-remote --exit-code --heads origin "$branch" >/dev/null 2>&1; then
  git fetch -q origin "$branch"
  git worktree add -q --detach "$tmp" FETCH_HEAD
else
  git worktree add -q --detach "$tmp"
  (cd "$tmp" && git checkout -q --orphan "$branch" && { git rm -rqf --cached . >/dev/null 2>&1 || true; } && git clean -fdxq)
fi

mkdir -p "$tmp/$dest"
cp "${shots[@]}" "$tmp/$dest/"
(
  cd "$tmp"
  git add "$dest"
  git commit -q -m "Screenshots: $dest"
  git push -q origin "HEAD:refs/heads/$branch"
)
sha=$(git -C "$tmp" rev-parse HEAD)

for shot in "${shots[@]}"; do
  name=$(basename "$shot")
  echo "![${name%.png}](https://raw.githubusercontent.com/$repo/$sha/$dest/$name)"
done
