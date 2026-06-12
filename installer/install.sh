#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-$HOME/.codex/skills}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$REPO_ROOT/skills/research-portal-harness"
DEST="$TARGET/research-portal-harness"

if [ ! -f "$SOURCE/SKILL.md" ]; then
  echo "Missing skill source: $SOURCE" >&2
  exit 1
fi

mkdir -p "$TARGET"
rm -rf "$DEST"
cp -R "$SOURCE" "$DEST"

echo "Installed research-portal-harness to $DEST"
echo "Invoke it with: Use \$research-portal-harness to connect my subscribed research portals."

