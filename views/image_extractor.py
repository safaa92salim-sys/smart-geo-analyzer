"""أداة استخراج الإحداثيات من صورة أو PDF ممسوح ضوئياً (قراءة مجانية + مراجعة + إسقاط)."""
import io
import math

import pandas as pd
import streamlit as st
from PIL import Image

from core import geo, kml_io, ocr, tabular
from ui.components import hero, ms, nav_pills, notice, section_title, stepper
from ui.results import render_results

st.markdown("""
<style>
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label { font-size: 16.5px !important; font-weight: 700 !important; color: #162746 !important; }
[data-testid="stRadio"] label p, [data-testid="stCheckbox"] label p { font-size: 15.5px !important; font-weight: 600 !important; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { font-size: 14.5px !important; font-weight: 600 !important; color: #475569 !important; }
[data-testid="stFileUploaderDropzone"] *, [data-testid="stAlert"] p, .notice-box { font-size: 15.5px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

MODES = ["رفع صورة أو PDF", "التقاط صورة بالكاميرا", "لصق نص الإحداثيات"]
SYS_LABEL = {"utm_wgs": "WGS84", "utm_clarke": "CLARKE1880"}
STEPS = ["رفع الملف", "اختيار النظام الإحداثي", "مراجعة الاحداثيات", "الإسقاط والنتائج"]

hero("استخراج الإحداثيات من صورة أو PDF", "قراءة جدول الإحداثيات من مستند ممسوح ضوئياً وإسقاطه كمضلع مغلق جاهز للتحليل")
step_slot = st.empty()


def draw_stepper():
    with step_slot.container():
        stepper(STEPS, active=2 if st.session_state.get("ie_result") else 0, large=True)


draw_stepper()

notice("تعليمات للمستخدم: لتحصل على أفضل نتيجة قم برفع صورة واضحة للإحداثيات أو لقطة شاشة بصيغة .PNG "
       "يتم التنبيه للإحداثيات غير الواضحة ليراجعها المستخدم مع خاصية التعديل قبل الاسقاط")
st.write("")

c1, c2 = st.columns([3, 2])
with c1:
    system = st.radio("النظام الإحداثي للإحداثيات الموجودة في المستند", list(SYS_LABEL), format_func=SYS_LABEL.get,
                      horizontal=True, key="ie_sys",
                      help="لا يمكن تمييز WGS84 عن كلارك من الأرقام وحدها، لذلك الاختيار لك. الدرجات العشرية تُعتبر WGS84.")
with c2:
    zone = st.radio("نطاق UTM", list(geo.ZONES), horizontal=True, key="ie_zone")

mode = nav_pills(MODES, key="ie_mode")
st.write("")


def _clear():
    st.session_state.pop("ie_result", None)


if st.session_state.get("ie_mode_prev") != mode:      # تغيير طريقة الإدخال يمسح النتيجة السابقة
    st.session_state["ie_mode_prev"] = mode
    _clear()


def _show_image(img):
    shown = img.copy()
    shown.thumbnail((1400, 1400))
    try:
        st.image(shown, width="stretch")
    except TypeError:
        st.image(shown, use_container_width=True)


def _editor(df, key):
    cfg = {
        "النقطة": st.column_config.TextColumn("النقطة"),
        "X (شرقي / طول)": st.column_config.NumberColumn("↔ الشرق X (طول)", format="%.3f"),
        "Y (شمالي / عرض)": st.column_config.NumberColumn("↕ الشمال Y (عرض)", format="%.3f"),
    }
    try:
        return st.data_editor(df, num_rows="dynamic", width="stretch", column_config=cfg, key=key)
    except TypeError:
        return st.data_editor(df, num_rows="dynamic", use_container_width=True, column_config=cfg, key=key)


# ------------------------------------------------------------------ القراءة
def _read_upload(up, page, variants):
    data, name = up.getvalue(), up.name.lower()
    if name.endswith(".pdf"):
        try:
            rows = ocr.pdf_text_rows(data, page)
        except ImportError:
            raise RuntimeError("لقراءة PDF ثبّت المكتبة: pip install pymupdf")
        block = ocr.block_from_rows(rows) if rows else None
        if block:
            return ocr.finalize(block, set(), 1, "pdf-text"), ocr.render_pdf_page(data, page, 130)
        img = ocr.render_pdf_page(data, page, 300)
    else:
        img = Image.open(io.BytesIO(data))
        img.load()
    if not ocr.ocr_available():
        raise RuntimeError("لقراءة الصور الممسوحة ثبّت المحرك المجاني: pip install rapidocr-onnxruntime — "
                           "أو استخدم خيار «لصق نص الإحداثيات».")
    return ocr.read_image(img, variants), img


def _from_text(text):
    block = ocr.block_from_rows(tabular.text_to_rows(text))
    return ocr.finalize(block, set(), 1, "text") if block else None


if mode in (MODES[0], MODES[1]):
    if mode == MODES[0]:
        up = st.file_uploader("ارفع صورة الإحداثيات أو ملف PDF",
                              type=["png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff", "pdf"], key="ie_file")
    else:
        up = st.camera_input("صوّر جدول الإحداثيات (الورقة مستقيمة وبإضاءة جيدة، والجدول يملأ الصورة)", key="ie_cam")
    file_sig = (up.name, up.size) if up is not None else None
    if st.session_state.get("ie_file_sig") != file_sig:   # صورة جديدة أو حُذفت الصورة: امسح بيانات السابقة
        st.session_state["ie_file_sig"] = file_sig
        _clear()
    if up is not None:
        page = 0
        if up.name.lower().endswith(".pdf"):
            try:
                n_pages = ocr.pdf_page_count(up.getvalue())
                guess = ocr.pdf_find_text_page(up.getvalue()) if n_pages > 1 else None
                page = int(st.number_input("رقم الصفحة", 1, n_pages, (guess or 0) + 1, key=f"ie_page_{up.name}_{up.size}")) - 1
            except ImportError:
                st.error("لقراءة PDF ثبّت المكتبة: pip install pymupdf")
                st.stop()
        fast = st.checkbox("قراءة سريعة (نسخة واحدة من الصورة، أقل دقة)", value=False, key="ie_fast")
        variants = 1 if fast else 3
        sig = (up.name, up.size, page, variants)
        if st.button("قراءة الإحداثيات", icon=":material/document_scanner:", key="ie_run"):
            with st.spinner("جارٍ قراءة المستند... قد يستغرق الأمر بضع ثوانٍ"):
                try:
                    res, img = _read_upload(up, page, variants)
                except Exception as e:  # noqa: BLE001
                    _clear()
                    st.error(str(e))
                    st.stop()
            if res is None:
                _clear()
                st.warning("لم أجد جدول إحداثيات واضحاً في المستند. جرّب صورة أوضح أو قصّ الجدول فقط، "
                           "أو استخدم «لصق نص الإحداثيات».")
            else:
                st.session_state["ie_result"] = {"sig": sig, "res": res, "img": img}
                st.rerun()
else:
    pasted = st.text_area("الصق جدول الإحداثيات هنا", height=150, key="ie_paste",
                          placeholder="LINE  NORTHING  EASTING  DIST\n1 2  2490949.59  563668.61  200.00\n2 3  2491040.48  563846.76  500.00")
    if not pasted.strip():
        _clear()
    else:
        sig = ("text", pasted.strip()[:100])
        cur = st.session_state.get("ie_result")
        if not cur or cur["sig"] != sig:
            res = _from_text(pasted)
            if res is None:
                _clear()
                st.warning("لم أجد عمودين متجاورين يشبهان إحداثيات في النص.")
            else:
                st.session_state["ie_result"] = {"sig": sig, "res": res, "img": None}
                st.rerun()

draw_stepper()

# ------------------------------------------------------------------ المراجعة والنتائج
state = st.session_state.get("ie_result")
if not state:
    st.stop()

res, img, sig = state["res"], state["img"], state["sig"]
is_utm = res["kind"] == "utm"

st.markdown("---")
section_title(f"{ms('check-square')} مراجعة الاحداثيات المقروءة")

for f in res["fixes"]:
    st.success(f"تم تصحيح قراءة النقطة {res['labels'][f['row']]} تلقائياً.")

v0 = ocr.validate(res["xs"], res["ys"], res["dists"], res["area"]) if is_utm and len(res["xs"]) >= 3 else None
unclear = set(res["disagree"]) | (v0["soft"] if v0 and v0["checked"] else set())
unclear -= {f["row"] for f in res["fixes"]}
if unclear:
    names = "، ".join(res["labels"][i] for i in sorted(unclear) if i < len(res["labels"]))
    st.warning(f"بعض الإحداثيات غير واضحة في الصورة ({names}). راجعها مع الصورة قبل الإسقاط.")

df = pd.DataFrame({"النقطة": res["labels"], "X (شرقي / طول)": res["xs"], "Y (شمالي / عرض)": res["ys"]})
if img is not None:
    left, right = st.columns([3, 2])
else:
    left, right = st.container(), None
with left:
    st.caption("عدّل أي رقم يخالف الصورة، ويمكن حذف صف أو إضافة صف.")
    edited = _editor(df, f"ie_ed_{hash(sig)}")
if right is not None:
    with right:
        _show_image(img)

clean = edited.dropna(subset=["X (شرقي / طول)", "Y (شمالي / عرض)"]).reset_index(drop=True)
if clean.empty:
    notice("أدخل نقطة واحدة على الأقل.")
    st.stop()
xs, ys = clean["X (شرقي / طول)"].astype(float).tolist(), clean["Y (شمالي / عرض)"].astype(float).tolist()
labels = [str(l) if pd.notna(l) and str(l).strip() else f"P{i + 1}" for i, l in enumerate(clean["النقطة"])]

conv_sys = system if is_utm else "decimal"
msg = geo.check_values(conv_sys, xs[0], ys[0])
if msg:
    st.warning(msg)
lls = [geo.to_ll(conv_sys, x, y, zone) for x, y in zip(xs, ys)]
if not all(math.isfinite(v) for p in lls for v in p):
    st.error("تعذّر تحويل بعض النقاط. تحقق من النظام والنطاق.")
    st.stop()

closed = st.checkbox("اعتبار النقاط مضلعاً مغلقاً", value=len(lls) >= 3, key="ie_closed") and len(lls) >= 3
if closed:
    features = [{"name": "الأرض", "type": "polygon", "coords": lls, "labels": labels}]
else:
    features = [{"name": l, "type": "point", "coords": [p]} for l, p in zip(labels, lls)]


def analyze_action():
    if st.button("تحليل الأرض في المحلل الجغرافي الذكي", icon=":material/travel_explore:",
                 key="ie_handoff", disabled=not closed):
        st.session_state["handoff_kml"] = ("الأرض_المستخرجة.kml", kml_io.build_kml(features, "الأرض المستخرجة"))
        st.switch_page("views/analyzer.py")


render_results(features, zone, key="ie", stats=False, table=False, actions=analyze_action,
               actions_title="إجراءات المستخدم")
