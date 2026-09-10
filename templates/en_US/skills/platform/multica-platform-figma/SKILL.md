---
name: multica-platform-figma
description: Figma integration—read Figma file metadata / design summaries for UI test points and design traceability. Credentials and CLI are only looked up here.
version: 1.0.0
metadata:
  scripts:
    - scripts/fetch_file.py
  externals:
    - figma-api
---

# Figma Platform

## Responsibility
Integrate Figma: read file metadata / design summaries so downstream skills (designer, tester) can derive UI test points and design traceability. All Figma credentials and the Figma API are only looked up here.

## Capabilities
- `fetch_file.py`: pull a Figma file's nodes/metadata by file key.
- Summarize design states (normal/empty/error/loading) for test-point generation.

## Usage
- Designer: consume design links produced here.
- Tester (T1): derive UI checkpoints from the design summary (see `multica-test-t1-design` → `web-ui-checkpoints.md`).

## Credentials
- `FIGMA_TOKEN` via environment variable or Secret; see `scripts/fetch_file.py --help`.
- Never hardcode tokens in skill content.
