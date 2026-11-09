"""التحويلات الجغرافية المشتركة بين كل أدوات المنصة.

إزاحة كلارك 1880 منقولة حرفياً من المحلل الجغرافي الذكي، وهي معتمدة للنطاقين 40N و41N.
"""
from functools import lru_cache
from statistics import median

from pyproj import Transformer

_CLARKE_K = 382.1899238
CLARKE_SHIFT_E = _CLARKE_K * 0.757628555   # ≈ 289.56 م
CLARKE_SHIFT_N = _CLARKE_K * 0.652685967   # ≈ 249.45 م

ZONES = {"40N": 32640, "41N": 32641}
DEFAULT_ZONE = "40N"

SYSTEMS = {
    "decimal": "درجات عشرية (WGS84)",
    "utm_wgs": "UTM — WGS84",
    "utm_clarke": "UTM — كلارك 1880",
}


@lru_cache(maxsize=None)
def _to_utm(zone):
    return Transformer.from_crs("EPSG:4326", f"EPSG:{ZONES[zone]}", always_xy=True)


@lru_cache(maxsize=None)
def _to_ll(zone):
    return Transformer.from_crs(f"EPSG:{ZONES[zone]}", "EPSG:4326", always_xy=True)


def ll_to_utm(lon, lat, zone=DEFAULT_ZONE):
    return _to_utm(zone).transform(lon, lat)


def utm_to_ll(e, n, zone=DEFAULT_ZONE):
    return _to_ll(zone).transform(e, n)


def utm_to_clarke(e, n):
    """UTM-WGS84 إلى UTM-كلارك (نفس معادلة الكود الأصلي)."""
    return e - CLARKE_SHIFT_E, n - CLARKE_SHIFT_N


def clarke_to_utm(e, n):
    return e + CLARKE_SHIFT_E, n + CLARKE_SHIFT_N


def ll_to_clarke(lon, lat, zone=DEFAULT_ZONE):
    return utm_to_clarke(*ll_to_utm(lon, lat, zone))


def clarke_to_ll(e, n, zone=DEFAULT_ZONE):
    return utm_to_ll(*clarke_to_utm(e, n), zone)


def to_ll(system, x, y, zone=DEFAULT_ZONE):
    """أي نظام إدخال إلى (lon, lat). x = الشرقي أو الطول، y = الشمالي أو العرض."""
    if system == "decimal":
        return x, y
    if system == "utm_wgs":
        return utm_to_ll(x, y, zone)
    return clarke_to_ll(x, y, zone)


def from_ll(system, lon, lat, zone=DEFAULT_ZONE):
    """(lon, lat) إلى نظام الإخراج (للرسم في DXF مثلاً)."""
    if system == "utm_wgs":
        return ll_to_utm(lon, lat, zone)
    if system == "utm_clarke":
        return ll_to_clarke(lon, lat, zone)
    return lon, lat


# ---------- التمييز بين الصيغ والفحص المبدئي للقيم ----------

def guess_format(a, b):
    """يخمّن صيغة زوج القيم: decimal أو utm (أو None)."""
    if abs(a) <= 180 and abs(b) <= 180:
        return "decimal"
    if abs(a) >= 1000 and abs(b) >= 1000:
        return "utm"
    return None


def check_values(system, x, y):
    """رسالة تنبيه إن بدت القيم غير متسقة مع النظام المختار، وإلا None."""
    guess = guess_format(x, y)
    if system == "decimal":
        if guess == "utm":
            return "القيم تبدو بصيغة UTM وليست درجات عشرية — غيّر نظام الإدخال."
        if not (40 <= x <= 70 and 10 <= y <= 35):
            return "القيم خارج النطاق المتوقع لمنطقة الخليج (الطول 40–70، العرض 10–35). تأكد من ترتيب الطول والعرض."
    else:
        if guess == "decimal":
            return "القيم تبدو درجات عشرية وليست UTM — غيّر نظام الإدخال."
        if not (100_000 <= x <= 900_000 and 1_000_000 <= y <= 4_000_000):
            return "القيم خارج المدى المعتاد لـ UTM (الشرقي 100000–900000، الشمالي 1000000–4000000). جرّب تبديل الشرقي والشمالي."
    return None


def autoswap(system, xs, ys):
    """يرتّب الأعمدة (x = شرقي/طول، y = شمالي/عرض) اعتماداً على حجم القيم. يعيد (xs, ys, swapped)."""
    mx, my = median(xs), median(ys)
    swapped = (mx < my) if system == "decimal" else (mx > my)
    return (ys, xs, True) if swapped else (xs, ys, False)
