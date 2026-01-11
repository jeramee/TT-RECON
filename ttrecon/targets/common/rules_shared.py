from typing import List
from ttrecon.core.models import Alteration

def has_gene(case_alts: List[Alteration], gene: str) -> bool:
    g = gene.upper()
    return any(a.gene == g for a in case_alts)
