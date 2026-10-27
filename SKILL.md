---
name: zeug-project-memory
description: Use the shared project memory and files of a Zeug Lab project (cmd.zeuglab.com). Search what the team knows before answering questions about the project, read its agreements and published pages, and record decisions and facts worth keeping. Use whenever the user mentions their Zeug Lab project, its memory, documents or drops.
---

# Zeug Lab project memory

Your user works on a project with Zeug Lab. Its shared memory, agreements (Documents) and published pages (Drops) live in the Zeug Lab command panel, cmd.zeuglab.com. This skill gives you read access to them, plus the ability to add notes when the user's key allows it.

## Setup check

The helper `bin/zm` next to this file reads the user's access key from `~/.config/zeug/<project>.env`, which the one-step install from cmd.zeuglab.com creates. Run it by its full path:

```bash
~/.claude/skills/zeug-project-memory/bin/zm projects     # which projects are set up on this machine
```

If no project is set up, ask the user to open their project on cmd.zeuglab.com, go to **Project memory → Connect your AI**, and run the command shown there (a PowerShell line on Windows, a terminal command on Mac and Linux). Never ask the user to paste the key into the chat.

## Commands

With more than one project set up, add `-p <project>` before the command.

```bash
zm project                        # overview: memory status, documents, drops
zm search "what did we decide about pricing"
zm recent                         # newest notes
zm doc <document-id>              # full text of an agreement (from `zm project`)
zm add "Short title" <<'EOF'      # record a note (keys with "search and add" only)
What was decided or learned, with names, dates and numbers.
EOF
```

`zm` is `~/.claude/skills/zeug-project-memory/bin/zm` (or the same path under `~/.codex/skills/`). On Windows, Claude Code's Bash (Git Bash) runs that same file; in PowerShell or cmd use `zm.cmd` next to it (`%USERPROFILE%\.claude\skills\zeug-project-memory\bin\zm.cmd`), and pipe note text into `zm.cmd add "title"`.

## How to work with it

- Search the memory before answering anything about the project. Name the notes you used.
- Search finds notes by their words: use the terms the team would have written (names, products, places), and try a second phrasing if the first finds nothing.
- Add a note when the user makes a decision, learns a fact worth keeping, or finishes a call. One topic per note, with a title someone could search for later. Notes cannot be edited or deleted, so write them carefully.
- Everyone on the project, and the AI tools they connect, can read what you add. Do not add passwords, keys, personal data such as birthdays or ID numbers, or anything about other clients.
- Documents are agreements under review or signed. Quote them exactly; for changes, tell the user to suggest them on cmd.zeuglab.com.
- The key works for one project only and acts as the user. Never print it or write it anywhere else.

## Errors

- `401`: the key was revoked or the user left the project. Ask them to reconnect on cmd.zeuglab.com.
- `403` on add: the key is search-only.
- `409`: project memory is off. The user can turn it on in cmd.
