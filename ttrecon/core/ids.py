import hashlib
from dataclasses import dataclass

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def stable_id(prefix: str, *parts: str) -> str:
    raw = "|".join(parts).encode("utf-8", errors="replace")
    h = sha256_hex(raw)[:16]
    return f"{prefix}-{h}"

@dataclass(frozen=True)
class IDPrefixes:
    EVID: str = "EVID"
    FEAT: str = "FEAT"
    CLAIM: str = "CLM"
    RUN: str = "RUN"
