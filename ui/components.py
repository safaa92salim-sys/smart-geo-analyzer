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
    """الشريط الأساسي الموحّد لكل الصفحات: نفس المقاس والخطوط والرسم (العناوين الطويلة بخط أصغر داخل الارتفاع نفسه)."""
    long_cls = " hero-long" if len(title) > 36 else ""
    st.html(
        f"<div class='hero-container hero-big{long_cls}'>"
        f"<div class='hero-text'><div class='hero-title'>{title}</div>"
        f"<div class='hero-subtitle'>{subtitle}</div></div>"
        f"<div class='hero-art'>{PARCEL_SVG}</div></div>"
    )


def hero_home(title, subtitle):
    hero(title, subtitle)


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


def _tile_css(key, uri, icon, accent, layout):
    sel = f"div.st-key-tile-{key}"
    img = f'background-image: url("{uri}") !important;' if uri else ""
    base = (f"{sel}, {sel} div.stButton {{ width: 100% !important; }}"
            f"{sel} button {{ position: relative; width: 100% !important; background-color: #FFFFFF !important; {img}"
            f"background-repeat: no-repeat !important; border: 1px solid #E2E8F0 !important; box-shadow: none !important;"
            f"transition: box-shadow .2s ease, transform .2s ease; }}"
            f"{sel} button:hover, {sel} button:focus, {sel} button:active {{ background-color: #FFFFFF !important; color: #162746 !important; }}"
            f"{sel} button p {{ color: #162746 !important; font-weight: 700 !important; white-space: normal !important; }}")
    if not uri:
        base += (f"{sel} button::before {{ content: \"\"; position: absolute; background-color: {accent}; {mask_css(icon)} }}")
    if layout == "card":
        base += (f"{sel} button {{ height: 262px !important; min-height: 262px !important; display: flex !important;"
                 f"align-items: flex-end !important; justify-content: center !important; padding: 190px 12px 14px 12px !important;"
                 f"border-right: 4px solid {accent} !important; border-radius: 10px !important;"
                 f"background-position: center 18px !important; background-size: 168px 168px !important; }}"
                 f"{sel} button:hover {{ box-shadow: 0 12px 28px rgba(22,39,70,0.14) !important; transform: translateY(-3px); }}"
                 f"{sel} button p {{ font-size: 16.5px !important; text-align: center !important; }}")
        if not uri:
            base += f"{sel} button::before {{ top: 48px; left: 50%; margin-left: -36px; width: 72px; height: 72px; }}"
    else:  # row: صورة يميناً، عنوان، سهم يساراً
        base += (f"{sel} button {{ height: 100px !important; min-height: 100px !important; display: flex !important;"
                 f"align-items: center !important; justify-content: flex-start !important; padding: 0 108px 0 46px !important;"
                 f"border-radius: 18px !important; box-shadow: 0 5px 16px rgba(22,39,70,0.08) !important;"
                 f"background-position: right 14px center !important; background-size: 76px 76px !important; }}"
                 f"{sel} button p {{ font-size: 17px !important; text-align: right !important; line-height: 1.6 !important; }}"
                 f"{sel} button::after {{ content: \"\"; position: absolute; left: 14px; top: 50%; margin-top: -12px; width: 24px;"
                 f"height: 24px; background-color: {accent}; {mask_css('chevron-left')} }}")
        if not uri:
            base += f"{sel} button::before {{ right: 30px; top: 50%; margin-top: -22px; width: 44px; height: 44px; }}"
    return base


def tile_button(key, title, image_file=None, icon="grid", accent="#790420", layout="card",
                page=None, on_click=None, args=()):
    """بطاقة أداة هي نفسها زر حقيقي (صورة + عنوان): الضغط عليها ينقل إلى الصفحة أو ينفّذ الإجراء."""
    uri = img_data_uri(get_asset(image_file)) if image_file else ""
    st.markdown(f"<style>{_tile_css(key, uri, icon, accent, layout)}</style>", unsafe_allow_html=True)
    clicked = st.button(title, key=f"tile-{key}", on_click=on_click, args=args)
    if clicked and page:
        st.switch_page(page)


def desktop_tile(key, title, image_file, icon, page, accent="#790420"):
    tile_button(key, title, image_file, icon, accent=accent, layout="card", page=page)


def section_title(text):
    st.html(f"<div class='section-title'>{text}</div>")


