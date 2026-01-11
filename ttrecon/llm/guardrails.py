BANNED_PHRASES = [
    "you should take",
    "start on",
    "dose",
    "mg",
]

def looks_prescriptive(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in BANNED_PHRASES)
