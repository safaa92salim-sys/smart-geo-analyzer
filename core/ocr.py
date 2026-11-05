"""استخراج جدول الإحداثيات من صورة أو PDF.

الطبقات (كلها مجانية وتعمل دون إرسال الملفات إلى أي خدمة خارجية):
1) PDF يحمل طبقة نص: تُقرأ الأرقام منه مباشرة بدقة كاملة دون OCR.
2) صورة أو PDF ممسوح: تحسين الصورة ثم OCR (RapidOCR) على أكثر من نسخة، وتصويت بين القراءات.
3) فحص حسابي: المسافات والمساحة المحسوبة مقابل المطبوعة، مع تصحيح ذاتي لرقم واحد خاطئ.
"""
import io
import math
import re
from collections import Counter

from . import tabular

_ENGINE = None


# ------------------------------------------------------------------ محرك OCR
def ocr_available():
    for mod in ("rapidocr_onnxruntime", "rapidocr"):
        try:
            __import__(mod)
            return True
        except Exception:  # noqa: BLE001
            continue
    return False


def _engine():
    global _ENGINE
    if _ENGINE is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _ENGINE = ("old", RapidOCR())
        except ImportError:
            from rapidocr import RapidOCR
            _ENGINE = ("new", RapidOCR())
    return _ENGINE


def run_engine(img):
    """يعيد قائمة (cx, cy, h, text, score) لكل مقطع نص."""
    import numpy as np
    kind, eng = _engine()
    arr = np.asarray(img.convert("RGB"))
    raw = []
    if kind == "old":
        res, _ = eng(arr)
        raw = [(b, t, float(sc)) for b, t, sc in (res or [])]
    else:
        out = eng(arr)
        if getattr(out, "boxes", None) is not None:
            raw = [(b, t, float(sc)) for b, t, sc in zip(out.boxes, out.txts, out.scores)]
    items = []
    for box, text, score in raw:
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        items.append(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(ys) - min(ys), str(text), score))
    return items


# ------------------------------------------------------------------ من مقاطع النص إلى صفوف
_CONFUSE = str.maketrans({"O": "0", "o": "0", "l": "1", "I": "1", "|": "1", "S": "5", "B": "8", "،": ","})


def fix_token(t):
    """يصحح الحروف الشائعة الخلط مع الأرقام داخل الرموز الرقمية فقط."""
    t = t.strip()
    if re.fullmatch(r"[0-9OolIS|B.,\-]+", t) and sum(ch.isdigit() for ch in t) >= len(t) / 2:
        return t.translate(_CONFUSE)
    return t


