"""تحويل ملف التقرير النهائي (Excel) إلى PDF مع الحفاظ على تنسيق الطباعة.

السلسلة: Microsoft Excel (الأدق، ويندوز فقط) ثم LibreOffice (بدون واجهة). وإن لم يتوفر أيٌّ منهما يُعطَّل الخيار.
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SOFFICE_CANDIDATES = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    "/usr/bin/soffice",
    "/usr/lib/libreoffice/program/soffice",
    "/opt/libreoffice*/program/soffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
]


def find_soffice():
    for name in ("soffice", "libreoffice"):
        p = shutil.which(name)
        if p:
            return p
    for pattern in SOFFICE_CANDIDATES:
        hits = sorted(glob.glob(pattern))
        if hits:
            return hits[-1]
    return None


def excel_com_available():
    if sys.platform != "win32":
        return False
    try:
        import win32com.client  # noqa: F401
        return True
    except ImportError:
        return False


def available_methods():
    methods = []
    if excel_com_available():
        methods.append("excel")
    if find_soffice():
        methods.append("libreoffice")
    return methods


def _via_excel(xlsx_path, pdf_path):
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    excel = None
    try:
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        wb = excel.Workbooks.Open(os.path.abspath(xlsx_path))
        wb.ExportAsFixedFormat(0, os.path.abspath(pdf_path))
        wb.Close(False)
    finally:
        if excel is not None:
            excel.Quit()
        pythoncom.CoUninitialize()


def _via_libreoffice(xlsx_path, out_dir, exe):
    profile = tempfile.mkdtemp(prefix="lo_profile_")
    try:
        subprocess.run([exe, f"-env:UserInstallation={Path(profile).as_uri()}", "--headless",
                        "--convert-to", "pdf", "--outdir", out_dir, xlsx_path],
                       capture_output=True, timeout=180)
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def convert(xlsx_bytes):
    """يعيد (bytes لملف PDF، اسم الطريقة المستخدمة) أو (None، سبب الفشل)."""
    methods = available_methods()
    if not methods:
        return None, "لا يتوفر Microsoft Excel ولا LibreOffice على هذا الجهاز."
    errors = []
    with tempfile.TemporaryDirectory() as tmp:
        xlsx_path = os.path.join(tmp, "report.xlsx")
        pdf_path = os.path.join(tmp, "report.pdf")
        with open(xlsx_path, "wb") as f:
            f.write(xlsx_bytes)
        for method in methods:
            try:
                if method == "excel":
                    _via_excel(xlsx_path, pdf_path)
                else:
                    _via_libreoffice(xlsx_path, tmp, find_soffice())
                if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                    with open(pdf_path, "rb") as f:
                        return f.read(), method
                errors.append(f"{method}: لم يُنتج ملف")
            except Exception as e:  # noqa: BLE001
                errors.append(f"{method}: {e}")
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
    return None, " | ".join(errors)
