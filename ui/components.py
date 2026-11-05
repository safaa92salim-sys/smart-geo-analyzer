"""مكونات الواجهة المشتركة (نفس الأصناف والألوان المستخدمة في الثيم الأصلي)."""
import base64
import io
import os

import streamlit as st
from PIL import Image

from core.assets import get_asset
from ui.icons import icon_uri, mask_css, ms  # noqa: F401

# مضلع الأرض في الهيرو: مأخوذ من نموذج الإسقاط (200 × 500 م، المساحة 100000 م²)
PARCEL_SVG = """
<svg viewBox="0 0 260 310" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="مخطط قطعة أرض">
  <polygon class="parcel-fill" points="28,65.4 117.1,20 230.7,242.7 141.6,288.1" fill="rgba(255,255,255,0.12)"/>
  <polygon class="parcel-line" points="28,65.4 117.1,20 230.7,242.7 141.6,288.1" fill="none"
           stroke="#FFFFFF" stroke-width="2" stroke-linejoin="round"/>
  <g fill="#FFFFFF">
    <circle cx="28" cy="65.4" r="3.5"/><circle cx="117.1" cy="20" r="3.5"/>
    <circle cx="230.7" cy="242.7" r="3.5"/><circle cx="141.6" cy="288.1" r="3.5"/>
  </g>
  <g font-size="12" font-weight="700">
    <text x="12" y="62">P1</text><text x="122" y="14">P2</text>
    <text x="236" y="248">P3</text><text x="148" y="304">P4</text>
  </g>
  <g font-size="10.5" opacity="0.85">
    <text x="40" y="38">200.00</text>
    <text x="190" y="128">500.00</text>
    <text x="104" y="162" font-size="12">100,000 م²</text>
  </g>
  <g opacity="0.85">
    <path d="M22 4 L27 18 L22 15 L17 18 Z" fill="#FFFFFF"/>
    <text x="18.5" y="30" font-size="10">N</text>
  </g>
</svg>
"""


def hero(title, subtitle=""):
    """الهيرو الأصلي للأدوات (نفس الشكل المعتمد سابقاً)."""
    st.markdown(f"""
<div class='hero-container'>
    <div class='hero-title'>{title}</div>
    <div class='hero-subtitle'>{subtitle}</div>
</div>
""", unsafe_allow_html=True)


def hero_home(title, subtitle):
    st.html(
        f"<div class='hero-container hero-big'>"
        f"<div class='hero-text'><div class='hero-title'>{title}</div>"
        f"<div class='hero-subtitle'>{subtitle}</div></div>"
        f"<div class='hero-art'>{PARCEL_SVG}</div></div>"
    )


def intro_box(text, years):
    st.html(f"<div class='intro-box'><span class='intro-text'>{text}</span>"
            f"<span class='intro-sep'>|</span><span class='intro-years'>{years}</span></div>")


def section_banner(ar, en=""):
    sep = "<span class='sep'>|</span><span class='en'>" + en + "</span>" if en else ""
    st.html(f"<div class='section-banner'>{ar}{sep}</div>")


@st.cache_data(show_spinner=False)
def img_data_uri(path, max_w=720):
    """يحوّل صورة من assets إلى data URI مضغوط (لا يمكن الإشارة إلى ملفات محلية من HTML مباشرة)."""
    if not os.path.exists(path):
        return ""
    im = Image.open(path)
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert("RGB")
    im.thumbnail((max_w, max_w * 2))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=86)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def tool_tile(image_file, title, icon="widgets", accent="#790420", badge=None):
    """بطاقة أداة: صورة داخل منطقة مربعة + اسم فقط (الانتقال عبر st.page_link أسفلها)."""
    uri = img_data_uri(get_asset(image_file))
    media = (f"<img class='tool-img' src='{uri}' alt=''>" if uri
             else f"<div class='tool-img tool-img-empty'>{ms(icon)}</div>")
    badge_html = f"<span class='tool-badge'>{badge}</span>" if badge else ""
    st.html(f"<div class='tool-tile' style='--accent:{accent};'>{media}"
            f"<div class='tool-name'><span>{title}</span>{badge_html}</div></div>")


def section_title(text):
    st.html(f"<div class='section-title'>{text}</div>")


def notice(text):
    st.html(f"<div class='notice-box'>{text}</div>")


def stepper(steps, active=-1):
    """مؤشر خطوات. active = رقم الخطوة الحالية (يبدأ من 0)، -1 لعدم تمييز أي خطوة."""
    items = ""
    for i, text in enumerate(steps):
        state = "done" if 0 <= active > i else ("active" if i == active else "")
        mark = "✓" if state == "done" else str(i + 1)
        items += f"<div class='step {state}'><div class='step-num'>{mark}</div><div class='step-text'>{text}</div></div>"
    st.html(f"<div class='stepper'>{items}</div>")


def tool_card(icon, title, desc, features, accent="#790420", primary=False, badge=None):
    feats = "".join(f"<li>{f}</li>" for f in features)
    badge_html = f"<span class='tool-badge'>{badge}</span>" if badge else ""
    cls = "tool-card primary" if primary else "tool-card"
    st.html(
        f"<div class='{cls}' style='--accent:{accent};'>"
        f"<div class='tool-head'><span class='tool-icon'>{icon}</span>"
        f"<span class='tool-title'>{title}</span>{badge_html}</div>"
        f"<p class='tool-desc'>{desc}</p><ul class='tool-list'>{feats}</ul></div>"
    )


def _set_step(key, label):
    st.session_state[key] = label


