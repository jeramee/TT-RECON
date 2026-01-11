from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class CivicEvidenceStub(BaseModel):
    """Placeholder structure for CIViC-derived evidence rows (v0.2 stub)."""
    civic_id: Optional[str] = None
    kind: str = "civic_stub"
    url: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
