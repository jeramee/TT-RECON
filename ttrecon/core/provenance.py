from datetime import datetime, timezone
from pathlib import Path
from .ids import sha256_hex

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def file_sha256(path: Path) -> str:
    return sha256_hex(path.read_bytes())
