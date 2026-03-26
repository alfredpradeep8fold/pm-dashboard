"""
data_loader.py — Live Google Sheets reader (read-only).

Auto-detects a service account JSON key file in the app directory.
Falls back to public CSV export if no key is found.
"""

import io
import os
import json
import glob as glob_module
import logging
import pandas as pd
import streamlit as st
import requests

logger = logging.getLogger(__name__)

# ── Google Sheet IDs ─────────────────────────────────────────────────────────
JIRA_SHEET_ID = "1_Y1yl7nY0YWZ2o5pebCu19Zx9dEy0mD5xscId7I2aj8"
MILESTONE_SHEET_ID = "1iIQEPa4ZnH1k9Z_tkoxN_6fPnJy0JakJkuu7638NlKc"

EXPORT_TEMPLATE = (
    "https://docs.google.com/spreadsheets/d/{sheet_id}"
    "/gviz/tq?tqx=out:csv&sheet={tab_name}"
)

# ── Try importing gspread (optional dependency) ─────────────────────────────
try:
    import gspread
    from google.oauth2.service_account import Credentials
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False


# ── Auto-detect service account key file ────────────────────────────────────
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_SA_CREDS = None  # Will hold parsed JSON dict if found
_SA_CREDS_PATH = None
_SA_EMAIL = None


def _load_from_streamlit_secrets():
    """Try loading service account credentials from st.secrets (Streamlit Cloud)."""
    global _SA_CREDS, _SA_CREDS_PATH, _SA_EMAIL
    try:
        if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
            sa = st.secrets["gcp_service_account"]
            # st.secrets returns an AttrDict; convert to plain dict
            _SA_CREDS = dict(sa)
            _SA_CREDS_PATH = "streamlit_secrets"
            _SA_EMAIL = _SA_CREDS.get("client_email")
            logger.info("Loaded service account from st.secrets")
            return _SA_CREDS
    except Exception:
        pass
    return None


def _find_service_account_key():
    """Search for a service account JSON key file in the app directory."""
    global _SA_CREDS, _SA_CREDS_PATH, _SA_EMAIL
    if _SA_CREDS is not None:
        return _SA_CREDS

    # 1) Try Streamlit Cloud secrets first
    found = _load_from_streamlit_secrets()
    if found:
        return found

    # 2) Fall back to local JSON file search
    search_dirs = [_APP_DIR, os.path.dirname(_APP_DIR)]
    for d in search_dirs:
        for fpath in glob_module.glob(os.path.join(d, "*.json")):
            try:
                with open(fpath) as f:
                    data = json.load(f)
                if data.get("type") == "service_account" and "client_email" in data:
                    _SA_CREDS = data
                    _SA_CREDS_PATH = fpath
                    _SA_EMAIL = data["client_email"]
                    logger.info(f"Found service account key: {fpath}")
                    return _SA_CREDS
            except Exception:
                continue
    return None

# Run auto-detection on import
_find_service_account_key()

# Expose for app.py
SA_KEY_FOUND = _SA_CREDS is not None
SA_EMAIL = _SA_EMAIL
SA_KEY_PATH = _SA_CREDS_PATH


# ═══════════════════════════════════════════════════════════════════════════════
#  METHOD 1 — Public CSV export (no auth)
# ═══════════════════════════════════════════════════════════════════════════════

def _build_url(sheet_id: str, tab_name: str) -> str:
    return EXPORT_TEMPLATE.format(sheet_id=sheet_id, tab_name=tab_name)


@st.cache_data(ttl=300, show_spinner="Fetching live data from Google Sheets…")
def _fetch_csv_public(sheet_id: str, tab_name: str) -> pd.DataFrame:
    url = _build_url(sheet_id, tab_name)
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return pd.read_csv(io.StringIO(resp.text))
    except Exception:
        return pd.DataFrame()


