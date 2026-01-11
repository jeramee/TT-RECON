from pathlib import Path
from typing import List

from ttrecon.config import TTReconConfig
from ttrecon.core.ids import stable_id, IDPrefixes
from ttrecon.core.io import write_json_model, write_json_models, write_jsonl
from ttrecon.core.models import Case, Evidence, Feature, Report, RunManifest
from ttrecon.core.provenance import utc_now_iso, file_sha256
from ttrecon.engine.feature_builder import build_base_features
from ttrecon.engine.scoring import rank_claims
from ttrecon.engine.claim_builder import finalize_claims
from ttrecon.engine.civic_claims import claims_from_civic_evidence
from ttrecon.ingest.normalize import normalize_case
from ttrecon.ingest.validators import validate_case
from ttrecon.targets.registry import resolve_target, load_rules_callable
from ttrecon.version import __version__

from ttrecon.connectors.civic.client import civic_enrich

def run_pipeline(
    config: TTReconConfig,
    case_path: Path,
    target: str,
    out_dir: Path,
    civic: bool = False,
    civic_mode: str | None = None,
    civic_source: str | None = None,
    civic_snapshot: Path | None = None,
    civic_claims: bool = False,
    civic_min_rating: float | None = None,
    civic_levels: str | None = None,
) -> RunManifest:
    started = utc_now_iso()
    out_dir.mkdir(parents=True, exist_ok=True)

    from ttrecon.ingest.case_loader import load_case_json
    case: Case = load_case_json(case_path)
    case = normalize_case(case)
    validate_case(case)

    run_id = stable_id(IDPrefixes.RUN, case.case_id, target.upper(), started)

    evidence: List[Evidence] = []
    for i, alt in enumerate(case.alterations):
        evid_id = stable_id(
            IDPrefixes.EVID,
            case.case_id,
            "local_case",
            str(i),
            alt.gene,
            alt.type,
            alt.protein_change or "",
            alt.exon or "",
        )
        evidence.append(Evidence(
            evid_id=evid_id,
            source="local_case",
            kind="alteration",
            ref=str(case_path),
            payload=alt.model_dump(),
        ))

    civic_enabled = civic or config.civic_enabled
    if civic_enabled:
        mode = (civic_mode or config.civic_mode or "strict").strip().lower()
        source = (civic_source or config.civic_source or "live").strip().lower()
        snap = civic_snapshot or config.civic_snapshot_path
        config.civic_cache_dir.mkdir(parents=True, exist_ok=True)
        evidence.extend(
            civic_enrich(
                case,
                cache_dir=config.civic_cache_dir,
                mode=mode,
                source=source,
                snapshot_path=snap,
                max_items=config.civic_max_items,
                min_delay_s=config.civic_min_delay_s,
            )
        )

    features: List[Feature] = build_base_features(case, evidence)

    target_name, _target_dir = resolve_target(config.targets_dir, target)
    rules_fn = load_rules_callable(target_name)
    claims = rules_fn(case, evidence, features)

    civic_claims_enabled = civic_claims or config.civic_claims_enabled
    if civic_claims_enabled:
        mr = config.civic_claims_min_rating if civic_min_rating is None else float(civic_min_rating)
        lv = config.civic_claims_levels if civic_levels is None else str(civic_levels or "")
        claims.extend(claims_from_civic_evidence(
            case,
            evidence=evidence,
            features=features,
            min_rating=mr,
            allowed_levels_csv=lv,
        ))

    claims = finalize_claims(claims)
    claims_ranked = rank_claims(claims)

    overview = f"TT-RECON v{__version__} run_id={run_id} target={target_name} case={case.case_id}"
    report = Report(
        run_id=run_id,
        target=target_name,
        case_id=case.case_id,
        overview=overview,
        claims_ranked=claims_ranked,
        limitations=[
            "v0.5 deterministic rules + optional CIViC enrichment/promotion; not clinical guidance.",
            "Snapshot mode is for reproducible, offline evidence indexing (not recommendations).",
            "Therapy history and assay-specific context not modeled unless provided in inputs.",
            "If you add an LLM narrator later, it must only paraphrase existing claims + cite evidence IDs."
        ]
    )

    outputs = {}
    p_case = out_dir / "case_normalized.json"
    write_json_model(p_case, case); outputs["case_normalized"] = str(p_case)

    p_evid = out_dir / "evidence.jsonl"
    write_jsonl(p_evid, (e.model_dump() for e in evidence)); outputs["evidence_jsonl"] = str(p_evid)

    p_feat = out_dir / "features.json"
    write_json_models(p_feat, features); outputs["features"] = str(p_feat)

    p_claims = out_dir / "claims.json"
    write_json_models(p_claims, claims_ranked); outputs["claims"] = str(p_claims)

    from ttrecon.report.render_md import render_report_md
    p_md = out_dir / "report.md"
    render_report_md(report, evidence, features, p_md); outputs["report_md"] = str(p_md)

    finished = utc_now_iso()
    manifest = RunManifest(
        run_id=run_id,
        version=__version__,
        target=target_name,
        case_path=str(case_path),
        case_sha256=file_sha256(case_path),
        started_utc=started,
        finished_utc=finished,
        outputs=outputs
    )

    p_manifest = out_dir / "run_manifest.json"
    write_json_model(p_manifest, manifest); outputs["run_manifest"] = str(p_manifest)

    manifest.outputs = outputs
    write_json_model(p_manifest, manifest)

    return manifest
