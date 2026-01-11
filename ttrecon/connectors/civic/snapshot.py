from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

from ttrecon.connectors.civic.graphql import EVIDENCE_ITEMS_QUERY
from ttrecon.connectors.civic.util import (
    CIVIC_GQL_ENDPOINT,
    post_graphql,
    hash_request,
    cache_paths,
    load_cache,
    save_cache,
)

def _now_utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def build_snapshot_for_genes(
    genes: List[str],
    out_path: Path,
    cache_dir: Path,
    max_items_per_gene: int = 500,
    min_delay_s: float = 0.35,
) -> Dict[str, Any]:
    genes_norm = sorted({g.strip().upper() for g in genes if g.strip()})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    snapshot: Dict[str, Any] = {
        "schema": "civic_snapshot_v1",
        "endpoint": CIVIC_GQL_ENDPOINT,
        "created_utc": _now_utc_iso(),
        "genes": genes_norm,
        "items_by_gene": {},
    }

    last_network_ts = 0.0

    for gene in genes_norm:
        after = None
        fetched = 0
        nodes_all: List[Dict[str, Any]] = []

        while fetched < max_items_per_gene:
            first = min(50, max_items_per_gene - fetched)
            variables = {
                "geneName": gene,
                "variantName": None,
                "status": "ACCEPTED",
                "after": after,
                "first": first,
            }

            key = hash_request(EVIDENCE_ITEMS_QUERY, variables)
            cache_json, cache_meta = cache_paths(cache_dir, key)
            data = load_cache(cache_json)

            if data is None:
                now = time.time()
                if last_network_ts > 0:
                    wait = (last_network_ts + min_delay_s) - now
                    if wait > 0:
                        time.sleep(wait)

                data = post_graphql(EVIDENCE_ITEMS_QUERY, variables)
                last_network_ts = time.time()
                save_cache(cache_json, cache_meta, data, {
                    "endpoint": CIVIC_GQL_ENDPOINT,
                    "variables": variables,
                    "cached_at_utc": _now_utc_iso(),
                })

            if "errors" in data and data["errors"]:
                snapshot["items_by_gene"][gene] = {"errors": data["errors"], "nodes": nodes_all}
                break

            conn = (((data.get("data") or {}).get("evidenceItems")) or {})
            nodes = conn.get("nodes") or []
            page_info = conn.get("pageInfo") or {}
            after = page_info.get("endCursor")
            has_next = bool(page_info.get("hasNextPage"))

            nodes_all.extend(nodes)
            fetched += len(nodes)
            if not has_next or not nodes:
                break

        snapshot["items_by_gene"][gene] = {"nodes": nodes_all}

    return snapshot

def write_snapshot(snapshot: Dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")

def load_snapshot(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
