"""الخريطة التفاعلية (نفس الطبقتين المستخدمتين في المحلل الجغرافي: OpenStreetMap + قمر صناعي Esri)."""
import folium

from .kml_io import labels_for

BURGUNDY, NAVY = "#790420", "#162746"
ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"


def build_map(features):
    coords = [c for f in features for c in f["coords"]]
    lats, lons = [c[1] for c in coords], [c[0] for c in coords]
    center = [(min(lats) + max(lats)) / 2, (min(lons) + max(lons)) / 2]
    m = folium.Map(location=center, zoom_start=16, tiles="OpenStreetMap")
    folium.TileLayer(tiles=ESRI, attr="Esri", name="صورة قمر صناعي", overlay=False, control=True).add_to(m)

    show_labels = len(coords) <= 12
    for f in features:
        latlon = [(lat, lon) for lon, lat in f["coords"]]
        if f["type"] == "polygon" and len(latlon) >= 3:
            folium.Polygon(latlon, color=BURGUNDY, weight=3, fill=True,
                           fill_color=BURGUNDY, fill_opacity=0.4).add_to(m)
        elif f["type"] in ("line", "polygon") and len(latlon) >= 2:
            folium.PolyLine(latlon, color=BURGUNDY, weight=3).add_to(m)
        if len(latlon) <= 200:
            for label, (lat, lon) in zip(labels_for(f), latlon):
                folium.CircleMarker((lat, lon), radius=5, color=NAVY, weight=2, fill=True,
                                    fill_color="#FFFFFF", fill_opacity=1,
                                    tooltip=folium.Tooltip(label, permanent=show_labels)).add_to(m)
    if len(coords) > 1:
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]], padding=(30, 30))
    folium.LayerControl().add_to(m)
    return m
