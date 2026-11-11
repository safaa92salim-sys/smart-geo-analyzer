"""أداة تحويل الإحداثيات."""
import math

import pandas as pd
import streamlit as st

from core import cad, geo, kml_io, oda, tabular
from core.device import is_mobile
from ui.components import hero, mobile_tile, notice, section_title, tab_nav
from ui.results import render_results

CONVERTER_CSS = """
<style>
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label {
    font-size: 17px !important; font-weight: 700 !important; color: #162746 !important;
}
[data-testid="stRadio"] label p { font-size: 16px !important; font-weight: 600 !important; }
[data-testid="stCheckbox"] label p { font-size: 16px !important; font-weight: 600 !important; }
input, textarea { font-size: 17px !important; font-weight: 600 !important; }
[data-baseweb="select"] * { font-size: 16px !important; font-weight: 600 !important; }
[data-testid="stSegmentedControl"] button, [data-testid="stSegmentedControl"] button p {
    font-size: 16px !important; font-weight: 700 !important;
}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
    font-size: 15px !important; font-weight: 600 !important; color: #475569 !important;
}
[data-testid="stFileUploaderDropzone"] *, [data-testid="stFileUploader"] small {
    font-size: 15px !important; font-weight: 600 !important;
}
[data-testid="stAlert"] p { font-size: 15.5px !important; font-weight: 600 !important; }
.notice-box { font-size: 16px !important; font-weight: 600 !important; }
</style>
"""

AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩٫", "0123456789.")

SECTIONS = ["تحويل نقطة", "مجموعة نقاط", "استخراج من KML", "KML ⇄ DXF / DWG"]
SECTION_ICONS = ["crosshair", "list", "map", "repeat"]

SAMPLE = {  # أمثلة مبدئية لتظهر النتيجة فور فتح الأداة
    "decimal": ("57.620000", "22.530000"),
    "utm_wgs": ("563668.61", "2490949.59"),
    "utm_clarke": ("563668.61", "2490949.59"),
}
AXES = {
    "decimal": ("خط الطول Longitude (E)", "خط العرض Latitude (N)"),
    "utm_wgs": ("الشرقي Easting", "الشمالي Northing"),
    "utm_clarke": ("الشرقي Easting", "الشمالي Northing"),
}


def _num(text):
    s = str(text).strip().translate(AR_DIGITS).replace(" ", "")
    if "," in s or "،" in s:
        s = s.replace("،", ",")
        s = s.replace(",", ".") if "." not in s and s.count(",") == 1 else s.replace(",", "")
    return float(s)


def _point_feature(name, lon, lat):
    return {"name": name, "type": "point", "coords": [(lon, lat)]}


def _system_radio(key, options=None, label="نظام الإدخال"):
    options = options or list(geo.SYSTEMS)
    return st.radio(label, options, format_func=geo.SYSTEMS.get, horizontal=True, key=key)


# ---------------------------------------------------------------- تحويل نقطة
def single_point(zone):
    system = _system_radio("sp_sys")
    lx, ly = AXES[system]
    dx, dy = SAMPLE[system]
    c1, c2 = st.columns(2)
    x_txt = c1.text_input(lx, value=dx, key=f"sp_x_{system}")
    y_txt = c2.text_input(ly, value=dy, key=f"sp_y_{system}")
    try:
        x, y = _num(x_txt), _num(y_txt)
    except ValueError:
        st.error("أدخل أرقاماً صحيحة في الحقلين (مثال: 563668.61).")
        return
    msg = geo.check_values(system, x, y)
    if msg:
        st.warning(msg)
    lon, lat = geo.to_ll(system, x, y, zone)
    if not (math.isfinite(lon) and math.isfinite(lat)):
        st.error("تعذّر التحويل لهذه القيم. تحقق من النظام المختار والنطاق.")
        return
    render_results([_point_feature("P1", lon, lat)], zone, key="sp")


# ---------------------------------------------------------------- مجموعة نقاط
KIND_AR = {"utm": "UTM (شرقي / شمالي)", "decimal": "درجات عشرية (طول / عرض)"}
SAMPLE_UTM = [(563668.61, 2490949.59), (563846.76, 2491040.48), (564073.98, 2490595.09), (563895.83, 2490504.20)]


def _editor(df, key, fmt):
    cfg = {
        "النقطة": st.column_config.TextColumn("النقطة"),
        "X (شرقي / طول)": st.column_config.NumberColumn("↔ الشرق X (طول)", format=fmt),
        "Y (شمالي / عرض)": st.column_config.NumberColumn("↕ الشمال Y (عرض)", format=fmt),
    }
    try:
        return st.data_editor(df, num_rows="dynamic", width="stretch", column_config=cfg, key=key)
    except TypeError:
        return st.data_editor(df, num_rows="dynamic", use_container_width=True, column_config=cfg, key=key)


