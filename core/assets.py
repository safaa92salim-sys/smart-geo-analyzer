"""الوصول إلى ملفات assets (الشعار، soil.kml، قوالب Excel) — نفس منطق get_asset الأصلي."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_asset(filename):
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = ROOT
    return os.path.join(base_path, "assets", filename)