def step_nav(steps, key):
    """مؤشر خطوات قابل للنقر بنفس مظهر stepper. الحالة الحالية في st.session_state[key]."""
    cur = st.session_state.get(key, steps[0])
    idx = steps.index(cur) if cur in steps else 0
    base = "stepnav-" + key.replace("_", "-")
    css = "<style>"
    for i in range(len(steps)):
        sel = f".st-key-{base}-{i}"
        mark = "✓" if i < idx else str(i + 1)
        css += f'{sel} button p::before {{ content: "{mark}"; }}'
        if i == idx:
            css += (f"{sel} button {{ border-color: #790420 !important; }}"
                    f"{sel} button p {{ color: #790420 !important; }}"
                    f"{sel} button p::before {{ background-color: #790420; color: #FFFFFF; }}")
        elif i < idx:
            css += f"{sel} button p::before {{ background-color: #162746; color: #FFFFFF; }}"
    css += "</style>"
    st.markdown(css, unsafe_allow_html=True)
    for i, (col, label) in enumerate(zip(st.columns(len(steps)), steps)):
        col.button(label, key=f"{base}-{i}", on_click=_set_step, args=(key, label))
    return st.session_state.get(key, steps[0])


@st.cache_data(show_spinner=False)
def png_data_uri(path, size=64):
    """أيقونة PNG صغيرة بخلفية شفافة كـ data URI."""
    if not os.path.exists(path):
        return ""
    im = Image.open(path).convert("RGBA")
    im.thumbnail((size, size))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def nav_pills(options, key):
    """أقسام أفقية قابلة للنقر. يُعرض القسم المختار فقط (يتجنب مشكلة الخرائط داخل تبويبات مخفية)."""
    if hasattr(st, "segmented_control"):
        kwargs = {} if key in st.session_state else {"default": options[0]}
        choice = st.segmented_control("القسم", options, key=key, label_visibility="collapsed", **kwargs)
        return choice or options[0]
    return st.radio("القسم", options, horizontal=True, key=key, label_visibility="collapsed")


def references_box():
    st.markdown("""
<div class='references-box'>
    <div class='references-title'><span class='ic ic-book-open'></span> مصادر البيانات والمراجع:</div>
    <div class='references-text'>
        <b>1-</b> الخارطة الاستثمارية الرسمية (صيغة KML) الصادرة عن الجهات المختصة، والتي تتضمن بيانات النطاقات الاستثمارية وخصائص التربة ومجالات الاستثمار المعتمدة لكل نطاق.<br>
        <b>2-</b> أطلس عُمان للتربة (Soil Atlas of Oman)، باعتباره المرجع الوطني المعتمد لتصنيف خصائص التربة، الطبعة الأولى (1411هـ / 1990م)، الصادر عن وزارة الزراعة والأسماك بسلطنة عُمان، وقد تم إعداد الأطلس بالتعاون مع منظمة الأغذية والزراعة للأمم المتحدة (FAO).
    </div>
    <div class='notice-box'>
        <b><span class='ic ic-info'></span> ملاحظة منهجية هامة:</b> تم استخدام هذه المصادر لأغراض التحليل الأولي وتقييم الملاءمة المبدئية فقط، ولا تُغني النتائج الواردة عن إجراء الدراسات الحقلية التفصيلية والفحوصات الموقعية اللازمة عند مرحلة التنفيذ الفعلي للمشروعات.
    </div>
</div>
""", unsafe_allow_html=True)


def footer():
    st.markdown("""
<div class='footer-text'>
    GeoTools © 2026 - Created by Eng. Safaa Al Harrasi<br>
    <a href='https://geo-tools.mystrikingly.com' target='_blank'>geo-tools.mystrikingly.com</a> | Geo.C.Tools@gmail.com
</div>
""", unsafe_allow_html=True)


def tab_icons(names):
    """أيقونات داخل st.tabs (بالترتيب) عبر CSS، بدل رموز Material التي قد تظهر كنص."""
    css = ('.stTabs button[role="tab"]{display:flex;align-items:center;color:#475569;}'
           '.stTabs button[role="tab"][aria-selected="true"]{color:#790420;}')
    for i, n in enumerate(names, 1):
        css += (f'.stTabs button[role="tab"]:nth-of-type({i})::before{{content:"";display:inline-block;width:20px;height:20px;'
                f'margin-inline-end:8px;background-color:currentColor;{mask_css(n)}}}')
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def tab_nav(labels, icons, key):
    """تبويبات قابلة للنقر بنفس مظهر st.tabs (يُعرض محتوى التبويب المختار فقط). الحالة في st.session_state[key]."""
    cur = st.session_state.get(key, labels[0])
    idx = labels.index(cur) if cur in labels else 0
    base = "tabnav-" + key.replace("_", "-")
    css = ""
    for i, name in enumerate(icons):
        sel = f".st-key-{base}-{i}"
        color = "#790420" if i == idx else "#475569"
        border = "#790420" if i == idx else "#E2E8F0"
        css += (f"{sel} button{{background:transparent !important;border:none !important;border-radius:0 !important;"
                f"border-bottom:3px solid {border} !important;padding:10px 14px !important;min-height:0 !important;width:100%;}}"
                f"{sel} button:hover{{background:#F8FAFC !important;}}"
                f"{sel} button p{{color:{color} !important;font-weight:700 !important;font-size:16px !important;"
                f"display:flex;align-items:center;gap:8px;margin:0 !important;text-align:right !important;}}"
                f"{sel} button p::before{{content:\"\";display:inline-block;width:20px;height:20px;"
                f"background-color:{color};{mask_css(name)}}}")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    widths = [max(len(l) for l in labels) + 8] * len(labels) + [6]
    for i, (col, label) in enumerate(zip(st.columns(widths, gap="small"), labels)):
        col.button(label, key=f"{base}-{i}", on_click=_set_step, args=(key, label))
    return st.session_state.get(key, labels[0])
