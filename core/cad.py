"""KML ⇄ DXF (صيغة DXF مفتوحة وتفتحها AutoCAD؛ DWG مغلقة وتحتاج محوّلاً خارجياً)."""
import io

from . import geo
from .kml_io import dedupe

try:
    import ezdxf
except ImportError:  # pragma: no cover
    ezdxf = None

AVAILABLE = ezdxf is not None
LAYERS = {"point": "KML_POINTS", "line": "KML_LINES", "polygon": "KML_POLYGONS"}


def features_to_dxf(features, zone, system="utm_wgs"):
    """يرسم العناصر بإحداثيات UTM (WGS84 أو كلارك) ويعيد bytes لملف DXF."""
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    for layer in LAYERS.values():
        doc.layers.add(layer)
    for f in features:
        pts = [geo.from_ll(system, lon, lat, zone) for lon, lat in f["coords"]]
        layer = LAYERS[f["type"]]
        if f["type"] == "point":
            msp.add_point(pts[0], dxfattribs={"layer": layer})
        else:
            msp.add_lwpolyline(pts, close=(f["type"] == "polygon" and len(pts) >= 3),
                               dxfattribs={"layer": layer})
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")


def read_dxf(data):
    """يقرأ DXF ويعيد عناصر بإحداثيات الرسم الأصلية (x, y)."""
    text = None
    for enc in ("utf-8", "cp1256", "cp1252"):
        try:
            text = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    doc = ezdxf.read(io.StringIO(text))
    features = []
    for e in doc.modelspace():
        kind, layer = e.dxftype(), e.dxf.layer
        closed = False
        if kind == "LWPOLYLINE":
            pts = [(p[0], p[1]) for p in e.get_points("xy")]
            closed = bool(e.closed)
        elif kind == "POLYLINE":
            pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
            closed = bool(e.is_closed)
        elif kind == "LINE":
            pts = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
        elif kind == "POINT":
            pts = [(e.dxf.location.x, e.dxf.location.y)]
        else:
            continue
        if not pts:
            continue
        if kind == "POINT":
            ftype = "point"
        elif closed and len(pts) >= 3:
            ftype = "polygon"
        else:
            ftype = "line"
        features.append({"name": f"{layer}-{len(features) + 1}", "type": ftype, "coords": pts})
    return dedupe(features)
