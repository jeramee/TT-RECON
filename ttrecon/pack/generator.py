from __future__ import annotations

import re
from pathlib import Path
from typing import Tuple

from ttrecon.pack.templates import default_template

_VALID = re.compile(r"^[A-Za-z0-9_]+$")

def normalize_target_name(name: str) -> str:
    n = name.strip().upper()
    if not n or not _VALID.match(n):
        raise ValueError("Target name must be alphanumeric/underscore (e.g., EGFR, KRAS, ERBB2)")
    return n

def generate_pack(targets_dir: Path, tests_dir: Path, target: str, overwrite: bool = False) -> Tuple[Path, Path]:
    T = normalize_target_name(target)
    pack_dir = targets_dir / T
    if pack_dir.exists() and not overwrite:
        raise FileExistsError(f"Target pack already exists: {pack_dir} (use --overwrite to replace)")

    tpl = default_template(T)

    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "__init__.py").write_text(tpl.init_py, encoding="utf-8")
    (pack_dir / "target.yml").write_text(tpl.target_yml, encoding="utf-8")
    (pack_dir / "rules.py").write_text(tpl.rules_py, encoding="utf-8")

    tests_dir.mkdir(parents=True, exist_ok=True)
    test_path = tests_dir / f"test_target_{T.lower()}_smoke.py"
    test_path.write_text(tpl.smoke_test_py, encoding="utf-8")

    return pack_dir, test_path
