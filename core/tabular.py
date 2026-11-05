"""قراءة ذكية لجداول الإحداثيات من Excel وCSV ونص ملصوق.

يبحث عن أطول كتلة صفوف فيها عمودان متجاوران يشبهان إحداثيات (UTM أو درجات عشرية)،
أينما كانت في الورقة وبأي ترتيب (شمالي/شرقي أو العكس)، ويتجاهل الأعمدة الأخرى (مثل DIST).
"""
import io
import numbers
import re

AR = str.maketrans("٠١٢٣٤٥٦٧٨٩٫٬", "0123456789.,")
_PLAIN = re.compile(r"^[+-]?\d+(?:\.\d+)?$")
_THOUSANDS = re.compile(r"^[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?$")
_COMMA_DEC = re.compile(r"^[+-]?\d+,\d+$")

UTM_E, UTM_N = (100_000, 900_000), (1_000_000, 4_000_000)
LON, LAT = (40, 70), (10, 35)


def to_number(v):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, numbers.Real):
        f = float(v)
        return None if f != f else f
    s = str(v).strip().translate(AR).replace(" ", "").replace("\u00a0", "")
    if _PLAIN.match(s):
        return float(s)
    if _THOUSANDS.match(s):
        return float(s.replace(",", ""))
    if _COMMA_DEC.match(s):
        return float(s.replace(",", "."))
    return None


def _in(v, rng):
    return rng[0] <= v <= rng[1]


def pair_kind(a, b):
    """(a, b) زوج إحداثيات؟ يعيد (النوع، معكوس؟) أو None. المعكوس يعني أن a شمالي/عرض وb شرقي/طول."""
    if _in(a, UTM_E) and _in(b, UTM_N):
        return "utm", False
    if _in(a, UTM_N) and _in(b, UTM_E):
        return "utm", True
    if _in(a, LON) and _in(b, LAT):
        return "decimal", False
    if _in(a, LAT) and _in(b, LON):
        return "decimal", True
    return None


def _label(v):
    if v is None:
        return None
    if isinstance(v, str):
        tokens = v.strip().split()
        if not tokens or tokens[0].lower() == "nan":
            return None
        t = to_number(tokens[0])
        return f"P{int(t)}" if t is not None and t == int(t) else tokens[0]
    n = to_number(v)
    return f"P{int(n)}" if n is not None and n == int(n) and abs(n) < 100000 else None


def find_block(rows):
    """rows: قائمة صفوف (قوائم قيم خام). يعيد أفضل كتلة إحداثيات أو None."""
    num = [[to_number(v) for v in r] for r in rows]
    ncols = max((len(r) for r in num), default=0)
    best = None
    for c in range(ncols - 1):
        run = []
        for i in range(len(num) + 1):
            k = None
            if i < len(num) and c + 1 < len(num[i]):
                a, b = num[i][c], num[i][c + 1]
                if a is not None and b is not None:
                    k = pair_kind(a, b)
            if k:
                run.append((i, k))
            else:
                if run and (best is None or len(run) > len(best["items"])):
                    best = {"col": c, "items": run}
                run = []
    if not best:
        return None
    c, items = best["col"], best["items"]
    kinds = [k for _, (k, _) in items]
    kind = max(set(kinds), key=kinds.count)
    items = [(i, k) for i, k in items if k[0] == kind]
    swaps = [k[1] for _, k in items]
    swapped = max((True, False), key=swaps.count)
    items = [(i, k) for i, k in items if k[1] == swapped]
    xs, ys, labels = [], [], []
    for n, (i, _) in enumerate(items):
        a, b = num[i][c], num[i][c + 1]
        xs.append(b if swapped else a)
        ys.append(a if swapped else b)
        lab = None
        if c >= 2 and c - 1 < len(rows[i]):
            a_, b_ = to_number(rows[i][c - 2]), to_number(rows[i][c - 1])
            if a_ is not None and b_ is not None and a_ == int(a_) and b_ == int(b_) and abs(a_) < 10000:
                lab = f"P{int(a_)}"          # جدول خطوط "LINE 1 2": رقم نقطة البداية
        if lab is None and c > 0 and c - 1 < len(rows[i]):
            lab = _label(rows[i][c - 1])
        labels.append(lab)
    if any(l is None for l in labels) or len(set(labels)) != len(labels):
        labels = [f"P{n + 1}" for n in range(len(xs))]
    return {"kind": kind, "swapped": swapped, "xs": xs, "ys": ys, "labels": labels,
            "first_row": items[0][0] + 1, "col": c + 1, "c0": c, "rows": [i for i, _ in items]}


def text_to_rows(text):
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            rows.append([])
            continue
        if "\t" in line:
            toks = line.split("\t")
        elif ";" in line:
            toks = line.split(";")
        elif re.search(r"\s", line):
            toks = line.split()
        else:
            toks = line.split(",")
        rows.append([t.strip().strip(",;") for t in toks])
    return rows


def _decode(data):
    for enc in ("utf-8-sig", "cp1256", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def from_text(text):
    block = find_block(text_to_rows(text))
    return (block, f"النص الملصوق (الصف {block['first_row']})") if block else (None, "")


def from_file(data, filename):
    """يقرأ Excel (كل الأوراق) أو CSV/TXT ويعيد (الكتلة، وصف موضعها)."""
    name = filename.lower()
    if name.endswith((".xlsx", ".xlsm", ".xls")):
        import pandas as pd
        sheets = pd.read_excel(io.BytesIO(data), sheet_name=None, header=None, dtype=object)
        best, where = None, ""
        for sheet, df in sheets.items():
            b = find_block(df.values.tolist())
            if b and (best is None or len(b["xs"]) > len(best["xs"])):
                best, where = b, f"الورقة «{sheet}» (من الصف {b['first_row']})"
        return best, where
    block = find_block(text_to_rows(_decode(data)))
    return (block, f"الملف (من الصف {block['first_row']})") if block else (None, "")