def notice(text, large=False):
    cls = "notice-box notice-lg" if large else "notice-box"
    st.html(f"<div class='{cls}'>{text}</div>")


def stepper(steps, active=-1, large=False):
    """مؤشر خطوات. active = رقم الخطوة الحالية (يبدأ من 0)، -1 لعدم تمييز أي خطوة."""
    items = ""
    for i, text in enumerate(steps):
        state = "done" if 0 <= active > i else ("active" if i == active else "")
        mark = "✓" if state == "done" else str(i + 1)
        items += f"<div class='step {state}'><div class='step-num'>{mark}</div><div class='step-text'>{text}</div></div>"
    st.html(f"<div class='stepper{' step-lg' if large else ''}'>{items}</div>")


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


# ====================================================================== قشرة الهاتف
SIGNATURE_LINE1 = "GeoTools © 2026 - Created by Eng. Safaa Al Harrasi"
SIGNATURE_LINE2 = "geo-tools.mystrikingly.com | Geo.C.Tools@gmail.com"

BOTTOM_NAV = [("views/home.py", "الرئيسية", "home"), ("views/image_extractor.py", "استخراج", "image"),
              ("views/analyzer.py", "المحلل", "compass"), ("views/converter.py", "المحوّل", "repeat")]


def mobile_shell_css():
    """CSS خاص بقشرة الهاتف: بلا شريط جانبي ولا رأس Streamlit، مع شريط تنقل سفلي."""
    css = """
    html body [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
    [data-testid="stExpandSidebarButton"], [data-testid="stHeader"] { display: none !important; }
    .block-container { padding: 0.35rem 0.75rem 6.5rem 0.75rem !important; }
    input, textarea, [data-baseweb="select"] * { font-size: 16px !important; }
    .mobile-appbar { display: flex; justify-content: center; align-items: center; height: 46px; padding: 0 0 6px 0; margin-bottom: 4px; }
    .mobile-appbar img { height: 34px; width: auto; }
    .mobile-sign { text-align: center !important; color: #64748B; font-size: 12.5px; line-height: 1.9; padding: 18px 8px 6px; direction: ltr; }
    .mobile-sign b { color: #162746; }

    /* المستطيل الرئيسي على الهاتف: أقصر، أضيق، والنص موسّط أفقياً وعمودياً */
    .hero-container.hero-big { height: 104px !important; min-height: 104px !important; max-height: 104px !important;
        padding: 10px 14px !important; margin: 0 6px 10px 6px !important; border-radius: 16px; display: flex !important;
        flex-direction: column; justify-content: center; align-items: center; overflow: hidden; }
    .hero-container.hero-big .hero-art { display: none !important; }
    .hero-container.hero-big .hero-text { width: 100%; }
    .hero-container.hero-big .hero-title { font-size: 18px !important; line-height: 1.45 !important; margin: 0 !important; white-space: normal !important; }
    .hero-container.hero-big .hero-subtitle { font-size: 12px !important; line-height: 1.5 !important; margin: 4px 0 0 0 !important; white-space: normal !important; }
    .hero-container.hero-big.hero-long .hero-title { font-size: 16px !important; }
    .hero-container.hero-big.hero-long .hero-subtitle { display: none !important; }

    /* شريط التنقل السفلي (أزرار حقيقية) */
    .st-key-mobile-bottom-nav { position: fixed; left: 0; right: 0; bottom: 0; z-index: 1000; background: #FFFFFF;
        border-top: 1px solid #E2E8F0; padding: 4px 4px calc(4px + env(safe-area-inset-bottom)); box-shadow: 0 -4px 14px rgba(22,39,70,0.08); }
    .st-key-mobile-bottom-nav [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; gap: 0 !important; }
    .st-key-mobile-bottom-nav [data-testid="stColumn"] { min-width: 0 !important; width: 25% !important; flex: 1 1 0 !important; }
    .st-key-mobile-bottom-nav button { display: flex !important; flex-direction: column !important; align-items: center !important;
        justify-content: center !important; width: 100% !important; min-height: 54px !important; height: auto !important; padding: 4px 2px !important;
        gap: 2px; background: transparent !important; border: none !important; box-shadow: none !important; }
    .st-key-mobile-bottom-nav button p { font-size: 11.5px !important; color: #475569 !important; font-weight: 700 !important;
        white-space: normal !important; text-align: center !important; margin: 0 !important; }
    .st-key-mobile-bottom-nav button:hover p, .st-key-mobile-bottom-nav button:active p { color: #790420 !important; }
    .st-key-mobile-bottom-nav button::before { content: ""; width: 23px; height: 23px; background-color: #475569; }
    .st-key-mobile-bottom-nav button:hover::before { background-color: #790420; }

    /* مراحل المحلل بصف أفقي مضغوط */
    [data-testid="stHorizontalBlock"]:has([class*="st-key-stepnav"]) { flex-direction: row !important; flex-wrap: nowrap !important; gap: 4px !important; }
    [data-testid="stHorizontalBlock"]:has([class*="st-key-stepnav"]) > [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }
    [class*="st-key-stepnav"] button { padding: 8px 4px !important; }
    [class*="st-key-stepnav"] button p { flex-direction: column; gap: 4px; text-align: center !important; font-size: 12px !important; line-height: 1.4 !important; }
    """
    for i, (_, _, icon) in enumerate(BOTTOM_NAV, start=1):
        css += f'.st-key-mobile-bottom-nav [data-testid="stColumn"]:nth-child({i}) button::before {{ {mask_css(icon)} }}'
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def mobile_appbar():
    uri = png_data_uri(get_asset("logo.png"), 420)
    if uri:
        st.html(f"<div class='mobile-appbar'><img src='{uri}' alt='GeoTools'></div>")


