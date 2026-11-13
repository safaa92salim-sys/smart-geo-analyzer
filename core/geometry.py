"""مساحة المضلع بالمتر المربع والفدان.

الطريقة نفسها المستخدمة في المحلل الجغرافي: مساحة مستوية في إحداثيات UTM (WGS84)، ومعامل الفدان 4200.833.
إزاحة كلارك انتقال ثابت، فلا تغيّر المساحة.
"""
from . import geo

FEDDAN_M2 = 4200.833


def polygon_area_m2(coords_ll, zone):
    pts = [geo.ll_to_utm(lon, lat, zone) for lon, lat in coords_ll]
    x0, y0 = pts[0]
    pts = [(x - x0, y - y0) for x, y in pts]          # تقليل الأخطاء العددية
    s = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]))
    return abs(s) / 2.0


def _orient(p, q, r):
    v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    return 0 if abs(v) < 1e-9 else (1 if v > 0 else -1)


def _cross(a, b, c, d):
    """هل يتقاطع القطعان ab وcd تقاطعاً حقيقياً؟"""
    return _orient(a, b, c) * _orient(a, b, d) < 0 and _orient(c, d, a) * _orient(c, d, b) < 0


def is_simple(coords_ll, zone):
    """False إذا كان المضلع يتقاطع مع نفسه (ترتيب النقاط غير صحيح)."""
    pts = [geo.ll_to_utm(lon, lat, zone) for lon, lat in coords_ll]
    n = len(pts)
    edges = [(pts[i], pts[(i + 1) % n]) for i in range(n)]
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue  # ضلعان متجاوران (الأول والأخير)
            if _cross(*edges[i], *edges[j]):
                return False
    return True


def area_info(coords_ll, zone):
    m2 = polygon_area_m2(coords_ll, zone)
    return {"m2": m2, "feddan": m2 / FEDDAN_M2, "valid": is_simple(coords_ll, zone)}
