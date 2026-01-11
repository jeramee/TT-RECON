# TT-RECON v0.5 — Install & Run

## Install (editable)
```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

## Run (baseline)
```bash
ttrecon run --case examples/cases/egfr_example.json --target EGFR --out out_egfr
```

## CIViC (live)
```bash
ttrecon run --case examples/cases/egfr_example.json --target EGFR --out out_egfr \
  --civic --civic-mode strict --civic-source live
```

## CIViC (cache-only; zero network)
```bash
ttrecon run --case examples/cases/egfr_example.json --target EGFR --out out_egfr \
  --civic --civic-source cache
```

## CIViC (snapshot; zero network)
### 1) Build a snapshot (network once)
```bash
ttrecon civic sync --genes EGFR,ALK,KRAS --out .ttrecon_cache/civic/snapshots/civic_snapshot.json
```

### 2) Run using the snapshot
```bash
ttrecon run --case examples/cases/egfr_example.json --target EGFR --out out_egfr \
  --civic --civic-source snapshot --civic-snapshot .ttrecon_cache/civic/snapshots/civic_snapshot.json \
  --civic-mode strict --civic-claims --civic-min-rating 3
```

Notes:
- Snapshot mode is deterministic and portable. Commit the snapshot if you want reproducible builds.
- `cache` mode is for "no network now" environments where you already have cached request files.
