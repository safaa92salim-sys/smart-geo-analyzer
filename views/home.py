"""الصفحة الرئيسية."""
import streamlit as st

from ui.components import hero_home, intro_box, section_banner, section_title, stepper, tool_tile

hero_home("منصة GeoTools للأدوات الجغرافية", "المرجع العملي لدراسة وتحليل الأراضي الاستثمارية")

intro_box(
    "منظومة رقمية متكاملة لدعم وتحسين إجراءات تحليل ودراسة الأراضي الاستثمارية "
    "باستخدام أدوات وتقنيات نظم المعلومات الجغرافية والأتمتة الرقمية",
    "2022 – 2026",
)

section_banner("الأدوات الجغرافية", "GeoTools")
c1, c2, c3 = st.columns(3, gap="medium")

with c1:
    tool_tile("coordinates.png", "استخراج الإحداثيات من الصورة", icon="document_scanner", accent="#162746")
    st.page_link("views/image_extractor.py", label="فتح الأداة")
with c2:
    tool_tile("smart.png", "المحلل الجغرافي الذكي", icon="travel_explore")
    st.page_link("views/analyzer.py", label="فتح الأداة")
with c3:
    tool_tile("convert.png", "محوّل الإحداثيات", icon="sync_alt", accent="#162746")
    st.page_link("views/converter.py", label="فتح الأداة")

section_title("مسار العمل")
stepper([
    "إدخال بيانات الطلب من القائمة الجانبية",
    "اختيار الأداة المناسبة",
    "مراجعة النتائج على الجداول والخريطة",
    "تنزيل التقرير بصيغة Excel أو KML",
])
