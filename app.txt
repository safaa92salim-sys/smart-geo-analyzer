import streamlit as st
import geopandas as gpd
import openpyxl
import os
import sys
import tempfile
import pandas as pd
import io
from datetime import datetime
from pyproj import Transformer
import folium
from streamlit_folium import st_folium
from PIL import Image

# --- 1. إدارة المسارات والوصول للملفات المرفقة (assets) ---
def get_asset(filename):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "assets", filename)

logo_path = get_asset("logo.png")
icon_path = get_asset("icon.png")

try:
    page_icon_img = Image.open(icon_path) if os.path.exists(icon_path) else (Image.open(logo_path) if os.path.exists(logo_path) else "🌍")
except:
    page_icon_img = "🌍"

# --- 2. إعدادات الصفحة المتقدمة ---
st.set_page_config(
    page_title="المحلل الجغرافي الذكي",
    page_icon=page_icon_img,
    layout="wide",
    initial_sidebar_state="expanded"
)

utm_wgs84 = Transformer.from_crs("EPSG:4326", "EPSG:32640", always_xy=True)

# --- 3. تحسينات CSS والتنسيقات البصرية وإخفاء زر طي القائمة الجانبية ---
st.markdown("""
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
""", unsafe_allow_html=True)

# --- 4. القائمة الجانبية (يمين) مع تصغير اللوجو ---
with st.sidebar:
    if os.path.exists(logo_path):
        col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
        with col_l2:
            st.image(logo_path, use_container_width=True)

    st.markdown("<h3 style='color:#162746; text-align:center; font-weight:700; margin-top:5px;'>📌 بيانات الطلب</h3>", unsafe_allow_html=True)

    owner_name = st.text_input("اسم صاحب العلاقة", placeholder="أدخل الاسم الرباعي...")
    location_name = st.text_input("الموقع الجغرافي / الولاية", placeholder="مثال: مسقط - السيب")
    notes = st.text_area("ملاحظات إضافية للموقع", placeholder="أدخل أي ملاحظات تخطيطية...", height=80)

    st.markdown("<h4 style='color:#162746; margin-top:12px; font-weight:700;'>📂 رفع ملف الأرض</h4>", unsafe_allow_html=True)
    uploaded_kml = st.file_uploader("اختر ملف الأرض (KML)", type=["kml"])

# --- 5. الهيدر الرئيسي ---
st.markdown("""
<div class='hero-container'>
    <div class='hero-title'>المحلل الجغرافي الذكي لدراسة خصائص التربة ومجال الاستثمار</div>
    <div class='hero-subtitle'>المرجع العملي لتحويل الاحداثيات الجغرافية</div>
</div>
""", unsafe_allow_html=True)

