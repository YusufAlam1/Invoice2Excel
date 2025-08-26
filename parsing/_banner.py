import pandas as pd

_BBOX_LEFT   = 30
_BBOX_RIGHT  = 570
_BBOX_TOP    = 258          
_BBOX_BOTTOM = 318          
_LINE_BIN    = 3            

_HDR_COLS: list[tuple[str, list[str]]] = [
    ("Candidate", ["Candidate"]),
    ("Work Order", ["Work", "Order"]),
    ("Purchase Order", ["Purchase", "Order"]),
    ("Period", ["Period"]),
    ("Type", ["Type"]),
    ("Unit(s)", ["Unit(s)", "Unit", "Units"]),
    ("Rate", ["Rate"]),
    ("Amount", ["Amount"]),
]

_COL_MAP = {
    "Candidate": "candidate",
    "Work Order": "work_order",
    "Purchase Order": "purchase_order",
    "Period": "period",
    "Type": "type",
    "Unit(s)": "units",
    "Units": "units",
    "Unit": "units",
    "Rate": "rate",
    "Amount": "amount",
}

def _fixed_banner_bbox(page) -> tuple[float, float, float, float]:
    """Return the fixed crop for the banner, clamped to the page."""
    return (
        max(0, _BBOX_LEFT),
        max(0, _BBOX_TOP),
        min(page.width, _BBOX_RIGHT),
        min(page.height, _BBOX_BOTTOM),
    )

def extract_banner_row(page) -> dict[str, str] | None:
    region = page.crop(_fixed_banner_bbox(page))
    words = region.extract_words() or []

    if not words:
        return None
 
    def bb_of(tokens: list[str]):
        ws = [w for w in words if w.get("text") in tokens]
        if not ws:
            return None
        return (min(w["x0"] for w in ws), max(w["x1"] for w in ws), min(w["top"] for w in ws))

    cols: list[tuple[str, float, float]] = []  
    for name, toks in _HDR_COLS:
        bb = bb_of(toks)
        if bb:
            x0, x1, top = bb
            cols.append((name, (x0 + x1) / 2.0, top))

    if len(cols) < 4:
        return None

    cols.sort(key=lambda t: t[1])                  
    header_y = min(c[2] for c in cols)             
    
    lines: dict[int, list] = {}
    for w in words:
        if w["top"] <= header_y + 2:
            continue  
        key = round(w["top"] / _LINE_BIN)
        lines.setdefault(key, []).append(w)

    if not lines:
        return None
    
    row_words = max(lines.values(), key=lambda L: len(L))
  
    cells = [""] * len(cols)
    for w in sorted(row_words, key=lambda w: w["x0"]):
        xmid = (w["x0"] + w["x1"]) / 2.0
        idx = min(range(len(cols)), key=lambda i: abs(xmid - cols[i][1]))
        cells[idx] = (cells[idx] + " " + w["text"]).strip()
  
    df = pd.DataFrame([cells], columns=[c[0] for c in cols])
    
    desired = [c[0] for c in _HDR_COLS if c[0] in df.columns]
    df = df[desired]
    
    df = df.rename(columns=lambda c: _COL_MAP.get(c, c))
    row = df.iloc[0].to_dict()
    return {k: ("" if v is None else str(v)).strip() for k, v in row.items()}