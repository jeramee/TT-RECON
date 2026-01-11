# CIViC connector (v0.5)

TT-RECON uses CIViC V2 GraphQL for enrichment and supports **offline operation**.

## Modes
- `live`: network + cache
- `cache`: cache-only (no network). Missing cache entries become `CACHE_MISS` evidence rows.
- `snapshot`: offline snapshot JSON (recommended for airgapped/reproducible runs)

## Build a snapshot
```bash
ttrecon civic sync --genes EGFR,ALK,KRAS --out .ttrecon_cache/civic/snapshots/civic_snapshot.json
```

Snapshot schema: `civic_snapshot_v1`
- Stores gene -> evidenceItems.nodes
- Designed to be portable and deterministic.

## Notes
- CIViC is a research knowledgebase; TT-RECON is not medical advice.
