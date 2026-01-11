from pathlib import Path
from ttrecon.config import load_config
from ttrecon.engine.orchestrator import run_pipeline

def test_run_egfr(tmp_path: Path):
    cfg = load_config()
    case_path = Path("examples/cases/egfr_example.json").resolve()
    out_dir = tmp_path / "out"
    manifest = run_pipeline(cfg, case_path=case_path, target="EGFR", out_dir=out_dir)

    assert (out_dir / "report.md").exists()
    assert (out_dir / "claims.json").exists()
    assert manifest.run_id
