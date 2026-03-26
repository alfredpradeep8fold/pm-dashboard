# Deploying PM Command Center to Streamlit Community Cloud

## Prerequisites
- A GitHub account
- Your Google service account JSON key file
- The email addresses of people you want to grant access

---

## Step 1: Push to GitHub

1. Create a **private** repository on GitHub (e.g., `pm-dashboard`)
2. From your `pm_dashboard/` folder, run:

```bash
git init
git add .
git commit -m "Initial commit — PM Command Center"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/pm-dashboard.git
git push -u origin main
```

> The `.gitignore` already excludes your service account JSON key, `venv/`, and other sensitive files.

---

## Step 2: Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
2. Click **"New app"**
3. Select your repo, branch (`main`), and main file path: `app.py`
4. Click **"Deploy"**

---

## Step 3: Add Secrets (Service Account Key)

1. In your deployed app, click **"Settings"** (⚙️ gear icon, bottom-right)
2. Go to the **"Secrets"** tab
3. Paste the contents of your service account key in this format:

```toml
[gcp_service_account]
type = "service_account"
project_id = "project-dashboard-491307"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_KEY_HERE\n-----END PRIVATE KEY-----\n"
client_email = "projectdashboard@project-dashboard-491307.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/projectdashboard%40project-dashboard-491307.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
```

4. Click **"Save"** — the app will reboot and connect to Google Sheets automatically.

> See `secrets.toml.example` for a full template.

---

## Step 4: Restrict Access (Allow Only Certain Users)

Streamlit Community Cloud supports **email-based authentication**. To restrict who can view the app:

### Option A: Via Streamlit Cloud Dashboard (Easiest)
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Find your app and click the **"..."** menu → **"Settings"**
3. Under **"Sharing"**, switch from **"Public"** to **"Invite-only"**
4. Add the email addresses of people you want to allow (they'll sign in via Google/GitHub/email)

### Option B: Via App-Level Password Gate
Add a simple password check at the top of `app.py` (already compatible):

```python
# Add this near the top of app.py, after imports
def check_password():
    """Simple password gate for the app."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        pwd = st.text_input("Enter access password:", type="password")
        if pwd == st.secrets.get("app_password", ""):
            st.session_state.authenticated = True
            st.rerun()
        elif pwd:
            st.error("Incorrect password")
        st.stop()

check_password()
```

Then add to your Secrets: `app_password = "your-shared-password"`

---

## Quick Reference

| What | Where |
|------|-------|
| App URL | `https://your-app.streamlit.app` |
| Manage app | [share.streamlit.io](https://share.streamlit.io) |
| Edit secrets | App Settings → Secrets |
| View logs | App Settings → Logs |
| Restrict access | App Settings → Sharing → Invite-only |

---

## Troubleshooting

- **"No data loaded"** → Check that your service account email has Viewer access to both Google Sheets
- **App crashes on boot** → Check the Logs tab in Streamlit Cloud for the error
- **Slow first load** → Normal — Streamlit Cloud cold-starts take ~30 seconds; subsequent loads use cache
