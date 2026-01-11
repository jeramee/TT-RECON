from importlib import import_module
from pathlib import Path
from typing import Callable, Dict, Tuple
import yaml
from ttrecon.core.errors import TargetNotFoundError

def list_targets(targets_dir: Path) -> Dict[str, Path]:
    out = {}
    if not targets_dir.exists():
        return out
    for p in targets_dir.iterdir():
        if p.is_dir() and (p / "target.yml").exists():
            out[p.name.upper()] = p
    return out

def load_target_meta(target_dir: Path) -> dict:
    return yaml.safe_load((target_dir / "target.yml").read_text(encoding="utf-8"))

def load_rules_callable(target_name: str) -> Callable:
    mod = import_module(f"ttrecon.targets.{target_name}.rules")
    return getattr(mod, "apply_rules")

def resolve_target(targets_dir: Path, target: str) -> Tuple[str, Path]:
    t = target.upper()
    targets = list_targets(targets_dir)
    if t not in targets:
        raise TargetNotFoundError(f"Target '{t}' not found. Available: {sorted(targets.keys())}")
    return t, targets[t]
