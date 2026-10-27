#!/bin/sh
# One-step setup for a Zeug Lab project's memory, run from the command shown on cmd.zeuglab.com:
#   curl -fsSL https://cmd.zeuglab.com/install.sh | ZEUG_PROJECT=<project> ZEUG_KEY=<key> sh
# Installs the zeug-project-memory skill for Claude Code (and Codex, if installed) and saves the key in
# ~/.config/zeug/<project>.env, readable only by you. Re-running it updates the skill and replaces the key.
set -eu

repo="https://raw.githubusercontent.com/Sidarau/zeug-project-memory/main"
project="${ZEUG_PROJECT:-}"
key="${ZEUG_KEY:-}"
api="${ZEUG_API:-https://cmd.zeuglab.com}"

case "$project" in ""|*[!a-z0-9-]*) echo "ZEUG_PROJECT is missing or not a project id. Copy the command again from cmd.zeuglab.com." >&2; exit 1;; esac
case "$key" in zlm_*) ;; *) echo "ZEUG_KEY is missing. Copy the command again from cmd.zeuglab.com." >&2; exit 1;; esac
command -v curl >/dev/null || { echo "curl is required." >&2; exit 1; }

install_skill() {
  dest="$1/zeug-project-memory"
  mkdir -p "$dest/bin"
  curl -fsSL "$repo/SKILL.md" -o "$dest/SKILL.md"
  curl -fsSL "$repo/bin/zm" -o "$dest/bin/zm"
  chmod 755 "$dest/bin/zm"
  echo "Installed the skill in $dest"
}

install_skill "$HOME/.claude/skills"
[ -d "$HOME/.codex" ] && install_skill "$HOME/.codex/skills"

conf="${ZEUG_CONFIG_DIR:-$HOME/.config/zeug}"
mkdir -p "$conf"
chmod 700 "$conf"
umask 077
printf 'ZEUG_PROJECT=%s\nZEUG_MEMORY_KEY=%s\nZEUG_API=%s\n' "$project" "$key" "$api" > "$conf/$project.env"
chmod 600 "$conf/$project.env"
echo "Saved your key for $project in $conf/$project.env"

if "$HOME/.claude/skills/zeug-project-memory/bin/zm" -p "$project" project | grep -q '"project"'; then
  echo "Connected. Ask your AI about $project, for example: \"What's in the $project project memory?\""
else
  echo "Installed, but the test call failed. Check the key on cmd.zeuglab.com and run the command again." >&2
  exit 1
fi
