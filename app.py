import streamlit as st
import requests
import json

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Codex — Flight Ops Intelligence",
    page_icon="✈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ─────────────────────────────────────────────────────────────────
MCP_URL = "https://ip82923.us-east-2.aws.snowflakecomputing.com/api/v2/databases/FSP_DWH/schemas/DWH_REPORTS/mcp-servers/FLIGHT_OPS_MCP"

ROLES = {
    "management": {
        "label": "Management",
        "icon": "◈",
        "color": "#f59e0b",
        "tag": "Full org access",
        "suggestions": [
            "Show Hobbs hours by location this week",
            "Which locations have at-risk students?",
            "Compare all locations by flight hours",
            "How many students are behind on pace?",
        ],
        "prompt": lambda name: f"""You are Codex, the Flight Operations Intelligence Analyst.
You are speaking with {name} — Management.
ACCESS: Full visibility — all locations, instructors, students, Hobbs hours, fleet (320 aircraft), reservations.
RULES: Always query live data via MCP tools. Present multi-row results as markdown tables. Lead with numbers, follow with 1–2 sentence insight. Flag anomalies proactively.
At-risk: 🔴 Danger = pace < 0.70 or past graduation | 🟡 At Risk = 0.70–0.95 | 🟢 On Track = ≥ 0.95. Filter ground-only enrollments.""",
    },
    "instructor": {
        "label": "Instructor",
        "icon": "✈",
        "color": "#38bdf8",
        "tag": "Your students only",
        "suggestions": [
            "How are my students doing?",
            "Which of my students are at risk?",
            "Who has the most lessons remaining?",
            "Show students behind on their pace",
        ],
        "prompt": lambda name: f"""You are Codex, the Flight Operations Intelligence Analyst.
You are speaking with {name} — Flight Instructor.
ACCESS: SCOPED — only students assigned to or who have flown with instructor "{name}". Never show other instructors' students.
RULES: Scope all queries to "{name}". Show pace ratio, lessons completed/remaining, projected graduation. Classify: 🔴 Danger (pace < 0.70 or past grad) | 🟡 At Risk (0.70–0.95) | 🟢 On Track (≥ 0.95). Filter ground-only enrollments. Lead with summary count, then detail table. Always use MCP tools.""",
    },
    "ops": {
        "label": "Ops Manager",
        "icon": "⬡",
        "color": "#a78bfa",
        "tag": "Fleet · locations · scheduling",
        "suggestions": [
            "Show today's Hobbs hours by location",
            "Which location is busiest this week?",
            "How many reservations are scheduled today?",
            "At-risk student count by location",
        ],
        "prompt": lambda name: f"""You are Codex, the Flight Operations Intelligence Analyst.
You are speaking with {name} — Operations Manager.
ACCESS: Fleet (320 aircraft), Hobbs hours, reservations, location-level student metrics.
RULES: Focus on operational intelligence — fleet utilization, Hobbs totals, location comparisons, scheduling. Hobbs tables: Location + Hours + Day Total row, rounded to 1 decimal. Use — for zero-hour locations. Flag anomalies. Always use MCP tools.""",
    },
    "student": {
        "label": "Student",
        "icon": "◉",
        "color": "#34d399",
        "tag": "Your training only",
        "suggestions": [
            "How am I doing in my training?",
            "Am I on track to graduate on time?",
            "How many lessons do I have left?",
            "What is my current pace ratio?",
        ],
        "prompt": lambda name: f"""You are Codex, the Flight Operations Intelligence Analyst.
You are speaking with {name} — Student.
ACCESS: SCOPED — only data for student "{name}". Never show other students' data.
RULES: Show enrollment, pace ratio (explain in plain language), lessons completed, remaining, projected graduation. If asked about org-wide data, politely decline. Keep tone encouraging. Always use MCP tools.""",
    },
}

