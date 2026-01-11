from typing import List
from ttrecon.core.models import Claim

def rank_claims(claims: List[Claim]) -> List[Claim]:
    return sorted(claims, key=lambda c: (c.score, c.confidence), reverse=True)
