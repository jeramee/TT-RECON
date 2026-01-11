from pathlib import Path
import json

from pydantic import TypeAdapter

from ttrecon.core.models import Case

_case_adapter = TypeAdapter(Case)

def load_case_json(path: Path) -> Case:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return _case_adapter.validate_python(data)