def mobile_footer():
    st.html(f"<div class='mobile-sign'><b>{SIGNATURE_LINE1}</b><br>{SIGNATURE_LINE2}</div>")


def bottom_nav():
    with st.container(key="mobile-bottom-nav"):
        targets = []
        for i, (col, (path, label, _)) in enumerate(zip(st.columns(len(BOTTOM_NAV)), BOTTOM_NAV)):
            with col:
                if st.button(label, key=f"mnav-{i}"):
                    targets.append(path)
    if targets:
        st.switch_page(targets[0])


def mobile_tile(key, title, image_file=None, icon="grid", page=None, on_click=None, args=()):
    tile_button(key, title, image_file, icon, layout="row", page=page, on_click=on_click, args=args)


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


# ====================================================================== قشرة الهاتف
SIGNATURE_LINE1 = "GeoTools © 2026 - Created by Eng. Safaa Al Harrasi"
SIGNATURE_LINE2 = "geo-tools.mystrikingly.com | Geo.C.Tools@gmail.com"

BOTTOM_NAV = [("views/home.py", "الرئيسية", "home"), ("views/image_extractor.py", "استخراج", "image"),
              ("views/analyzer.py", "المحلل", "compass"), ("views/converter.py", "المحوّل", "repeat")]


def mobile_shell_css():
    """CSS خاص بقشرة الهاتف: بلا شريط جانبي ولا رأس Streamlit، مع شريط تنقل سفلي."""
    css = """
    html body [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
    [data-testid="stExpandSidebarButton"], [data-testid="stHeader"] { display: none !important; }
    .block-container { padding: 0.5rem 0.75rem 6.5rem 0.75rem !important; }
    input, textarea, [data-baseweb="select"] * { font-size: 16px !important; }
    .mobile-appbar { display: flex; justify-content: center; padding: 4px 0 12px 0; }
    .mobile-appbar img { height: 58px; width: auto; }
    .mobile-sign { text-align: center !important; color: #64748B; font-size: 12.5px; line-height: 1.9; padding: 18px 8px 6px; direction: ltr; }
    .mobile-sign b { color: #162746; }
    .mtile { display: flex; align-items: center; gap: 14px; background: #FFFFFF; border: 1px solid #E2E8F0;
             border-radius: 20px; padding: 12px 14px; box-shadow: 0 6px 16px rgba(22,39,70,0.07); margin-bottom: 4px; }
    .mtile-media { width: 84px; height: 84px; flex-shrink: 0; border-radius: 16px; object-fit: contain; background: #FFFFFF; }
    .mtile-ic { display: flex; align-items: center; justify-content: center; background: #F1F5F9; color: #790420; }
    .mtile-ic .ic { width: 42px; height: 42px; margin: 0; }
    .mtile-title { flex: 1; font-size: 17px; font-weight: 700; color: #162746; line-height: 1.6; }
    .mtile-chev { width: 26px; height: 26px; background-color: #790420; """ + mask_css("chevron-left") + """ }
    [class*="st-key-mtile-"] { position: relative; margin-bottom: 10px; }
    [class*="st-key-mtile-"] [data-testid="stPageLink"], [class*="st-key-mtile-"] div.stButton { position: absolute !important; inset: 0; margin: 0 !important; z-index: 5; }
    [class*="st-key-mtile-"] [data-testid="stPageLink"] a, [class*="st-key-mtile-"] div.stButton button {
        width: 100% !important; height: 100% !important; opacity: 0; border: none !important; }
    .st-key-mobile-bottom-nav { position: fixed; left: 0; right: 0; bottom: 0; z-index: 1000; background: #FFFFFF;
        border-top: 1px solid #E2E8F0; padding: 4px 4px calc(4px + env(safe-area-inset-bottom)); box-shadow: 0 -4px 14px rgba(22,39,70,0.08); }
    .st-key-mobile-bottom-nav [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; gap: 0 !important; }
    .st-key-mobile-bottom-nav [data-testid="stColumn"] { min-width: 0 !important; width: 25% !important; flex: 1 1 0 !important; }
    .st-key-mobile-bottom-nav [data-testid="stPageLink"] a { flex-direction: column; border: none !important; padding: 4px 2px !important;
        min-height: 54px !important; gap: 2px; width: 100%; justify-content: center; background: transparent !important; }
    .st-key-mobile-bottom-nav [data-testid="stPageLink"] a * { font-size: 11.5px !important; color: #475569 !important; font-weight: 700 !important;
        white-space: normal !important; text-align: center; }
    .st-key-mobile-bottom-nav [data-testid="stPageLink"] a[aria-current="page"] *, .st-key-mobile-bottom-nav [data-testid="stPageLink"] a:hover * { color: #790420 !important; }
    .st-key-mobile-bottom-nav [data-testid="stPageLink"] a:hover { background: transparent !important; }
    [data-testid="stHorizontalBlock"]:has([class*="st-key-stepnav"]) { flex-direction: row !important; flex-wrap: nowrap !important; gap: 4px !important; }
    [data-testid="stHorizontalBlock"]:has([class*="st-key-stepnav"]) > [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }
    [class*="st-key-stepnav"] button { padding: 8px 4px !important; }
    [class*="st-key-stepnav"] button p { flex-direction: column; gap: 4px; text-align: center !important; font-size: 12px !important; line-height: 1.4 !important; }
    .st-key-mobile-bottom-nav [data-testid="stPageLink"] a::before { content: ""; width: 23px; height: 23px; background-color: #475569; }
    .st-key-mobile-bottom-nav [data-testid="stPageLink"] a[aria-current="page"]::before { background-color: #790420; }
    """
    for i, (_, _, icon) in enumerate(BOTTOM_NAV, start=1):
        css += (f'.st-key-mobile-bottom-nav [data-testid="stColumn"]:nth-child({i}) [data-testid="stPageLink"] a::before '
                f"{{ {mask_css(icon)} }}")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def mobile_appbar():
    uri = png_data_uri(get_asset("logo.png"), 420)
    if uri:
        st.html(f"<div class='mobile-appbar'><img src='{uri}' alt='GeoTools'></div>")


def mobile_footer():
    st.html(f"<div class='mobile-sign'><b>{SIGNATURE_LINE1}</b><br>{SIGNATURE_LINE2}</div>")


def bottom_nav():
    with st.container(key="mobile-bottom-nav"):
        for col, (path, label, _) in zip(st.columns(len(BOTTOM_NAV)), BOTTOM_NAV):
            with col:
                st.page_link(path, label=label)


def mobile_tile(key, title, image_file=None, icon="grid", page=None, on_click=None, args=()):
    """بطاقة أداة للهاتف: صورة + عنوان + سهم، والبطاقة كلها قابلة للضغط (صفحة أو إجراء)."""
    uri = img_data_uri(get_asset(image_file)) if image_file else ""
    media = (f"<img class='mtile-media' src='{uri}' alt=''>" if uri
             else f"<div class='mtile-media mtile-ic'>{ms(icon)}</div>")
    with st.container(key=f"mtile-{key}"):
        st.html(f"<div class='mtile'>{media}<div class='mtile-title'>{title}</div><span class='mtile-chev'></span></div>")
        if page:
            st.page_link(page, label="فتح")
        else:
            st.button("فتح", key=f"mtile-btn-{key}", on_click=on_click, args=args)
