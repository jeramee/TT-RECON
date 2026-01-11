# TT-RECON — Targeted Therapy Recon (truth-first)

**TT-RECON** is a standalone, truth-first pipeline that converts oncology alteration inputs (e.g., SNVs/indels/CNVs/fusions) into an **auditable targeted-therapy dossier**.

Core idea (strict, on purpose):

> Separate **what was observed**, **what was inferred**, and **what is speculative** —  
> and preserve an evidence trail for every claim.

TT-RECON is built to scale beyond a single gene (ALK/EGFR/etc.) by using **target packs** (rules + mappings + drug-class logic) and **connectors** (e.g., CIViC) while keeping the core engine deterministic and reproducible.

⚠️ **Research/education only — not medical advice.**  
This tool is not a clinical decision system and must not be used to prescribe treatment.

---

## Why this exists

People keep trying to build “one biology LLM” (DNA/RNA/proteins/drugs/receptor binding). That can be valuable, but it’s also the fastest way to get:

- hallucinated biomedical “facts”
- missing provenance
- non-reproducible outputs
- accidental clinical tone / liability

TT-RECON is the *scaffold* that keeps you honest:

- deterministic pipeline first
- evidence objects for every observation/enrichment
- explainable rules and scored hypotheses
- optional LLM layer later (translator-only), never the “oracle”

---

## What TT-RECON does (v0.5+)

Given a **Case JSON** (or future ingestion formats), TT-RECON:

1. **Loads + normalizes** the case
2. Builds **Evidence objects** for input observations
3. Optionally enriches evidence via **CIViC** (real connector)
4. Computes **Features** (signals derived from evidence)
5. Applies **Target Pack** rules (e.g., EGFR logic)
6. Emits **Claims** that must link back to evidence/features
7. Renders a human-readable **report** + a machine-readable manifest

---

## Quick start

### 1) Create + activate a venv (Windows PowerShell)
```powershell
cd TT-RECON
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

### 2) Install TT-RECON (editable)
```powershell
pip install -e .
```

### 3) Run the EGFR example
```powershell
ttrecon init
ttrecon list-targets
ttrecon run --case examples/cases/egfr_example.json --target EGFR --out out_egfr
```

Open:
- `out_egfr/report.md`

### 4) Run tests
```powershell
pip install pytest
pytest -q
```

---

## Inputs

### Case JSON (current “source of truth”)
TT-RECON expects a case file like:

- tumor metadata (optional)
- a list of alterations (SNV/INDEL/FUSION/CNV/EXPRESSION)
- optional notes

See:
- `examples/cases/egfr_example.json`

> The case input is treated as **Observed** data (Evidence objects are created from it).

---

## Outputs (auditable by design)

A run writes:

- `case_normalized.json` — normalized case snapshot
- `evidence.jsonl` — evidence objects (each has a stable ID)
- `features.json` — computed signals (evidence-linked)
- `claims.json` — scored claims (must link to evidence + features)
- `report.md` — human-readable dossier
- `run_manifest.json` — fingerprints + output paths + run metadata

**The invariant:** claims must be traceable to evidence IDs.  
If you can’t point at evidence, it shouldn’t be a claim.

---

## Target Packs (how TT-RECON scales beyond ALK)

Targets are **plug-ins** under `ttrecon/targets/<TARGET>/`.

A target pack usually includes:

- `target.yml` — metadata + drug-class map + known patterns
- `mappings.yml` — synonyms, numbering quirks, alias handling
- `rules.py` — deterministic rules that produce claims
- tests — minimal proof that the pack triggers correctly

This lets you add targets without rewriting the core engine.

Examples you’ll likely want next:
- KRAS, BRAF, MET, RET, ROS1, ERBB2 (HER2)

---

## CIViC integration (real connector)

TT-RECON can optionally enrich a case using CIViC evidence (variant ↔ interpretation ↔ citations).

Common modes:

- **strict (default)**: tries to match CIViC evidence to the specific alteration (gene + protein change when available)
- **loose**: pulls broader CIViC evidence for the gene (useful for discovery; noisier)

Caching:
- requests are cached under something like:
  - `.ttrecon_cache/civic/requests/`

Delete the cache folder to force re-fetching.

Environment variables (typical knobs):
- `TTRECON_CIVIC_ENABLED=1`
- `TTRECON_CIVIC_MODE=strict|loose`
- `TTRECON_CACHE_DIR=.ttrecon_cache`

> CIViC enrichments become **Evidence objects**, never “free text knowledge.”

---

## How to think about “one biology LLM” here

You can still pursue the “language of life” direction — just don’t make it the core truth engine.

**Recommended framing:**
- “Biology foundation models” produce **features** (embeddings, similarity scores, cluster assignments)
- TT-RECON still gates **claims** via evidence + deterministic logic + tests

That gives you the upside (pattern discovery) without letting a model invent “facts.”

### Using ChatGPT vs a Custom GPT (recommended split)

**ChatGPT (general) is great for:**
- drafting readable summaries *from already-produced claims*
- literature triage *when you provide the documents/snippets*
- brainstorming hypotheses (must be labeled speculative)

**A Custom GPT is best as a strict operator UI:**
- only answers by calling TT-RECON tools
- refuses to generate claims without evidence IDs
- enforces “Observed / Inferred / Speculative” formatting
- blocks clinical phrasing (dose/regimen/prescription language)

> The Custom GPT should behave like a cockpit, not a brain.

---

## Safety, boundaries, and provenance (non-negotiables)

TT-RECON is designed to reduce common failure modes:

- **Hallucinations:** claims must link to evidence IDs
- **Reproducibility:** same inputs → same outputs (plus cached snapshots)
- **Medical advice boundary:** reports avoid prescriptive language by design
- **PHI hygiene:** don’t feed patient identifiers into LLM prompts; keep runs local

If you later add an LLM narrator:
- it should be **translator-only**
- it should cite **evidence IDs**
- it must fail closed (fallback to deterministic template) if it can’t comply

---

## Repository layout (high level)

- `ttrecon/engine/` — orchestrator + scoring
- `ttrecon/ingest/` — case loader + normalization
- `ttrecon/targets/` — target packs (EGFR, etc.)
- `ttrecon/connectors/` — CIViC and future stubs (OncoKB, DepMap, ChEMBL…)
- `ttrecon/report/` — renderers/templates
- `examples/` — example cases/configs
- `tests/` — minimal regression tests

---

## Roadmap (suggested)

**Near-term “high ROI”:**
- Add more target packs (KRAS/BRAF/MET/ERBB2)
- Expand case ingestion (VCF/MAF, CNV tables, RNA outliers)
- Add more curated connectors (OncoKB/DepMap/ChEMBL) as evidence sources

**Research track (parallel, optional):**
- sequence/protein/chemistry embeddings → feature-only modules
- clustering + similarity search across resistance “profiles”

---

## License

MIT
