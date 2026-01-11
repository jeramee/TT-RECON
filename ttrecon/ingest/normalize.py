from ttrecon.core.models import Case

def normalize_case(case: Case) -> Case:
    for alt in case.alterations:
        alt.gene = (alt.gene or "").upper().strip()
        if alt.protein_change:
            alt.protein_change = alt.protein_change.strip().upper()
        if alt.exon:
            alt.exon = alt.exon.strip().lower().replace(" ", "")
    return case
