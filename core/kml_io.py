"""قراءة وكتابة KML.

العنصر (feature) قاموس: {"name", "type": point|line|polygon, "coords": [(lon, lat)], "labels": [...] اختياري}
المضلع يُخزَّن بدون تكرار النقطة الأولى، ويُغلق تلقائياً عند الكتابة (بحيث يقرؤه المحلل الجغرافي مباشرة).
"""
import re
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

TYPE_AR = {"point": "نقطة", "line": "خط", "polygon": "مضلع"}


def labels_for(f):
    if f.get("labels"):
        return list(f["labels"])
    if f["type"] == "point":
        return [f["name"]]
    return [f"P{i + 1}" for i in range(len(f["coords"]))]


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _parse_coords(text):
    out = []
    # بعض الملفات تكتب "lon, lat, alt" بمسافات؛ نوحّدها قبل التقسيم
    for token in re.sub(r"\s*,\s*", ",", text or "").split():
        parts = token.split(",")
        if len(parts) >= 2:
            try:
                out.append((float(parts[0]), float(parts[1])))
            except ValueError:
                continue
    return out


def _r(c):
    return (round(c[0], 8), round(c[1], 8))


def dedupe(features):
    """يزيل التكرار الشائع في ملفات KML/DXF:
    نقاط متتالية متطابقة، عناصر متطابقة، ونقاط/خطوط تعيد رسم رؤوس مضلع موجود (دبابيس الرؤوس وخط الحدود)."""
    cleaned = []
    for f in features:
        pts = []
        for c in f["coords"]:
            if not pts or _r(c) != _r(pts[-1]):
                pts.append(c)
        if f["type"] == "polygon" and len(pts) > 1 and _r(pts[0]) == _r(pts[-1]):
            pts = pts[:-1]
        if not pts:
            continue
        g = dict(f)
        g["coords"] = pts
        if g["type"] == "polygon" and len(pts) < 3:
            g["type"] = "line" if len(pts) > 1 else "point"
        if g["type"] == "line" and len(pts) == 1:
            g["type"] = "point"
        cleaned.append(g)

    seen, uniq = set(), []
    for f in cleaned:
        key = (f["type"], frozenset(_r(c) for c in f["coords"]))
        if key not in seen:
            seen.add(key)
            uniq.append(f)

    poly_sets = [frozenset(_r(c) for c in f["coords"]) for f in uniq if f["type"] == "polygon"]
    if not poly_sets:
        return uniq
    return [f for f in uniq
            if f["type"] == "polygon" or not any({_r(c) for c in f["coords"]} <= ps for ps in poly_sets)]


def parse_kml(data, with_stats=False):
    """يعيد قائمة عناصر من ملف KML (نقاط، خطوط، مضلعات) بعد إزالة التكرار."""
    root = ET.fromstring(data)
    features = []
    for pm in root.iter():
        if _local(pm.tag) != "Placemark":
            continue
        name = None
        for child in pm:
            if _local(child.tag) == "name" and child.text:
                name = child.text.strip()
        inside_poly = {id(e) for pol in pm.iter() if _local(pol.tag) == "Polygon" for e in pol.iter()}
        for g in pm.iter():
            kind = _local(g.tag)
            if kind == "Track":  # gx:Track: كل gx:coord نص "lon lat alt"
                pts = []
                for c in g.iter():
                    if _local(c.tag) == "coord" and c.text:
                        parts = c.text.split()
                        if len(parts) >= 2:
                            try:
                                pts.append((float(parts[0]), float(parts[1])))
                            except ValueError:
                                pass
                if pts:
                    features.append({"name": name or f"مسار {len(features) + 1}", "type": "line", "coords": pts})
                continue
            if kind not in ("Point", "LineString", "Polygon", "LinearRing") or id(g) in inside_poly and kind != "Polygon":
                continue
            coords_el = next((c for c in g.iter() if _local(c.tag) == "coordinates"), None)
            if coords_el is None:
                continue
            coords = _parse_coords(coords_el.text)
            if not coords:
                continue
            closed = len(coords) > 3 and coords[0] == coords[-1]
            if kind in ("Polygon", "LinearRing") or (kind == "LineString" and closed):
                if len(coords) > 1 and coords[0] == coords[-1]:
                    coords = coords[:-1]
                ftype = "polygon" if len(coords) >= 3 else "line"
            else:
                ftype = "point" if kind == "Point" else "line"
            features.append({"name": name or f"عنصر {len(features) + 1}", "type": ftype, "coords": coords})
    cleaned = dedupe(features)
    if with_stats:
        return cleaned, len(features) - len(cleaned)
    return cleaned


def _c(lon, lat):
    return f"{lon:.8f},{lat:.8f},0"


def build_kml(features, doc_name="GeoTools"):
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
        f"<name>{escape(doc_name)}</name>",
        '<Style id="geo"><LineStyle><color>ff200479</color><width>3</width></LineStyle>'
        "<PolyStyle><color>66200479</color></PolyStyle></Style>",
    ]
    for f in features:
        coords, ftype = f["coords"], f["type"]
        if ftype == "polygon" and len(coords) < 3:
            ftype = "line"
        if ftype == "point":
            geom = f"<Point><coordinates>{_c(*coords[0])}</coordinates></Point>"
        elif ftype == "line":
            geom = "<LineString><tessellate>1</tessellate><coordinates>" + " ".join(_c(*p) for p in coords) + "</coordinates></LineString>"
        else:
            ring = list(coords) + [coords[0]]
            geom = ("<Polygon><tessellate>1</tessellate><outerBoundaryIs><LinearRing><coordinates>"
                    + " ".join(_c(*p) for p in ring) + "</coordinates></LinearRing></outerBoundaryIs></Polygon>")
        out.append(f"<Placemark><name>{escape(f['name'])}</name><styleUrl>#geo</styleUrl>{geom}</Placemark>")
    out.append("</Document></kml>")
    return "\n".join(out).encode("utf-8")


def _simple_xy(pts):
    """True إذا لم يتقاطع المضلع مع نفسه (تقريب مستوٍ على الإحداثيات كما هي)."""
    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return 0 if v == 0 else (1 if v > 0 else -1)
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            c, d = pts[j], pts[(j + 1) % n]
            if orient(a, b, c) * orient(a, b, d) < 0 and orient(c, d, a) * orient(c, d, b) < 0:
                return False
    return True


def to_polygon(features, name="المضلع"):
    """يبني مضلعاً مغلقاً من مسار (خطوط) أو من نقاط الدبابيس، بالترتيب الوارد في الملف.
    إن تقاطعت الحدود وكان المصدر نقاطاً فقط تُرتَّب النقاط زاوياً حول المركز. يعيد None إن قلّت النقاط عن 3."""
    lines = [f for f in features if f["type"] == "line"]
    source = "line" if lines else "point"
    src = lines or [f for f in features if f["type"] == "point"]
    pts = []
    for f in src:
        for c in f["coords"]:
            if not pts or _r(c) != _r(pts[-1]):
                pts.append(c)
    if len(pts) > 1 and _r(pts[0]) == _r(pts[-1]):
        pts.pop()
    if len(pts) < 3:
        return None
    if source == "point" and not _simple_xy(pts):
        import math
        cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
        pts = sorted(pts, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
    return {"name": name, "type": "polygon", "coords": pts, "source": source}