def items_to_rows(items):
    if not items:
        return []
    hs = sorted(i[2] for i in items)
    tol = max(4.0, 0.6 * hs[len(hs) // 2])
    items = sorted(items, key=lambda i: i[1])
    groups, cur, cur_y = [], [], None
    for it in items:
        if cur_y is None or abs(it[1] - cur_y) <= tol:
            cur.append(it)
            cur_y = sum(i[1] for i in cur) / len(cur)
        else:
            groups.append(cur)
            cur, cur_y = [it], it[1]
    if cur:
        groups.append(cur)
    rows = []
    for g in groups:
        row = []
        for it in sorted(g, key=lambda i: i[0]):
            row.extend(fix_token(tok) for tok in it[3].split())
        rows.append(row)
    return rows


# ------------------------------------------------------------------ مسافات ومساحة من نص الصفوف
def extras(rows, block):
    c0, dists = block["c0"], []
    for i in block["rows"]:
        v = None
        for k in (c0 + 2, c0 + 3):
            if k < len(rows[i]):
                x = tabular.to_number(rows[i][k])
                if x is not None and 0 < x < 100000:
                    v = x
                    break
        dists.append(v)
    if not all(v is not None for v in dists):
        dists = None
    text = " ".join(" ".join(str(c) for c in r) for r in rows)
    m = re.search(r"(?:AREA|المساحة)\s*[=:]?\s*([0-9][0-9.,]*)", text, re.I)
    area = tabular.to_number(m.group(1).rstrip(".,")) if m else None
    return dists, area


def block_from_rows(rows):
    block = tabular.find_block(rows)
    if not block:
        return None
    block["dists"], block["area"] = extras(rows, block)
    return block


# ------------------------------------------------------------------ التصويت بين القراءات
def vote(blocks):
    """يدمج كتل قراءات متعددة. يعيد (كتلة نهائية، مجموعة صفوف اختلفت فيها القراءات، عدد القراءات المتفقة في الشكل)."""
    blocks = [b for b in blocks if b]
    if not blocks:
        return None, set(), 0
    base = max(blocks, key=lambda b: len(b["xs"]))
    n = len(base["xs"])
    same = [b for b in blocks if len(b["xs"]) == n and b["kind"] == base["kind"] and b["swapped"] == base["swapped"]]
    out = dict(base)
    out["xs"], out["ys"] = list(base["xs"]), list(base["ys"])
    dists = list(base["dists"]) if base["dists"] else None
    disagree = set()
    if len(same) >= 2:
        for i in range(n):
            for key in ("xs", "ys"):
                cnt = Counter(b[key][i] for b in same)
                if len(cnt) > 1:
                    disagree.add(i)
                    val, c = cnt.most_common(1)[0]
                    if c >= 2:
                        out[key][i] = val
        if dists:
            for i in range(n):
                vals = [b["dists"][i] for b in same if b["dists"]]
                if vals:
                    dists[i] = Counter(vals).most_common(1)[0][0]
    out["dists"] = dists
    out["area"] = next((b["area"] for b in blocks if b.get("area")), None)
    return out, disagree, len(same)


# ------------------------------------------------------------------ التحقق الحسابي
def shoelace(xs, ys):
    n = len(xs)
    x0, y0 = xs[0], ys[0]
    s = sum((xs[i] - x0) * (ys[(i + 1) % n] - y0) - (xs[(i + 1) % n] - x0) * (ys[i] - y0) for i in range(n))
    return abs(s) / 2.0


def validate(xs, ys, dists=None, area=None, tol_d=0.02, tol_a=0.003):
    """يقارن المسافات والمساحة المحسوبة بالمطبوعة (إحداثيات UTM بالمتر)."""
    n = len(xs)
    segs = []
    for i in range(n):
        j = (i + 1) % n
        d = math.hypot(xs[j] - xs[i], ys[j] - ys[i])
        p = dists[i] if dists and len(dists) == n else None
        segs.append({"i": i, "calc": d, "printed": p, "bad": p is not None and abs(d - p) > tol_d})
    bad = {s["i"] for s in segs if s["bad"]}
    hard = {i for i in bad if (i - 1) % n in bad}
    soft = set()
    for i in bad:
        soft |= {i, (i + 1) % n}
    area_calc = shoelace(xs, ys) if n >= 3 else None
    area_bad = bool(area and area_calc and abs(area_calc - area) / area > tol_a)
    return {"segs": segs, "bad": bad, "hard": hard, "soft": soft,
            "area_calc": area_calc, "area_printed": area, "area_bad": area_bad,
            "checked": any(s["printed"] is not None for s in segs) or bool(area)}


def autofix(xs, ys, dists, area, max_fixes=3):
    """يحاول تصحيح رقم واحد خاطئ في إحداثية مشكوك فيها، ولا يقبل إلا ما يطابق المسافات المطبوعة."""
    xs, ys, fixes = list(xs), list(ys), []
    if not dists or len(dists) != len(xs):
        return xs, ys, fixes
    for _ in range(max_fixes):
        v = validate(xs, ys, dists, area)
        if not v["bad"]:
            break
        cur = len(v["bad"])
        rows = v["hard"] or v["soft"]
        best = None
        for r in rows:
            for name, arr in (("E", xs), ("N", ys)):
                s = f"{arr[r]:.2f}"
                for pos, ch in enumerate(s):
                    if not ch.isdigit():
                        continue
                    for d in "0123456789":
                        if d == ch:
                            continue
                        cand = float(s[:pos] + d + s[pos + 1:])
                        old = arr[r]
                        arr[r] = cand
                        left = len(validate(xs, ys, dists, area)["bad"])
                        arr[r] = old
                        if left <= cur - 2 and (best is None or left < best[0]):
                            best = (left, r, name, old, cand)
        if not best:
            break
        _, r, name, old, cand = best
        (xs if name == "E" else ys)[r] = cand
        fixes.append({"row": r, "axis": name, "old": old, "new": cand})
    return xs, ys, fixes


# ------------------------------------------------------------------ تحسين الصورة
def _otsu(gray):
    import numpy as np
    hist = np.bincount(gray.ravel(), minlength=256).astype(float)
    total = gray.size
    sum_all = (np.arange(256) * hist).sum()
    w0 = s0 = 0.0
    best, thr = 0.0, 127
    for t in range(256):
        w0 += hist[t]
        if w0 == 0:
            continue
        w1 = total - w0
        if w1 == 0:
            break
        s0 += t * hist[t]
        m0, m1 = s0 / w0, (sum_all - s0) / w1
        between = w0 * w1 * (m0 - m1) ** 2
        if between > best:
            best, thr = between, t
    return thr


def _deskew(img):
    import numpy as np
    from PIL import Image
    small = img.convert("L")
    small.thumbnail((900, 900))
    best_angle, best_score = 0.0, -1.0
    for a in [x / 2 for x in range(-6, 7)]:
        arr = np.asarray(small.rotate(a, resample=Image.BILINEAR, fillcolor=255)) < 128
        score = float(np.var(arr.sum(axis=1)))
        if score > best_score:
            best_angle, best_score = a, score
    if best_angle == 0:
        return img
    return img.rotate(best_angle, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255))


def preprocess(img, variants=3):
    """نسخ محسّنة من الصورة: أصل مكبّر، تباين وحدّة، ثم ثنائية (أبيض وأسود)."""
    import numpy as np
    from PIL import Image, ImageFilter, ImageOps
    img = ImageOps.exif_transpose(img).convert("RGB")
    w = img.width
    if w < 2000:
        scale = min(3.0, 2000 / w)
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    elif w > 3600:
        img = img.resize((3600, int(img.height * 3600 / w)), Image.LANCZOS)
    img = _deskew(img)
    out = [("الأصل", img)]
    if variants >= 2:
        g = ImageOps.autocontrast(img.convert("L"), cutoff=2).filter(ImageFilter.UnsharpMask(radius=2, percent=150))
        out.append(("تباين وحدّة", g.convert("RGB")))
    if variants >= 3:
        g = np.asarray(ImageOps.autocontrast(img.convert("L"), cutoff=1))
        thr = _otsu(g)
        out.append(("ثنائية", Image.fromarray(((g > thr) * 255).astype("uint8")).convert("RGB")))
    return out


def image_quality(img):
    """ملاحظات جودة قبل القراءة."""
    import numpy as np
    notes = []
    if img.width < 900:
        notes.append("دقة الصورة منخفضة؛ يُفضّل لقطة شاشة أو مسح بدقة 300 dpi.")
    g = np.asarray(img.convert("L").resize((min(img.width, 1200), int(img.height * min(img.width, 1200) / img.width))), dtype=float)
    lap = g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    if float(lap.var()) < 60:
        notes.append("الصورة تبدو غير واضحة (ضبابية)؛ قد تقلّ دقة القراءة.")
    return notes


# ------------------------------------------------------------------ PDF
def pdf_page_count(data):
    import fitz
    with fitz.open(stream=data, filetype="pdf") as doc:
        return doc.page_count


def pdf_text_rows(data, page_no):
    """صفوف من طبقة النص في الصفحة (إن وُجدت)."""
    import fitz
    with fitz.open(stream=data, filetype="pdf") as doc:
        words = doc[page_no].get_text("words")
    items = [((w[0] + w[2]) / 2, (w[1] + w[3]) / 2, w[3] - w[1], w[4], 1.0) for w in words]
    return items_to_rows(items)


def pdf_find_text_page(data):
    """رقم أول صفحة (من 0) فيها جدول إحداثيات في طبقة النص، أو None."""
    for p in range(pdf_page_count(data)):
        try:
            if tabular.find_block(pdf_text_rows(data, p)):
                return p
        except Exception:  # noqa: BLE001
            continue
    return None


def render_pdf_page(data, page_no, dpi=300):
    import fitz
    from PIL import Image
    with fitz.open(stream=data, filetype="pdf") as doc:
        pix = doc[page_no].get_pixmap(dpi=dpi)
        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)


# ------------------------------------------------------------------ المسار الكامل
def finalize(block, disagree, reads, source):
    """يطبّق الفحص الحسابي والتصحيح الذاتي ويجهّز النتيجة للعرض."""
    xs, ys, dists, area = block["xs"], block["ys"], block["dists"], block["area"]
    fixes = []
    if block["kind"] == "utm":
        xs, ys, fixes = autofix(xs, ys, dists, area)
    result = {"source": source, "kind": block["kind"], "swapped": block["swapped"],
              "labels": list(block["labels"]), "xs": list(xs), "ys": list(ys),
              "dists": dists, "area": area, "disagree": sorted(disagree), "fixes": fixes, "reads": reads}
    return result


def analyze_rows_variants(rows_list, source="OCR"):
    blocks = [block_from_rows(r) for r in rows_list if r]
    merged, disagree, reads = vote(blocks)
    return finalize(merged, disagree, reads, source) if merged else None


def read_image(img, variants=3):
    """OCR على نسخ محسّنة من الصورة ثم دمج القراءات."""
    rows_list = [items_to_rows(run_engine(v)) for _, v in preprocess(img, variants)]
    return analyze_rows_variants(rows_list, "OCR")
