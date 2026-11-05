"""نقطة الدخول: الإعدادات والثيم والتنقل بين أدوات المنصة."""
import os

import streamlit as st
from PIL import Image

from core.assets import get_asset
from ui.components import footer, ms, png_data_uri
from ui.theme import inject_theme

logo_path = get_asset("logo.png")
icon_path = get_asset("icon.png")

try:
    page_icon_img = Image.open(icon_path) if os.path.exists(icon_path) else (Image.open(logo_path) if os.path.exists(logo_path) else ":material/public:")
except Exception:
    page_icon_img = ":material/public:"

st.set_page_config(
    page_title="GeoTools | المحلل الجغرافي الذكي",
    page_icon=page_icon_img,
    layout="wide",
    initial_sidebar_state="auto",
)
inject_theme()

pages = [
    st.Page("views/home.py", title="الرئيسية", icon=":material/home:", default=True),
    st.Page("views/image_extractor.py", title="استخراج الإحداثيات من صورة", icon=":material/document_scanner:", url_path="image-extractor"),
    st.Page("views/analyzer.py", title="المحلل الجغرافي الذكي", icon=":material/travel_explore:", url_path="analyzer"),
    st.Page("views/converter.py", title="محوّل الإحداثيات", icon=":material/sync_alt:", url_path="converter"),
]
page = st.navigation(pages)

# أيقونات مخصصة اختيارية: ضعي في assets صوراً بهذه الأسماء (PNG شفاف مربع نحو 64 بكسل) فتحلّ محل الأيقونات الافتراضية
NAV_IMAGES = ["nav_home.png", "nav_extract.png", "nav_analyzer.png", "nav_converter.png"]
_nav_css = ""
for _i, _name in enumerate(NAV_IMAGES, start=1):
    _uri = png_data_uri(get_asset(_name))
    if _uri:
        _nav_css += (
            f'[data-testid="stSidebarNavItems"] li:nth-child({_i}) [data-testid="stIconMaterial"],'
            f'[data-testid="stSidebarNavItems"] li:nth-child({_i}) [data-testid="stIconEmoji"]'
            f'{{font-size:0 !important;color:transparent !important;width:26px;height:26px;display:inline-block;'
            f'background:url({_uri}) center/contain no-repeat;}}'
        )
if _nav_css:
    st.markdown(f"<style>{_nav_css}</style>", unsafe_allow_html=True)

if os.path.exists(logo_path):
    try:
        st.logo(logo_path, size="large")
    except Exception:
        pass

# بيانات الطلب: تُدخل مرة واحدة وتُستخدم في كل الأدوات عبر session_state
with st.sidebar:
    st.markdown(f"<h3 style='color:#162746; text-align:center; font-weight:700; margin-top:5px;'>{ms('assignment')} بيانات الطلب</h3>", unsafe_allow_html=True)
    st.text_input("اسم صاحب العلاقة", placeholder="أدخل الاسم الرباعي...", key="owner_name")
    st.text_input("الموقع الجغرافي / الولاية", placeholder="مثال: مسقط - السيب", key="location_name")
    st.text_area("ملاحظات إضافية للموقع", placeholder="أدخل أي ملاحظات تخطيطية...", height=80, key="notes")

page.run()
footer()
