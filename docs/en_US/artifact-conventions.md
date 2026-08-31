# Artifact conventions: local-first fixed paths

Every stage artifact in multi-agent work is written to the project repository, version-reviewed, and handed off by repo-relative path. Artifact sync skills must never access external platforms, read credentials, make network requests, or return URLs.

## Fixed mapping

| Artifact | Owner | Skill | Repo-relative path |
| --- | --- | --- | --- |
| PRD | @ProductManager | `multica-artifact-req-sync` | `artifacts/<issue-id>/prd.md` |
| Technical design | @Architect | `multica-artifact-design-sync` | `artifacts/<issue-id>/technical-design.md` |
| API contract | @BackendDev | `multica-artifact-api-sync` | `artifacts/<issue-id>/api-contract.md` |
| UI / interaction design | @Designer | `multica-artifact-ui-sync` | `artifacts/<issue-id>/ui-design.md` |
| Test cases / report | @Tester | `multica-artifact-test-sync` | `artifacts/<issue-id>/test-cases.md` |
| CI/CD result | @DevOps | `multica-artifact-cicd-sync` | `artifacts/<issue-id>/cicd-result.md` |

## Hard rules

1. Roles own content; artifact sync skills write it to fixed paths.
2. The Leader passes upstream repo-relative paths explicitly; downstream reads those paths without searching.
3. Absolute paths, `..`, external URLs, and “uploaded” responses without local files are forbidden.
4. Updating an Issue overwrites the same path; content changes immediately invalidate affected downstream gates.
5. The CI/CD skill records locally verifiable results; it does not call a remote pipeline.

## Why it works

Fixed paths make artifacts discoverable, diffable, and traceable while keeping the starter runnable without accounts, credentials, or network access.

## Common failures

- Content exists only in a comment: write the fixed file.
- A machine-local absolute path is returned: convert it to a repo-relative path.
- An external link replaces the content: land the required content in the repository first.
