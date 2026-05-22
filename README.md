# Codex — Streamlit Deployment Guide

## Deploy in 4 steps (all free)

---

### Step 1 — Put this on GitHub
1. Go to github.com → New repository → name it `codex-analyst`
2. Upload all files from this folder
3. Commit

---

### Step 2 — Deploy on Streamlit Cloud
1. Go to share.streamlit.io → Sign in with GitHub
2. Click "New app"
3. Choose your `codex-analyst` repo
4. Main file: `app.py`
5. Click Deploy

---

### Step 3 — Add your secrets
In Streamlit Cloud → your app → Settings → Secrets

Paste this and fill in your values:

```toml
ANTHROPIC_API_KEY = "sk-ant-api03-your-key-here"
SNOWFLAKE_TOKEN   = "eyJ-your-token-here"

[users]
"tiru@flightschool.com"       = { name = "Tiru",        role = "management" }
"john@flightschool.com"       = { name = "John Smith",  role = "instructor" }
"sarah@flightschool.com"      = { name = "Sarah Jones", role = "ops"        }
"mike@flightschool.com"       = { name = "Mike Brown",  role = "student"    }
```

---

### Step 4 — Share the URL
Streamlit gives you: `https://your-app-name.streamlit.app`
Send that to your team. Done.

---

## Adding/removing users
Streamlit Cloud → App → Settings → Secrets → edit [users] section → Save
App restarts automatically in ~10 seconds.

## Valid roles
`management` | `instructor` | `ops` | `student`
