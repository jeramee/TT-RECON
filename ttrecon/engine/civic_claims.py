from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

from ttrecon.core.ids import stable_id, IDPrefixes
from ttrecon.core.models import Case, Claim, Evidence, Feature

def _parse_levels(levels_csv: str) -> Set[str]:
    if not levels_csv:
        return set()
    return {x.strip().upper() for x in levels_csv.split(",") if x.strip()}

def _safe_float(x) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0

def _short_drug_list(node: Dict) -> str:
    drugs = node.get("drugs") or []
    names = [d.get("name") for d in drugs if d.get("name")]
    if not names:
        return "N/A"
    if len(names) <= 4:
        return ", ".join(names)
    return ", ".join(names[:4]) + f" (+{len(names)-4} more)"

def _node_signature(node: Dict) -> Tuple[str, str, str]:
    gene = ((node.get("gene") or {}).get("name") or "").upper()
    var = ((node.get("variant") or {}).get("name") or "")
    eid = str(node.get("id") or "")
    return gene, var, eid

def claims_from_civic_evidence(
    case: Case,
    evidence: List[Evidence],
    features: List[Feature],
    min_rating: float = 0.0,
    allowed_levels_csv: str = "",
) -> List[Claim]:
    """Promote CIViC evidence items (Evidence rows) into structured Claims.

    This is *not* a recommender; it's an auditable summarizer:
    - Every Claim cites one CIViC evidence row by evid_id.
    - Filters can be applied via rating and evidenceLevel allowlist.
    """
    allowed_levels = _parse_levels(allowed_levels_csv)
    feat_ids = [f.feat_id for f in features]

    out: List[Claim] = []
    seen: Set[Tuple[str, str, str]] = set()

    for ev in evidence:
        if ev.source != "civic" or ev.kind != "annotation":
            continue

        civic = (ev.payload or {}).get("civic") or {}
        if not civic:
            continue

        gene, var, eid = _node_signature(civic)
        if not eid:
            continue

        # De-dup (sometimes multiple alterations query same node)
        sig = (gene, var, eid)
        if sig in seen:
            continue
        seen.add(sig)

        rating = _safe_float(civic.get("evidenceRating"))
        if rating < (min_rating or 0.0):
            continue

        level = (civic.get("evidenceLevel") or "").upper()
        if allowed_levels and level and (level not in allowed_levels):
            continue

        e_type = civic.get("evidenceType") or "UNKNOWN"
        direction = civic.get("evidenceDirection") or "UNKNOWN"
        disease = ((civic.get("disease") or {}).get("name")) or "N/A"
        drugs = _short_drug_list(civic)
        citation = ((civic.get("source") or {}).get("citation")) or ""
        desc = (civic.get("description") or "").strip()

        # Conservative scoring: rating is 1..5 in CIViC; map to 0..1
        score = max(0.0, min(1.0, rating / 5.0))
        confidence = score  # keep simple & transparent

        statement = (
            f"CIViC evidence {eid}: [{gene} {var}] {e_type} ({level}), {direction}. " 
            f"Disease: {disease}. Drugs: {drugs}. Rating: {rating}."
        )
        if citation:
            statement += f" Source: {citation}."
        if desc:
            statement += f" Summary: {desc[:280]}" + ("…" if len(desc) > 280 else "")

        claim_id = stable_id(IDPrefixes.CLAIM, case.case_id, "CIVIC", eid)

        out.append(Claim(
            claim_id=claim_id,
            type="EVIDENCE",
            statement=statement,
            score=score,
            confidence=confidence,
            evidence_ids=[ev.evid_id],
            feature_ids=feat_ids,
            generated_by="civic",
            tags=["CIVIC", gene] + ([var] if var else []) + ([level] if level else [])
        ))

    return out
