"""الصيغ الثلاث للإحداثيات وجدول العرض (نفس تنسيق coord-table في المحلل الجغرافي الذكي)."""
import pandas as pd

from . import geo

COLS = ["النقطة", "LONGITUDE (E)", "LATITUDE (N)", "Utm_Easting", "Utm_Northing",
        "Utm_Easting (Adj)", "Utm_Northing (Adj)"]


def build_rows(points, zone):
    """points: [(label, lon, lat)] → قائمة صفوف بالصيغ الثلاث."""
    rows = []
    for label, lon, lat in points:
        e, n = geo.ll_to_utm(lon, lat, zone)
        ce, cn = geo.utm_to_clarke(e, n)
        rows.append({"label": label, "lon": lon, "lat": lat,
                     "utm_e": e, "utm_n": n, "ck_e": ce, "ck_n": cn})
    return rows


def coord_table_html(rows):
    body = ""
    for r in rows:
        body += f"""
            <tr>
                <td style='font-weight:700; color:#162746;'>{r['label']}</td>
                <td>{r['lon']:.6f}</td>
                <td>{r['lat']:.6f}</td>
                <td>{r['utm_e']:.2f}</td>
                <td>{r['utm_n']:.2f}</td>
                <td>{r['ck_e']:.2f}</td>
                <td>{r['ck_n']:.2f}</td>
            </tr>
        """
    return f"""
    <table class='coord-table'>
        <thead>
            <tr>
                <th rowspan='2' style='vertical-align:middle; width:8%;'>النقطة</th>
                <th colspan='2' style='background-color:#162746;'>Decimal Degree / WGS84</th>
                <th colspan='2' style='background-color:#790420;'>UTM - WGS84</th>
                <th colspan='2' style='background-color:#162746;'>UTM - CLARKE1880</th>
            </tr>
            <tr>
                <th class='sub-header'>LONGITUDE (E)</th>
                <th class='sub-header'>LATITUDE (N)</th>
                <th class='sub-header'>Utm_Easting</th>
                <th class='sub-header'>Utm_Northing</th>
                <th class='sub-header'>Utm_Easting (Adj)</th>
                <th class='sub-header'>Utm_Northing (Adj)</th>
            </tr>
        </thead>
        <tbody>{body}</tbody>
    </table>
    """


def rows_dataframe(rows):
    return pd.DataFrame(
        [[r["label"], round(r["lon"], 6), round(r["lat"], 6), round(r["utm_e"], 3),
          round(r["utm_n"], 3), round(r["ck_e"], 3), round(r["ck_n"], 3)] for r in rows],
        columns=COLS,
    )