def _drop_repeats(lls, labels, closed):
    """يحذف النقاط المتتالية المتطابقة، ونقطة الإغلاق المكررة (الأولى في آخر القائمة) عند المضلع."""
    keep = [0]
    for i in range(1, len(lls)):
        if (round(lls[i][0], 9), round(lls[i][1], 9)) != (round(lls[keep[-1]][0], 9), round(lls[keep[-1]][1], 9)):
            keep.append(i)
    if closed and len(keep) > 3 and (round(lls[keep[-1]][0], 9), round(lls[keep[-1]][1], 9)) == (round(lls[0][0], 9), round(lls[0][1], 9)):
        keep.pop()
    return [lls[i] for i in keep], [labels[i] for i in keep], len(lls) - len(keep)


def batch_points(zone):
    st.caption("يقرأ البرنامج الجدول تلقائياً أينما كان في الملف أو في أي ورقة، وبأي ترتيب للشمالي والشرقي، "
               "ويتجاهل الأعمدة الأخرى. المطلوب فقط أن يكون الشرقي والشمالي (أو الطول والعرض) في عمودين متجاورين.")
    up = st.file_uploader("رفع ملف نقاط (Excel أو CSV أو TXT) — اختياري", type=["xlsx", "xlsm", "xls", "csv", "txt"], key="bt_file")
    pasted = st.text_area("أو الصق الإحداثيات هنا (من Excel أو من أي نص)", height=100, key="bt_paste",
                          placeholder="مثال:\nP1   563668.61   2490949.59\nP2   563846.76   2491040.48")

    block, where, sig = None, "", None
    try:
        if up is not None:
            block, where = tabular.from_file(up.getvalue(), up.name)
            sig = ("file", up.name, up.size)
        elif pasted.strip():
            block, where = tabular.from_text(pasted)
            sig = ("text", pasted.strip()[:80])
    except Exception as e:  # noqa: BLE001
        st.error(f"تعذّرت قراءة البيانات: {e}")
    if sig and block is None:
        st.warning("لم أجد عمودين متجاورين يشبهان إحداثيات (شرقي وشمالي أو طول وعرض). يمكنك لصق النقاط في الجدول أدناه.")

    # تحديد الصيغة تلقائياً مرة واحدة لكل ملف (يبقى اختيار WGS84 أو كلارك للمستخدم)
    if block and st.session_state.get("bt_sig") != sig:
        st.session_state["bt_sig"] = sig
        if block["kind"] == "decimal":
            st.session_state["bt_sys"] = "decimal"
        elif st.session_state.get("bt_sys", "utm_wgs") == "decimal":
            st.session_state["bt_sys"] = "utm_wgs"
    system = _system_radio("bt_sys")

    if block:
        st.success(f"تم العثور على {len(block['xs'])} نقطة تلقائياً في {where}. الصيغة المكتشفة: {KIND_AR[block['kind']]}.")
        if block["swapped"]:
            st.info("ترتيب الشمالي والشرقي في الملف معكوس، وقد صُحّح تلقائياً.")
        df = pd.DataFrame({"النقطة": block["labels"], "X (شرقي / طول)": block["xs"], "Y (شمالي / عرض)": block["ys"]})
    elif system == "decimal":
        df = pd.DataFrame({"النقطة": ["P1"], "X (شرقي / طول)": [57.62], "Y (شمالي / عرض)": [22.53]})
    else:
        df = pd.DataFrame({"النقطة": [f"P{i + 1}" for i in range(4)],
                           "X (شرقي / طول)": [p[0] for p in SAMPLE_UTM], "Y (شمالي / عرض)": [p[1] for p in SAMPLE_UTM]})
    st.caption("يمكن تعديل القيم أو لصقها مباشرة، وإضافة صفوف من أسفل الجدول.")
    edited = _editor(df, f"bt_ed_{system}_{hash(sig)}", "%.6f" if system == "decimal" else "%.3f")

    clean = edited.dropna(subset=[edited.columns[1], edited.columns[2]]).reset_index(drop=True)
    if clean.empty:
        notice("أدخل نقطة واحدة على الأقل لعرض النتائج.")
        return
    xs, ys = clean.iloc[:, 1].astype(float).tolist(), clean.iloc[:, 2].astype(float).tolist()
    labels = [str(l) if pd.notna(l) and str(l).strip() else f"P{i + 1}" for i, l in enumerate(clean.iloc[:, 0])]

    msg = geo.check_values(system, xs[0], ys[0])
    if msg:
        st.warning(msg)
    lls = [geo.to_ll(system, x, y, zone) for x, y in zip(xs, ys)]
    if not all(math.isfinite(v) for p in lls for v in p):
        st.error("تعذّر تحويل بعض النقاط. تحقق من النظام المختار والنطاق.")
        return

    closed = st.checkbox("اعتبار النقاط مضلعاً مغلقاً (للخريطة وملف KML والمساحة)", value=len(lls) >= 3, key="bt_closed")
    closed = closed and len(lls) >= 3
    lls, labels, removed = _drop_repeats(lls, labels, closed)
    if removed:
        st.info(f"تم تجاهل {removed} نقطة مكررة (نقاط متتالية متطابقة أو نقطة إغلاق تعيد النقطة الأولى).")
    if closed and len(lls) >= 3:
        features = [{"name": "المضلع", "type": "polygon", "coords": lls, "labels": labels}]
    else:
        features = [_point_feature(l, lon, lat) for l, (lon, lat) in zip(labels, lls)]
    render_results(features, zone, key="bt")


