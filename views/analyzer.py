"""صفحة المحلل الجغرافي الذكي.

منطق التحليل والجداول والتصدير أدناه منقول من app.py الأصلي دون تغيير في سلوكه.
التعديلات الوحيدة: قراءة soil.kml مع تخزين مؤقت، حذف ملف KML المؤقت داخل finally،
وإزالة وسوم <div> المفتوحة/المغلقة بشكل منفصل (حلّ محلها تنسيق التبويبات في الثيم).
"""
import io
import os
import tempfile
from datetime import datetime

import folium
import geopandas as gpd
import openpyxl
import pandas as pd
import streamlit as st
from pyproj import Transformer
from streamlit_folium import st_folium

from core.assets import get_asset
from core.device import is_mobile
from ui.components import hero, notice, references_box, step_nav, tab_icons

utm_wgs84 = Transformer.from_crs("EPSG:4326", "EPSG:32640", always_xy=True)


@st.cache_data(show_spinner=False)
def load_soil_map(path):
    return gpd.read_file(path, engine="pyogrio")


def _polygon_from_any_geometry(path):
    """بديل عند عدم قراءة مضلع بالطريقة المعتادة: يُقرأ الملف بقارئ KML الداخلي (نفس قارئ محوّل الإحداثيات)،
    فتؤخذ المضلعات إن وُجدت، وإلا تُبنى الحدود من مسار أو من نقاط الدبابيس وتُغلق تلقائياً."""
    from shapely.geometry import Polygon

    from core import kml_io
    with open(path, "rb") as f:
        feats = kml_io.parse_kml(f.read())
    polys = [p for p in feats if p["type"] == "polygon" and len(p["coords"]) >= 3]
    if polys:
        geoms = []
        for p in polys:
            g = Polygon(p["coords"])
            geoms.append(g if g.is_valid else g.buffer(0))
        gdf = gpd.GeoDataFrame({"Name": [p["name"] for p in polys]}, geometry=geoms, crs="EPSG:4326")
        return gdf, "polygon", sum(len(p["coords"]) for p in polys)
    poly = kml_io.to_polygon(feats)
    if poly is None:
        return None
    g = Polygon(poly["coords"])
    g = g if g.is_valid else g.buffer(0)
    return gpd.GeoDataFrame({"Name": [poly["name"]]}, geometry=[g], crs="EPSG:4326"), poly["source"], len(poly["coords"])


