import re
from dateutil import parser as dparser

def num(x) -> float:
    if x is None: return 0.0
    if isinstance(x, (int,float)): return float(x)
    s = str(x).replace(",", "").replace("$", "").strip()
    try: return float(s)
    except: return 0.0

def clean_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def normalize_newlines(s: str) -> str:
    return (s or "").replace("\r\n","\n").replace("\r","\n")

def collapse_spaces_keep_newlines(s: str) -> str:
    """Collapse spaces/tabs but preserve line breaks."""
    return "\n".join(re.sub(r"[ \t]+", " ", ln).strip() for ln in normalize_newlines(s).split("\n"))

def to_first_last(name: str) -> str:
    name = clean_spaces(name)
    if "," in name:
        last, first = [p.strip() for p in name.split(",", 1)]
        name = f"{first} {last}"
    parts = []
    for w in name.split():
        sub = re.split(r"([-’'])", w)
        parts.append("".join(p.capitalize() if i % 2 == 0 else p for i,p in enumerate(sub)))
    return " ".join(parts)

def find(pattern: str, text: str, flags=re.I|re.M, group: int = 1, default: str = "") -> str:
    m = re.search(pattern, text, flags)
    return (m.group(group).strip() if m else default)

def norm_date(s: str) -> str:
    s = clean_spaces(s)
    if not s: return ""
    try: return dparser.parse(s, dayfirst=False, fuzzy=True).date().isoformat()
    except Exception: return s

def norm_period(s: str) -> str:
    s = clean_spaces(s)
    if not s: return ""
    s = re.sub(r"[–—−]", "-", s)
    parts = [p.strip() for p in re.split(r"\bto\b|-", s, maxsplit=1, flags=re.I)]
    if len(parts) == 2:
        a, b = norm_date(parts[0]), norm_date(parts[1])
        if a and b: return f"{a}–{b}"
    return s
