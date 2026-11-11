"""الثيم البصري للمنصة.

BASE_CSS منقول حرفياً من app.py الأصلي (الخط El Messiri والألوان #790420 و#162746).
EXTRA_CSS طبقة إضافية للتنقل والتبويبات والصفحة الرئيسية، ولا تغيّر ما سبق.
"""
import streamlit as st

from ui.icons import icon_css

BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=El+Messiri:wght@400;600;700&display=swap');

/* إخفاء عناصر Streamlit غير المرغوبة وزر طي الشريط الجانبي */
.stAppDeployButton {display: none !important;}
#MainMenu {visibility: hidden !important;}
footer {visibility: hidden !important;}
[data-testid="stSidebarCollapseButton"] {display: none !important;}

/* تطبيق الخط العربي والاتجاه RTL */
html, body, [class*="css"], div, span, label, input, textarea, button {
    font-family: 'El Messiri', 'Segoe UI', sans-serif !important;
    direction: rtl !important;
    text-align: right !important;
}

.stApp {
    background-color: #FAFAFB;
}

/* 1. الشريط الجانبي */
[data-testid="stSidebar"] {
    min-width: 360px !important;
    max-width: 380px !important;
    background-color: #FFFFFF !important;
    border-left: 1.5px solid #E2E8F0 !important;
    box-shadow: -4px 0 15px rgba(0,0,0,0.03) !important;
    padding-top: 15px !important;
}

[data-testid="stSidebar"] label {
    font-size: 15px !important;
    font-weight: 700 !important;
    color: #162746 !important;
    margin-bottom: 4px !important;
}