def load_land_polygons(path):
    """يقرأ ملف الأرض كمضلع. الملفات المعتادة تمر كما كانت (المضلعات فقط، دون النقاط والخطوط الإضافية).
    وإن رُسمت الحدود كمسار أو كنقاط دبوس فتُبنى منها حدود الأرض وتُغلق تلقائياً."""
    import pyogrio
    gdf = None
    try:
        frames = []
        for row in pyogrio.list_layers(path):
            try:
                g = gpd.read_file(path, layer=str(row[0]), engine="pyogrio")
            except Exception:
                continue
            if not g.empty:
                frames.append(g)
        if frames:
            gdf = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
            is_gc = gdf.geometry.geom_type == "GeometryCollection"   # MultiGeometry: مضلع + نقاط/خطوط في عنصر واحد
            if is_gc.any():
                gdf = pd.concat([gdf[~is_gc], gdf[is_gc].explode(index_parts=False, ignore_index=True)], ignore_index=True)
            gdf = gdf[gdf.geometry.notna() & gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
            gdf = gdf[~gdf.geometry.apply(lambda g: g.wkb).duplicated()].reset_index(drop=True)
            if not gdf.empty:
                return gpd.GeoDataFrame(gdf, geometry="geometry", crs=frames[0].crs)
    except Exception:
        gdf = None
    built = _polygon_from_any_geometry(path)
    if built is None:
        raise ValueError("لم يُعثر في الملف على مضلع ولا على مسار أو نقاط كافية (3 نقاط على الأقل) لبناء حدود الأرض.")
    gdf, source, n = built
    if source != "polygon":
        st.info(f"لا يحتوي الملف على مضلع، فتم بناء حدود الأرض من {'المسار' if source == 'line' else 'النقاط'} "
                f"({n} نقطة) وإغلاقها تلقائياً.")
    return gdf


class _HandoffFile:
    """ملف مُمرَّر من أداة استخراج الصور بدل الرفع اليدوي."""
    def __init__(self, name, data):
        self.name, self._data, self.size = name, data, len(data)

    def getvalue(self):
        return self._data


# بيانات الطلب تُدخل مرة واحدة من الشريط الجانبي المشترك (app.py)
owner_name = st.session_state.get("owner_name", "")
location_name = st.session_state.get("location_name", "")
notes = st.session_state.get("notes", "")

hero(
    "المحلل الجغرافي الذكي لدراسة خصائص التربة ومجال الاستثمار",
    "تحليل تلقائي لموقع الأرض: خصائص التربة ومجال الاستثمار والمساحة والإحداثيات في تقرير جاهز",
)

mobile = is_mobile()


def _sync(wkey, key):
    st.session_state[key] = st.session_state.get(wkey, "")


# الكمبيوتر: الشريط الجانبي. الهاتف: لا شريط جانبي، فتُعرض بيانات الطلب ورفع الملف داخل الصفحة
_box = (st.expander("بيانات الطلب ورفع ملف الأرض", expanded=st.session_state.get("an_sig") is None)
        if mobile else st.sidebar)
with _box:
    if mobile:
        st.text_input("اسم صاحب العلاقة", value=st.session_state.get("owner_name", ""), placeholder="أدخل الاسم الرباعي...",
                      key="m_owner", on_change=_sync, args=("m_owner", "owner_name"))
        st.text_input("الموقع الجغرافي / الولاية", value=st.session_state.get("location_name", ""), placeholder="مثال: مسقط - السيب",
                      key="m_location", on_change=_sync, args=("m_location", "location_name"))
        st.text_area("ملاحظات إضافية للموقع", value=st.session_state.get("notes", ""), placeholder="أدخل أي ملاحظات تخطيطية...",
                     height=80, key="m_notes", on_change=_sync, args=("m_notes", "notes"))
    st.markdown("<h4 style='color:#162746; margin-top:12px; font-weight:700;'><span class='ic ic-upload'></span> رفع ملف الأرض</h4>", unsafe_allow_html=True)
    uploaded_kml = st.file_uploader("اختر ملف الأرض (KML)", type=["kml"])
    _handoff = st.session_state.get("handoff_kml")
    if uploaded_kml is None and _handoff:
        uploaded_kml = _HandoffFile(*_handoff)
        st.info("الأرض المستخرجة من الصورة جاهزة للتحليل.")
        st.button("إلغاء الأرض المستخرجة", on_click=lambda: st.session_state.pop("handoff_kml", None))

STAGES = ["رفع ملف الأرض (KML)", "التحليل والنتائج", "تصدير التقرير"]

# عند رفع ملف جديد ينتقل المستخدم تلقائياً إلى مرحلة التحليل
_sig = (uploaded_kml.name, uploaded_kml.size) if uploaded_kml is not None else None
if st.session_state.get("an_sig") != _sig:
    st.session_state["an_sig"] = _sig
    st.session_state["an_stage"] = STAGES[1] if _sig else STAGES[0]
stage = step_nav(STAGES, key="an_stage")


def render_summary_boxes():
    cols = st.columns(4)
    items = [
        ("صاحب العلاقة", owner_name if owner_name else "غير محدد", "font-size:14px;"),
        ("الموقع الجغرافي / الولاية", location_name if location_name else "غير محدد", "font-size:14px;"),
        ("المساحة الإجمالية (متر مربع)", f"{total_area_sqm:,.2f} م²", ""),
        ("المساحة الإجمالية (بالفدان)", f"{total_area_feddan:,.2f} فدان", ""),
    ]
    for col, (title, value, style) in zip(cols, items):
        with col:
            st.markdown(f"""
            <div class='metric-box'>
                <div class='metric-title'>{title}</div>
                <div class='metric-value' style='{style}'>{value}</div>
            </div>
            """, unsafe_allow_html=True)


if uploaded_kml is None or stage == STAGES[0]:
    if uploaded_kml is None:
        notice("يرجى رفع ملف الأرض (KML) وتعبئة <b>بيانات الطلب</b> " + ("في القسم أعلاه" if mobile else "من القائمة الجانبية")
               + " لبدء المعالجة الجغرافية واستعراض نتائج التحليل.", large=True)
    else:
        notice(f"تم رفع الملف <b>{uploaded_kml.name}</b>. انتقل إلى مرحلة التحليل لعرض النتائج.")
        st.button("متابعة إلى التحليل والنتائج", on_click=lambda: st.session_state.update(an_stage=STAGES[1]))
else:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".kml") as tmp_file:
        tmp_file.write(uploaded_kml.getvalue())
        temp_kml_path = tmp_file.name

    try:
        soil_kml_path = get_asset("soil.kml")
        soil_map = load_soil_map(soil_kml_path)
        land_site = load_land_polygons(temp_kml_path)
        # توحيد أعمدة الأرض مع أعمدة soil.kml: يضمن أن يُعاد تسمية الأعمدة المتشابهة بعد التقاطع
        # (description_1 / description_2) كما في الملفات المعتادة، فلا يظهر وصف التربة فارغاً
        for _col in soil_map.columns:
            if _col != soil_map.geometry.name and _col not in land_site.columns:
                land_site[_col] = None
        
        land_site_metric = land_site.to_crs(epsg=32640)
        total_area_sqm = land_site_metric.geometry.area.iloc[0]
        total_area_feddan = total_area_sqm / 4200.833

        intersected = gpd.overlay(land_site, soil_map, how='intersection')

        original_geom = land_site.geometry.iloc[0]
        if original_geom.geom_type == 'Polygon':
            original_points = list(original_geom.exterior.coords)
        elif original_geom.geom_type == 'MultiPolygon':
            original_points = list(original_geom.geoms[0].exterior.coords)
        else:
            original_points = []

        if stage == STAGES[1]:
            tab_icons(["map", "bar-chart-2"])
            tab_map, tab_report = st.tabs(["العرض الجغرافي", "نتائج التحليل"])

            with tab_map:
                st.subheader("اسقاط موقع الأرض على الخريطة")
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

            with tab_report:
                st.markdown("<h4 style='color:#162746; font-weight:700; margin-bottom:12px;'><span class='ic ic-list'></span> البيانات الأساسية للموقع الاستثماري</h4>", unsafe_allow_html=True)
            
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

                st.markdown("<h4 style='color:#162746; font-weight:700; margin-bottom:10px;'><span class='ic ic-layers'></span> ملخص تحليل خصائص التربة ومجال الاستثمار للموقع</h4>", unsafe_allow_html=True)
            
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
                        if not desc_lines:
                            st.warning(f"لم تُقرأ خصائص التربة للنطاق {idx + 1} من ملف soil.kml.")

                        zone_header = f"<span class='ic ic-map-pin'></span> النطاق الجغرافي {idx + 1} — نسبة التغطية من الأرض: {formatted_percent}"
                    
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
                    st.warning("الموقع يقع خارج نطاق خريطة التربة المعتمدة.")

                st.divider()

                st.markdown("<h4 style='color:#162746; font-weight:700; margin-bottom:10px;'><span class='ic ic-map-pin'></span> احداثيات الموقع الاستثماري</h4>", unsafe_allow_html=True)


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

        else:
            render_summary_boxes()
            st.write("")
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

                st.success("تم إعداد التقرير بنجاح، وهو جاهز للتحميل عند الطلب.")

                st.download_button(
                    label="تحميل التقرير النهائي (Excel)",
                    icon=":material/download:",
                    data=excel_buffer,
                    file_name=output_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("لم يتم العثور على قالب الأكسل في مجلد assets!")

    except Exception as e:
        st.error(f"حدث خطأ أثناء المعالجة: {str(e)}")
    finally:
        try:
            os.remove(temp_kml_path)
        except OSError:
            pass


references_box()