# ═══════════════════════════════════════════════════════════════════════════════
#  METHOD 2 — Service Account (gspread)
# ═══════════════════════════════════════════════════════════════════════════════

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


@st.cache_data(ttl=300, show_spinner="Fetching live data via service account…")
def _fetch_service_account(_creds_json_str: str, sheet_id: str, tab_name: str) -> tuple:
    """Returns (DataFrame, error_string_or_None). No st.* calls inside cache."""
    try:
        creds_json = json.loads(_creds_json_str)
        creds = Credentials.from_service_account_info(creds_json, scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(tab_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data), None
    except Exception as e:
        err = str(e)
        if "403" in err or "PERMISSION_DENIED" in err:
            return pd.DataFrame(), (
                f"Permission denied for '{tab_name}'. "
                "Share the sheet with the service account email as Viewer."
            )
        return pd.DataFrame(), f"Error loading '{tab_name}': {err}"


# ═══════════════════════════════════════════════════════════════════════════════
#  UNIFIED FETCH
# ═══════════════════════════════════════════════════════════════════════════════

def _fetch(sheet_id: str, tab_name: str) -> pd.DataFrame:
    """Fetch a sheet tab. Uses service account if key found, else public URL."""
    # Prefer service account if available
    creds_json = _SA_CREDS
    # Also check session state (for uploaded keys via sidebar)
    if not creds_json and st.session_state.get("sa_creds_json"):
        try:
            creds_json = json.loads(st.session_state["sa_creds_json"])
        except Exception:
            pass

    if creds_json and HAS_GSPREAD:
        creds_str = json.dumps(creds_json)
        df, err = _fetch_service_account(creds_str, sheet_id, tab_name)
        if err:
            st.warning(f"⚠️ {err}")
        return df
    else:
        return _fetch_csv_public(sheet_id, tab_name)


# ═══════════════════════════════════════════════════════════════════════════════
#  PUBLIC LOADER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def load_projects() -> pd.DataFrame:
    df = _fetch(JIRA_SHEET_ID, "Projects")
    if df.empty:
        return df
    if "Record Type" in df.columns:
        df = df[df["Record Type"] == "Project"].copy()
    # Parse date columns
    for col in ["Next Go-Live Date", "Created", "Updated", "Due date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    # Parse any numeric columns if present
    for col in ["Eightfold UAT Score"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_resources() -> pd.DataFrame:
    df = _fetch(JIRA_SHEET_ID, "Projects")
    if df.empty:
        return df
    if "Record Type" in df.columns:
        df = df[df["Record Type"] == "Resource"].copy()
    return df


def load_bugs() -> pd.DataFrame:
    df = _fetch(JIRA_SHEET_ID, "Bugs")
    if df.empty:
        return df
    for col in ["Created", "Updated", "Due date", "SLA Due date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def load_ers() -> pd.DataFrame:
    df = _fetch(JIRA_SHEET_ID, "ERs")
    if df.empty:
        return df
    for col in ["Created", "Updated", "Due date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def load_scheduler_log() -> pd.DataFrame:
    df = _fetch(JIRA_SHEET_ID, "Scheduler_Log")
    if df.empty:
        return df
    for col in ["Started (local time)", "Finished (local time)"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    if "Duration (ms)" in df.columns:
        df["Duration (ms)"] = pd.to_numeric(df["Duration (ms)"], errors="coerce")
        df["Duration (s)"] = df["Duration (ms)"] / 1000
    return df


def load_milestones() -> pd.DataFrame:
    df = _fetch(MILESTONE_SHEET_ID, "Sheet1")
    if df.empty:
        return df
    for col in ["Due date", "Start date", "Next Go-Live Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def load_all() -> dict[str, pd.DataFrame]:
    """Load every dataset live from Google Sheets."""
    return {
        "projects": load_projects(),
        "resources": load_resources(),
        "bugs": load_bugs(),
        "ers": load_ers(),
        "scheduler_log": load_scheduler_log(),
        "milestones": load_milestones(),
    }
