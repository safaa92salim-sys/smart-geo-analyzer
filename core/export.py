"""تصدير الجداول إلى Excel بنفس ألوان المنصة."""
import io

import pandas as pd
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from .formats import rows_dataframe

NAVY, BURGUNDY = "162746", "790420"
_thin = Side(style="thin", color="CBD5E1")
BORDER = Border(left=_thin, right=_thin, top=_thin, bottom=_thin)


def _style(cell, color=None, bold=False, white=False):
    if color:
        cell.fill = PatternFill("solid", fgColor=color)
    cell.font = Font(bold=bold, color="FFFFFF" if white else "000000")
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = BORDER


def rows_to_excel(rows, zone, areas=None):
    """areas: قائمة (الاسم، {m2, feddan}) للمضلعات؛ تُكتب في ورقة مستقلة."""
    df = rows_dataframe(rows)
    df["UTM Zone"] = zone
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        df.to_excel(xw, index=False, sheet_name="Coordinates", startrow=1)
        ws = xw.sheets["Coordinates"]
        ws.sheet_view.rightToLeft = True

        # الصف الأول: أسماء الأنظمة الإحداثية (مدموجة فوق أعمدتها)
        groups = [("A1:A2", "النقطة", NAVY), ("B1:C1", "Decimal Degree / WGS84", NAVY),
                  ("D1:E1", "UTM - WGS84", BURGUNDY), ("F1:G1", "UTM - CLARKE1880", NAVY),
                  ("H1:H2", "UTM Zone", NAVY)]
        for rng, title, color in groups:
            ws.merge_cells(rng)
            first = ws[rng.split(":")[0]]
            first.value = title
            for row in ws[rng]:
                for cell in row:
                    _style(cell, color, True, True)
        # الصف الثاني: العناوين الفرعية
        for col_idx, color in zip(range(2, 8), (NAVY, NAVY, BURGUNDY, BURGUNDY, NAVY, NAVY)):
            _style(ws.cell(row=2, column=col_idx), color, True, True)
        for row in ws.iter_rows(min_row=3):
            for cell in row:
                _style(cell)
        for idx in range(1, ws.max_column + 1):
            ws.column_dimensions[get_column_letter(idx)].width = 22
        ws.row_dimensions[1].height = 24
        ws.row_dimensions[2].height = 22

        if areas:
            adf = pd.DataFrame([[n, round(a["m2"], 2), round(a["feddan"], 4)] for n, a in areas],
                               columns=["المضلع", "المساحة (م²)", "المساحة (فدان)"])
            adf.to_excel(xw, index=False, sheet_name="Area")
            wa = xw.sheets["Area"]
            wa.sheet_view.rightToLeft = True
            for cell in wa[1]:
                _style(cell, NAVY, True, True)
            for row in wa.iter_rows(min_row=2):
                for cell in row:
                    _style(cell)
            for col in wa.columns:
                wa.column_dimensions[col[0].column_letter].width = 24
    return buf.getvalue()
