from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests

CIVIC_GQL_ENDPOINT = "https://civicdb.org/api/graphql"

def hash_request(query: str, variables: Dict[str, Any]) -> str:
    b = (query + "\n" + json.dumps(variables, sort_keys=True)).encode("utf-8")
    return hashlib.sha256(b).hexdigest()

def cache_paths(cache_dir: Path, key: str) -> Tuple[Path, Path]:
    req_dir = cache_dir / "requests"
    req_dir.mkdir(parents=True, exist_ok=True)
    return req_dir / f"{key}.json", req_dir / f"{key}.meta.json"

def load_cache(cache_json: Path) -> Optional[Dict[str, Any]]:
    if cache_json.exists():
        try:
            return json.loads(cache_json.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None

def save_cache(cache_json: Path, cache_meta: Path, data: Dict[str, Any], meta: Dict[str, Any]) -> None:
    cache_json.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    cache_meta.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

def post_graphql(query: str, variables: Dict[str, Any], timeout_s: int = 30) -> Dict[str, Any]:
    resp = requests.post(
        CIVIC_GQL_ENDPOINT,
        json={"query": query, "variables": variables},
        headers={"Accept": "application/json"},
        timeout=timeout_s,
    )
    resp.raise_for_status()
    return resp.json()

def evidence_link(evidence_id: int) -> str:
    return f"https://civicdb.org/links/evidence/{evidence_id}"