def _maybe_polygon(feats, key):
    """إن لم يوجد مضلع (مسار أو نقاط فقط) يعرض خيار اعتبار الإحداثيات مضلعاً مغلقاً لحساب المساحة."""
    if any(f["type"] == "polygon" for f in feats):
        return feats
    poly = kml_io.to_polygon(feats)
    if poly is None:
        return feats
    what = "المسار" if poly["source"] == "line" else "النقاط"
    if st.checkbox(f"اعتبار {what} مضلعاً مغلقاً (لحساب المساحة وإظهار حدود الأرض)", value=poly["source"] == "line", key=key):
        return [poly]
    return feats


# ---------------------------------------------------------------- استخراج من KML
def kml_extract(zone):
    up = st.file_uploader("ارفع ملف KML", type=["kml"], key="kx_file")
    if up is None:
        notice("ارفع ملف KML لاستخراج إحداثياته بالصيغ الثلاث (درجات عشرية، UTM-WGS84، UTM-كلارك).")
        return
    try:
        feats, dropped = kml_io.parse_kml(up.getvalue(), with_stats=True)
    except Exception as e:  # noqa: BLE001
        st.error(f"تعذّرت قراءة ملف KML: {e}")
        return
    if not feats:
        st.error("لم يُعثر على نقاط أو خطوط أو مضلعات داخل الملف.")
        return
    if dropped:
        st.info(f"تم تجاهل {dropped} عنصر مكرر (دبابيس رؤوس أو خطوط تعيد رسم حدود المضلع).")
    options = ["كل العناصر"] + [f"{i + 1}. {f['name']} ({kml_io.TYPE_AR[f['type']]})" for i, f in enumerate(feats)]
    sel = st.selectbox("العنصر", options, key="kx_sel") if len(feats) > 1 else options[0]
    chosen = feats if sel == options[0] else [feats[options.index(sel) - 1]]
    chosen = _maybe_polygon(chosen, "kx_poly")
    render_results(chosen, zone, key="kx")


# ---------------------------------------------------------------- KML <-> DXF / DWG
SAVEAS_HINT = ("الرجاء إعادة حفظ الملف بصيغة <b>.DXF</b>: افتح الملف في AutoCAD ونفّذ الأمر <b>SAVEAS</b> "
               "ثم اختر <b>AutoCAD 2010 DXF</b> واحفظه، ثم أعد رفع ملف DXF هنا.")


def _read_cad_upload(up):
    """DXF مباشرة، وDWG عبر ODA File Converter إن كان مثبتاً. يعيد bytes لملف DXF أو None."""
    if not up.name.lower().endswith(".dwg"):
        return up.getvalue()
    exe = oda.find_converter(st.session_state.get("oda_path", ""))
    if not exe:
        notice(SAVEAS_HINT)
        with st.expander("للأجهزة المثبّت عليها برنامج ODA File Converter (قراءة DWG مباشرة)"):
            st.caption("برنامج مجاني يتطلب تسجيلاً وفتحه مرة واحدة للتفعيل، ولا يتوفر على الاستضافة السحابية.")
            st.text_input("مسار ODAFileConverter.exe (إن لم يُكتشف تلقائياً)", key="oda_path")
        return None
    with st.spinner("جارٍ تحويل DWG إلى DXF..."):
        return oda.dwg_to_dxf_bytes(up.getvalue(), exe)


