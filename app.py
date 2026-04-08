"""
GenAI Project Management Dashboard — Glassmorphic Looker-style Layout (Light Theme)
Cross-filtered, eggshell-background, powered by Claude AI.
"""

import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from data_loader import load_all, HAS_GSPREAD, SA_KEY_FOUND, SA_EMAIL, SA_KEY_PATH
from ai_engine import (
    generate_project_pulse,
    generate_risk_assessment,
    parse_nl_query,
    execute_nl_query,
    HAS_ANTHROPIC,
)

# ═══════════════════════════════════════════════════════════════════════════════
#  APP CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="EtherCommand",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════════════════════
#  ETHEREAL COMMAND CENTER — DARK GLASSMORPHIC THEME
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100;300;400;500;700;900&display=swap');

    /* ── Root Variables ─────────────────────────────────────────── */
    :root {
        --surface: #0e0e0e;
        --surface-container-low: #131313;
        --surface-container: #1a1919;
        --surface-container-high: #201f1f;
        --surface-container-highest: #262626;
        --surface-bright: #2c2c2c;
        --on-surface: #ffffff;
        --on-surface-variant: #adaaaa;
        --primary: #c39bff;
        --primary-dim: #924bf3;
        --secondary: #00f4fe;
        --tertiary: #ffeea6;
        --error: #ff6e84;
        --outline-variant: #494847;
        --ghost-border: rgba(73, 72, 71, 0.15);
    }

    .stApp {
        background: var(--surface) !important;
        font-family: 'Inter', sans-serif;
        color: var(--on-surface);
    }

    /* Hide sidebar completely */
    section[data-testid="stSidebar"] { display: none !important; }

    /* Hide Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }

    /* ── Top Navbar ────────────────────────────────────────────── */
    .top-navbar {
        background: var(--surface-container);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--ghost-border);
        border-radius: 2rem;
        padding: 8px 16px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
    }
    .navbar-brand {
        font-size: 20px;
        font-weight: 700;
        color: var(--primary);
        white-space: nowrap;
        margin-right: 12px;
        letter-spacing: -0.02em;
    }
    .navbar-brand span {
        font-size: 12px;
        font-weight: 400;
        color: var(--on-surface-variant);
        margin-left: 8px;
    }

    /* Style the Streamlit tabs as navbar pills */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent;
        gap: 4px;
        border-bottom: none;
        padding: 0;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: none;
        border-radius: 9999px;
        padding: 8px 18px;
        margin: 0 2px;
        color: var(--on-surface-variant);
        font-weight: 500;
        font-size: 13px;
        height: auto;
        white-space: nowrap;
        transition: all 0.25s ease;
        letter-spacing: 0.01em;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: var(--surface-bright);
        color: var(--on-surface);
    }
    .stTabs [aria-selected="true"] {
        background: var(--surface-bright) !important;
        color: var(--on-surface) !important;
        font-weight: 600 !important;
        box-shadow: none;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }
    .stTabs [data-baseweb="tab-border"] { display: none; }

    /* Settings bar */
    .settings-bar {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 6px 0;
    }
    .settings-badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        background: rgba(0, 244, 254, 0.1);
        border: 1px solid rgba(0, 244, 254, 0.25);
        border-radius: 9999px;
        padding: 4px 12px;
        font-size: 11px;
        color: var(--secondary);
        font-weight: 500;
    }
    .settings-badge-warn {
        background: rgba(255, 238, 166, 0.1);
        border-color: rgba(255, 238, 166, 0.25);
        color: var(--tertiary);
    }

    /* ── Metric Glow KPI Card ────────────────────────────────── */
    .glass-card {
        background: var(--surface-container);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--ghost-border);
        border-radius: 2rem;
        padding: 24px 18px;
        text-align: center;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .glass-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--accent, #c39bff), transparent);
        opacity: 1;
    }
    .glass-card::after {
        content: '';
        position: absolute;
        top: -40px; left: 50%;
        transform: translateX(-50%);
        width: 120px;
        height: 120px;
        border-radius: 50%;
        background: var(--accent, #c39bff);
        opacity: 0.06;
        filter: blur(40px);
        pointer-events: none;
    }
    .glass-card:hover {
        transform: translateY(-3px);
        border-color: rgba(195, 155, 255, 0.2);
        box-shadow: 0 24px 48px rgba(0, 0, 0, 0.4);
    }
    .glass-value {
        font-size: 32px;
        font-weight: 900;
        color: var(--on-surface);
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    .glass-label {
        font-size: 11px;
        font-weight: 500;
        color: var(--on-surface-variant);
        margin-top: 6px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    /* ── Glass Panel (chart containers) ──────────────────────── */
    .glass-panel {
        background: var(--surface-container);
        backdrop-filter: blur(20px);
        border: 1px solid var(--ghost-border);
        border-radius: 2rem;
        padding: 24px;
        margin-bottom: 16px;
    }

    /* ── Section Headers ──────────────────────────────────────── */
    .section-header {
        font-size: 12px;
        font-weight: 700;
        color: var(--on-surface-variant);
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin: 32px 0 16px 0;
        padding-bottom: 0;
        border-bottom: none;
    }

    /* ── Status Badges ────────────────────────────────────────── */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 600;
    }
    .badge-green { background: rgba(0, 244, 254, 0.12); color: #00f4fe; }
    .badge-yellow { background: rgba(255, 238, 166, 0.12); color: #ffeea6; }
    .badge-red { background: rgba(255, 110, 132, 0.12); color: #ff6e84; }
    .badge-blue { background: rgba(195, 155, 255, 0.12); color: #c39bff; }

    /* ── Data tables ──────────────────────────────────────────── */
    .stDataFrame { border-radius: 1rem; overflow: hidden; }
    div[data-testid="stDataFrame"] > div {
        border-radius: 1rem;
        background: var(--surface-container) !important;
    }

    /* ── Input styling ────────────────────────────────────────── */
    .stSelectbox > div > div,
    .stSelectbox [data-baseweb="select"] > div {
        background: var(--surface-container-high) !important;
        border: 1px solid var(--ghost-border) !important;
        border-radius: 1rem !important;
        color: var(--on-surface) !important;
    }
    .stTextInput input {
        background: var(--surface-container-high) !important;
        border: 1px solid var(--ghost-border) !important;
        color: var(--on-surface) !important;
        border-radius: 1rem !important;
    }
    .stTextInput input::placeholder {
        color: var(--on-surface-variant) !important;
    }
    .stTextInput input:focus {
        border-color: rgba(195, 155, 255, 0.4) !important;
        box-shadow: 0 0 0 1px rgba(195, 155, 255, 0.15) !important;
    }

    /* ── Button styling ───────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary), var(--primary-dim)) !important;
        color: white !important;
        border: none !important;
        border-radius: 9999px !important;
        font-weight: 600 !important;
        padding: 8px 20px !important;
        transition: all 0.25s ease !important;
    }
    .stButton > button:hover {
        box-shadow: 0 8px 24px rgba(195, 155, 255, 0.3) !important;
        transform: translateY(-1px);
    }
    /* Secondary / ghost buttons */
    .stButton > button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid var(--ghost-border) !important;
        color: var(--on-surface) !important;
    }

    /* ── Page title ────────────────────────────────────────────── */
    .page-title {
        font-size: 42px;
        font-weight: 900;
        color: var(--on-surface);
        margin-bottom: 4px;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }
    .page-subtitle {
        font-size: 14px;
        color: var(--on-surface-variant);
        margin-bottom: 24px;
        line-height: 1.5;
    }

    /* ── Timestamp footer ──────────────────────────────────────── */
    .timestamp {
        font-size: 11px;
        color: var(--on-surface-variant);
        text-align: right;
        padding: 16px 0 4px 0;
    }

    /* ── Streamlit overrides for dark consistency ──────────────── */
    .stMarkdown h5 {
        color: var(--on-surface) !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        font-size: 13px !important;
    }
    .stMarkdown p, .stMarkdown li {
        color: var(--on-surface-variant);
    }
    .stWarning, .stInfo {
        background: var(--surface-container) !important;
        border-radius: 1rem !important;
        border: 1px solid var(--ghost-border) !important;
    }
    .stSpinner > div {
        border-top-color: var(--primary) !important;
    }

    /* ── Plotly chart container fix ─────────────────────────────── */
    .stPlotlyChart {
        background: transparent !important;
        border-radius: 1rem;
    }

    /* ── Scrollbar ─────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--surface-container-low); }
    ::-webkit-scrollbar-thumb { background: var(--surface-bright); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--outline-variant); }

    /* ── Selectbox label color ─────────────────────────────────── */
    .stSelectbox label, .stTextInput label {
        color: var(--on-surface-variant) !important;
        font-size: 12px !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
    }
</style>
""", unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#adaaaa", family="Inter, sans-serif", size=12),
    margin=dict(l=40, r=20, t=36, b=40),
    xaxis=dict(gridcolor="rgba(73,72,71,0.2)", zerolinecolor="rgba(73,72,71,0.2)"),
    yaxis=dict(gridcolor="rgba(73,72,71,0.2)", zerolinecolor="rgba(73,72,71,0.2)"),
    legend=dict(bgcolor="rgba(26,25,25,0.8)", font=dict(size=11, color="#adaaaa"),
                bordercolor="rgba(73,72,71,0.15)", borderwidth=1),
    colorway=["#c39bff", "#00f4fe", "#ff6e84", "#ffeea6",
              "#924bf3", "#00e5ee", "#d73357", "#edd139"],
    hoverlabel=dict(bgcolor="#1a1919", font_size=12, font_family="Inter",
                    font_color="#ffffff", bordercolor="rgba(73,72,71,0.3)"),
)

STATUS_COLORS = {
    "On Track": "#00f4fe", "At Risk": "#ffeea6", "Off Track": "#ff6e84",
    "New": "#c39bff", "Blocked": "#924bf3",
}

PHASE_COLORS = {
    "Launch": "#00f4fe", "Verify": "#00e5ee", "Deploy": "#ff6e84",
    "Align": "#ffeea6", "Initiate and Plan": "#c39bff",
    "Initiate and Preview": "#924bf3",
    "Design & Integrate": "#00f4fe", "Not Started": "#494847",
}


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def styled_chart(fig, height=380):
    fig.update_layout(**PLOTLY_LAYOUT, height=height)
    return fig


def fmt_date(val):
    """Format date/datetime to 'Mar 25, 2026' format."""
    try:
        if val is None or val is pd.NaT or (isinstance(val, float) and pd.isna(val)):
            return ""
        if pd.isna(val):
            return ""
    except (TypeError, ValueError):
        pass
    if isinstance(val, str):
        if not val.strip() or val.lower() in ("none", "nat"):
            return ""
        try:
            val = pd.to_datetime(val)
        except Exception:
            return str(val)
    try:
        if isinstance(val, (pd.Timestamp, datetime)):
            return val.strftime("%b %d, %Y")
    except ValueError:
        return ""
    return str(val) if val else ""


def format_date_columns(df, date_cols=None):
    """Format date columns in dataframe."""
    if df.empty:
        return df
    df_copy = df.copy()
    if date_cols is None:
        date_cols = ["Due date", "Start date", "Next Go-Live Date", "Created", "SLA Due date",
                     "Started (local time)", "Finished (local time)", "Customer Requested Month"]
    for col in date_cols:
        if col in df_copy.columns:
            df_copy[col] = df_copy[col].apply(fmt_date)
    return df_copy


JIRA_BASE_URL = "https://eightfold.atlassian.net/browse"


def show_table(df, cols=None, height=400):
    """Display a dataframe with clickable Jira links and formatted dates."""
    show_df = df[cols].copy() if cols else df.copy()

    # Format date columns
    date_cols = [c for c in show_df.columns if c in
                 ["Due date", "Start date", "Next Go-Live Date", "Created", "SLA Due date",
                  "Started (local time)", "Finished (local time)", "Customer Requested Month"]]
    for col in date_cols:
        if col in show_df.columns:
            show_df[col] = show_df[col].apply(fmt_date)

    col_config = {}
    if "Key" in show_df.columns:
        show_df["Jira"] = show_df["Key"].apply(
            lambda k: f"{JIRA_BASE_URL}/{k}" if pd.notna(k) and str(k).strip() else None
        )
        col_config["Jira"] = st.column_config.LinkColumn("Jira", display_text="Open →")
    st.dataframe(show_df, use_container_width=True, height=height, column_config=col_config)


def kpi(label, value, color="#c39bff"):
    st.markdown(f"""
    <div class="glass-card" style="--accent: {color};">
        <div class="glass-value" style="color: {color};">{value}</div>
        <div class="glass-label">{label}</div>
    </div>""", unsafe_allow_html=True)


def small_kpi(label, value, color="#c39bff"):
    st.markdown(f"""
    <div class="glass-card" style="--accent: {color}; padding: 16px 10px;">
        <div class="glass-value" style="color: {color}; font-size: 24px;">{value}</div>
        <div class="glass-label" style="font-size: 10px;">{label}</div>
    </div>""", unsafe_allow_html=True)


def section(title):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


def count_status(df, pattern):
    """Count rows where Status contains pattern (handles emoji prefixes)."""
    if "Status" not in df.columns or df.empty:
        return 0
    return int(df["Status"].str.contains(pattern, case=False, na=False).sum())


def count_priority(df, pattern):
    if "Priority" not in df.columns or df.empty:
        return 0
    return int(df["Priority"].str.contains(pattern, case=False, na=False).sum())


# ═══════════════════════════════════════════════════════════════════════════════
#  TOP NAVBAR — Brand + Status + Settings
# ═══════════════════════════════════════════════════════════════════════════════

_nb_left, _nb_right = st.columns([7, 3])
with _nb_left:
    _conn_html = '<span class="settings-badge">✓ Google Sheets</span>' if SA_KEY_FOUND else (
        '<span class="settings-badge settings-badge-warn">⚠ No SA Key</span>')
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:12px;">'
        f'<span class="navbar-brand">EtherCommand</span>'
        f'{_conn_html}'
        f'</div>',
        unsafe_allow_html=True,
    )
with _nb_right:
    _r1, _r2, _r3 = st.columns([4, 3, 3])
    with _r1:
        api_key = st.text_input("Anthropic API Key", type="password",
                                value=st.session_state.get("anthropic_api_key", ""),
                                label_visibility="collapsed", placeholder="Anthropic API Key")
        if api_key:
            st.session_state["anthropic_api_key"] = api_key
    with _r2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with _r3:
        ai_label = "🤖 AI On" if st.session_state.get("anthropic_api_key") and HAS_ANTHROPIC else "🤖 AI Off"
        st.markdown(
            f'<div style="text-align:center;padding:6px 0;font-size:12px;'
            f'color:{"#00f4fe" if "On" in ai_label else "#494847"};">'
            f'{ai_label}</div>',
            unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  LOAD DATA
# ═══════════════════════════════════════════════════════════════════════════════

data = load_all()
projects_df = data["projects"]
bugs_df = data["bugs"]
ers_df = data["ers"]
milestones_df = data["milestones"]
scheduler_df = data["scheduler_log"]

AI_ENABLED = bool(st.session_state.get("anthropic_api_key")) and HAS_ANTHROPIC
ALL_EMPTY = all(df.empty for df in [projects_df, bugs_df, ers_df, milestones_df, scheduler_df])

if ALL_EMPTY:
    st.markdown('<div class="page-title">EtherCommand</div>', unsafe_allow_html=True)
    st.info("No data loaded. Place your service account JSON key in the app folder and click Refresh Data.")
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
#  CROSS-FILTERS (shared across all pages via session_state)
# ═══════════════════════════════════════════════════════════════════════════════

def _opts(df, col):
    """Get sorted unique values for a column, prepended with 'All'."""
    if col not in df.columns or df.empty:
        return ["All"]
    vals = sorted(df[col].dropna().unique().tolist())
    return ["All"] + vals


def apply_project_filters(df):
    """Apply the shared cross-filters stored in session_state to any project-like df."""
    f = df.copy()
    if st.session_state.get("f_theater", "All") != "All" and "Theater" in f.columns:
        f = f[f["Theater"] == st.session_state["f_theater"]]
    if st.session_state.get("f_customer", "All") != "All" and "Customer Name" in f.columns:
        f = f[f["Customer Name"] == st.session_state["f_customer"]]
    if st.session_state.get("f_project", "All") != "All" and "Project Name" in f.columns:
        f = f[f["Project Name"] == st.session_state["f_project"]]
    if st.session_state.get("f_status", "All") != "All" and "Status" in f.columns:
        f = f[f["Status"].str.contains(st.session_state["f_status"], case=False, na=False)]
    if st.session_state.get("f_team", "All") != "All" and "Implementing Team" in f.columns:
        f = f[f["Implementing Team"] == st.session_state["f_team"]]
    return f


def render_filters(page_name="default", show_all=True):
    """Render the top filter bar. Stores values in session_state for cross-filtering."""
    cols = st.columns(5 if show_all else 3)
    with cols[0]:
        st.session_state["f_theater"] = st.selectbox(
            "Theater", _opts(projects_df, "Theater"), key=f"filt_theater_{page_name}",
            index=_opts(projects_df, "Theater").index(st.session_state.get("f_theater", "All"))
            if st.session_state.get("f_theater", "All") in _opts(projects_df, "Theater") else 0
        )
    with cols[1]:
        st.session_state["f_customer"] = st.selectbox(
            "Customer Name", _opts(projects_df, "Customer Name"), key=f"filt_cust_{page_name}",
            index=0
        )
    with cols[2]:
        st.session_state["f_project"] = st.selectbox(
            "Project Name", _opts(projects_df, "Project Name"), key=f"filt_proj_{page_name}",
            index=0
        )
    if show_all and len(cols) > 3:
        with cols[3]:
            status_opts = ["All", "On Track", "At Risk", "Off Track", "New"]
            st.session_state["f_status"] = st.selectbox(
                "Status", status_opts, key=f"filt_status_{page_name}", index=0
            )
        with cols[4]:
            st.session_state["f_team"] = st.selectbox(
                "Implementing Team", _opts(projects_df, "Implementing Team"),
                key=f"filt_team_{page_name}", index=0
            )


# ═══════════════════════════════════════════════════════════════════════════════
#  TOP NAVIGATION TABS
# ═══════════════════════════════════════════════════════════════════════════════

TAB_NAMES = [
    "🏠 Summary", "📋 Projects", "🐛 Bugs", "💡 ERs",
    "🎯 Milestones", "📅 Timeline", "⚙️ Scheduler Logs",
]
tab_summary, tab_projects, tab_bugs, tab_ers, tab_milestones, tab_timeline, tab_scheduler = \
    st.tabs(TAB_NAMES)

# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

with tab_summary:
    st.markdown('<div class="page-title">Operational Insight</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Monitoring global project trajectories and resource allocation in real-time.</div>', unsafe_allow_html=True)

    render_filters(page_name="summary")
    fp = apply_project_filters(projects_df)
    # Also cross-filter bugs/ERs by customer/project
    fb = bugs_df.copy()
    fe = ers_df.copy()
    if st.session_state.get("f_customer", "All") != "All":
        if "Customer Name" in fb.columns:
            fb = fb[fb["Customer Name"] == st.session_state["f_customer"]]
        if "Customer Name" in fe.columns:
            fe = fe[fe["Customer Name"] == st.session_state["f_customer"]]
    if st.session_state.get("f_project", "All") != "All":
        if "Project Name" in fb.columns:
            fb = fb[fb["Project Name"] == st.session_state["f_project"]]
        if "Project Name" in fe.columns:
            fe = fe[fe["Project Name"] == st.session_state["f_project"]]

    st.markdown("")

    # ── Row 1: Main KPIs ─────────────────────────────────────────────────
    section("Implementation Overview")
    r1 = st.columns(8)
    with r1[0]:
        kpi("IMPLS", len(fp), "#c39bff")
    with r1[1]:
        kpi("On Track", count_status(fp, "On Track"), "#00f4fe")
    with r1[2]:
        kpi("At Risk", count_status(fp, "At Risk"), "#ffeea6")
    with r1[3]:
        kpi("Off Track", count_status(fp, "Off Track"), "#ff6e84")
    with r1[4]:
        kpi("New", count_status(fp, "New"), "#924bf3")
    with r1[5]:
        americas = len(fp[fp["Theater"] == "Americas"]) if "Theater" in fp.columns else 0
        small_kpi("Americas", americas, "#00f4fe")
    with r1[6]:
        emea = len(fp[fp["Theater"] == "EMEA"]) if "Theater" in fp.columns else 0
        small_kpi("EMEA", emea, "#c39bff")
    with r1[7]:
        apjc = len(fp[fp["Theater"] == "APJC"]) if "Theater" in fp.columns else 0
        small_kpi("APJC", apjc, "#ff6e84")

    st.markdown("")

    # ── Row 2: Bug & ER KPIs ─────────────────────────────────────────────
    r2 = st.columns(8)
    with r2[0]:
        small_kpi("Total ERs", len(fe), "#ffeea6")
    with r2[1]:
        small_kpi("P0 ERs", count_priority(fe, "P0"), "#ff6e84")
    with r2[2]:
        small_kpi("P1 ERs", count_priority(fe, "P1"), "#d73357")
    with r2[3]:
        small_kpi("P2 ERs", count_priority(fe, "P2"), "#ffeea6")
    with r2[4]:
        small_kpi("Total Bugs", len(fb), "#ff6e84")
    with r2[5]:
        small_kpi("P0 Bugs", count_priority(fb, "P0"), "#ff6e84")
    with r2[6]:
        small_kpi("P1 Bugs", count_priority(fb, "P1"), "#d73357")
    with r2[7]:
        p2p3 = count_priority(fb, "P2") + count_priority(fb, "P3")
        small_kpi("P2+P3 Bugs", p2p3, "#ffeea6")

    st.markdown("")

    # ── Charts Row ────────────────────────────────────────────────────────
    section("Visual Analytics")
    ch1, ch2, ch3 = st.columns(3)

    with ch1:
        st.markdown("##### IMPL by Theater")
        if "Theater" in fp.columns and not fp.empty:
            tc = fp["Theater"].value_counts().reset_index()
            tc.columns = ["Theater", "Count"]
            fig = px.pie(tc, names="Theater", values="Count", hole=0.5,
                         color_discrete_sequence=["#00f4fe", "#c39bff", "#ff6e84", "#ffeea6"])
            fig.update_traces(textinfo="label+value", textfont_size=12,
                            hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>")
            st.plotly_chart(styled_chart(fig, 340), use_container_width=True)

    with ch2:
        st.markdown("##### Implementation Team")
        if "Implementing Team" in fp.columns and not fp.empty:
            team_c = fp["Implementing Team"].value_counts().head(10).reset_index()
            team_c.columns = ["Team", "Count"]
            fig = px.pie(team_c, names="Team", values="Count", hole=0.5)
            fig.update_traces(textinfo="label+value", textfont_size=11,
                            hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>")
            st.plotly_chart(styled_chart(fig, 340), use_container_width=True)

    with ch3:
        st.markdown("##### Status by Customer")
        if "Customer Name" in fp.columns and "Status" in fp.columns and not fp.empty:
            cross = fp.groupby(["Customer Name", "Status"]).size().reset_index(name="Count")
            fig = px.bar(cross, y="Customer Name", x="Count", color="Status",
                         orientation="h", barmode="stack",
                         color_discrete_map={s: c for s, c in STATUS_COLORS.items()})
            fig.update_layout(yaxis=dict(autorange="reversed", dtick=1),
                              showlegend=True, legend=dict(orientation="h", y=1.05))
            fig.update_traces(hovertemplate="<b>%{y}</b><br>Status: %{fullData.name}<br>Count: %{x}<extra></extra>")
            st.plotly_chart(styled_chart(fig, 340), use_container_width=True)

    # ── Project Pulse (AI) ────────────────────────────────────────────────
    if AI_ENABLED:
        section("AI Executive Summary")
        if st.button("Generate Project Pulse", type="primary", key="btn_pulse"):
            with st.spinner("Claude is analyzing your portfolio…"):
                pulse = generate_project_pulse(fp, fb, milestones_df)
            st.session_state["last_pulse"] = pulse
        if "last_pulse" in st.session_state:
            st.markdown(st.session_state["last_pulse"])

    # ── NL Search ─────────────────────────────────────────────────────────
    section("Ask Your Data")
    nl_query = st.text_input("Search", placeholder="e.g. 'P1 bugs for HSBC' or 'At Risk projects in EMEA'",
                             label_visibility="collapsed")
    if nl_query and AI_ENABLED:
        with st.spinner("Analyzing…"):
            spec = parse_nl_query(nl_query, data)
            result_df, explanation = execute_nl_query(spec, data)
        st.info(f"💡 {explanation}")
        if not result_df.empty:
            show_table(result_df, height=250)
    elif nl_query:
        st.caption("Enter your Anthropic API key in the sidebar to enable AI search.")

    # ── Project Details Table ─────────────────────────────────────────────
    section("Project Details")
    detail_cols = [c for c in ["Project Name", "Customer Name", "Assignee", "Status",
                                "Project Phase", "Timeline", "Scope", "Budget",
                                "Dependencies", "Customer Sentiment",
                                "Next Go-Live Date", "Implementing Team", "Key"]
                   if c in fp.columns]
    show_table(fp, detail_cols, height=400)

    st.markdown(f'<div class="timestamp">Data as of {fmt_date(pd.Timestamp.now())}</div>',
                unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: PROJECTS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_projects:
    st.markdown('<div class="page-title">Command Center / Projects</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Managing active workflows across sectors. Track execution, priority, and fleet allocation.</div>',
                unsafe_allow_html=True)

    if projects_df.empty:
        st.warning("No project data loaded.")
    else:
        render_filters(page_name="projects")
        fp = apply_project_filters(projects_df)

        st.markdown("")
        r = st.columns(4)
        with r[0]:
            kpi("Projects", len(fp), "#c39bff")
        with r[1]:
            kpi("On Track", count_status(fp, "On Track"), "#00f4fe")
        with r[2]:
            kpi("At Risk / Off Track",
                count_status(fp, "At Risk") + count_status(fp, "Off Track"), "#ff6e84")
        with r[3]:
            teams = fp["Implementing Team"].nunique() if "Implementing Team" in fp.columns else 0
            kpi("Teams", teams, "#ffeea6")

        st.markdown("")

        ch1, ch2 = st.columns(2)
        with ch1:
            st.markdown("##### Project Health Indicators")
            health_cols = ["Timeline", "Budget", "Scope", "Dependencies", "Customer Sentiment"]
            health_data = []
            for col in health_cols:
                if col in fp.columns:
                    for val, cnt in fp[col].value_counts().items():
                        health_data.append({"Indicator": col, "Rating": str(val), "Count": cnt})
            if health_data:
                hdf = pd.DataFrame(health_data)
                fig = px.bar(hdf, x="Indicator", y="Count", color="Rating",
                             color_discrete_map={"G": "#00f4fe", "Y": "#ffeea6", "R": "#ff6e84"},
                             text="Count", barmode="stack")
                fig.update_traces(textposition="inside",
                                hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y}<extra></extra>")
                st.plotly_chart(styled_chart(fig), use_container_width=True)

        with ch2:
            st.markdown("##### Project Phase Breakdown")
            if "Project Phase" in fp.columns and not fp.empty:
                pc = fp["Project Phase"].value_counts().reset_index()
                pc.columns = ["Phase", "Count"]
                fig = px.pie(pc, names="Phase", values="Count", hole=0.5,
                             color="Phase", color_discrete_map=PHASE_COLORS)
                fig.update_traces(textinfo="label+value",
                                hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>")
                st.plotly_chart(styled_chart(fig), use_container_width=True)

        # Risk Advisor
        if AI_ENABLED:
            section("Smart Risk Advisor")
            pnames = sorted(fp["Project Name"].dropna().unique().tolist()) if "Project Name" in fp.columns else []
            if pnames:
                sel = st.selectbox("Select project", pnames, key="risk_proj_sel")
                if st.button("Analyze Risks", type="primary", key="btn_analyze_risks"):
                    with st.spinner(f"Analyzing {sel}…"):
                        risk = generate_risk_assessment(sel, projects_df, bugs_df, milestones_df)
                    st.markdown(risk)

        section("Project Details")
        cols = [c for c in ["Project Name", "Customer Name", "Assignee", "Status",
                             "Project Phase", "Theater", "Implementing Team",
                             "Timeline", "Budget", "Scope", "Dependencies",
                             "Customer Sentiment", "Next Go-Live Date", "Status Trend", "Key"]
                if c in fp.columns]
        show_table(fp, cols)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: BUGS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_bugs:
    st.markdown('<div class="page-title">Bugs & Issues</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Real-time resolution hub for high-performance engineering squads. Monitor, triage, and execute fixes.</div>',
                unsafe_allow_html=True)

    if bugs_df.empty:
        st.warning("No bugs data loaded.")
    else:
        fc = st.columns(4)
        with fc[0]:
            p = ["All"] + sorted(bugs_df["Priority"].dropna().unique().tolist()) if "Priority" in bugs_df.columns else ["All"]
            sel_p = st.selectbox("Priority", p, key="bp")
        with fc[1]:
            s = ["All"] + sorted(bugs_df["Status"].dropna().unique().tolist()) if "Status" in bugs_df.columns else ["All"]
            sel_s = st.selectbox("Status", s, key="bs")
        with fc[2]:
            pa = ["All"] + sorted(bugs_df["Product Area"].dropna().unique().tolist()) if "Product Area" in bugs_df.columns else ["All"]
            sel_pa = st.selectbox("Product Area", pa, key="bpa")
        with fc[3]:
            bc = ["All"] + sorted(bugs_df["Customer Name"].dropna().unique().tolist()) if "Customer Name" in bugs_df.columns else ["All"]
            sel_bc = st.selectbox("Customer", bc, key="bcu")

        fb = bugs_df.copy()
        if sel_p != "All" and "Priority" in fb.columns:
            fb = fb[fb["Priority"] == sel_p]
        if sel_s != "All" and "Status" in fb.columns:
            fb = fb[fb["Status"] == sel_s]
        if sel_pa != "All" and "Product Area" in fb.columns:
            fb = fb[fb["Product Area"] == sel_pa]
        if sel_bc != "All" and "Customer Name" in fb.columns:
            fb = fb[fb["Customer Name"] == sel_bc]

        # Also apply cross-filter from sidebar
        if st.session_state.get("f_customer", "All") != "All" and "Customer Name" in fb.columns:
            fb = fb[fb["Customer Name"] == st.session_state["f_customer"]]

        st.markdown("")
        r = st.columns(4)
        with r[0]:
            kpi("Total Bugs", len(fb), "#ff6e84")
        with r[1]:
            kpi("P1 Critical", count_priority(fb, "P1"), "#d73357")
        with r[2]:
            overdue = 0
            if "SLA Due date" in fb.columns:
                overdue = int(fb["SLA Due date"].dropna().lt(pd.Timestamp.now()).sum())
            kpi("SLA Overdue", overdue, "#ffeea6")
        with r[3]:
            blocked = len(fb[fb["Status"].str.contains("Blocked", case=False, na=False)]) if "Status" in fb.columns else 0
            kpi("Blocked", blocked, "#924bf3")

        st.markdown("")

        ch1, ch2 = st.columns(2)
        with ch1:
            st.markdown("##### Bugs by Priority & Status")
            if "Priority" in fb.columns and "Status" in fb.columns and not fb.empty:
                cross = fb.groupby(["Priority", "Status"]).size().reset_index(name="Count")
                fig = px.bar(cross, x="Priority", y="Count", color="Status",
                             text="Count", barmode="stack")
                fig.update_traces(textposition="inside",
                                hovertemplate="<b>Priority: %{x}</b><br>Status: %{fullData.name}<br>Count: %{y}<extra></extra>")
                st.plotly_chart(styled_chart(fig), use_container_width=True)

        with ch2:
            st.markdown("##### Bugs by Product Area")
            if "Product Area" in fb.columns and not fb.empty:
                pac = fb["Product Area"].value_counts().head(10).reset_index()
                pac.columns = ["Product Area", "Count"]
                fig = px.bar(pac, y="Product Area", x="Count", orientation="h",
                             color="Count", color_continuous_scale=["#924bf3", "#ff6e84"])
                fig.update_layout(yaxis=dict(autorange="reversed"))
                fig.update_traces(hovertemplate="<b>%{y}</b><br>Count: %{x}<extra></extra>")
                st.plotly_chart(styled_chart(fig), use_container_width=True)

        st.markdown("##### Bug Creation Trend")
        if "Created" in fb.columns and not fb.empty:
            trend = fb.dropna(subset=["Created"]).copy()
            if not trend.empty:
                trend["Month"] = trend["Created"].dt.to_period("M").astype(str)
                monthly = trend.groupby("Month").size().reset_index(name="Count")
                fig = px.area(monthly, x="Month", y="Count", color_discrete_sequence=["#c39bff"])
                fig.update_layout(xaxis_title="", yaxis_title="New Bugs")
                fig.update_traces(hovertemplate="<b>Month: %{x}</b><br>Count: %{y}<extra></extra>")
                st.plotly_chart(styled_chart(fig), use_container_width=True)

        section("Bug Details")
        cols = [c for c in ["Key", "Summary", "Priority", "Status", "Customer Name",
                             "Product Area", "POD Name", "Assignee", "SLA Due date", "Created"]
                if c in fb.columns]
        show_table(fb, cols)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: ERs
# ═══════════════════════════════════════════════════════════════════════════════

with tab_ers:
    st.markdown('<div class="page-title">Enhancement Requests</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Curate the future of <strong style="color:#c39bff">EtherCommand</strong>. Propose features, upvote high-impact requests, and track implementation evolution.</div>',
                unsafe_allow_html=True)

    if ers_df.empty:
        st.warning("No ER data loaded.")
    else:
        fc = st.columns(3)
        with fc[0]:
            ep = ["All"] + sorted(ers_df["Priority"].dropna().unique().tolist()) if "Priority" in ers_df.columns else ["All"]
            sel_ep = st.selectbox("Priority", ep, key="ep")
        with fc[1]:
            es = ["All"] + sorted(ers_df["Status"].dropna().unique().tolist()) if "Status" in ers_df.columns else ["All"]
            sel_es = st.selectbox("Status", es, key="es")
        with fc[2]:
            epa = ["All"] + sorted(ers_df["Product Area"].dropna().unique().tolist()) if "Product Area" in ers_df.columns else ["All"]
            sel_epa = st.selectbox("Product Area", epa, key="epa")

        fe = ers_df.copy()
        if sel_ep != "All" and "Priority" in fe.columns:
            fe = fe[fe["Priority"] == sel_ep]
        if sel_es != "All" and "Status" in fe.columns:
            fe = fe[fe["Status"] == sel_es]
        if sel_epa != "All" and "Product Area" in fe.columns:
            fe = fe[fe["Product Area"] == sel_epa]

        st.markdown("")
        r = st.columns(3)
        with r[0]:
            kpi("Total ERs", len(fe), "#ffeea6")
        with r[1]:
            top_imp = fe["Feature Impact"].value_counts().index[0] if "Feature Impact" in fe.columns and not fe.empty else "N/A"
            kpi("Top Impact", top_imp, "#c39bff")
        with r[2]:
            uniq_c = fe["Customer Name"].nunique() if "Customer Name" in fe.columns else 0
            kpi("Unique Customers", uniq_c, "#00f4fe")

        st.markdown("")

        ch1, ch2 = st.columns(2)
        with ch1:
            st.markdown("##### ERs by Status")
            if "Status" in fe.columns and not fe.empty:
                sc = fe["Status"].value_counts().reset_index()
                sc.columns = ["Status", "Count"]
                fig = px.bar(sc, x="Status", y="Count", color="Status", text="Count")
                fig.update_traces(textposition="outside",
                                hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>")
                st.plotly_chart(styled_chart(fig), use_container_width=True)

        with ch2:
            st.markdown("##### ERs by Feature Impact")
            if "Feature Impact" in fe.columns and not fe.empty:
                ic = fe["Feature Impact"].value_counts().reset_index()
                ic.columns = ["Impact", "Count"]
                fig = px.pie(ic, names="Impact", values="Count", hole=0.45)
                fig.update_traces(textinfo="label+value",
                                hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>")
                st.plotly_chart(styled_chart(fig), use_container_width=True)

        st.markdown("##### Top 10 Customers by ER Volume")
        if "Customer Name" in fe.columns and not fe.empty:
            cc = fe["Customer Name"].value_counts().head(10).reset_index()
            cc.columns = ["Customer", "Count"]
            fig = px.bar(cc, y="Customer", x="Count", orientation="h", text="Count",
                         color_discrete_sequence=["#c39bff"])
            fig.update_traces(textposition="outside",
                            hovertemplate="<b>%{y}</b><br>Count: %{x}<extra></extra>")
            fig.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(styled_chart(fig), use_container_width=True)

        section("ER Details")
        cols = [c for c in ["Key", "Summary", "Priority", "Status", "Customer Name",
                             "Product Area", "Feature Impact", "Customer Requested Month"]
                if c in fe.columns]
        show_table(fe, cols)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: MILESTONES
# ═══════════════════════════════════════════════════════════════════════════════

with tab_milestones:
    st.markdown('<div class="page-title">Project Milestones</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Tracking the critical path for deployment and high-performance scalability.</div>',
                unsafe_allow_html=True)

    if milestones_df.empty:
        st.warning("No milestones data loaded.")
    else:
        fc = st.columns(3)
        with fc[0]:
            ms = ["All"] + sorted(milestones_df["Status"].dropna().unique().tolist()) if "Status" in milestones_df.columns else ["All"]
            sel_ms = st.selectbox("Status", ms, key="ms")
        with fc[1]:
            mc = ["All"] + sorted(milestones_df["Customer Name"].dropna().unique().tolist()) if "Customer Name" in milestones_df.columns else ["All"]
            sel_mc = st.selectbox("Customer", mc, key="mc")
        with fc[2]:
            mp = ["All"] + sorted(milestones_df["Project Name"].dropna().unique().tolist()) if "Project Name" in milestones_df.columns else ["All"]
            sel_mp = st.selectbox("Project Name", mp, key="mp")

        fm = milestones_df.copy()
        if sel_ms != "All" and "Status" in fm.columns:
            fm = fm[fm["Status"] == sel_ms]
        if sel_mc != "All" and "Customer Name" in fm.columns:
            fm = fm[fm["Customer Name"] == sel_mc]
        if sel_mp != "All" and "Project Name" in fm.columns:
            fm = fm[fm["Project Name"] == sel_mp]

        st.markdown("")

        # KPIs
        r = st.columns(5)
        with r[0]:
            kpi("Total Milestones", len(fm), "#c39bff")
        with r[1]:
            completed = len(fm[fm["Status"].str.contains("Closed", case=False, na=False)]) if "Status" in fm.columns else 0
            kpi("Completed", completed, "#00f4fe")
        with r[2]:
            in_progress = len(fm[fm["Status"].str.contains("Progress", case=False, na=False)]) if "Status" in fm.columns else 0
            kpi("In Progress", in_progress, "#924bf3")
        with r[3]:
            if len(fm) > 0:
                completion_pct = int((completed / len(fm)) * 100)
            else:
                completion_pct = 0
            small_kpi("Completion %", f"{completion_pct}%", "#00f4fe")
        with r[4]:
            overdue = int(fm["Due date"].dropna().lt(pd.Timestamp.now()).sum()) if "Due date" in fm.columns else 0
            small_kpi("Overdue", overdue, "#ff6e84")

        st.markdown("")

        # Gantt Chart with status coloring and text on bars
        st.markdown("##### Milestone Timeline (Top 20)")
        if "Start date" in fm.columns and "Due date" in fm.columns:
            gantt = fm.dropna(subset=["Start date", "Due date"]).head(20)
            if not gantt.empty:
                # Define status colors
                gantt_colors = {"New": "#c39bff", "In Progress": "#00f4fe", "Closed": "#00e5ee"}
                gantt["color"] = gantt["Status"].map(gantt_colors).fillna("#494847")

                fig = go.Figure()
                for _, row in gantt.iterrows():
                    proj_name = row.get("Project Name", "Unknown")
                    status = row.get("Status", "Unknown")
                    customer = row.get("Customer Name", "")
                    summary = row.get("Summary", "")[:30]

                    fig.add_trace(go.Bar(
                        y=[proj_name],
                        x=[(row["Due date"] - row["Start date"]).days],
                        base=row["Start date"],
                        orientation="h",
                        name=status,
                        marker_color=gantt_colors.get(status, "#494847"),
                        text=f"{summary}" if summary else proj_name,
                        textposition="inside",
                        textfont=dict(size=10, color="white"),
                        hovertemplate=f"<b>{proj_name}</b><br>Status: {status}<br>Customer: {customer}<br>Start: " +
                                    "%{base|%b %d, %Y}<br>Duration: %{x} days<extra></extra>",
                        showlegend=False,
                    ))

                fig.update_layout(
                    barmode="overlay",
                    yaxis=dict(autorange="reversed"),
                    xaxis=dict(type="date"),
                    height=400,
                    showlegend=False,
                )
                fig.update_layout(**PLOTLY_LAYOUT)
                st.plotly_chart(fig, use_container_width=True)

        ch1, ch2 = st.columns(2)
        with ch1:
            st.markdown("##### Milestones by Status")
            if "Status" in fm.columns and not fm.empty:
                sc = fm["Status"].value_counts().reset_index()
                sc.columns = ["Status", "Count"]
                fig = px.pie(sc, names="Status", values="Count", hole=0.45)
                fig.update_traces(textinfo="label+value+percent",
                                hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>")
                st.plotly_chart(styled_chart(fig), use_container_width=True)

        with ch2:
            st.markdown("##### Milestones by Customer")
            if "Customer Name" in fm.columns and not fm.empty:
                cc = fm["Customer Name"].value_counts().head(10).reset_index()
                cc.columns = ["Customer", "Count"]
                fig = px.bar(cc, y="Customer", x="Count", orientation="h", text="Count",
                             color_discrete_sequence=["#c39bff"])
                fig.update_traces(textposition="outside",
                                hovertemplate="<b>%{y}</b><br>Count: %{x}<extra></extra>")
                fig.update_layout(yaxis=dict(autorange="reversed"))
                st.plotly_chart(styled_chart(fig), use_container_width=True)

        section("Milestone Details")
        cols = [c for c in ["Customer Name", "Project Name", "Key", "Summary",
                             "Status", "Assignee", "Start date", "Due date", "Next Go-Live Date"]
                if c in fm.columns]
        show_table(fm, cols)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: TIMELINE
# ═══════════════════════════════════════════════════════════════════════════════

with tab_timeline:
    st.markdown('<div class="page-title">Project Timeline</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Strategic roadmap for Alpha Systems. Track delivery windows and resource allocation across departments.</div>',
                unsafe_allow_html=True)

    if projects_df.empty:
        st.warning("No project data loaded.")
    else:
        # ── Filters (4 columns: Theater, Project Name, Project Phase, Summary) ──
        fc = st.columns(4)
        with fc[0]:
            tt = _opts(projects_df, "Theater")
            sel_tt = st.selectbox("Theater", tt, key="tt")
        with fc[1]:
            tp = _opts(projects_df, "Project Name")
            sel_tp = st.selectbox("Project Name", tp, key="tp")
        with fc[2]:
            tph = _opts(projects_df, "Project Phase")
            sel_tph = st.selectbox("Project Phase", tph, key="tph")
        with fc[3]:
            # Summary filter from milestones
            if not milestones_df.empty and "Summary" in milestones_df.columns:
                ts_opts = ["All"] + sorted(milestones_df["Summary"].dropna().unique().tolist())
            else:
                ts_opts = ["All"]
            sel_ts = st.selectbox("Summary", ts_opts, key="ts")

        # ── Session state for cross-filter clicks ──
        if "tl_click_rag" not in st.session_state:
            st.session_state["tl_click_rag"] = None
        if "tl_click_status" not in st.session_state:
            st.session_state["tl_click_status"] = None

        # ── Apply dropdown filters to projects ──
        tl = projects_df.copy()
        if sel_tt != "All" and "Theater" in tl.columns:
            tl = tl[tl["Theater"] == sel_tt]
        if sel_tp != "All" and "Project Name" in tl.columns:
            tl = tl[tl["Project Name"] == sel_tp]
        if sel_tph != "All" and "Project Phase" in tl.columns:
            tl = tl[tl["Project Phase"] == sel_tph]

        # Apply RAG cross-filter if set
        _rag_filter = st.session_state.get("tl_click_rag")
        if _rag_filter and isinstance(_rag_filter, dict):
            _rag_col = _rag_filter.get("col")
            _rag_val = _rag_filter.get("val")
            if _rag_col and _rag_val and _rag_col in tl.columns:
                tl = tl[tl[_rag_col].astype(str).str.contains(_rag_val, case=False, na=False)]

        # Apply milestone status cross-filter if set
        _ms_status_filter = st.session_state.get("tl_click_status")

        # Clear cross-filters button
        if st.session_state.get("tl_click_rag") or st.session_state.get("tl_click_status"):
            if st.button("✕ Clear Cross-Filters", key="tl_clear_cf"):
                st.session_state["tl_click_rag"] = None
                st.session_state["tl_click_status"] = None
                st.rerun()

        # ═══════════════════════════════════════════════════════════════════
        # ROW 1: Go-Live by Month + Project Phase Breakdown
        # ═══════════════════════════════════════════════════════════════════
        r1c1, r1c2 = st.columns([3, 2])

        with r1c1:
            st.markdown("##### Project Count by Go-Live Month")
            if "Next Go-Live Date" in tl.columns:
                gl = tl.dropna(subset=["Next Go-Live Date"]).copy()
                if not gl.empty:
                    gl["Month"] = gl["Next Go-Live Date"].dt.to_period("M").astype(str)
                    gl["Go-Live"] = gl["Next Go-Live Date"].apply(fmt_date)
                    if "Project Phase" in gl.columns:
                        # Build custom hover with project details
                        gl["_hover"] = gl.apply(
                            lambda r: (f"<b>{r.get('Project Name', '')}</b><br>"
                                       f"Go-Live: {r.get('Go-Live', '')}<br>"
                                       f"Phase: {r.get('Project Phase', '')}<br>"
                                       f"Summary: {str(r.get('Summary', ''))[:60]}"),
                            axis=1)
                        grp = gl.groupby(["Month", "Project Phase"]).agg(
                            Count=("Project Name", "size"),
                            Projects=("Project Name", lambda x: "<br>".join(
                                [f"• {n}" for n in x.head(5)] + (["…"] if len(x) > 5 else [])
                            )),
                            GoLiveDates=("Go-Live", lambda x: ", ".join(x.head(3)))
                        ).reset_index()
                        fig = px.bar(grp, y="Month", x="Count", color="Project Phase",
                                     orientation="h", barmode="stack", text="Count",
                                     color_discrete_map=PHASE_COLORS,
                                     custom_data=["Projects", "GoLiveDates"])
                        fig.update_traces(
                            textposition="inside",
                            hovertemplate=(
                                "<b>%{y}</b> · %{fullData.name}<br>"
                                "Count: %{x}<br>"
                                "<br>%{customdata[0]}<br>"
                                "<i>Go-Live: %{customdata[1]}</i>"
                                "<extra></extra>"
                            ))
                    else:
                        grp = gl.groupby("Month").size().reset_index(name="Count")
                        fig = px.bar(grp, y="Month", x="Count", orientation="h", text="Count",
                                     color_discrete_sequence=["#c39bff"])
                        fig.update_traces(textposition="outside",
                                        hovertemplate="<b>%{y}</b><br>Count: %{x}<extra></extra>")
                    fig.update_layout(
                        yaxis=dict(categoryorder="category ascending"),
                        hoverlabel=dict(bgcolor="#1a1919", font_size=12, font_family="Inter", font_color="#ffffff", bordercolor="rgba(73,72,71,0.3)"))
                    st.plotly_chart(styled_chart(fig, 420), use_container_width=True)

        with r1c2:
            st.markdown("##### Project Phase Breakdown")
            if "Project Phase" in tl.columns and not tl.empty:
                pc = tl["Project Phase"].value_counts().reset_index()
                pc.columns = ["Phase", "Count"]
                fig = px.pie(pc, names="Phase", values="Count", hole=0.5,
                             color="Phase", color_discrete_map=PHASE_COLORS)
                fig.update_traces(
                    textinfo="label+value",
                    hovertemplate="<b>%{label}</b><br>Count: %{value} (%{percent})<extra></extra>")
                fig.update_layout(
                    hoverlabel=dict(bgcolor="#1a1919", font_size=12, font_family="Inter", font_color="#ffffff", bordercolor="rgba(73,72,71,0.3)"))
                st.plotly_chart(styled_chart(fig, 420), use_container_width=True)

        # ═══════════════════════════════════════════════════════════════════
        # ROW 2: Project Health Indicators (RAG) with project names
        # ═══════════════════════════════════════════════════════════════════
        st.markdown("##### Project Health Indicators (RAG)")
        health_cols = ["Timeline", "Budget", "Scope", "Dependencies", "Customer Sentiment"]
        _rag_map = {
            "G": {"color": "#00f4fe", "label": "Green (On Track)"},
            "Y": {"color": "#ffeea6", "label": "Amber (At Risk)"},
            "R": {"color": "#ff6e84", "label": "Red (Off Track)"},
        }
        health_data = []
        for col in health_cols:
            if col in tl.columns:
                for _, row in tl.iterrows():
                    raw_val = str(row.get(col, "")).strip()
                    # Extract G/Y/R from values like "🟩G", "🟨Y", "🟥R" or just "G","Y","R"
                    rag = ""
                    for c in ["G", "Y", "R"]:
                        if c in raw_val.upper():
                            rag = c
                            break
                    if rag:
                        health_data.append({
                            "Indicator": col,
                            "RAG": rag,
                            "Color Label": _rag_map.get(rag, {}).get("label", rag),
                            "Project": row.get("Project Name", ""),
                            "Customer": row.get("Customer Name", ""),
                            "Status": row.get("Status", ""),
                        })
        if health_data:
            hdf = pd.DataFrame(health_data)
            # Aggregate for chart
            hdf_agg = hdf.groupby(["Indicator", "RAG"]).agg(
                Count=("Project", "size"),
                Projects=("Project", lambda x: "<br>".join(
                    [f"• {n}" for n in x.head(6)] + (["…"] if len(x) > 6 else [])
                ))
            ).reset_index()
            hdf_agg["Color Label"] = hdf_agg["RAG"].map(
                lambda r: _rag_map.get(r, {}).get("label", r))

            fig = px.bar(hdf_agg, x="Indicator", y="Count", color="RAG",
                         color_discrete_map={
                             "G": "#00f4fe",  # Cyan (On Track)
                             "Y": "#ffeea6",  # Gold (At Risk)
                             "R": "#ff6e84",  # Coral (Off Track)
                         },
                         text="Count", barmode="stack",
                         category_orders={"RAG": ["R", "Y", "G"]},
                         custom_data=["Color Label", "Projects"])
            fig.update_traces(
                textposition="inside",
                hovertemplate=(
                    "<b>%{x}</b> — %{customdata[0]}<br>"
                    "Count: %{y}<br><br>"
                    "%{customdata[1]}"
                    "<extra></extra>"
                ))
            fig.update_layout(
                legend_title_text="RAG Status",
                hoverlabel=dict(bgcolor="#1a1919", font_size=12, font_family="Inter", font_color="#ffffff", bordercolor="rgba(73,72,71,0.3)"),
                xaxis_title="Health Indicator",
                yaxis_title="Project Count")
            # Rename legend entries
            for trace in fig.data:
                if trace.name == "G":
                    trace.name = "🟢 Green"
                elif trace.name == "Y":
                    trace.name = "🟡 Amber"
                elif trace.name == "R":
                    trace.name = "🔴 Red"
            event = st.plotly_chart(styled_chart(fig, 400), use_container_width=True,
                                    key="tl_rag_chart", on_select="rerun")
            # Handle RAG cross-filter click
            if event and hasattr(event, "selection") and event.selection and event.selection.get("points"):
                pt = event.selection["points"][0]
                clicked_indicator = pt.get("x", "")
                clicked_rag = pt.get("legendgroup", "")
                # Map legend name back to G/Y/R
                rag_key = clicked_rag
                for k, v in {"🟢 Green": "G", "🟡 Amber": "Y", "🔴 Red": "R"}.items():
                    if k == clicked_rag:
                        rag_key = v
                        break
                if clicked_indicator and rag_key:
                    st.session_state["tl_click_rag"] = {"col": clicked_indicator, "val": rag_key}
                    st.rerun()

        # ═══════════════════════════════════════════════════════════════════
        # ROW 3: Milestone Gantt Chart (with Summary on bars, cross-filter)
        # ═══════════════════════════════════════════════════════════════════
        st.markdown("##### Milestone Gantt Chart")
        _gantt_status_colors = {
            "Closed": "#00f4fe",       # Cyan
            "In Progress": "#c39bff",  # Primary purple
            "New": "#ffeea6",          # Gold
            "Waiting for customer": "#924bf3",  # Purple dim
        }
        if not milestones_df.empty and "Start date" in milestones_df.columns and "Due date" in milestones_df.columns:
            # Filter milestones by the same projects
            if "Project Name" in tl.columns and "Project Name" in milestones_df.columns:
                project_names = tl["Project Name"].dropna().unique()
                mg = milestones_df[milestones_df["Project Name"].isin(project_names)]
            else:
                mg = milestones_df
            # Apply Summary filter
            if sel_ts != "All" and "Summary" in mg.columns:
                mg = mg[mg["Summary"] == sel_ts]
            # Apply milestone status cross-filter
            if _ms_status_filter and "Status" in mg.columns:
                mg = mg[mg["Status"].str.contains(_ms_status_filter, case=False, na=False)]

            gantt = mg.dropna(subset=["Start date", "Due date"]).copy()
            # Remove rows where start == end (zero-duration)
            gantt = gantt[gantt["Start date"] < gantt["Due date"]]
            gantt = gantt.head(25)

            if not gantt.empty:
                # Build bar label: "ProjectName | Summary (Status)"
                gantt["_bar_label"] = gantt.apply(
                    lambda r: f"{str(r.get('Summary', ''))[:35]}" if pd.notna(r.get("Summary")) else str(r.get("Project Name", ""))[:30],
                    axis=1)
                gantt["_start_fmt"] = gantt["Start date"].apply(fmt_date)
                gantt["_end_fmt"] = gantt["Due date"].apply(fmt_date)

                fig = px.timeline(
                    gantt, x_start="Start date", x_end="Due date",
                    y="Project Name", color="Status",
                    color_discrete_map=_gantt_status_colors,
                    text="_bar_label",
                    custom_data=["Summary", "Status", "_start_fmt", "_end_fmt", "Customer Name"])
                fig.update_traces(
                    textposition="inside",
                    insidetextanchor="middle",
                    textfont=dict(size=10, color="#0e0e0e"),
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Summary: %{customdata[0]}<br>"
                        "Status: %{customdata[1]}<br>"
                        "Start: %{customdata[2]}<br>"
                        "End: %{customdata[3]}<br>"
                        "Customer: %{customdata[4]}"
                        "<extra></extra>"
                    ))
                fig.update_layout(
                    yaxis=dict(autorange="reversed"),
                    hoverlabel=dict(bgcolor="#1a1919", font_size=12, font_family="Inter", font_color="#ffffff", bordercolor="rgba(73,72,71,0.3)"),
                    legend_title_text="Status")
                event_gantt = st.plotly_chart(styled_chart(fig, 500), use_container_width=True,
                                              key="tl_gantt_chart", on_select="rerun")
                # Handle Gantt cross-filter click
                if event_gantt and hasattr(event_gantt, "selection") and event_gantt.selection and event_gantt.selection.get("points"):
                    pt = event_gantt.selection["points"][0]
                    clicked_status = pt.get("legendgroup", "")
                    if clicked_status:
                        st.session_state["tl_click_status"] = clicked_status
                        st.rerun()

        # ═══════════════════════════════════════════════════════════════════
        # Project Details Table
        # ═══════════════════════════════════════════════════════════════════
        section("Project Details")
        cols = [c for c in ["Project Name", "Customer Name", "Status", "Project Phase",
                             "Theater", "Next Go-Live Date", "Timeline", "Budget",
                             "Scope", "Dependencies", "Customer Sentiment",
                             "Implementing Team", "Key"]
                if c in tl.columns]
        show_table(tl, cols, height=500)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE: SCHEDULER LOGS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_scheduler:
    st.markdown('<div class="page-title">Scheduler Logs</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Data rebuild monitoring and automation health.</div>',
                unsafe_allow_html=True)

    if scheduler_df.empty:
        st.warning("No scheduler log data loaded.")
    else:
        r = st.columns(4)
        with r[0]:
            kpi("Total Runs", len(scheduler_df), "#c39bff")
        with r[1]:
            s_ok = len(scheduler_df[scheduler_df["Status"] == "success"]) if "Status" in scheduler_df.columns else 0
            kpi("Successful", s_ok, "#00f4fe")
        with r[2]:
            s_err = len(scheduler_df[scheduler_df["Status"].str.contains("error|fail", case=False, na=False)]) if "Status" in scheduler_df.columns else 0
            kpi("Errors", s_err, "#ff6e84")
        with r[3]:
            avg_d = f"{scheduler_df['Duration (s)'].mean():.1f}s" if "Duration (s)" in scheduler_df.columns else "N/A"
            kpi("Avg Duration", avg_d, "#ffeea6")

        st.markdown("")

        ch1, ch2 = st.columns(2)
        with ch1:
            st.markdown("##### Run Status Distribution")
            if "Status" in scheduler_df.columns and not scheduler_df.empty:
                sc = scheduler_df["Status"].value_counts().reset_index()
                sc.columns = ["Status", "Count"]
                fig = px.pie(sc, names="Status", values="Count",
                             color="Status",
                             color_discrete_map={"success": "#00f4fe", "error": "#ff6e84", "info": "#c39bff"},
                             hole=0.45)
                fig.update_traces(textinfo="label+value+percent",
                                hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>")
                st.plotly_chart(styled_chart(fig), use_container_width=True)

        with ch2:
            st.markdown("##### Run Duration Over Time")
            if "Started (local time)" in scheduler_df.columns and "Duration (s)" in scheduler_df.columns:
                dd = scheduler_df.dropna(subset=["Started (local time)", "Duration (s)"])
                dd = dd[dd["Duration (s)"] > 0].sort_values("Started (local time)")
                if not dd.empty:
                    fig = px.scatter(dd, x="Started (local time)", y="Duration (s)",
                                     color="Status", size="Duration (s)",
                                     color_discrete_map={"success": "#00f4fe", "error": "#ff6e84", "info": "#c39bff"})
                    fig.update_traces(hovertemplate="<b>Time: %{x}</b><br>Duration: %{y}s<br>Status: %{fullData.name}<extra></extra>")
                    st.plotly_chart(styled_chart(fig), use_container_width=True)

        section("Recent Runs")
        recent = scheduler_df.sort_values("Started (local time)", ascending=False).head(100) \
            if "Started (local time)" in scheduler_df.columns else scheduler_df.head(100)

        # Format dates in recent logs
        recent_display = recent.copy()
        for col in ["Started (local time)", "Finished (local time)"]:
            if col in recent_display.columns:
                recent_display[col] = recent_display[col].apply(fmt_date)

        cols = [c for c in ["Started (local time)", "Finished (local time)",
                             "Duration (s)", "Status", "Error Message", "Details"]
                if c in recent_display.columns]
        st.dataframe(recent_display[cols] if cols else recent_display, use_container_width=True, height=400)

    st.markdown(f'<div class="timestamp">Data as of {fmt_date(pd.Timestamp.now())}</div>',
                unsafe_allow_html=True)