# --- 6. معالجة البيانات واستعراض التبويبات ---
if uploaded_kml is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".kml") as tmp_file:
        tmp_file.write(uploaded_kml.getvalue())
        temp_kml_path = tmp_file.name

    try:
        soil_kml_path = get_asset("soil.kml")
        soil_map = gpd.read_file(soil_kml_path, engine="pyogrio")
        land_site = gpd.read_file(temp_kml_path, engine="pyogrio")
        
        land_site_metric = land_site.to_crs(epsg=32640)
        total_area_sqm = land_site_metric.geometry.area.iloc[0]
        total_area_feddan = total_area_sqm / 4200.833

        intersected = gpd.overlay(land_site, soil_map, how='intersection')

        tab_map, tab_report, tab_export = st.tabs(["🗺️ العرض الجغرافي التفاعلي", "📊 نتائج التحليل", "📥 تصدير التقرير النهائي"])

        with tab_map:
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            st.subheader("إسقاط موقع الأرض على الخريطة التفاعلية")
            bounds = land_site.total_bounds
            center_lat = (bounds[1] + bounds[3]) / 2
            center_lon = (bounds[0] + bounds[2]) / 2

            m = folium.Map(location=[center_lat, center_lon], zoom_start=15, tiles="OpenStreetMap")
            
            folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attr='Esri',
                name='صورة قمر صناعي',
                overlay=False,
                control=True
            ).add_to(m)

            folium.GeoJson(
                land_site,
                name="مضلع الأرض",
                style_function=lambda x: {'fillColor': '#790420', 'color': '#790420', 'weight': 3, 'fillOpacity': 0.4}
            ).add_to(m)

            folium.LayerControl().add_to(m)
            st_folium(m, width="100%", height=460)
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_report:
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color:#162746; font-weight:700; margin-bottom:12px;'>📋 البيانات الأساسية للموقع الاستثماري</h4>", unsafe_allow_html=True)
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.markdown(f"""
                <div class='metric-box'>
                    <div class='metric-title'>صاحب العلاقة</div>
                    <div class='metric-value' style='font-size:14px;'>{owner_name if owner_name else 'غير محدد'}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_m2:
                st.markdown(f"""
                <div class='metric-box'>
                    <div class='metric-title'>الموقع الجغرافي / الولاية</div>
                    <div class='metric-value' style='font-size:14px;'>{location_name if location_name else 'غير محدد'}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_m3:
                st.markdown(f"""
                <div class='metric-box'>
                    <div class='metric-title'>المساحة الإجمالية (متر مربع)</div>
                    <div class='metric-value'>{total_area_sqm:,.2f} م²</div>
                </div>
                """, unsafe_allow_html=True)
            with col_m4:
                st.markdown(f"""
                <div class='metric-box'>
                    <div class='metric-title'>المساحة الإجمالية (بالفدان)</div>
                    <div class='metric-value'>{total_area_feddan:,.2f} فدان</div>
                </div>
                """, unsafe_allow_html=True)

            st.divider()

            st.markdown("<h4 style='color:#162746; font-weight:700; margin-bottom:10px;'>🌱 ملخص تحليل خصائص التربة ومجال الاستثمار للموقع</h4>", unsafe_allow_html=True)
            
            if not intersected.empty:
                intersected_metric = intersected.to_crs(epsg=32640)
                
                field_labels = [
                    "نوع النطاق",
                    "نوع الاستعمال",
                    "وصف نوع الاستعمال",
                    "تصنيف التربة",
                    "وصف تصنيف التربة",
                    "صلاحية التربة",
                    "درجة صلاحية التربة",
                    "المعوقات القابلة للاصلاح",
                    "أساليب الاصلاح المقترحة",
                    "المعوقات الدائمة"
                ]

                for idx, row in intersected_metric.iterrows():
                    percentage = (row.geometry.area / total_area_sqm) * 100
                    formatted_percent = f"{percentage:.1f}%"
                    description = str(row.get('Description', row.get('description_2', '')))
                    desc_lines = [line.strip() for line in description.split('\n') if line.strip()]

                    zone_header = f"📌 النطاق الجغرافي {idx + 1} — نسبة التغطية من الأرض: {formatted_percent}"
                    
                    rows_html = ""
                    if desc_lines:
                        for i_line, line_text in enumerate(desc_lines[:10]):
                            label_title = field_labels[i_line] if i_line < len(field_labels) else f"خاصية إضافية ({i_line + 1})"
                            rows_html += f"<tr><td style='font-weight:700; color:#162746;'>{label_title}</td><td>{line_text}</td></tr>"
                    
                    full_soil_table = f"""
                    <div style='background-color:#F8FAFC; border-right: 4px solid #790420; border-radius: 8px; padding: 12px; margin-bottom: 12px;'>
                        <h5 style='color:#790420; margin:0 0 8px 0; font-weight:700;'>{zone_header}</h5>
                        <table class='custom-table'>
                            <thead>
                                <tr>
                                    <th style='width:30%;'>توصيف العنصر</th>
                                    <th>تفاصيل الخصائص ومجال الاستثمار</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rows_html}
                            </tbody>
                        </table>
                    </div>
                    """
                    st.html(full_soil_table)
            else:
                st.warning("⚠️ الموقع يقع خارج نطاق خريطة التربة المعتمدة.")

            st.divider()

            st.markdown("<h4 style='color:#162746; font-weight:700; margin-bottom:10px;'>📍 احداثيات الموقع الاستثماري</h4>", unsafe_allow_html=True)

            original_geom = land_site.geometry.iloc[0]
            if original_geom.geom_type == 'Polygon':
                original_points = list(original_geom.exterior.coords)
            elif original_geom.geom_type == 'MultiPolygon':
                original_points = list(original_geom.geoms[0].exterior.coords)
            else:
                original_points = []

            coord_rows_html = ""
            for i, pt in enumerate(original_points[:-1]):
                lon_dec, lat_dec = pt[0], pt[1]
                utm_e, utm_n = utm_wgs84.transform(lon_dec, lat_dec)
                
                clarke_adj_e = utm_e - (382.1899238 * 0.757628555)
                clarke_adj_n = utm_n - (382.1899238 * 0.652685967)

                coord_rows_html += f"""
                    <tr>
                        <td style='font-weight:700; color:#162746;'>P{i + 1}</td>
                        <td>{lon_dec:.6f}</td>
                        <td>{lat_dec:.6f}</td>
                        <td>{utm_e:.2f}</td>
                        <td>{utm_n:.2f}</td>
                        <td>{clarke_adj_e:.2f}</td>
                        <td>{clarke_adj_n:.2f}</td>
                    </tr>
                """

            full_coord_table = f"""
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
                <tbody>
                    {coord_rows_html}
                </tbody>
            </table>
            """
            st.html(full_coord_table)
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_export:
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            st.subheader("إصدار وتصنيع التقرير النهائي")
            num_zones = len(intersected) if not intersected.empty else 0
            template_name = "soil_report_multi.xlsx" if num_zones > 1 else "Soil_Report.xlsx"
            template_path = get_asset(template_name)

            if os.path.exists(template_path):
                wb = openpyxl.load_workbook(template_path)
                ws = wb.active
                
                ws['B11'] = owner_name if owner_name else ""
                ws['B12'] = location_name if location_name else ""
                ws['B14'] = notes if notes else ""
                ws['B13'] = datetime.now().strftime("%Y-%m-%d")

                if num_zones > 1:
                    intersected_metric = intersected.to_crs(epsg=32640)
                    for idx, row in intersected_metric.iterrows():
                        if idx > 1: break 
                        
                        percentage = (row.geometry.area / total_area_sqm) * 100
                        formatted_percent = f"{percentage:.1f}%"
                        
                        description = str(row.get('Description', row.get('description_2', '')))
                        desc_lines = [line.strip() for line in description.split('\n') if line.strip()]
                        
                        if idx == 0:
                            ws["H20"] = formatted_percent
                            ws["E46"] = formatted_percent
                            f_cell, d_cell, b_cell = "F20", "D20", "B20"
                            full_desc_start_row = 47
                        else:
                            ws["H21"] = formatted_percent
                            ws["E58"] = formatted_percent
                            f_cell, d_cell, b_cell = "F21", "D21", "B21"
                            full_desc_start_row = 59

                        if len(desc_lines) >= 1: ws[f_cell] = desc_lines[0]
                        if len(desc_lines) >= 4: ws[d_cell] = desc_lines[3]
                        if len(desc_lines) >= 2: ws[b_cell] = desc_lines[1]
                        for line_idx, line in enumerate(desc_lines):
                            ws.cell(row=full_desc_start_row + line_idx, column=2, value=line)
                else:
                    if not intersected.empty:
                        target_row = intersected.iloc[0]
                        description = str(target_row.get('Description', target_row.get('description_2', '')))
                        desc_lines = description.split('\n')
                        for i, line in enumerate(desc_lines[:10]):
                            ws.cell(row=18 + i, column=2, value=line.strip())

                for i, pt in enumerate(original_points[:-1]):
                    lon, lat = pt[0], pt[1]
                    ws.cell(row=13 + i, column=13, value=round(lon, 6))
                    ws.cell(row=13 + i, column=14, value=round(lat, 6))
                    utm_e, utm_n = utm_wgs84.transform(lon, lat)
                    ws.cell(row=13 + i, column=15, value=round(utm_e, 3))
                    ws.cell(row=13 + i, column=16, value=round(utm_n, 3))
                    ws.cell(row=13 + i, column=17, value=round(utm_e - (382.1899238 * 0.757628555), 3))
                    ws.cell(row=13 + i, column=18, value=round(utm_n - (382.1899238 * 0.652685967), 3))

                excel_buffer = io.BytesIO()
                wb.save(excel_buffer)
                excel_buffer.seek(0)

                output_filename = f"Geo_Report_{datetime.now().strftime('%d%m_%H%M')}.xlsx"

                st.success("✅ تم إعداد التقرير بنجاح، وهو جاهز للتحميل عند الطلب.")

                st.download_button(
                    label="🚀 تحميل التقرير النهائي (Excel)",
                    data=excel_buffer,
                    file_name=output_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("⚠️ لم يتم العثور على قالب الأكسل في مجلد assets!")
            st.markdown("</div>", unsafe_allow_html=True)

        os.remove(temp_kml_path)

    except Exception as e:
        st.error(f"حدث خطأ أثناء المعالجة: {str(e)}")

else:
    st.markdown("""
    <div style='text-align: center; padding: 50px 20px; background-color: #FFFFFF; border-radius: 16px; border: 1px dashed #CBD5E1; margin-top: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.02);'>
        <h3 style='color: #162746; font-weight:700;'>👋 أهلاً بكِ في المحلل الجغرافي الذكي</h3>
        <p style='color: #64748B; font-size:15px;'>يرجى رفع ملف الأرض (KML) وتعبئة <b>بيانات الطلب</b> من القائمة الجانبية لبدء المعالجة الجغرافية واستعراض نتائج التحليل.</p>
    </div>
    """, unsafe_allow_html=True)

# --- 7. قسم مصادر البيانات والمراجع والتنبيه المنهجي (قبل التوقيع مباشرة) ---
st.markdown("""
<div class='references-box'>
    <div class='references-title'>📚 مصادر البيانات والمراجع:</div>
    <div class='references-text'>
        <b>1-</b> الخارطة الاستثمارية الرسمية (صيغة KML) الصادرة عن الجهات المختصة، والتي تتضمن بيانات النطاقات الاستثمارية وخصائص التربة ومجالات الاستثمار المعتمدة لكل نطاق.<br>
        <b>2-</b> أطلس عُمان للتربة (Soil Atlas of Oman)، باعتباره المرجع الوطني المعتمد لتصنيف خصائص التربة، الطبعة الأولى (1411هـ / 1990م)، الصادر عن وزارة الزراعة والأسماك بسلطنة عُمان، وقد تم إعداد الأطلس بالتعاون مع منظمة الأغذية والزراعة للأمم المتحدة (FAO).
    </div>
    <div class='notice-box'>
        <b>💡 ملاحظة منهجية هامة:</b> تم استخدام هذه المصادر لأغراض التحليل الأولي وتقييم الملاءمة المبدئية فقط، ولا تُغني النتائج الواردة عن إجراء الدراسات الحقلية التفصيلية والفحوصات الموقعية اللازمة عند مرحلة التنفيذ الفعلي للمشروعات.
    </div>
</div>
""", unsafe_allow_html=True)

# --- 8. التوقيع والحق الفكري في أسفل الصفحة ---
st.markdown("""
<div class='footer-text'>
    GeoTools © 2026 - Created by Eng. Safaa Al Harrasi<br>
    <a href='https://geo-tools.mystrikingly.com' target='_blank'>geo-tools.mystrikingly.com</a> | Geo.C.Tools@gmail.com
</div>
""", unsafe_allow_html=True)