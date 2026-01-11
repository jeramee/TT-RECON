from typing import List
from ttrecon.core.ids import stable_id, IDPrefixes
from ttrecon.core.models import Case, Evidence, Feature, Claim

def _alt_evidence_ids(evidence: List[Evidence]) -> List[str]:
    return [e.evid_id for e in evidence if e.kind == "alteration"]

def apply_rules(case: Case, evidence: List[Evidence], features: List[Feature]) -> List[Claim]:
    claims: List[Claim] = []
    alt_eids = _alt_evidence_ids(evidence)

    egfr_exon19del = any(a.gene == "EGFR" and (a.exon == "exon19del") for a in case.alterations)
    egfr_l858r = any(a.gene == "EGFR" and (a.protein_change == "L858R") for a in case.alterations)
    egfr_t790m = any(a.gene == "EGFR" and (a.protein_change == "T790M") for a in case.alterations)
    met_amp = any(a.gene == "MET" and a.type == "CNV" and a.cnv_call in ("AMP", "GAIN") for a in case.alterations)

    if egfr_exon19del:
        features.append(Feature(
            feat_id=stable_id(IDPrefixes.FEAT, case.case_id, "EGFR", "exon19del"),
            name="EGFR_exon19del_present",
            value=True,
            evidence_ids=alt_eids
        ))
    if egfr_l858r:
        features.append(Feature(
            feat_id=stable_id(IDPrefixes.FEAT, case.case_id, "EGFR", "L858R"),
            name="EGFR_L858R_present",
            value=True,
            evidence_ids=alt_eids
        ))
    if egfr_t790m:
        features.append(Feature(
            feat_id=stable_id(IDPrefixes.FEAT, case.case_id, "EGFR", "T790M"),
            name="EGFR_T790M_present",
            value=True,
            evidence_ids=alt_eids
        ))
    if met_amp:
        features.append(Feature(
            feat_id=stable_id(IDPrefixes.FEAT, case.case_id, "MET", "AMP"),
            name="MET_amplification_signal",
            value=True,
            evidence_ids=alt_eids
        ))

    feat_ids = [f.feat_id for f in features]

    if egfr_exon19del or egfr_l858r:
        claims.append(Claim(
            claim_id=stable_id(IDPrefixes.CLAIM, case.case_id, "EGFR", "SENSITIZING"),
            type="SENSITIVITY",
            statement="EGFR sensitizing alteration detected (exon19del and/or L858R).",
            score=0.85,
            confidence=0.70,
            evidence_ids=alt_eids,
            feature_ids=feat_ids,
            generated_by="rule",
            tags=["EGFR", "SENSITIZING"]
        ))

    if egfr_t790m:
        claims.append(Claim(
            claim_id=stable_id(IDPrefixes.CLAIM, case.case_id, "EGFR", "T790M"),
            type="RESISTANCE",
            statement="EGFR T790M detected, consistent with acquired resistance to earlier-generation EGFR TKIs.",
            score=0.80,
            confidence=0.65,
            evidence_ids=alt_eids,
            feature_ids=feat_ids,
            generated_by="rule",
            tags=["EGFR", "RESISTANCE", "T790M"]
        ))

    if met_amp:
        claims.append(Claim(
            claim_id=stable_id(IDPrefixes.CLAIM, case.case_id, "EGFR", "MET_BYPASS"),
            type="MECHANISM",
            statement="MET amplification signal detected; bypass signaling is a plausible resistance mechanism in EGFR-driven disease.",
            score=0.70,
            confidence=0.55,
            evidence_ids=alt_eids,
            feature_ids=feat_ids,
            generated_by="rule",
            tags=["BYPASS", "MET"]
        ))

    if not claims:
        claims.append(Claim(
            claim_id=stable_id(IDPrefixes.CLAIM, case.case_id, "EGFR", "NO_FINDINGS"),
            type="NOTE",
            statement="No EGFR target-pack findings triggered by current deterministic rules. Consider additional data (therapy history, RNA programs, broader variant interpretation).",
            score=0.10,
            confidence=0.30,
            evidence_ids=alt_eids,
            feature_ids=feat_ids,
            generated_by="rule",
            tags=["NO_TRIGGER"]
        ))

    return claims
