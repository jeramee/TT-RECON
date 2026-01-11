from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent

@dataclass(frozen=True)
class PackTemplate:
    target_yml: str
    rules_py: str
    init_py: str
    smoke_test_py: str

def default_template(target: str) -> PackTemplate:
    T = target.upper()
    target_yml = dedent(f"""\
    name: {T}
    description: "{T} target pack (generated skeleton)"
    drug_classes:
      - "{T}_INHIBITOR"
    known_sensitizing: []
    known_resistance: []
    bypass_markers: []
    """)

    rules_py = dedent(f"""\
    from typing import List
    from ttrecon.core.ids import stable_id, IDPrefixes
    from ttrecon.core.models import Case, Evidence, Feature, Claim

    def _alt_evidence_ids(evidence: List[Evidence]) -> List[str]:
        return [e.evid_id for e in evidence if e.kind == "alteration"]

    def apply_rules(case: Case, evidence: List[Evidence], features: List[Feature]) -> List[Claim]:
        """Deterministic v0.2 skeleton for {T}.

        Edit this file to:
        - define flags/features from case alterations and enriched evidence
        - emit auditable claims with evidence_ids and feature_ids
        """
        claims: List[Claim] = []
        alt_eids = _alt_evidence_ids(evidence)

        # TODO: replace with real detection logic
        has_target_gene = any(a.gene == "{T}" for a in case.alterations)

        if has_target_gene:
            claims.append(Claim(
                claim_id=stable_id(IDPrefixes.CLAIM, case.case_id, "{T}", "FOUND"),
                type="NOTE",
                statement="{T} alterations detected (skeleton rule).",
                score=0.20,
                confidence=0.20,
                evidence_ids=alt_eids,
                feature_ids=[f.feat_id for f in features],
                generated_by="rule",
                tags=["{T}", "SKELETON"]
            ))
        else:
            claims.append(Claim(
                claim_id=stable_id(IDPrefixes.CLAIM, case.case_id, "{T}", "NO_FINDINGS"),
                type="NOTE",
                statement="No {T} findings triggered by skeleton rules.",
                score=0.05,
                confidence=0.10,
                evidence_ids=alt_eids,
                feature_ids=[f.feat_id for f in features],
                generated_by="rule",
                tags=["NO_TRIGGER", "{T}"]
            ))

        return claims
    """)

    init_py = "# generated target pack\n"

    smoke_test = dedent(f"""\
    from pathlib import Path
    from ttrecon.config import load_config
    from ttrecon.engine.orchestrator import run_pipeline

    def test_target_{T.lower()}_smoke(tmp_path: Path):
        cfg = load_config()
        case_path = Path("examples/cases/egfr_example.json").resolve()
        out_dir = tmp_path / "out"
        manifest = run_pipeline(cfg, case_path=case_path, target="{T}", out_dir=out_dir)
        assert manifest.run_id
    """)

    return PackTemplate(
        target_yml=target_yml,
        rules_py=rules_py,
        init_py=init_py,
        smoke_test_py=smoke_test,
    )
