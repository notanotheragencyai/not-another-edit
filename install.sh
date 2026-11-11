#!/bin/bash
# Installs or updates the Not Another Edit skills into Claude Code's skills folder:
# both by default (not-another-edit and edit-this-video), or only the ones named.
# Safe to run again: an older copy is moved to a backup folder (never deleted), and each skill's saved
# settings (config.json) are carried over. Your style folder and your videos are never touched.
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
ALL="not-another-edit edit-this-video"
PICK="${*:-$ALL}"
SKILLS="$HOME/.claude/skills"
BACKUP="$HOME/.claude/skills-backup/$(date +%Y-%m-%d-%H%M%S)"

for NAME in $PICK; do
  [ -f "$HERE/skills/$NAME/SKILL.md" ] || { echo "No skill called $NAME. Pick from: $ALL"; exit 1; }
done
mkdir -p "$SKILLS"

for NAME in $PICK; do
  DEST="$SKILLS/$NAME"
  if [ -e "$DEST" ]; then
    mkdir -p "$BACKUP"
    mv "$DEST" "$BACKUP/$NAME"
    echo "  moved your old $NAME to $BACKUP/$NAME"
  fi
  cp -R "$HERE/skills/$NAME" "$DEST"
  find "$DEST" \( -name "__pycache__" -o -name ".DS_Store" -o -name "._*" \) -prune -exec rm -rf {} +
  if [ -f "$BACKUP/$NAME/config.json" ]; then
    cp "$BACKUP/$NAME/config.json" "$DEST/config.json"
    echo "  kept your saved settings for $NAME"
  fi
  echo "  installed $NAME"
done

echo ""
echo "Done. Start a new Claude Code chat, then type /not-another-edit to build your editing style."
echo "When your style is ready, type /edit-this-video and point it at a folder of clips."
