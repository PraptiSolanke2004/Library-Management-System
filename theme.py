"""
theme.py - custom look for the app: background image + styled cards.

BACKGROUND IMAGE
    The app uses  assets/background.<jpg|jpeg|png|webp|svg>  (first one found).
    To use your own picture, put it in the assets folder and name it
    background.jpg  (or .png / .webp). No code change needed.
"""
import base64
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).with_name("assets")
MIME = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "svg": "image/svg+xml",
}


@st.cache_resource
def _background_data_uri() -> str:
    for ext in ("jpg", "jpeg", "png", "webp", "svg"):
        path = ASSETS / f"background.{ext}"
        if path.exists():
            encoded = base64.b64encode(path.read_bytes()).decode()
            return f"data:{MIME[ext]};base64,{encoded}"
    return ""


def apply_theme():
    bg = _background_data_uri()
    image_layer = f', url("{bg}")' if bg else ""

    css = f"""
<style>
/* ---------- page background ---------- */
.stApp {{
    background-image:
        linear-gradient(135deg, rgba(15,23,42,0.78), rgba(30,41,59,0.55)){image_layer};
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}
[data-testid="stHeader"] {{ background: transparent; }}

/* ---------- main content panel ---------- */
.block-container, [data-testid="stMainBlockContainer"] {{
    background: rgba(255,255,255,0.94);
    border-radius: 20px;
    padding: 2rem 2.4rem 2.4rem 2.4rem;
    margin-top: 1rem;
    max-width: 1250px;
    box-shadow: 0 18px 50px rgba(0,0,0,0.35);
}}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] > div:first-child {{
    background: linear-gradient(180deg, #1e1b4b 0%, #0f172a 100%);
}}
[data-testid="stSidebar"] * {{ color: #e2e8f0 !important; }}
.brand {{
    display:flex; align-items:center; gap:12px;
    padding: 6px 4px 18px 4px; margin-bottom: 8px;
    border-bottom: 1px solid rgba(255,255,255,0.12);
}}
.brand .logo {{
    font-size: 30px; background: linear-gradient(135deg,#6366f1,#ec4899);
    border-radius: 12px; width: 48px; height: 48px;
    display:flex; align-items:center; justify-content:center;
}}
.brand .name {{ font-weight:700; font-size:17px; line-height:1.2; }}
.brand .sub  {{ font-size:12px; opacity:.7; }}

/* ---------- hero banner ---------- */
.hero {{
    background: linear-gradient(120deg, #4f46e5 0%, #7c3aed 50%, #db2777 100%);
    border-radius: 18px; padding: 26px 30px; color: #fff;
    margin-bottom: 22px; position: relative; overflow: hidden;
    box-shadow: 0 10px 30px rgba(79,70,229,0.35);
}}
.hero::after {{
    content: "📚"; position:absolute; right: 26px; top: 6px;
    font-size: 96px; opacity: .18;
}}
.hero h1 {{ margin:0; font-size: 30px; color:#fff; padding:0; }}
.hero p  {{ margin:6px 0 0 0; opacity:.9; font-size:15px; }}

/* ---------- KPI cards ---------- */
.kpi-grid {{
    display:grid; gap:14px; margin-bottom: 22px;
    grid-template-columns: repeat(auto-fit, minmax(175px, 1fr));
}}
.kpi {{
    border-radius: 16px; padding: 18px 18px; color:#fff;
    display:flex; align-items:center; gap:14px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.18);
    transition: transform .15s ease, box-shadow .15s ease;
}}
.kpi:hover {{ transform: translateY(-3px); box-shadow: 0 12px 26px rgba(0,0,0,0.25); }}
.kpi-icon {{
    font-size: 26px; width: 48px; height: 48px; border-radius: 12px;
    background: rgba(255,255,255,0.22);
    display:flex; align-items:center; justify-content:center; flex-shrink:0;
}}
.kpi-value {{ font-size: 28px; font-weight: 800; line-height: 1.1; }}
.kpi-label {{ font-size: 13px; opacity: .92; margin-top: 2px; }}

/* ---------- section titles & panels ---------- */
.section-title {{
    font-size: 17px; font-weight: 700; color:#1e293b;
    margin: 4px 0 8px 0; padding-left: 10px; border-left: 4px solid #6366f1;
}}
[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 16px !important;
    background: #ffffff;
    box-shadow: 0 4px 14px rgba(15,23,42,0.08);
}}

/* ---------- availability bar ---------- */
.avail-wrap {{ margin: 6px 0 4px 0; }}
.avail-bar {{
    height: 22px; border-radius: 11px; background:#e2e8f0; overflow:hidden;
}}
.avail-fill {{
    height:100%; border-radius: 11px;
    background: linear-gradient(90deg,#10b981,#34d399);
}}
.avail-text {{ display:flex; justify-content:space-between; font-size:13px; color:#475569; margin-top:6px; }}

/* ---------- activity feed ---------- */
.feed-item {{
    display:flex; align-items:center; gap:12px; padding: 9px 4px;
    border-bottom: 1px solid #eef2f7; font-size: 14px; color:#1e293b;
}}
.feed-item:last-child {{ border-bottom:none; }}
.badge {{
    font-size: 11px; font-weight:700; padding: 3px 10px; border-radius: 999px; white-space:nowrap;
}}
.badge.issued   {{ background:#fef3c7; color:#92400e; }}
.badge.returned {{ background:#d1fae5; color:#065f46; }}
.feed-sub {{ color:#64748b; font-size:12px; }}

/* ---------- buttons ---------- */
.stButton > button, .stFormSubmitButton > button {{
    border-radius: 10px; font-weight: 600;
}}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)


def sidebar_brand():
    st.sidebar.markdown(
        '<div class="brand"><div class="logo">📚</div>'
        '<div><div class="name">City Library</div>'
        '<div class="sub">Management System</div></div></div>',
        unsafe_allow_html=True,
    )


def kpi_card(icon: str, label: str, value, gradient: str) -> str:
    """Return the HTML of one KPI card (single line, so Markdown doesn't mangle it)."""
    return (
        f'<div class="kpi" style="background:{gradient}">'
        f'<div class="kpi-icon">{icon}</div>'
        f'<div><div class="kpi-value">{value}</div><div class="kpi-label">{label}</div></div>'
        f"</div>"
    )