WELCOME = {
    "management": lambda n: f"Welcome back, {n}. Full organizational visibility is active — all locations, instructors, and students. What would you like to see?",
    "instructor":  lambda n: f"Welcome, {n}. I'm scoped to your students only. Ask me how they're doing, who's at risk, or who has the most lessons remaining.",
    "ops":         lambda n: f"Welcome, {n}. Live fleet and location data is ready. Try asking about today's Hobbs hours or reservation counts.",
    "student":     lambda n: f"Welcome, {n}. I can show your training progress, current pace, and projected graduation date. What would you like to know?",
}

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=DM+Mono:wght@400;500&display=swap');

  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
  .stApp { background: #07090f; }

  /* Hide default Streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding: 0 !important; max-width: 100% !important; }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: #0b0f1a !important;
    border-right: 1px solid rgba(255,255,255,0.05) !important;
  }
  [data-testid="stSidebar"] > div { padding: 20px 16px !important; }

  /* Chat messages */
  [data-testid="stChatMessage"] { background: transparent !important; }
  [data-testid="stChatMessageContent"] { background: rgba(255,255,255,0.03) !important; border: 1px solid rgba(255,255,255,0.07) !important; border-radius: 4px 14px 14px 14px !important; color: #cbd5e1 !important; }

  /* Chat input */
  [data-testid="stChatInput"] textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
  }

  /* Text input */
  .stTextInput input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
  }

  /* Buttons */
  .stButton button {
    background: linear-gradient(135deg, #f59e0b, #f59e0baa) !important;
    color: #000 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
  }

  /* Tables */
  table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
  th { padding: 7px 12px; text-align: left; background: rgba(255,255,255,0.03); font-size: 0.75rem; letter-spacing: 0.06em; text-transform: uppercase; font-weight: 700; }
  td { padding: 7px 12px; color: #cbd5e1; border-bottom: 1px solid rgba(255,255,255,0.04); }

  /* Error box */
  .error-box {
    background: rgba(239,68,68,0.08);
    border: 1px solid rgba(239,68,68,0.25);
    border-radius: 8px;
    padding: 10px 14px;
    color: #f87171;
    font-size: 0.85rem;
    margin-top: 8px;
  }

  /* Role chip */
  .role-chip {
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 20px;
  }

  /* Suggestion button */
  .suggestion { color: #4b5563; font-size: 0.75rem; cursor: pointer; }
  .suggestion:hover { color: #f59e0b; }

  /* Live dot */
  .live-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 7px #22c55e; margin-right: 6px; vertical-align: middle; }
</style>
""", unsafe_allow_html=True)


# ── Auth helpers ──────────────────────────────────────────────────────────────
def lookup_user(email: str):
    """Check email against secrets-based user registry. Returns (name, role) or None."""
    try:
        users = st.secrets.get("users", {})
        email_lower = email.strip().lower()
        for registered_email, info in users.items():
            if registered_email.lower() == email_lower:
                return info["name"], info["role"]
    except Exception:
        pass
    return None, None


# ── Anthropic API call ────────────────────────────────────────────────────────
def call_codex(system_prompt: str, messages: list) -> str:
    """Call Anthropic API with MCP server attached. Returns assistant reply text."""
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    snowflake_token = st.secrets.get("SNOWFLAKE_TOKEN", "")

    if not api_key:
        return "⚠️ ANTHROPIC_API_KEY not configured. Ask your administrator."

    mcp_server = {"type": "url", "name": "flight-ops-enterprise", "url": MCP_URL}
    if snowflake_token:
        mcp_server["authorization_token"] = snowflake_token

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1500,
        "system": system_prompt,
        "messages": messages,
        "mcp_servers": [mcp_server],
    }

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "anthropic-beta": "mcp-client-2025-04-04",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        data = resp.json()
        if not resp.ok:
            return f"⚠️ API error: {data.get('error', {}).get('message', 'Unknown error')}"

        return "\n".join(
            b["text"] for b in data.get("content", []) if b.get("type") == "text"
        ) or "No response. Please try rephrasing."

    except requests.Timeout:
        return "⚠️ Request timed out — Snowflake may be slow. Please try again."
    except Exception as e:
        return f"⚠️ Error: {str(e)}"


# ── Session state init ────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "user_role" not in st.session_state:
    st.session_state.user_role = ""
if "messages" not in st.session_state:
    st.session_state.messages = []      # display messages
if "api_history" not in st.session_state:
    st.session_state.api_history = []   # API message history


# ── LOGIN SCREEN ──────────────────────────────────────────────────────────────
if not st.session_state.authenticated:
    # Centre the login form
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)

        # Wordmark
        st.markdown("""
        <div style='text-align:center;margin-bottom:36px'>
          <div style='font-size:2.8rem;font-weight:800;letter-spacing:0.24em;color:#f8fafc;line-height:1'>CODEX</div>
          <div style='font-size:0.62rem;letter-spacing:0.28em;color:#374151;text-transform:uppercase;margin-top:6px'>Flight Operations Intelligence</div>
          <div style='width:40px;height:2px;background:linear-gradient(90deg,transparent,#f59e0b,transparent);margin:14px auto 0'></div>
        </div>
        """, unsafe_allow_html=True)

        # Role preview — read only
        role_chips_html = "<div style='display:flex;gap:6px;justify-content:center;margin-bottom:28px;flex-wrap:wrap'>"
        for r in ROLES.values():
            role_chips_html += f"""<div style='display:flex;align-items:center;gap:5px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:4px 10px'>
              <span style='color:{r["color"]};font-size:0.8rem'>{r["icon"]}</span>
              <span style='font-size:0.65rem;color:{r["color"]};font-weight:700;letter-spacing:0.05em;text-transform:uppercase'>{r["label"]}</span>
            </div>"""
        role_chips_html += "</div>"
        st.markdown(role_chips_html, unsafe_allow_html=True)

        # Email input
        st.markdown("<div style='font-size:0.65rem;letter-spacing:0.14em;color:#374151;text-transform:uppercase;margin-bottom:6px'>Work email</div>", unsafe_allow_html=True)
        email = st.text_input("", placeholder="you@flightschool.com", label_visibility="collapsed", key="login_email")

        if st.button("Access Codex →", use_container_width=True):
            if email.strip():
                name, role = lookup_user(email)
                if name:
                    st.session_state.authenticated = True
                    st.session_state.user_name = name
                    st.session_state.user_role = role
                    st.session_state.messages = [{"from": "ai", "text": WELCOME[role](name)}]
                    st.session_state.api_history = []
                    st.rerun()
                else:
                    st.markdown('<div class="error-box">🚫 Access denied. Your email is not registered in Codex.<br>Contact your administrator to get access.</div>', unsafe_allow_html=True)

        st.markdown("<div style='text-align:center;margin-top:20px;font-size:0.62rem;color:#1f2937;text-transform:uppercase;letter-spacing:0.08em'>Powered by Anthropic · Live Snowflake FSP_DWH</div>", unsafe_allow_html=True)

    st.stop()


# ── CHAT SCREEN ───────────────────────────────────────────────────────────────
role_id   = st.session_state.user_role
user_name = st.session_state.user_name
role      = ROLES[role_id]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown("""
    <div style='margin-bottom:20px'>
      <div style='font-size:1.1rem;font-weight:800;letter-spacing:0.22em;color:#f8fafc'>CODEX</div>
      <div style='font-size:0.55rem;letter-spacing:0.2em;color:#1f2937;text-transform:uppercase;margin-top:2px'>Ops Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    # Role chip
    st.markdown(f"""
    <div class="role-chip" style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08)">
      <div style='display:flex;align-items:center;gap:5px;margin-bottom:4px'>
        <span style='color:{role["color"]}'>{role["icon"]}</span>
        <span style='font-size:0.68rem;font-weight:700;color:{role["color"]};letter-spacing:0.07em;text-transform:uppercase'>{role["label"]}</span>
      </div>
      <div style='font-size:0.85rem;color:#e2e8f0;font-weight:600;margin-bottom:2px'>{user_name}</div>
      <div style='font-size:0.67rem;color:#4b5563'>{role["tag"]}</div>
    </div>
    """, unsafe_allow_html=True)

    # Live indicator
    st.markdown(f"""
    <div style='display:flex;align-items:center;margin-bottom:20px'>
      <span class="live-dot"></span>
      <span style='font-size:0.6rem;color:#374151;letter-spacing:0.07em;font-family:monospace'>LIVE · FSP_DWH</span>
    </div>
    """, unsafe_allow_html=True)

    # Suggestions
    st.markdown("<div style='font-size:0.6rem;letter-spacing:0.12em;color:#1f2937;text-transform:uppercase;margin-bottom:8px'>Quick asks</div>", unsafe_allow_html=True)
    for suggestion in role["suggestions"]:
        if st.button(suggestion, key=f"sug_{suggestion}", use_container_width=True):
            st.session_state._prefill = suggestion

    st.markdown("<div style='margin-top:auto'></div>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color:rgba(255,255,255,0.05);margin:20px 0'>", unsafe_allow_html=True)

    if st.button("← Sign Out", use_container_width=True, key="signout"):
        for key in ["authenticated", "user_name", "user_role", "messages", "api_history"]:
            st.session_state[key] = False if key == "authenticated" else "" if key in ["user_name", "user_role"] else []
        st.rerun()

# ── Chat messages ─────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message("user" if msg["from"] == "user" else "assistant"):
        st.markdown(msg["text"])

# ── Chat input ────────────────────────────────────────────────────────────────
prefill = st.session_state.pop("_prefill", "") if hasattr(st.session_state, "_prefill") else ""
user_input = st.chat_input(
    "Ask about your students…" if role_id == "instructor" else
    "Ask about your training…" if role_id == "student" else
    "Ask Codex anything…"
) or prefill

if user_input:
    # Show user message
    st.session_state.messages.append({"from": "user", "text": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Build API history
    st.session_state.api_history.append({"role": "user", "content": user_input})

    # Call Codex
    with st.chat_message("assistant"):
        with st.spinner("Querying Snowflake…"):
            reply = call_codex(role["prompt"](user_name), st.session_state.api_history)

        st.markdown(reply)
        st.session_state.messages.append({"from": "ai", "text": reply})
        st.session_state.api_history.append({"role": "assistant", "content": reply})
