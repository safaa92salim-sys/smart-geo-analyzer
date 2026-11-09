"""الوصول إلى ملفات assets (الشعار، soil.kml، قوالب Excel) — نفس منطق get_asset الأصلي مع بحث لا يفرّق بين الأحرف الكبيرة والصغيرة."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_asset(filename):
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = ROOT
    folder = os.path.join(base_path, "assets")
    path = os.path.join(folder, filename)
    if not os.path.exists(path) and os.path.isdir(folder):
        wanted = filename.lower()
        for name in os.listdir(folder):          # ويندوز لا يفرّق بين smart.png وSmart.PNG، أما لينكس (Streamlit Cloud) فيفرّق
            if name.lower() == wanted:
                return os.path.join(folder, name)
    return path
