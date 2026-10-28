# zeug-project-memory

A skill that lets your AI tools (Claude Code, Codex, and any agent that can run a shell command) use your Zeug Lab project: its shared memory, its agreements and its published pages, on [cmd.zeuglab.com](https://cmd.zeuglab.com).

## Install (one step)

Open your project on cmd.zeuglab.com, go to **Project memory → Connect your AI**, press **Connect my AI**, and paste the command it shows into a terminal. It looks like this:

Mac and Linux (terminal):

```bash
curl -fsSL https://cmd.zeuglab.com/install.sh | ZEUG_PROJECT=<project> ZEUG_KEY=<your key> sh
```

Windows (PowerShell):

```powershell
$env:ZEUG_PROJECT='<project>'; $env:ZEUG_KEY='<your key>'; irm https://cmd.zeuglab.com/install.ps1 | iex
```

The command:
- installs the skill in `~/.claude/skills/zeug-project-memory`, and in `~/.codex/skills/` if you use Codex;
- saves your key in `~/.config/zeug/<project>.env`, readable only by you;
- checks the connection.

Then ask your AI about the project.

For Cursor or another tool, point it at `SKILL.md` (for example, copy it into `.cursor/rules/`). The helper commands work from any terminal.

## What the key can do

A key belongs to one person and one project. It can search that project's memory and read its documents and drops. A "search and add" key can also add notes. It cannot see other projects or Zeug Lab's internal memory, and it stops working when you revoke it on cmd.zeuglab.com or leave the project.

## Commands

```bash
zm project                     # memory status, documents, drops
zm search "question"
zm recent
zm doc <document-id>
zm add "title" < note.txt
```

`zm` lives at `~/.claude/skills/zeug-project-memory/bin/zm`; on Windows, PowerShell and cmd use `zm.cmd` in the same folder, and Git Bash or WSL use `zm`. Both read the same key file. Read [install.sh](install.sh), [install.ps1](install.ps1), [bin/zm](bin/zm) and [bin/zm.ps1](bin/zm.ps1) before running them; all are short. The installers are tested on Windows, macOS and Linux against a local stand-in for cmd ([.github/workflows/installers.yml](.github/workflows/installers.yml)).


## Full collaborator project setup

Project memory now offers **Download project setup** and an expanded one-click
command. The owner configures the project's Linear workspace once in CMD. Each
collaborator receives the appropriate profile without seeing another client's
settings. The public kit has no client data or credentials.

The kit creates AGENTS.md for Codex, CLAUDE.md for Claude Code, a universal
`zeug-collaborate` skill, Linear SOPs and project-scoped MCP configurations.
Python 3.9 or newer is required for this optional project setup. Existing files
are preserved; conflicts stop preflight before any project file is written.
Each person completes their own OAuth sign-ins. The existing memory-only
installer still works without enabling project setup.

Download the current GitHub sources with **Code → Download ZIP**, or clone
this repository. For a configured project use the authenticated download in
CMD; it adds your project's profile and START-HERE.md. Generic source alone
does not contain a client profile.

At each AI session the project instructions run a GitHub update check. Your
agent reads the refreshed skill/SOPs, reports the installed content revision,
and reports an offline or conflicting copy as stale. See
[maintaining the kit](collaborator/MAINTAINING.md) to publish SOPs and features
once for all collaborators.

Official configuration references:
[Codex](https://learn.chatgpt.com/docs/extend/mcp?surface=cli),
[Claude Code](https://code.claude.com/docs/en/mcp), and
[Linear](https://linear.app/docs/mcp).
