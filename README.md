# منصة GeoTools

## التشغيل محلياً (Miniforge)

```bash
mamba create -n geotools -c conda-forge python=3.11 geopandas pyogrio pyproj folium openpyxl pillow pandas
mamba activate geotools
pip install streamlit streamlit-folium ezdxf pymupdf rapidocr-onnxruntime xlrd
streamlit run app.py
```

انسخ مجلد `assets/` الحالي (logo.png, icon.png, soil.kml, Soil_Report.xlsx, soil_report_multi.xlsx, smart.png, convert.png, coordinates.png)
إلى جذر المشروع بجانب `app.py` قبل التشغيل.

## الهيكل

- `app.py` — الإعدادات والثيم والتنقل وبيانات الطلب المشتركة
- `views/` — الصفحات: الرئيسية، المحلل الجغرافي، المحوّل، استخراج من صورة (معاينة)
- `core/` — التحويلات (UTM وكلارك)، الصيغ، KML، DXF، الخريطة، Excel
- `ui/` — الثيم والمكونات المشتركة

## ملاحظات
- أداة استخراج الإحداثيات من الصور تعتمد على `rapidocr-onnxruntime` (مجاني، يعمل محلياً دون إرسال الملفات لأي جهة)، وتتطلب بايثون 3.11 أو 3.12.
- لقراءة ملفات DWG مباشرة ثبّت برنامج ODA File Converter (مجاني بتسجيل) على الجهاز؛ وإلا يُحفظ الملف من AutoCAD بصيغة DXF.
- أيقونات اختيارية للشريط الجانبي في `assets/`: nav_home.png, nav_analyzer.png, nav_extract.png, nav_converter.png
- تقرير PDF للمحلل يُنشأ من ملف Excel النهائي عبر Microsoft Excel (ويندوز مع `pip install pywin32`) أو LibreOffice. على Streamlit Cloud غيّر اسم `packages.txt.disabled` إلى `packages.txt` ليُثبَّت LibreOffice (التثبيت أبطأ).
- تقارير PDF للأدوات الأخرى تحتاج reportlab وarabic-reshaper وpython-bidi، وخطاً عربياً (Tahoma/Arial على ويندوز، أو ضع خطاً في assets).
- على Streamlit Cloud اختر Python 3.11 أو 3.12 من Advanced settings.
