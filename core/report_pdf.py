"""تقرير PDF للأدوات (المحوّل واستخراج الصور) يُبرمج من البيانات المدخلة، بثيم المنصة (عربي RTL).

يتطلب: reportlab وarabic-reshaper وpython-bidi وخطاً عربياً (خط في assets إن دعم أشكال العرض العربية، وإلا Tahoma/Arial/DejaVu).
"""
import glob
import io
import os
from datetime import datetime

from .assets import get_asset

NAVY, BURGUNDY, LIGHT = "#162746", "#790420", "#F1F5F9"
_FONTS = None


def _has_forms(path):
    """هل يحتوي الخط أشكال العرض العربية (مطلوبة بعد ربط الحروف)؟"""
    try:
        from reportlab.pdfbase.ttfonts import TTFontFile
        return 0xFE8D in TTFontFile(path).charToGlyph
    except Exception:  # noqa: BLE001
        return False


def _find_fonts():
    """يعيد (عادي، عريض). الأولوية لخط في assets (مثل El Messiri) إن كان يدعم العربية، ثم خطوط النظام."""
    here = os.path.dirname(get_asset("x"))
    for path in sorted(glob.glob(os.path.join(here, "*.ttf"))):
        if _has_forms(path) and "bold" not in os.path.basename(path).lower():
            base = os.path.basename(path)
            bolds = [h for h in glob.glob(os.path.join(here, "*.ttf")) if "bold" in os.path.basename(h).lower()
                     and os.path.basename(h).split("-")[0] == base.split("-")[0]]
            return path, (bolds[0] if bolds else None)
    pairs = [(r"C:\Windows\Fonts\tahoma.ttf", r"C:\Windows\Fonts\tahomabd.ttf"),
             (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
             (r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\segoeuib.ttf"),
             ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
             ("/usr/share/fonts/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
             ("/Library/Fonts/Arial Unicode.ttf", None)]
    for reg, bold in pairs:
        if os.path.exists(reg) and _has_forms(reg):
            return reg, (bold if bold and os.path.exists(bold) else None)
    return None, None


def _register():
    global _FONTS
    if _FONTS:
        return _FONTS
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    regular, bold = _find_fonts()
    if not regular:
        raise RuntimeError("لا يوجد خط عربي مناسب لملف PDF.")
    pdfmetrics.registerFont(TTFont("GT-Regular", regular))
    pdfmetrics.registerFont(TTFont("GT-Bold", bold or regular))
    _FONTS = ("GT-Regular", "GT-Bold")
    return _FONTS


def shape(text):
    """ربط الحروف العربية وترتيب الاتجاه ليظهر النص صحيحاً داخل PDF."""
    text = str(text)
    if not any("\u0600" <= ch <= "\u06FF" for ch in text):
        return text
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(text))
    except ImportError:
        return text


def available():
    try:
        import arabic_reshaper  # noqa: F401
        import bidi  # noqa: F401
        import reportlab  # noqa: F401
        _register()
        return True
    except Exception:  # noqa: BLE001
        return False


def build_report(title, request, rows, zone, areas=None):
    """request: {'owner','location','notes'}؛ rows: صفوف formats.build_rows؛ areas: [(name, {m2, feddan})]."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    reg, bold = _register()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=14 * mm,
                            bottomMargin=14 * mm, title=shape(title))
    st_title = ParagraphStyle("t", fontName=bold, fontSize=18, leading=26, alignment=1, textColor=colors.HexColor(NAVY))
    st_sub = ParagraphStyle("s", fontName=reg, fontSize=10, leading=14, alignment=1, textColor=colors.HexColor("#64748B"))
    st_h = ParagraphStyle("h", fontName=bold, fontSize=12.5, leading=18, alignment=2, textColor=colors.HexColor(BURGUNDY))
    st_cell = ParagraphStyle("c", fontName=reg, fontSize=10, leading=14, alignment=2)
    st_cell_l = ParagraphStyle("cl", fontName=reg, fontSize=9, leading=12, alignment=1)

    story = []
    logo = get_asset("logo.png")
    if os.path.exists(logo):
        try:
            img = Image(logo)
            ratio = img.imageHeight / float(img.imageWidth)
            img.drawWidth, img.drawHeight = 38 * mm, 38 * mm * ratio
            img.hAlign = "CENTER"
            story += [img, Spacer(1, 4 * mm)]
        except Exception:  # noqa: BLE001
            pass
    story += [Paragraph(shape(title), st_title),
              Paragraph(shape(datetime.now().strftime("%Y/%m/%d  %H:%M")), st_sub), Spacer(1, 6 * mm)]

    def kv_table(pairs):
        data = [[Paragraph(shape(v) or "-", st_cell), Paragraph(shape(k), st_cell)] for k, v in pairs]
        t = Table(data, colWidths=[110 * mm, 70 * mm])
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                               ("BACKGROUND", (1, 0), (1, -1), colors.HexColor(LIGHT)),
                               ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                               ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        return t

    info = [("صاحب العلاقة", request.get("owner") or "غير محدد"),
            ("الموقع الجغرافي / الولاية", request.get("location") or "غير محدد")]
    if request.get("notes"):
        info.append(("ملاحظات", request["notes"]))
    story += [Paragraph(shape("بيانات الطلب"), st_h), Spacer(1, 2 * mm), kv_table(info), Spacer(1, 5 * mm)]

    if areas:
        pairs = []
        for name, a in areas:
            pairs.append((f"المساحة بالمتر المربع — {name}" if len(areas) > 1 else "المساحة بالمتر المربع", f"{a['m2']:,.2f} م²"))
            pairs.append((f"المساحة بالفدان — {name}" if len(areas) > 1 else "المساحة بالفدان", f"{a['feddan']:,.2f} فدان"))
        story += [Paragraph(shape("مساحة القطعة"), st_h), Spacer(1, 2 * mm), kv_table(pairs), Spacer(1, 5 * mm)]

    # جدول الإحداثيات بالصيغ الثلاث (الأرقام تُكتب من اليسار لليمين كما في الجداول)
    head1 = ["", "Decimal Degree / WGS84", "", f"UTM - WGS84 ({zone})", "", "UTM - CLARKE1880", ""]
    head2 = [shape("النقطة"), "LONGITUDE", "LATITUDE", "Easting", "Northing", "Easting (Adj)", "Northing (Adj)"]
    body = [[Paragraph(shape(r["label"]), st_cell_l), f"{r['lon']:.6f}", f"{r['lat']:.6f}", f"{r['utm_e']:.2f}",
             f"{r['utm_n']:.2f}", f"{r['ck_e']:.2f}", f"{r['ck_n']:.2f}"] for r in rows]
    t = Table([head1, head2] + body, repeatRows=2,
              colWidths=[20 * mm, 27 * mm, 27 * mm, 27 * mm, 27 * mm, 27 * mm, 27 * mm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), reg), ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("SPAN", (1, 0), (2, 0)), ("SPAN", (3, 0), (4, 0)), ("SPAN", (5, 0), (6, 0)),
        ("BACKGROUND", (0, 0), (-1, 1), colors.HexColor(NAVY)), ("BACKGROUND", (3, 0), (4, 1), colors.HexColor(BURGUNDY)),
        ("TEXTCOLOR", (0, 0), (-1, 1), colors.white), ("FONTNAME", (0, 0), (-1, 1), bold),
        ("ROWBACKGROUNDS", (0, 2), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    story += [Paragraph(shape("احداثيات النقاط"), st_h), Spacer(1, 2 * mm), t, Spacer(1, 6 * mm),
              Paragraph(shape("GeoTools — منصة الأدوات الجغرافية"), st_sub)]

    doc.build(story)
    return buf.getvalue()
