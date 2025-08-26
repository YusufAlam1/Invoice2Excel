import re

HEADER_RE = re.compile(r'^.*\bAmount\b\s*$', re.IGNORECASE)

ROW_RE = re.compile(
    r"""
    ^(?P<candidate>.+?)\s+
    (?P<work_order>\d{6,})\s+
    (?:PO[:\s]*\S+\s+)?
    (?P<period>\d{2}/\d{2}/\d{2}\s*[-–]\s*\d{2}/\d{2}/\d{2})\s+
    (?P<type>[A-Za-z]+)\s+
    (?P<units>\d+(?:\.\d+)?)\s+
    (?P<rate>\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s+
    (?P<amount>\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*$
    """,
    re.VERBOSE,
)
BACKSTOP_RE = re.compile(
    r"""
    ^(?P<candidate>.+?)\s+
    (?P<work_order>\d{6,})\s+
    (?P<rest>.+?)$
    """,
    re.VERBOSE,
)

def _normalize_lines(text: str) -> list[str]:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    
    return [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.split("\n")]

def extract_row_from_text(text: str) -> dict[str, str] | None:
    lines = _normalize_lines(text)
    
    idx = next((i for i, ln in enumerate(lines) if HEADER_RE.match(ln)), None)
    if idx is None:
        return None
    
    row_line = None
    for j in range(idx + 1, min(idx + 6, len(lines))):
        if lines[j]:
            row_line = lines[j]
            break
    if not row_line:
        return None

    m = ROW_RE.match(row_line)
    if m:
        return {k: v.strip() for k, v in m.groupdict().items()}

    m = BACKSTOP_RE.match(row_line)
    if not m:
        return None
    candidate = m.group("candidate").strip()
    work_order = m.group("work_order").strip()
    tail = m.group("rest").split()

    if len(tail) < 5:
        return None
    amount = tail[-1]
    rate   = tail[-2]
    units  = tail[-3]
    type_  = tail[-4]
    period = " ".join(tail[:-4])

    return {
        "candidate": candidate,
        "work_order": work_order,
        "period": period,
        "type": type_,
        "units": units,
        "rate": rate,
        "amount": amount,
    }
