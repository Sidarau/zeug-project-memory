# Linear workflow

Read the `linear` object in `.zeug/project.json`. Before the first write in a
session, use the connected tools to resolve that organization, team and the
specific issue's project. Match IDs, not display names alone. If the tools
cannot expose the organization ID, verify its workspace URL plus team and
project IDs. A personal OAuth login may have access to several workspaces;
being authenticated does not establish that the right one is active.

For a new request, search within the configured scope before creating an
issue. Record the goal, deliverable, acceptance checks and dependencies. Use
the project's actual workflow states; map by state type and meaning rather
than assuming every workspace uses the same names. Do not create states or
labels to make this SOP fit, take another person's assignment, or bulk change
issues without an explicit request. If several listed projects could own the
work, ask which one rather than silently choosing the first.

For an existing request, read its full description, dependencies and newest
handoff. Confirm it is in an allowed team/project. Put it in progress while
working. If blocked, record the failing check, what is needed and what can
continue. Use review while a required review, merge or deployment remains.
Use done only when the issue's acceptance checks are evidenced.

Leave a concise receipt with the artifact or pull request URL, revision,
verification result and remaining work. A partial handoff also names the
branch, exact next step and commands needed to verify. Do not duplicate the
same progress comment on retries. On an uncertain write, read the object back
before retrying so you do not create duplicate issues or comments.

If Linear is unavailable, keep a temporary handoff in `.zeug/HANDOFF.md` with
the issue ID and exact error. Continue independent authorized work, reconcile
the handoff when access returns and report unresolved tracking honestly.
