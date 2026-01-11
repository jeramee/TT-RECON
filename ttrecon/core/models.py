from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

AlterationType = Literal["SNV", "INDEL", "FUSION", "CNV", "EXPRESSION"]
ClaimType = Literal["MECHANISM", "SENSITIVITY", "RESISTANCE", "NOTE"]

class Alteration(BaseModel):
    gene: str
    type: AlterationType
    protein_change: Optional[str] = None
    exon: Optional[str] = None
    partner: Optional[str] = None
    cnv_call: Optional[Literal["AMP", "DEL", "GAIN", "LOSS"]] = None
    expression_call: Optional[Literal["HIGH", "LOW"]] = None
    meta: Dict[str, Any] = Field(default_factory=dict)

class Case(BaseModel):
    case_id: str
    tumor_type: Optional[str] = None
    specimen_type: Optional[str] = None
    assay_type: Optional[str] = None
    alterations: List[Alteration] = Field(default_factory=list)
    notes: Optional[str] = None

class Evidence(BaseModel):
    evid_id: str
    source: str
    kind: str
    ref: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)

class Feature(BaseModel):
    feat_id: str
    name: str
    value: Any
    evidence_ids: List[str] = Field(default_factory=list)

class Claim(BaseModel):
    claim_id: str
    type: ClaimType
    statement: str
    score: float = 0.0
    confidence: float = 0.0
    evidence_ids: List[str] = Field(default_factory=list)
    feature_ids: List[str] = Field(default_factory=list)
    generated_by: Literal["rule", "ml", "llm"] = "rule"
    tags: List[str] = Field(default_factory=list)

class Report(BaseModel):
    run_id: str
    target: str
    case_id: str
    overview: str
    claims_ranked: List[Claim]
    limitations: List[str] = Field(default_factory=list)

class RunManifest(BaseModel):
    run_id: str
    version: str
    target: str
    case_path: str
    case_sha256: str
    started_utc: str
    finished_utc: str
    outputs: Dict[str, str] = Field(default_factory=dict)
