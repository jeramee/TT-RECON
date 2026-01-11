import os
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class TTReconConfig:
    cache_dir: Path
    targets_dir: Path

    civic_enabled: bool
    civic_cache_dir: Path
    civic_mode: str
    civic_source: str  # live|cache|snapshot
    civic_snapshot_path: Path
    civic_max_items: int
    civic_min_delay_s: float

    civic_claims_enabled: bool
    civic_claims_min_rating: float
    civic_claims_levels: str  # comma-separated, empty means allow all

def _env_bool(name: str, default: str = "0") -> bool:
    v = os.getenv(name, default).strip().lower()
    return v in ("1", "true", "yes", "y", "on")

def _env_int(name: str, default: str) -> int:
    try:
        return int(os.getenv(name, default).strip())
    except Exception:
        return int(default)

def _env_float(name: str, default: str) -> float:
    try:
        return float(os.getenv(name, default).strip())
    except Exception:
        return float(default)

def load_config() -> TTReconConfig:
    cache_dir = Path(os.getenv("TTRECON_CACHE_DIR", ".ttrecon_cache")).resolve()
    targets_dir = Path(os.getenv("TTRECON_TARGETS_DIR", "ttrecon/targets")).resolve()

    civic_enabled = _env_bool("TTRECON_CIVIC_ENABLED", "0")
    civic_cache_dir = Path(os.getenv("TTRECON_CIVIC_CACHE_DIR", str(cache_dir / "civic"))).resolve()
    civic_mode = os.getenv("TTRECON_CIVIC_MODE", "strict").strip().lower()
    civic_source = os.getenv("TTRECON_CIVIC_SOURCE", "live").strip().lower()
    civic_snapshot_path = Path(os.getenv("TTRECON_CIVIC_SNAPSHOT", str(civic_cache_dir / "snapshots" / "civic_snapshot.json"))).resolve()
    civic_max_items = _env_int("TTRECON_CIVIC_MAX_ITEMS", "50")
    civic_min_delay_s = _env_float("TTRECON_CIVIC_MIN_DELAY_S", "0.35")

    civic_claims_enabled = _env_bool("TTRECON_CIVIC_CLAIMS_ENABLED", "0")
    civic_claims_min_rating = _env_float("TTRECON_CIVIC_CLAIMS_MIN_RATING", "0")
    civic_claims_levels = os.getenv("TTRECON_CIVIC_CLAIMS_LEVELS", "").strip()

    return TTReconConfig(
        cache_dir=cache_dir,
        targets_dir=targets_dir,
        civic_enabled=civic_enabled,
        civic_cache_dir=civic_cache_dir,
        civic_mode=civic_mode,
        civic_source=civic_source,
        civic_snapshot_path=civic_snapshot_path,
        civic_max_items=civic_max_items,
        civic_min_delay_s=civic_min_delay_s,
        civic_claims_enabled=civic_claims_enabled,
        civic_claims_min_rating=civic_claims_min_rating,
        civic_claims_levels=civic_claims_levels,
    )
