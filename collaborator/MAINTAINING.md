# Publish an SOP or feature update

Collaborators check the published kit on GitHub at the start of each AI session.
No scheduled job or new service is needed.

1. Edit the universal skill and references in the canonical `Sidarau/skills`
   authoring checkout under `zeug-collaborate`. Validate it and open a review PR.
2. Export the reviewed source into this repository:
   `python3 collaborator/build.py --skill /path/to/skills/zeug-collaborate`.
3. Run `python3 -m unittest discover -s collaborator -p 'test_*.py'` and review
   the public export. It must contain no client configuration or credentials.
4. Commit `collaborator/skill`, `collaborator/setup.py` and `collaborator/kit.json`
   together in a PR. Merge after checks and review. This is the publication step.
5. At the next session, each configured agent runs its local
   `.zeug/setup.py refresh --target .`. It fetches the current kit from GitHub,
   checks every file's content digest, preserves unrelated local files, and
   records the installed kit digest. Network errors or local conflicts stop
   updates and are reported. New installer code is saved but not executed by
   the current updater invocation.

The exported plain Markdown files live in `collaborator/skill`, so they can be
reviewed on GitHub without opening generated JSON. When editing this export
first, reconcile it into the canonical skill review branch before publishing.
`python3 collaborator/build.py` rebuilds the kit from the exported files;
continuous integration rejects a stale generated kit.

For client-specific Linear mappings, use **Project setup settings** in that
project's Memory page. New downloads and one-click installs read the saved
mapping. Existing folders get a revised mapping by downloading and applying a
new profile. Do not put workspace IDs, client names or private SOPs in this
public distribution. Project-specific decisions belong in scoped shared memory.

A profile never supplies permission to Linear. Each collaborator authenticates
with their own account, and the agent verifies workspace/team/project IDs before
writing. A wrong account or missing membership cannot be repaired by copying
Alex's credentials.