def kml_dxf(zone):
    notice("هذه الأداة تمكّنك من تحويل وعرض موقعك الاستثماري بين برنامج الأوتوكاد (.DXF / .DWG) "
           "وبرنامج جوجل إيرث (.KML).")
    st.write("")
    if not cad.AVAILABLE:
        st.error("مكتبة ezdxf غير مثبتة. نفّذ: pip install ezdxf")
        return
    mode = st.radio("اتجاه التحويل", ["KML → DXF", "DXF / DWG → KML"], horizontal=True, key="cad_mode")

    if mode == "KML → DXF":
        up = st.file_uploader("ارفع ملف KML", type=["kml"], key="cad_kml")
        if up is None:
            return
        try:
            feats = kml_io.parse_kml(up.getvalue())
            if not feats:
                st.error("لم يُعثر على عناصر داخل الملف.")
                return
            dxf_wgs = cad.features_to_dxf(feats, zone, "utm_wgs")
            dxf_ck = cad.features_to_dxf(feats, zone, "utm_clarke")
        except Exception as e:  # noqa: BLE001
            st.error(f"تعذّر التحويل: {e}")
            return
        notice("موقع الأرض أصبح جاهز للاستخدام في برنامج AutoCAD")
        st.write("")
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("تنزيل موقع الأرض بالنظام الاحداثي WGS84", dxf_wgs, file_name="GeoTools_WGS-UTM.dxf",
                               mime="application/dxf", icon=":material/download:", key="cad_dl_wgs")
        with c2:
            st.download_button("تنزيل موقع الأرض بالنظام الاحداثي CLARKE-1880", dxf_ck, file_name="GeoTools_CLARKE1880.dxf",
                               mime="application/dxf", icon=":material/download:", key="cad_dl_ck")
        render_results(feats, zone, key="cad1", stats=False, kml_button=False)
    else:
        system = _system_radio("cad_sys", ["utm_wgs", "utm_clarke"], label="النظام الإحداثي للملف الذي سترفعه")
        up = st.file_uploader("ارفع ملف الأوتوكاد (DXF أو DWG)", type=["dxf", "dwg"], key="cad_dxf")
        if up is None:
            return
        try:
            data = _read_cad_upload(up)
            if data is None:
                return
            raw = cad.read_dxf(data)
        except Exception as e:  # noqa: BLE001
            st.error(f"تعذّرت قراءة الملف (يلزم DXF نصي ASCII وليس ثنائياً): {e}")
            return
        if not raw:
            st.error("لم يُعثر على نقاط أو خطوط أو مضلعات (LWPOLYLINE / POLYLINE / LINE / POINT) داخل الرسم.")
            return
        msg = geo.check_values("utm_wgs", raw[0]["coords"][0][0], raw[0]["coords"][0][1])
        if msg:
            st.warning("إحداثيات الرسم لا تبدو UTM: " + msg)
        feats = [{**f, "coords": [geo.to_ll(system, x, y, zone) for x, y in f["coords"]]} for f in raw]
        if not all(math.isfinite(v) for f in feats for p in f["coords"] for v in p):
            st.error("تعذّر تحويل إحداثيات الرسم. تحقق من النظام والنطاق.")
            return
        feats = _maybe_polygon(feats, "cad_poly")
        # زر KML مباشرة بعد رفع الملف (إجراء سريع)
        st.download_button("تنزيل الموقع بصيغة KML", kml_io.build_kml(feats), file_name="GeoTools.kml",
                           mime="application/vnd.google-earth.kml+xml", icon=":material/download:", key="cad_kml_dl")
        render_results(feats, zone, key="cad2", stats=False, kml_button=False)


# ---------------------------------------------------------------- الصفحة
CONV_IMAGES = ["conv_point.png", "conv_batch.png", "conv_kml.png", "conv_cad.png"]   # اختيارية: ضعها في assets لتحلّ محل الأيقونات


def _open_section(label):
    st.session_state["conv_section"] = label


def _back_to_menu():
    st.session_state.pop("conv_section", None)


st.markdown(CONVERTER_CSS, unsafe_allow_html=True)
hero("محوّل الإحداثيات", "تحويل فوري بين الدرجات العشرية وUTM-WGS84 وUTM-كلارك 1880")

mobile = is_mobile()
if mobile and st.session_state.get("conv_section") not in SECTIONS:
    # الهاتف: صفحة بطاقات للانتقال إلى أداة التحويل المطلوبة
    for i, label in enumerate(SECTIONS):
        mobile_tile(f"conv{i}", label, CONV_IMAGES[i], SECTION_ICONS[i], on_click=_open_section, args=(label,))
else:
    if mobile:
        st.button("‹  أدوات التحويل", key="conv_back", on_click=_back_to_menu)
    zone = st.radio("نطاق UTM", list(geo.ZONES), horizontal=True, key="utm_zone",
                    help="النطاق الافتراضي 40N. تُطبَّق إزاحة كلارك نفسها على النطاقين.")
    section = st.session_state["conv_section"] if mobile else tab_nav(SECTIONS, SECTION_ICONS, key="conv_section")
    st.write("")

    if section == SECTIONS[0]:
        single_point(zone)
    elif section == SECTIONS[1]:
        batch_points(zone)
    elif section == SECTIONS[2]:
        kml_extract(zone)
    else:
        kml_dxf(zone)
