from ttrecon.core.errors import ValidationError
from ttrecon.core.models import Case

def validate_case(case: Case) -> None:
    if not case.case_id or not case.case_id.strip():
        raise ValidationError("case_id is required")
    if case.alterations is None:
        raise ValidationError("alterations must be present (can be empty list)")
