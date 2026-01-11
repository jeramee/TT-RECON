import argparse
from pathlib import Path

from ttrecon.config import load_config
from ttrecon.logging import get_logger, log_event
from ttrecon.engine.orchestrator import run_pipeline
from ttrecon.targets.registry import list_targets
from ttrecon.pack.generator import generate_pack
from ttrecon.version import __version__

from ttrecon.connectors.civic.snapshot import build_snapshot_for_genes, write_snapshot

def cmd_init() -> int:
    cfg = load_config()
    cfg.cache_dir.mkdir(parents=True, exist_ok=True)
    (cfg.cache_dir / "README.txt").write_text(
        "TT-RECON cache directory (snapshots, connector caches, etc.)\n",
        encoding="utf-8",
    )
    return 0

def cmd_list_targets() -> int:
    cfg = load_config()
    targets = list_targets(cfg.targets_dir)
    for k in sorted(targets.keys()):
        print(k)
    return 0

def cmd_pack_add(target: str, overwrite: bool) -> int:
    cfg = load_config()
    pack_dir, test_path = generate_pack(
        targets_dir=cfg.targets_dir,
        tests_dir=Path("tests"),
        target=target,
        overwrite=overwrite,
    )
    print(f"Created target pack: {pack_dir}")
    print(f"Created smoke test: {test_path}")
    print("Next: edit rules.py + target.yml, then run pytest.")
    return 0

def cmd_civic_sync(genes_csv: str | None, genes_file: str | None, out_path: str | None, max_items: int, min_delay_s: float) -> int:
    cfg = load_config()
    genes = []
    if genes_csv:
        genes.extend([g.strip() for g in genes_csv.split(",") if g.strip()])
    if genes_file:
        p = Path(genes_file)
        txt = p.read_text(encoding="utf-8")
        for line in txt.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            genes.append(line)

    genes = sorted({g.strip().upper() for g in genes if g.strip()})
    if not genes:
        raise SystemExit("No genes provided. Use --genes EGFR,ALK or --genes-file genes.txt")

    outp = Path(out_path) if out_path else (cfg.civic_cache_dir / "snapshots" / "civic_snapshot.json")
    cfg.civic_cache_dir.mkdir(parents=True, exist_ok=True)

    snap = build_snapshot_for_genes(
        genes=genes,
        out_path=outp,
        cache_dir=cfg.civic_cache_dir,
        max_items_per_gene=max_items,
        min_delay_s=min_delay_s,
    )
    write_snapshot(snap, outp)
    print(f"OK: wrote snapshot {outp}")
    print(f"Genes: {', '.join(genes)}")
    return 0

def cmd_run(case_path: Path, target: str, out_dir: Path,
            civic: bool, civic_mode: str | None, civic_source: str | None, civic_snapshot: str | None,
            civic_claims: bool, civic_min_rating: float | None, civic_levels: str | None) -> int:
    logger = get_logger()
    cfg = load_config()
    cmode = (civic_mode or cfg.civic_mode or "strict").strip().lower()
    csrc = (civic_source or cfg.civic_source or "live").strip().lower()
    csnap = Path(civic_snapshot).resolve() if civic_snapshot else cfg.civic_snapshot_path
    log_event(
        logger,
        "run.start",
        version=__version__,
        case=str(case_path),
        target=target,
        out=str(out_dir),
        civic=civic,
        civic_mode=cmode,
        civic_source=csrc,
        civic_snapshot=str(csnap),
        civic_claims=civic_claims,
        civic_min_rating=civic_min_rating,
        civic_levels=civic_levels,
    )

    manifest = run_pipeline(
        cfg,
        case_path=case_path,
        target=target,
        out_dir=out_dir,
        civic=civic,
        civic_mode=cmode,
        civic_source=csrc,
        civic_snapshot=csnap,
        civic_claims=civic_claims,
        civic_min_rating=civic_min_rating,
        civic_levels=civic_levels,
    )

    log_event(logger, "run.done", run_id=manifest.run_id, outputs=manifest.outputs)
    print(f"OK: run_id={manifest.run_id}")
    print(f"Report: {out_dir / 'report.md'}")
    return 0

def main() -> None:
    parser = argparse.ArgumentParser(prog="ttrecon", description="TT-RECON v0.5")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Initialize cache dirs")
    p_init.set_defaults(_fn=lambda a: cmd_init())

    p_lt = sub.add_parser("list-targets", help="List installed target packs")
    p_lt.set_defaults(_fn=lambda a: cmd_list_targets())

    p_run = sub.add_parser("run", help="Run TT-RECON")
    p_run.add_argument("--case", required=True, type=str, help="Path to case JSON")
    p_run.add_argument("--target", required=True, type=str, help="Target pack name (e.g., EGFR)")
    p_run.add_argument("--out", required=True, type=str, help="Output directory")

    p_run.add_argument("--civic", action="store_true", help="Enable CIViC enrichment")
    p_run.add_argument("--civic-mode", choices=["strict", "loose"], default=None, help="CIViC matching mode")
    p_run.add_argument("--civic-source", choices=["live", "cache", "snapshot"], default=None, help="Where CIViC data comes from")
    p_run.add_argument("--civic-snapshot", type=str, default=None, help="Path to CIViC snapshot JSON (for snapshot mode)")

    p_run.add_argument("--civic-claims", action="store_true", help="Promote CIViC evidence items into structured Claims")
    p_run.add_argument("--civic-min-rating", type=float, default=None, help="Minimum CIViC evidenceRating (0-5) for promotion")
    p_run.add_argument("--civic-levels", type=str, default=None, help="Comma-separated allowlist of CIViC evidenceLevel (e.g., A,B)")

    p_run.set_defaults(_fn=lambda a: cmd_run(
        Path(a.case), a.target, Path(a.out),
        a.civic, a.civic_mode, a.civic_source, a.civic_snapshot,
        a.civic_claims, a.civic_min_rating, a.civic_levels
    ))

    p_pack = sub.add_parser("pack", help="Target pack utilities")
    pack_sub = p_pack.add_subparsers(dest="pack_cmd", required=True)
    p_add = pack_sub.add_parser("add", help="Generate a new target pack skeleton")
    p_add.add_argument("target", type=str, help="Target name (e.g., KRAS, ERBB2)")
    p_add.add_argument("--overwrite", action="store_true", help="Overwrite if target pack exists")
    p_add.set_defaults(_fn=lambda a: cmd_pack_add(a.target, a.overwrite))

    p_civic = sub.add_parser("civic", help="CIViC utilities")
    civic_sub = p_civic.add_subparsers(dest="civic_cmd", required=True)

    p_sync = civic_sub.add_parser("sync", help="Build/update an offline CIViC snapshot")
    p_sync.add_argument("--genes", type=str, default=None, help="Comma-separated gene list (e.g., EGFR,ALK,KRAS)")
    p_sync.add_argument("--genes-file", type=str, default=None, help="Path to a file with one gene per line")
    p_sync.add_argument("--out", type=str, default=None, help="Output snapshot path (default: cache snapshots/civic_snapshot.json)")
    p_sync.add_argument("--max-items", type=int, default=500, help="Max evidence items per gene to store")
    p_sync.add_argument("--min-delay-s", type=float, default=0.35, help="Minimum delay between network calls (uncached)")
    p_sync.set_defaults(_fn=lambda a: cmd_civic_sync(a.genes, a.genes_file, a.out, a.max_items, a.min_delay_s))

    args = parser.parse_args()
    raise SystemExit(args._fn(args))
