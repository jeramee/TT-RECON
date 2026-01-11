from pathlib import Path
from typing import List
from jinja2 import Environment, FileSystemLoader, select_autoescape

from ttrecon.core.models import Report, Evidence, Feature

def render_report_md(report: Report, evidence: List[Evidence], features: List[Feature], out_path: Path) -> None:
    templates_dir = Path(__file__).parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(enabled_extensions=())
    )
    tmpl = env.get_template("dossier.md.j2")
    text = tmpl.render(report=report, evidence=evidence, features=features)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
