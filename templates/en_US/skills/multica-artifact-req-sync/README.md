# multica-artifact-req-sync

PRD landing orchestration: repository-local Markdown by default; call `multica-platform-confluence` and `multica-platform-jira` only when external synchronization is explicitly required.

## Quick start

1. Copy this directory into Multica Skills.
2. Local mode needs no configuration:

```bash
bash scripts/publish-local.sh --issue-id <ISSUE-ID> --input <PRD.md>
```

The script returns `artifacts/<issue-id>/prd.md`; downstream uses that repo-relative path.

3. For external mode, also install and configure the required `multica-platform-*` skills, then invoke that adapter as described in its `SKILL.md`.

See `SKILL.md` for the mode contract and fallback rules.