[data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea {
    font-size: 14px !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    padding: 8px !important;
    background-color: #F8FAFC !important;
}

/* 2. زر رفع الملفات */
[data-testid="stFileUploader"] {
    background-color: #F8FAFC;
    border: 1.5px dashed #790420;
    border-radius: 10px;
    padding: 10px;
    text-align: center;
}
[data-testid="stFileUploader"] section {
    padding: 5px !important;
}
[data-testid="stFileUploader"] button {
    background-color: #790420 !important;
    color: #FFFFFF !important;
    border-radius: 6px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 5px 14px !important;
}

/* الهيدر والعناوين الرئيسية */
.hero-container {
    background: linear-gradient(135deg, #790420 0%, #162746 100%);
    padding: 20px 15px;
    border-radius: 14px;
    color: #FFFFFF;
    text-align: center;
    box-shadow: 0 6px 16px rgba(121, 4, 32, 0.12);
    margin-bottom: 20px;
}

.hero-title {
    color: #FFFFFF !important;
    font-size: 25px !important;
    font-weight: 700 !important;
    margin-bottom: 4px;
    text-align: center !important;
}

.hero-subtitle {
    color: #E2E8F0 !important;
    font-size: 15px !important;
    font-weight: 400;
    text-align: center !important;
}

.custom-card {
    background-color: #FFFFFF;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #E9ECEF;
    box-shadow: 0 3px 10px rgba(0,0,0,0.02);
    margin-bottom: 12px;
}

/* كروت المساحة والبيانات الأساسية */
.metric-box {
    background-color: #F8FAFC;
    border: 1.2px solid #CBD5E1;
    border-radius: 10px;
    padding: 10px 8px;
    text-align: center !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.01);
}

.metric-title {
    color: #162746;
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 3px;
}

.metric-value {
    color: #790420;
    font-size: 17px;
    font-weight: 700;
}

/* 3. تنسيق جداول HTML المخصصة العامة */
.custom-table {
    width: 100%;
    border-collapse: collapse;
    direction: rtl;
    text-align: center;
    margin-top: 8px;
}
.custom-table th {
    background-color: #162746;
    color: #FFFFFF;
    padding: 8px;
    font-size: 13px;
    font-weight: 600;
    border: 1px solid #CBD5E1;
}
.custom-table th.sub-header {
    background-color: #790420;
    color: #FFFFFF;
    font-size: 12px;
}
.custom-table td {
    padding: 7px 8px;
    font-size: 12.5px;
    border: 1px solid #E2E8F0;
    text-align: center;
}
.custom-table tr:nth-child(even) {
    background-color: #F8FAFC;
}

/* 4. تنسيق مخصص لجدول إحداثيات الموقع الاستثماري (خط أكبر و Bold) */
.coord-table {
    width: 100%;
    border-collapse: collapse;
    direction: rtl;
    text-align: center;
    margin-top: 8px;
}
.coord-table th {
    background-color: #162746;
    color: #FFFFFF;
    padding: 10px;
    font-size: 14px;
    font-weight: 700;
    border: 1px solid #CBD5E1;
}
.coord-table th.sub-header {
    background-color: #790420;
    color: #FFFFFF;
    font-size: 13px;
    font-weight: 700;
}
.coord-table td {
    padding: 10px 8px;
    font-size: 14.5px !important;
    font-weight: bold !important;
    color: #162746 !important;
    border: 1px solid #E2E8F0;
    text-align: center;
}
.coord-table tr:nth-child(even) {
    background-color: #F8FAFC;
}

/* 5. قسم المراجع والملاحظة */
.references-box {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-right: 4px solid #162746;
    border-radius: 12px;
    padding: 18px;
    margin-top: 25px;
    box-shadow: 0 3px 10px rgba(0,0,0,0.02);
}
.references-title {
    color: #162746;
    font-size: 15px;
    font-weight: 700;
    margin-bottom: 10px;
}
.references-text {
    color: #475569;
    font-size: 13px;
    line-height: 1.7;
    margin-bottom: 12px;
}
.notice-box {
    background-color: #F8FAFC;
    border: 1px dashed #790420;
    border-radius: 8px;
    padding: 10px 14px;
    color: #790420;
    font-size: 12.5px;
    font-weight: 600;
    line-height: 1.6;
}

.footer-text {
    text-align: center !important;
    color: #64748B;
    font-size: 12px;
    font-weight: 600;
    margin-top: 25px;
    padding: 12px 0;
    border-top: 1px solid #E2E8F0;
}

.footer-text a {
    color: #790420;
    text-decoration: none;
}
</style>
"""

EXTRA_CSS = """
<style>
/* ============ طبقة التحسينات: تُضاف فوق الثيم الأصلي دون تعديله ============ */

/* حماية أيقونات Material من قاعدة الخط العامة في الثيم الأصلي */
[data-testid="stIconMaterial"], .material-symbols-rounded, [class*="material-icons"] {
    font-family: 'Material Symbols Rounded', 'Material Icons' !important;
    direction: ltr !important;
}

.block-container { padding-top: 2.2rem !important; max-width: 1240px; }

/* ---------- التنقل في الشريط الجانبي ---------- */
[data-testid="stSidebarNavLink"] {
    border-radius: 8px !important;
    margin: 2px 8px !important;
    padding: 9px 12px !important;
}
[data-testid="stSidebarNavLink"] span {
    color: #162746 !important;
    font-weight: 600 !important;
    font-size: 15px !important;
}
[data-testid="stSidebarNavLink"]:hover { background-color: #F1F5F9 !important; }
[data-testid="stSidebarNavLink"][aria-current="page"] { background-color: #790420 !important; }
[data-testid="stSidebarNavLink"][aria-current="page"] span { color: #FFFFFF !important; }

/* ---------- التبويبات ---------- */
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1.5px solid #E2E8F0; }
.stTabs [data-baseweb="tab"] { padding: 10px 18px; }
.stTabs [data-baseweb="tab"] p { font-weight: 700; color: #475569; }
.stTabs [aria-selected="true"] p { color: #790420 !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color: #790420 !important; height: 3px !important; }
.stTabs [data-baseweb="tab-panel"] {
    background-color: #FFFFFF;
    border: 1px solid #E9ECEF;
    border-radius: 12px;
    padding: 20px;
    margin-top: 14px;
}

/* ---------- الأزرار وروابط الصفحات ---------- */
.stButton button, .stDownloadButton button {
    background-color: #790420 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.55rem 1.3rem !important;
}
.stButton button p, .stDownloadButton button p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}
.stButton button:hover, .stDownloadButton button:hover { background-color: #5E031A !important; }

[data-testid="stPageLink"] a {
    border: 1.5px solid #790420 !important;
    border-radius: 8px !important;
    justify-content: center;
    width: 100%;
}
[data-testid="stPageLink"] a, [data-testid="stPageLink"] a * {
    color: #790420 !important;
    font-weight: 700 !important;
}
[data-testid="stPageLink"] a:hover { background-color: #790420 !important; }
[data-testid="stPageLink"] a:hover * { color: #FFFFFF !important; }

/* ---------- الهيرو: خطوط كنتورية خفيفة فوق التدرج الأصلي ---------- */
.hero-container { position: relative; overflow: hidden; }
.hero-container > * { position: relative; }
.hero-container::before {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background:
        repeating-radial-gradient(ellipse 70% 120% at 8% 115%, transparent 0 26px, rgba(255,255,255,0.075) 26px 27.5px),
        repeating-radial-gradient(ellipse 60% 100% at 100% -10%, transparent 0 34px, rgba(255,255,255,0.055) 34px 35.5px);
}

/* هيرو الصفحة الرئيسية */
.hero-big {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 28px;
    padding: 34px 38px !important;
    text-align: right !important;
}
.hero-big .hero-text { flex: 1 1 auto; }
.hero-big .hero-title { text-align: right !important; font-size: 34px !important; line-height: 1.4; }
.hero-big .hero-subtitle { text-align: right !important; font-size: 16px !important; line-height: 1.9; max-width: 48ch; }
.hero-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
.hero-chip {
    border: 1px solid rgba(255,255,255,0.38);
    color: #FFFFFF;
    padding: 3px 12px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
}
.hero-art { flex: 0 0 250px; }
.hero-art svg { width: 100%; height: auto; display: block; }
.hero-art text { font-family: 'El Messiri', sans-serif; fill: #FFFFFF; }

/* لحظة الحركة الوحيدة: رسم حدود الأرض مرة واحدة عند فتح الصفحة */
.parcel-line { stroke-dasharray: 700; stroke-dashoffset: 700; animation: parcel-draw 2.2s ease-out 0.3s forwards; }
.parcel-fill { opacity: 0; animation: parcel-fill 0.8s ease 2.2s forwards; }
@keyframes parcel-draw { to { stroke-dashoffset: 0; } }
@keyframes parcel-fill { to { opacity: 1; } }
@media (prefers-reduced-motion: reduce) {
    .parcel-line { animation: none; stroke-dashoffset: 0; }
    .parcel-fill { animation: none; opacity: 1; }
}

/* ---------- عنوان القسم ---------- */
.section-title {
    color: #162746;
    font-size: 20px;
    font-weight: 700;
    margin: 28px 0 12px 0;
    padding-right: 12px;
    border-right: 4px solid #790420;
}

/* ---------- بطاقات الأدوات (نفس لغة الشريط الجانبي في جدول التربة) ---------- */
.tool-card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-right: 4px solid var(--accent, #790420);
    border-radius: 10px;
    padding: 20px 22px;
    margin-bottom: 10px;
}
.tool-card.primary { padding: 26px 28px; }
.tool-head { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.tool-icon { font-size: 26px; line-height: 1; }
.tool-title { color: #162746; font-size: 19px; font-weight: 700; }
.tool-card.primary .tool-title { font-size: 23px; }
.tool-desc { color: #64748B; font-size: 14px; line-height: 1.8; margin: 0 0 10px 0; }
.tool-list { margin: 0; padding: 0 18px 0 0; color: #475569; font-size: 13.5px; line-height: 1.95; }
.tool-card.primary .tool-list { columns: 2; column-gap: 28px; }
.tool-badge {
    margin-inline-start: auto;
    background-color: #FEF3C7;
    color: #92400E;
    font-size: 11.5px;
    font-weight: 700;
    padding: 2px 9px;
    border-radius: 5px;
}

/* ---------- مؤشر الخطوات ---------- */
.stepper { display: flex; flex-wrap: wrap; gap: 10px; margin: 6px 0 18px 0; }
.step {
    flex: 1;
    min-width: 150px;
    display: flex;
    align-items: center;
    gap: 10px;
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 10px 12px;
}
.step-num {
    width: 28px;
    height: 28px;
    flex-shrink: 0;
    border-radius: 50%;
    background-color: #E2E8F0;
    color: #162746;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 700;
    text-align: center !important;
}
.step-text { color: #475569; font-size: 13px; font-weight: 600; line-height: 1.5; }
.step.active { border-color: #790420; }
.step.active .step-num { background-color: #790420; color: #FFFFFF; }
.step.active .step-text { color: #790420; }
.step.done .step-num { background-color: #162746; color: #FFFFFF; }

/* ---------- الأرقام والإحداثيات ---------- */
.coord-table td, .metric-value { font-variant-numeric: tabular-nums; }

/* ---------- الجوال ---------- */
@media (max-width: 768px) {
    html body [data-testid="stSidebar"] { min-width: 0 !important; width: 86vw !important; max-width: 86vw !important; }
    html body [data-testid="stSidebar"][aria-expanded="false"] { display: none !important; }
    [data-testid="stSidebarCollapseButton"] { display: flex !important; }
    .hero-big { flex-direction: column-reverse; padding: 24px 20px !important; }
    .hero-big .hero-title { font-size: 25px !important; }
    .hero-art { flex-basis: auto; width: 170px; }
    .tool-card.primary .tool-list { columns: 1; }
}

/* ============ الدفعة الأولى: تعديلات الرئيسية والشعار ============ */

/* الهيرو: العنوان والوصف في سطر واحد */
.hero-big .hero-title { white-space: nowrap; font-size: clamp(24px, 2.6vw, 34px) !important; }
.hero-big .hero-subtitle { white-space: nowrap; max-width: none !important; font-size: clamp(14px, 1.3vw, 17px) !important; margin-top: 6px; }
.hero-art { flex: 0 0 200px; }
@media (max-width: 1100px) {
    .hero-big .hero-title, .hero-big .hero-subtitle { white-space: normal; }
}

/* مستطيل وصف المنظومة */
.intro-box {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-right: 5px solid #790420;
    border-radius: 10px;
    padding: 18px 24px;
    margin: 18px 0 4px 0;
}
.intro-text { color: #334155; font-size: 16.5px; font-weight: 600; line-height: 2; }
.intro-years {
    background-color: #162746;
    color: #FFFFFF;
    font-weight: 700;
    font-size: 15px;
    padding: 5px 14px;
    border-radius: 6px;
    white-space: nowrap;
}

/* بطاقات الأدوات الأفقية */
.tool-tile {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-right: 4px solid var(--accent, #790420);
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 10px;
}
.tool-img { display: block; width: 100%; height: 150px; object-fit: cover; }
.tool-img-empty {
    display: flex; align-items: center; justify-content: center;
    font-size: 44px; background-color: #F1F5F9;
}
.tool-name {
    display: flex; align-items: center; gap: 8px;
    padding: 12px 16px;
    color: #162746; font-size: 18px; font-weight: 700;
}

/* الشعار في الشريط الجانبي: أكبر وأوضح */
[data-testid="stSidebarHeader"] {
    height: auto !important;
    min-height: 0 !important;
    padding: 1.1rem 1rem 0.4rem 1rem !important;
    justify-content: center !important;
}
[data-testid="stSidebarHeader"] img, img[data-testid="stLogo"] {
    height: 5.6rem !important;
    max-width: 100% !important;
    width: auto !important;
    object-fit: contain !important;
}

/* ============ الدفعة الثانية ============ */

/* هيرو مُوسَّط (الرسم صار زخرفة جانبية) */
.hero-big { display: block !important; text-align: center !important; padding: 38px 190px !important; }
.hero-big .hero-text, .hero-big .hero-title, .hero-big .hero-subtitle { text-align: center !important; }
.hero-big .hero-subtitle { margin-inline: auto; }
.hero-big .hero-art { position: absolute; left: 26px; top: 50%; transform: translateY(-50%); width: 118px; flex: none; opacity: 0.92; }
@media (max-width: 1100px) {
    .hero-big { padding: 26px 20px !important; }
    .hero-big .hero-art { display: none; }
}

/* مستطيل الوصف: نص واحد مُوسَّط والسنوات ضمنه */
.intro-box { display: block !important; text-align: center !important; padding: 20px 30px; }
.intro-text { display: inline; text-align: center; }
.intro-sep { color: #790420; font-weight: 700; margin: 0 8px; }
.intro-years {
    display: inline;
    background: none !important;
    color: #790420 !important;
    padding: 0 !important;
    font-size: 16.5px;
    font-weight: 700;
}

/* عنوان القسم داخل مستطيل منقط (نفس لغة صناديق الإرشاد) */
.section-banner {
    border: 2px dashed #790420;
    background-color: #F8FAFC;
    border-radius: 10px;
    padding: 12px 20px;
    margin: 26px 0 16px 0;
    text-align: center !important;
    color: #162746;
    font-size: 22px;
    font-weight: 700;
    text-shadow: 1px 1px 0 rgba(121, 4, 32, 0.15);
}
.section-banner .sep { color: #790420; margin: 0 12px; }
.section-banner .en { color: #790420; letter-spacing: 0.5px; }

/* مؤشر الخطوات القابل للنقر (نفس مظهر stepper) */
[class*="st-key-stepnav"] div.stButton { width: 100%; }
[class*="st-key-stepnav"] button {
    width: 100%;
    justify-content: flex-start !important;
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    padding: 10px 12px !important;
    min-height: 0 !important;
}
[class*="st-key-stepnav"] button:hover { border-color: #790420 !important; background-color: #FFFFFF !important; }
[class*="st-key-stepnav"] button p {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 0 !important;
    color: #475569 !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
    text-align: right !important;
}
[class*="st-key-stepnav"] button p::before {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background-color: #E2E8F0;
    color: #162746;
    font-size: 14px;
    font-weight: 700;
}

/* ============ الدفعة الثالثة: أيقونات Material داخل HTML ============ */
.ms {
    font-family: 'Material Symbols Rounded', 'Material Icons' !important;
    font-weight: normal;
    font-style: normal;
    font-size: 1.25em;
    line-height: 1;
    letter-spacing: normal;
    text-transform: none;
    display: inline-block;
    white-space: nowrap;
    direction: ltr;
    vertical-align: -0.2em;
    margin-inline-end: 6px;
    font-feature-settings: 'liga';
    -webkit-font-feature-settings: 'liga';
}
.section-title .ms, .references-title .ms { color: #790420; }
.tool-img-empty .ms { font-size: 56px; margin: 0; color: #790420; }

/* ============ بطاقة الأداة: منطقة صورة مربعة ============ */
.tool-tile { text-align: center; }
.tool-img {
    display: block !important;
    width: 170px !important;
    height: 170px !important;
    aspect-ratio: 1 / 1;
    margin: 20px auto 6px auto;
    object-fit: contain !important;
    border-radius: 16px;
    background-color: #FFFFFF;
}
.tool-img-empty { display: flex !important; align-items: center; justify-content: center; font-size: 56px; background-color: #F1F5F9; }
.tool-img-empty .ic { width: 64px; height: 64px; margin: 0; color: #790420; }
.tool-name { justify-content: center; }
.section-title .ic, .references-title .ic { color: #790420; }

/* ============ الدفعة الرابعة: نصوص كاملة + عناوين تبويبات بارزة + الهاتف واللوح ============ */
.stButton button, .stDownloadButton button {
    white-space: normal !important; height: auto !important; min-height: 3rem !important; line-height: 1.5 !important;
}
.stButton button p, .stDownloadButton button p { white-space: normal !important; line-height: 1.5 !important; }
[data-testid="stPageLink"] a { white-space: normal !important; min-height: 3rem; }

/* عناوين التبويبات الرئيسية فقط */
.stTabs [data-baseweb="tab"] p { font-size: 17px !important; font-weight: 700 !important; }
[class*="st-key-stepnav"] button p { font-size: 16px !important; font-weight: 700 !important; }
[data-testid="stSegmentedControl"] button, [data-testid="stSegmentedControl"] button p { font-size: 16px !important; font-weight: 700 !important; }
[class*="st-key-tabnav"] button { white-space: normal !important; min-height: 3.2rem !important; }
[class*="st-key-tabnav"] button p { white-space: normal !important; line-height: 1.4 !important; }

/* ============ الدفعة الخامسة: تخفيف أحجام الخطوط وإخفاء أدوات المطوّر ============ */
[data-testid="stToolbar"], [data-testid="stToolbarActions"], [data-testid="stAppDeployButton"],
[data-testid="stMainMenu"], [data-testid="stStatusWidget"], .stAppDeployButton, #MainMenu { display: none !important; }

.hero-container .hero-title { font-size: clamp(21px, 2.1vw, 28px) !important; }
.hero-container .hero-subtitle { font-size: clamp(13px, 1.05vw, 15px) !important; }
.hero-big .hero-title { font-size: clamp(22px, 2.2vw, 30px) !important; }
.hero-big .hero-subtitle { font-size: clamp(13px, 1.1vw, 15.5px) !important; }
.section-banner { font-size: 20px; }
.section-title { font-size: 18px; }
.tool-name { font-size: 16.5px; }
.stTabs [data-baseweb="tab"] p { font-size: 15px !important; }
[class*="st-key-stepnav"] button p { font-size: 14px !important; }
[class*="st-key-tabnav"] button p { font-size: 15px !important; }
[data-testid="stSegmentedControl"] button, [data-testid="stSegmentedControl"] button p { font-size: 14.5px !important; }

/* ============ الدفعة السادسة: شريط موحّد + هامش علوي + مراحل موحدة ============ */
.block-container { padding-top: 4.4rem !important; }
[data-testid="stHeader"] { background: transparent !important; }

.hero-big {
    display: flex !important;
    flex-direction: column;
    justify-content: center;
    min-height: 150px;
    padding: 30px clamp(20px, 13vw, 150px) !important;
}
.hero-big .hero-title, .hero-big .hero-subtitle { white-space: normal !important; }
.hero-big .hero-art { width: 96px; left: 22px; }

.notice-box.notice-lg { font-size: 17.5px !important; line-height: 2 !important; padding: 16px 20px !important; }

.step-lg .step { padding: 12px 14px; }
.step-lg .step-text { font-size: 15px !important; font-weight: 700 !important; }
[class*="st-key-stepnav"] button { padding: 12px 14px !important; }
[class*="st-key-stepnav"] button p { font-size: 15px !important; }

/* ----- الأجهزة اللوحية ----- */
@media (max-width: 1024px) and (min-width: 769px) {
    .block-container { padding: 1.6rem 1.2rem 3rem 1.2rem !important; }
    .hero-big { padding: 26px 22px !important; }
    .tool-img { width: 140px !important; height: 140px !important; }
}

/* ----- الهاتف: لا يعمل إلا على الشاشات الضيقة، فلا يتغير شكل الكمبيوتر ----- */
@media (max-width: 768px) {
    .block-container { padding: 1rem 0.75rem 3rem 0.75rem !important; }
    .hero-container { padding: 16px 12px !important; }
    .hero-title { font-size: 19px !important; line-height: 1.5 !important; }
    .hero-subtitle { font-size: 12.5px !important; }
    .hero-big { padding: 20px 14px !important; }
    .hero-big .hero-title { font-size: 21px !important; white-space: normal !important; }
    .hero-big .hero-subtitle { font-size: 13.5px !important; white-space: normal !important; }
    .intro-box { padding: 14px 14px; }
    .intro-text, .intro-years { font-size: 14px !important; line-height: 1.9; }
    .section-banner { font-size: 17px; padding: 10px 12px; margin: 18px 0 12px 0; }
    .section-title { font-size: 17px; margin-top: 20px; }
    .tool-img { width: 112px !important; height: 112px !important; margin: 12px auto 4px auto !important; }
    .tool-name { font-size: 16px; padding: 8px 10px; }
    .stepper { flex-direction: column; gap: 6px; }
    .step { min-width: 0; padding: 8px 10px; }
    .metric-box { padding: 10px; }
    .metric-value { font-size: 17px !important; }
    .coord-table { display: block; overflow-x: auto; white-space: nowrap; font-size: 12px; }
    iframe[title*="st_folium"] { height: 330px !important; }
    .stButton button, .stDownloadButton button, [data-testid="stPageLink"] a { width: 100% !important; min-height: 3.2rem !important; }
    .stTabs [data-baseweb="tab-list"] { overflow-x: auto; }
    .stTabs [data-baseweb="tab"] { padding: 8px 10px; }
    .stTabs [data-baseweb="tab"] p { font-size: 15px !important; }
    .stTabs [data-baseweb="tab-panel"] { padding: 10px; }
    [class*="st-key-tabnav"] button p { font-size: 15px !important; }
    html body [data-testid="stSidebar"] { min-width: 0 !important; width: 86vw !important; max-width: 86vw !important; }
    html body [data-testid="stSidebar"][aria-expanded="false"] { display: none !important; }
    [data-testid="stSidebarCollapseButton"] { display: flex !important; }
    .notice-box { font-size: 14px !important; padding: 10px 12px; line-height: 1.8; }
    .references-box { font-size: 13px; padding: 12px; }
    .footer-text { font-size: 12px; }
    [data-testid="stFileUploaderDropzone"] * { font-size: 14px !important; }
}

/* ============ الدفعة السابعة: بطاقة الأداة قابلة للضغط على الكمبيوتر ============ */
.tool-tile { transition: box-shadow 0.2s ease, transform 0.2s ease; }
[class*="st-key-dtile-"] { position: relative; cursor: pointer; }
[class*="st-key-dtile-"] [data-testid="stPageLink"] { position: absolute !important; inset: 0; margin: 0 !important; z-index: 5; }
[class*="st-key-dtile-"] [data-testid="stPageLink"] a { width: 100% !important; height: 100% !important; opacity: 0; border: none !important; }
[class*="st-key-dtile-"]:hover .tool-tile { box-shadow: 0 12px 28px rgba(22, 39, 70, 0.14); transform: translateY(-3px); }

</style>
"""


def inject_theme():
    st.markdown(BASE_CSS + EXTRA_CSS + icon_css(), unsafe_allow_html=True)
