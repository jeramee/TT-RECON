from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ttrecon.core.ids import stable_id, IDPrefixes
from ttrecon.core.models import Case, Evidence
from ttrecon.connectors.civic.graphql import EVIDENCE_ITEMS_QUERY
from ttrecon.connectors.civic.snapshot import load_snapshot
from ttrecon.connectors.civic.util import (
    CIVIC_GQL_ENDPOINT,
    post_graphql,
    hash_request,
    cache_paths,
    load_cache,
    save_cache,
    evidence_link,
)

def _normalize_variant_query(alt: Dict[str, Any]) -> Optional[str]:
    pc = (alt.get("protein_change") or "").strip()
    if pc:
        return pc
    name = (alt.get("name") or alt.get("alteration") or "").strip()
    if name:
        return name
    return None

def _variant_match_strict(case_alt: Dict[str, Any], civic_node: Dict[str, Any]) -> bool:
    pc = (case_alt.get("protein_change") or "").strip()
    if not pc:
        return True
    vname = ((civic_node.get("variant") or {}).get("name") or "")
    return pc.upper() in vname.upper()

def civic_enrich_from_snapshot(
    case: Case,
    snapshot_path: Path,
    mode: str = "strict",
    max_items: int = 50,
) -> List[Evidence]:
    snap = load_snapshot(snapshot_path)
    items_by_gene = (snap.get("items_by_gene") or {})
    out: List[Evidence] = []

    for alt_idx, alt in enumerate(case.alterations):
        gene = (alt.gene or "").strip().upper()
        if not gene:
            continue
        bucket = items_by_gene.get(gene) or {}
        nodes = bucket.get("nodes") or []
        picked: List[Dict[str, Any]] = []

        for node in nodes:
            if mode == "strict" and not _variant_match_strict(alt.dict(), node):
                continue
            picked.append(node)
            if len(picked) >= max_items:
                break

        for node in picked:
            eid = node.get("id")
            if eid is None:
                continue
            evid_id = stable_id(IDPrefixes.EVID, case.case_id, "civic", str(eid))
            out.append(Evidence(
                evid_id=evid_id,
                source="civic",
                kind="annotation",
                ref=evidence_link(int(eid)),
                payload={
                    "mode": mode,
                    "source_mode": "snapshot",
                    "snapshot": str(snapshot_path),
                    "civic": node,
                    "case_alteration": alt.dict(),
                    "from_cache": True,
                }
            ))
    return out

def civic_enrich(
    case: Case,
    cache_dir: Path,
    mode: str = "strict",
    max_items: int = 50,
    min_delay_s: float = 0.35,
    source: str = "live",
    snapshot_path: Path | None = None,
) -> List[Evidence]:
    source = (source or "live").strip().lower()
    mode = (mode or "strict").strip().lower()
    if mode not in ("strict", "loose"):
        mode = "strict"
    if source not in ("live", "cache", "snapshot"):
        source = "live"

    if source == "snapshot":
        if not snapshot_path:
            raise ValueError("snapshot_path is required when source='snapshot'")
        return civic_enrich_from_snapshot(case, snapshot_path=snapshot_path, mode=mode, max_items=max_items)

    out: List[Evidence] = []
    cache_dir.mkdir(parents=True, exist_ok=True)

    last_network_ts = 0.0

    for alt_idx, alt in enumerate(case.alterations):
        gene = (alt.gene or "").strip().upper()
        if not gene:
            continue

        variant_q = _normalize_variant_query(alt.dict())
        gene_q = gene

        if mode == "loose":
            variant_q = None

        after = None
        fetched = 0

        while fetched < max_items:
            first = min(25, max_items - fetched)
            variables = {
                "geneName": gene_q,
                "variantName": variant_q,
                "status": "ACCEPTED",
                "after": after,
                "first": first,
            }

            key = hash_request(EVIDENCE_ITEMS_QUERY, variables)
            cache_json, cache_meta = cache_paths(cache_dir, key)

            data = load_cache(cache_json)
            from_cache = data is not None

            if data is None:
                if source == "cache":
                    evid_id = stable_id(IDPrefixes.EVID, case.case_id, "civic", gene, str(alt_idx), "CACHE_MISS")
                    out.append(Evidence(
                        evid_id=evid_id,
                        source="civic",
                        kind="annotation",
                        ref=str(cache_json),
                        payload={
                            "mode": mode,
                            "source_mode": "cache",
                            "gene": gene_q,
                            "variantName": variant_q,
                            "error": "CACHE_MISS (no network allowed)",
                        }
                    ))
                    break

                now = time.time()
                if last_network_ts > 0:
                    wait = (last_network_ts + min_delay_s) - now
                    if wait > 0:
                        time.sleep(wait)

                data = post_graphql(EVIDENCE_ITEMS_QUERY, variables)
                last_network_ts = time.time()

                meta = {
                    "endpoint": CIVIC_GQL_ENDPOINT,
                    "variables": variables,
                    "cached_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
                save_cache(cache_json, cache_meta, data, meta)

            if "errors" in data and data["errors"]:
                evid_id = stable_id(IDPrefixes.EVID, case.case_id, "civic", gene, str(alt_idx), "ERROR")
                out.append(Evidence(
                    evid_id=evid_id,
                    source="civic",
                    kind="annotation",
                    ref=CIVIC_GQL_ENDPOINT,
                    payload={
                        "mode": mode,
                        "source_mode": source,
                        "gene": gene_q,
                        "variantName": variant_q,
                        "errors": data.get("errors"),
                        "from_cache": from_cache,
                    }
                ))
                break

            conn = (((data.get("data") or {}).get("evidenceItems")) or {})
            nodes = conn.get("nodes") or []
            page_info = conn.get("pageInfo") or {}
            after = page_info.get("endCursor")
            has_next = bool(page_info.get("hasNextPage"))

            for node in nodes:
                eid = node.get("id")
                if eid is None:
                    continue
                evid_id = stable_id(IDPrefixes.EVID, case.case_id, "civic", str(eid))
                out.append(Evidence(
                    evid_id=evid_id,
                    source="civic",
                    kind="annotation",
                    ref=evidence_link(int(eid)),
                    payload={
                        "mode": mode,
                        "source_mode": source,
                        "query": {"geneName": gene_q, "variantName": variant_q},
                        "civic": node,
                        "case_alteration": alt.dict(),
                        "from_cache": from_cache,
                    }
                ))

            fetched += len(nodes)
            if not has_next or not nodes:
                break

    return out
