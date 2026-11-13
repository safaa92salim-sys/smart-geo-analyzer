"""تحديد قشرة العرض: هاتف أم كمبيوتر.

يُحدَّد من نوع المتصفح (User-Agent). ويمكن فرض القشرة بإضافة ?view=mobile أو ?view=desktop إلى الرابط
(مفيد لتجربة شكل الهاتف من الكمبيوتر، ولأجهزة آيباد التي تُعرَّف كحاسوب). يُحفظ الاختيار طوال الجلسة.
"""
import re

import streamlit as st

_PHONE = re.compile(r"Mobi|iPhone|iPod|Windows Phone", re.I)


def is_mobile():
    forced = st.query_params.get("view")
    if forced in ("mobile", "desktop"):
        st.session_state["view_mode"] = forced
    mode = st.session_state.get("view_mode")
    if mode:
        return mode == "mobile"
    try:
        ua = st.context.headers.get("User-Agent", "")
    except Exception:  # noqa: BLE001
        ua = ""
    st.session_state["view_mode"] = "mobile" if _PHONE.search(ua) else "desktop"
    return st.session_state["view_mode"] == "mobile"
