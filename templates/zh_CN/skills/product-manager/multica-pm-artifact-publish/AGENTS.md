# multica-pm-artifact-publish — Agent notes

- Orchestrates `multica-platform-confluence` + `multica-platform-jira`; do not duplicate REST scripts here.
- Resolve platform paths via `scripts/按 skill 名.sh` or `MULTICA_SKILLS_ROOT`.
- Credential priority: `JIRA_USERNAME / JIRA_PASSWORD` → skill `.env`.
