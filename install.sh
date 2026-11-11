#!/bin/bash
# Installs or updates the Not Another Edit skill into Claude Code's skills folder.
# Safe to run again: an older copy is moved to a backup folder (never deleted), and the saved
# style folder setting (config.json) is carried over. Your style folder itself is never touched.
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
NAME="not-another-edit"
SKILLS="$HOME/.claude/skills"
DEST="$SKILLS/$NAME"

[ -f "$HERE/skills/$NAME/SKILL.md" ] || { echo "Can't find skills/$NAME next to this script."; exit 1; }
mkdir -p "$SKILLS"

if [ -e "$DEST" ]; then
  BACKUP="$HOME/.claude/skills-backup/$(date +%Y-%m-%d-%H%M%S)"
  mkdir -p "$BACKUP"
  mv "$DEST" "$BACKUP/$NAME"
  echo "  moved your old copy to $BACKUP/$NAME"
fi

cp -R "$HERE/skills/$NAME" "$DEST"
find "$DEST" \( -name "__pycache__" -o -name ".DS_Store" \) -prune -exec rm -rf {} +

if [ -n "$BACKUP" ] && [ -f "$BACKUP/$NAME/config.json" ]; then
  cp "$BACKUP/$NAME/config.json" "$DEST/config.json"
  echo "  kept your saved style folder"
fi

echo "  installed $NAME"
echo ""
echo "Done. Start a new Claude Code chat, then type /not-another-edit to build your editing style."
