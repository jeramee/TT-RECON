# TT-RECON (v0.5)

Standalone, truth-first targeted therapy recon pipeline.

## Install & Run
See `INSTALL.md`.

## What v0.5 adds (over v0.4)
- **Offline CIViC snapshot mode** (run with zero network)
- `ttrecon civic sync` command to build/update a local snapshot JSON
- `--civic-source live|cache|snapshot` controls where CIViC data comes from:
  - `live` (default): network + cache
  - `cache`: cache-only (no network; uses cached request files)
  - `snapshot`: local snapshot JSON (recommended for airgapped runs)
