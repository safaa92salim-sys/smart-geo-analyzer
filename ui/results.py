"""منطقة النتائج المشتركة: إحصاءات + مساحة + جدول الصيغ الثلاث + الخريطة + إجراءات التنزيل."""
from datetime import datetime

import streamlit as st
from streamlit_folium import st_folium

from core import export, formats, geometry, kml_io, map_view, report_pdf
from ui.components import ms, section_title


def collect_points(features):
    multi = len(features) > 1
    points = []
    for f in features:
        for label, (lon, lat) in zip(kml_io.labels_for(f), f["coords"]):
            if multi and f["type"] != "point":
                label = f"{f['name']} / {label}"
            points.append((label, lon, lat))
    return points


def land_features(features):
    """مضلعات الأرض من العناصر، أو مضلع مبني من مسار/نقاط (3 نقاط على الأقل)، وإلا قائمة فارغة."""
    polys = [f for f in features if f["type"] == "polygon" and len(f["coords"]) >= 3]
    if polys:
        return polys
    poly = kml_io.to_polygon(features)
    return [poly] if poly else []


def _analyze_button(features, key):
    land = land_features(features)
    if st.button("تحليل الأرض في المحلل الجغرافي الذكي", icon=":material/travel_explore:", key=f"{key}_analyze",
                 disabled=not land, help=None if land else "يلزم 3 نقاط على الأقل لبناء حدود الأرض"):
        st.session_state["handoff_kml"] = ("الأرض.kml", kml_io.build_kml(land, "الأرض"))
        st.switch_page("views/analyzer.py")


def _pdf_button(title, rows, zone, areas, key):
    request = {"owner": st.session_state.get("owner_name", ""), "location": st.session_state.get("location_name", ""),
               "notes": st.session_state.get("notes", "")}
    data, why = None, "يتطلب تثبيت reportlab وarabic-reshaper وpython-bidi"
    if report_pdf.available():
        try:
            data = report_pdf.build_report(title, request, rows, zone, areas)
        except Exception as e:  # noqa: BLE001
            why = str(e)
    if data is None:
        st.button("تنزيل تقرير PDF", disabled=True, help=why, key=f"{key}_pdf_off")
        return
    st.download_button("تنزيل تقرير PDF", data, icon=":material/picture_as_pdf:",
                       file_name=f"Report_{datetime.now().strftime('%d%m_%H%M')}.pdf", mime="application/pdf", key=f"{key}_pdf")


def render_results(features, zone, key, stats=True, table=True, kml_button=True, excel_button=True,
                   actions=None, actions_title="إجراءات المستخدم", pdf=True, analyze=True,
                   pdf_title="تقرير تحويل الإحداثيات"):
    """stats: صناديق (عدد النقاط، النطاق، نوع العنصر). table: جدول الإحداثيات بالصيغ الثلاث.
    actions: دالة اختيارية تُرسم أزراراً إضافية بجانب أزرار التنزيل (تستلم قائمة الأعمدة)."""
    points = collect_points(features)
    if not points:
        st.info("لا توجد نقاط لعرضها.")
        return
    rows = formats.build_rows(points, zone)
    kinds = {kml_io.TYPE_AR[f["type"]] for f in features}

    if stats:
        c1, c2, c3 = st.columns(3)
        for col, title, value in ((c1, "عدد النقاط", f"{len(points)}"),
                                  (c2, "نطاق UTM", zone),
                                  (c3, "نوع العنصر", " / ".join(sorted(kinds)))):
            col.markdown(f"<div class='metric-box'><div class='metric-title'>{title}</div>"
                         f"<div class='metric-value'>{value}</div></div>", unsafe_allow_html=True)

    # مساحة المضلعات (م² وفدان) بنفس طريقة المحلل الجغرافي
    polys = [f for f in features if f["type"] == "polygon" and len(f["coords"]) >= 3]
    areas = [(f["name"], geometry.area_info(f["coords"], zone)) for f in polys]
    if areas:
        section_title(f"{ms('maximize')} مساحة القطعة")
        if len(areas) == 1:
            _, info = areas[0]
            a1, a2 = st.columns(2)
            for col, title, value in ((a1, "المساحة (متر مربع)", f"{info['m2']:,.2f} م²"),
                                      (a2, "المساحة (بالفدان)", f"{info['feddan']:,.2f} فدان")):
                col.markdown(f"<div class='metric-box'><div class='metric-title'>{title}</div>"
                             f"<div class='metric-value'>{value}</div></div>", unsafe_allow_html=True)
        else:
            body = "".join(f"<tr><td style='font-weight:700; color:#162746;'>{n}</td>"
                           f"<td>{a['m2']:,.2f}</td><td>{a['feddan']:,.2f}</td></tr>" for n, a in areas)
            tot_m2 = sum(a["m2"] for _, a in areas)
            body += (f"<tr><td style='font-weight:700; color:#790420;'>الإجمالي</td>"
                     f"<td style='font-weight:700;'>{tot_m2:,.2f}</td>"
                     f"<td style='font-weight:700;'>{tot_m2 / geometry.FEDDAN_M2:,.2f}</td></tr>")
            st.html("<table class='coord-table'><thead><tr><th>المضلع</th><th>المساحة (م²)</th>"
                    f"<th>المساحة (فدان)</th></tr></thead><tbody>{body}</tbody></table>")
        if any(not a["valid"] for _, a in areas):
            st.warning("المضلع يتقاطع مع نفسه (ترتيب النقاط غير صحيح)، وقد تكون المساحة غير دقيقة. راجع ترتيب النقاط.")

    if table:
        section_title(f"{ms('map-pin')} احداثيات النقاط")
        st.html(formats.coord_table_html(rows))
        st.caption(f"نطاق UTM المستخدم: {zone} — إزاحة كلارك 1880 المعتمدة في المحلل الجغرافي الذكي.")

    section_title(f"{ms('map')} العرض على الخريطة التفاعلية")
    st_folium(map_view.build_map(features), width="100%", height=440,
              returned_objects=[], key=f"{key}_map")

    buttons = []
    stamp = datetime.now().strftime("%d%m_%H%M")
    if kml_button:
        buttons.append(lambda: st.download_button(
            "تنزيل الموقع بصيغة KML", kml_io.build_kml(features), icon=":material/download:",
            file_name=f"GeoTools_{stamp}.kml", mime="application/vnd.google-earth.kml+xml", key=f"{key}_kml"))
    if excel_button:
        buttons.append(lambda: st.download_button(
            "تنزيل الاحداثيات بصيغة EXCEL", export.rows_to_excel(rows, zone, areas), icon=":material/table_view:",
            file_name=f"Coordinates_{stamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"{key}_xlsx"))
    if pdf:
        buttons.append(lambda: _pdf_button(pdf_title, rows, zone, areas, key))
    if actions is not None:
        buttons.append(actions)
    elif analyze:
        buttons.append(lambda: _analyze_button(features, key))
    if buttons:
        section_title(f"{ms('download')} {actions_title}")
        for col, draw in zip(st.columns(len(buttons)), buttons):
            with col:
                draw()
