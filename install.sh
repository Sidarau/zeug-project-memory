#!/bin/sh
# One-step setup for a Zeug Lab project's memory, run from the command shown on cmd.zeuglab.com:
#   curl -fsSL https://cmd.zeuglab.com/install.sh | ZEUG_PROJECT=<project> ZEUG_KEY=<key> sh
# Installs the zeug-project-memory skill for Claude Code (and Codex, if installed) and saves the key in
# ~/.config/zeug/<project>.env, readable only by you. Re-running it updates the skill and replaces the key.
set -eu

repo="${ZEUG_REPO_RAW:-https://raw.githubusercontent.com/Sidarau/zeug-project-memory/main}"
project="${ZEUG_PROJECT:-}"
key="${ZEUG_KEY:-}"
api="${ZEUG_API:-https://cmd.zeuglab.com}"

case "$project" in ""|*[!a-z0-9-]*) echo "ZEUG_PROJECT is missing or not a project id. Copy the command again from cmd.zeuglab.com." >&2; exit 1;; esac
case "$key" in zlm_*) ;; *) echo "ZEUG_KEY is missing. Copy the command again from cmd.zeuglab.com." >&2; exit 1;; esac
command -v curl >/dev/null || { echo "curl is required." >&2; exit 1; }

# Optional full project setup, requested by CMD's current one-click command. No key enters the project directory.
if [ "${ZEUG_PROJECT_SETUP:-0}" = "1" ]; then
  command -v python3 >/dev/null || { echo "Project setup requires Python 3.9 or newer; use the project download after installing Python." >&2; exit 1; }
  setup_tmp=$(mktemp -d)
  trap 'rm -rf "$setup_tmp"' EXIT
  printf 'Authorization: Bearer %s\n' "$key" | curl -fsSL -H @- "$api/api/agent/setup" -o "$setup_tmp/project.json"
  curl -fsSL "$repo/collaborator/kit.json" -o "$setup_tmp/kit.json"
  python3 - "$setup_tmp" <<'PYKIT'
import hashlib,json,pathlib,sys
p=pathlib.Path(sys.argv[1]);k=json.loads((p/'kit.json').read_text());s=k['files']['setup.py']
assert hashlib.sha256(s.encode()).hexdigest()==k['sha256']['setup.py'], 'Invalid setup checksum'
(p/'setup.py').write_text(s)
PYKIT
  python3 "$setup_tmp/setup.py" init --kit "$setup_tmp/kit.json" --profile "$setup_tmp/project.json" --target "${ZEUG_PROJECT_DIR:-$PWD/$project}"
  echo "Project setup is ready. Your existing global skills and saved keys were not changed. Sign in to the project connectors with your own accounts."
  exit 0
fi

install_skill() {
  dest="$1/zeug-project-memory"
  mkdir -p "$dest/bin"
  curl -fsSL "$repo/SKILL.md" -o "$dest/SKILL.md"
  curl -fsSL "$repo/bin/zm" -o "$dest/bin/zm"
  chmod 755 "$dest/bin/zm"
  curl -fsSL "$repo/bin/zm.ps1" -o "$dest/bin/zm.ps1"   # for PowerShell on the same machine
  curl -fsSL "$repo/bin/zm.cmd" -o "$dest/bin/zm.cmd"
  echo "Installed the skill in $dest"
}

install_home="${ZEUG_INSTALL_HOME:-$HOME}"
install_skill "$install_home/.claude/skills"
[ -d "$install_home/.codex" ] && install_skill "$install_home/.codex/skills"

conf="${ZEUG_CONFIG_DIR:-$HOME/.config/zeug}"
mkdir -p "$conf"
chmod 700 "$conf"
umask 077
printf 'ZEUG_PROJECT=%s\nZEUG_MEMORY_KEY=%s\nZEUG_API=%s\n' "$project" "$key" "$api" > "$conf/$project.env"
chmod 600 "$conf/$project.env"
echo "Saved your key for $project in $conf/$project.env"

if "$install_home/.claude/skills/zeug-project-memory/bin/zm" -p "$project" project | grep -q '"project"'; then
  echo "Connected. Ask your AI about $project, for example: \"What's in the $project project memory?\""
else
  echo "Installed, but the test call failed. Check the key on cmd.zeuglab.com and run the command again." >&2
  exit 1
fi
