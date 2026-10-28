# Setup and updates

The public distribution is
[Sidarau/zeug-project-memory](https://github.com/Sidarau/zeug-project-memory).
The owner maintains the universal skill in `Sidarau/skills/zeug-collaborate`
and publishes a reviewed kit to `collaborator/kit.json` in the distribution.
Client workspace metadata stays in CMD and the collaborator's project profile,
outside the public repository.

Download the project kit from Project memory → Project setup. Extract it,
review START-HERE.md, and run `python3 setup.py init --profile project.json
--target /path/to/project` (Windows: `python`). It creates project instructions,
SOPs, local skills for both tools, and credential-free MCP configuration. For
existing projects it appends a marked instruction block and preserves unrelated
configuration; a conflicting file stops the whole preflight before any write.
It never changes global permissions, signs in or installs dependencies.

In Codex, trust the project when prompted, then authenticate the two named MCP
servers using `codex mcp login <name>` or the app's connection controls. In
Claude Code, open the project, review its MCP servers and use `/mcp` to sign in.
Select the Linear workspace listed in `.zeug/PROJECT.md`; do not approve an
unrelated organization. Restart the agent after installing a new skill.

Run `python3 .zeug/setup.py refresh --target .` at each session start. It checks
GitHub's published kit and updates only previously managed files that have not
been edited locally. A content digest in `.zeug/installed.json` records the
actual kit. Local changes, network failures or unsupported versions produce a
nonzero exit and leave the installation intact. The updater does not run any
downloaded program; a changed setup program takes effect on the next invocation.

Profile identifiers are not an access-control mechanism. The service enforces
membership and each person's OAuth permissions. When a project's Linear mapping
changes, the owner updates Project setup settings in CMD; collaborators download
the revised profile and rerun init. Universal SOP/features update from GitHub
without redistributing each client profile. Check shared memory for project
decisions in addition to GitHub for operating instructions.

Official references checked October 2026:

- [Codex project skills](https://learn.chatgpt.com/docs/build-skills)
- [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Claude Code project MCP](https://code.claude.com/docs/en/mcp)
- [Linear MCP](https://linear.app/docs/mcp)
