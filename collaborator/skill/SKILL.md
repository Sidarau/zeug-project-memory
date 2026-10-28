---
name: zeug-collaborate
description: Work in a configured collaborator project with its own Linear workspace, shared memory and document workflow. Use for project onboarding, starting or resuming tracked work, recording decisions, and updating project SOPs in Codex or Claude Code.
metadata:
  tier: 1
  triggers: collaborator project setup, start project work, Linear handoff, shared project memory
  companions: —
---

# Collaborate on a Zeug project

Read `.zeug/project.json` in the current project directory. It identifies this
project's Linear organization, permitted teams/projects and memory connector.
This configuration is a scope boundary, not a credential or a grant of access.
Do not use another client's configuration, Alex's internal workspace or a
similarly named Linear project as a fallback.

## Start each session

1. Run `python3 .zeug/setup.py refresh --target .` (`python` on Windows).
   This checks the published GitHub kit, refreshes unchanged managed files and
   prints the exact content revision. Re-read this skill and the referenced
   SOPs after an update. If refresh fails or finds edits, report the actual
   failure and installed revision. Continue useful local reads/drafts; hold
   external writes until current instructions are verified. Never call a
   cached copy "latest". A running session must refresh again when asked to
   use an updated SOP.
2. Read `.zeug/PROJECT.md` and inspect the repository state. Use the user's
   own authenticated accounts. Setup does not sign in, accept consent,
   install a CLI or grant access on anyone's behalf.
3. Follow [Linear](references/linear.md) for tracked work. Read the issue and
   latest handoff before resuming; verify the workspace/team/project first.
4. Follow [shared memory](references/memory.md) for project context and durable
   decisions. Use only the configured project connector or the existing
   project-memory helper with an explicit project ID.

## During the work

Use [documents](references/documents.md) for reviews, suggestions and approvals.
Keep tracker state in Linear, deliverables in their repository or document,
and reusable facts in shared memory. A note is not proof of implementation.
Preserve local work, check the relevant result, and leave a handoff that another
person's AI can resume without this chat.

For onboarding or maintenance, read [setup and updates](references/updates.md).
If `.zeug/project.json` is missing, direct the user to their project's Memory
page on cmd.zeuglab.com and its project setup download; do not guess identifiers.
