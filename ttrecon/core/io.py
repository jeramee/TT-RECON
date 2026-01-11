import json
from pathlib import Path
from typing import Any, Iterable

def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def write_json_model(path: Path, model: Any) -> None:
    write_json(path, model.model_dump())

def write_json_models(path: Path, models: Iterable[Any]) -> None:
    write_json(path, [m.model_dump() for m in models])

def write_jsonl(path: Path, rows: Iterable[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
