"""الصفحة الرئيسية."""
import streamlit as st

from core.device import is_mobile
from ui.components import desktop_tile, hero_home, intro_box, mobile_tile, section_banner, section_title, stepper

hero_home("منصة GeoTools للأدوات الجغرافية", "المرجع العملي لدراسة وتحليل الأراضي الاستثمارية")

intro_box(
    "منظومة رقمية متكاملة لدعم وتحسين إجراءات تحليل ودراسة الأراضي الاستثمارية "
    "باستخدام أدوات وتقنيات نظم المعلومات الجغرافية والأتمتة الرقمية",
    "2022 – 2026",
)

section_banner("الأدوات الجغرافية", "GeoTools")

if is_mobile():
    mobile_tile("extract", "استخراج الإحداثيات من الصورة", "coordinates.png", "document_scanner", page="views/image_extractor.py")
    mobile_tile("analyzer", "المحلل الجغرافي الذكي", "smart.png", "travel_explore", page="views/analyzer.py")
    mobile_tile("converter", "محوّل الإحداثيات", "convert.png", "sync_alt", page="views/converter.py")
else:
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        desktop_tile("extract", "استخراج الإحداثيات من الصورة", "coordinates.png", "document_scanner",
                     "views/image_extractor.py", accent="#162746")
    with c2:
        desktop_tile("analyzer", "المحلل الجغرافي الذكي", "smart.png", "travel_explore", "views/analyzer.py")
    with c3:
        desktop_tile("converter", "محوّل الإحداثيات", "convert.png", "sync_alt", "views/converter.py", accent="#162746")

section_title("مسار العمل")
stepper([
    "إدخال بيانات الطلب" if is_mobile() else "إدخال بيانات الطلب من القائمة الجانبية",
    "اختيار الأداة المناسبة",
    "مراجعة النتائج على الجداول والخريطة",
    "تنزيل التقرير بصيغة Excel أو KML",
])
