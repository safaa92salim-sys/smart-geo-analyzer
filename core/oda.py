"""قراءة ملفات DWG عبر ODA File Converter (برنامج مجاني بتسجيل، يُثبَّت على الجهاز).

لا يعمل على الاستضافة السحابية (Streamlit Cloud) لأن البرنامج لا يُثبَّت عبر apt؛ هناك يُرفع DXF بدلاً من DWG.
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile

CANDIDATES = [
    r"C:\Program Files\ODA\*\ODAFileConverter.exe",
    r"C:\Program Files (x86)\ODA\*\ODAFileConverter.exe",
    r"C:\Program Files\ODA\ODAFileConverter\ODAFileConverter.exe",
    "/usr/bin/ODAFileConverter",
    "/opt/ODAFileConverter*/ODAFileConverter",
    "/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter",
]


def find_converter(custom=""):
    for path in (custom, os.environ.get("ODA_CONVERTER", "")):
        if path and os.path.isfile(path):
            return path
    found = shutil.which("ODAFileConverter")
    if found:
        return found
    for pattern in CANDIDATES:
        hits = sorted(glob.glob(pattern))
        if hits:
            return hits[-1]
    return None


def dwg_to_dxf_bytes(data, exe, timeout=180):
    """يحوّل DWG (أي إصدار) إلى DXF نصي بإصدار AutoCAD 2010 ويعيد bytes."""
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = os.path.join(tmp, "in"), os.path.join(tmp, "out")
        os.makedirs(src)
        os.makedirs(dst)
        with open(os.path.join(src, "input.dwg"), "wb") as f:
            f.write(data)
        kwargs = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
        proc = subprocess.run([exe, src, dst, "ACAD2010", "DXF", "0", "1", "input.dwg"],
                              capture_output=True, timeout=timeout, **kwargs)
        outs = glob.glob(os.path.join(dst, "*.dxf")) + glob.glob(os.path.join(dst, "*.DXF"))
        if not outs:
            detail = (proc.stderr or proc.stdout or b"").decode(errors="ignore").strip()[:200]
            raise RuntimeError("فشل تحويل DWG. افتح برنامج ODA File Converter مرة واحدة وأكمل التفعيل المجاني ثم أعد المحاولة. " + detail)
        with open(outs[0], "rb") as f:
            return f.read()
