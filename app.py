
import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
import io
import re
import pytz
from supabase import create_client

st.set_page_config(
    page_title="RapidSurge Warehouse",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@500;600&display=swap');
/* Force sidebar to stay open on desktop only */
[data-testid="collapsedControl"] {
    display: none !important;
}
@media (min-width: 768px) {
    section[data-testid="stSidebar"] {
        min-width: 250px !important;
        width: 250px !important;
    }
}
/* Reduce top padding */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
}

/* Reduce sidebar padding */
section[data-testid="stSidebar"] {
    padding-top: 0.5rem !important;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 0.5rem !important;
}

/* Reduce gap between elements */
.element-container {
    margin-bottom: 0.3rem !important;
}

/* Reduce button height */
.stButton > button {
    padding: 0.3rem 0.5rem !important;
    font-size: 0.85rem !important;
}

/* Reduce metric padding */
[data-testid="metric-container"] {
    padding: 0.3rem !important;
}

/* Reduce header margins */
h1 { margin-bottom: 0.3rem !important; margin-top: 0rem !important; }
h2 { margin-bottom: 0.3rem !important; margin-top: 0.3rem !important; }
h3 { margin-bottom: 0.2rem !important; margin-top: 0.2rem !important; }

/* Reduce divider margin */
hr { margin: 0.3rem 0 !important; }

/* Sidebar text smaller */
section[data-testid="stSidebar"] p {
    font-size: 0.85rem !important;
    margin-bottom: 0.2rem !important;
}

/* Hide streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ── COMMANDO THEME: navy #0B1F33 · olive #4B5D2E · gold #C9A227 ── */
h1, h2 { font-family: 'Oswald', sans-serif !important; letter-spacing: 0.04em; text-transform: uppercase; }
h1 { font-size: 1.9rem !important; }
h3 { font-family: 'Oswald', sans-serif !important; letter-spacing: 0.02em; }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #0B1F33 0%, #16324d 100%) !important; }
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] [data-testid="stMetricValue"],
section[data-testid="stSidebar"] [data-testid="stMetricLabel"] { color: #E8E4D8 !important; }
section[data-testid="stSidebar"] .stButton > button { background: rgba(255,255,255,0.06) !important;
    color: #E8E4D8 !important; border: 1px solid rgba(201,162,39,0.45) !important; }
section[data-testid="stSidebar"] .stButton > button:hover { border-color: #C9A227 !important; color: #fff !important; }
section[data-testid="stSidebar"] .stButton > button[kind="primary"] { background: #4B5D2E !important; border-color: #C9A227 !important; }
section[data-testid="stSidebar"] [data-testid="stAlert"] { background: rgba(201,162,39,0.14) !important; border-left: 3px solid #C9A227 !important; }
.stButton > button[kind="primary"], .stFormSubmitButton > button, .stDownloadButton > button[kind="primary"] {
    background: #4B5D2E !important; border: 1px solid #C9A227 !important; color: #fff !important; }
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button:hover { background: #5d7238 !important; }
[data-testid="stMetric"] { background: rgba(201,162,39,0.07); border-left: 3px solid #C9A227;
    border-radius: 6px; padding: 0.35rem 0.6rem !important; }
.mission-banner { position: relative; border-radius: 10px; padding: 0.9rem 1.1rem; margin: 0.2rem 0 0.6rem 0;
    background: linear-gradient(120deg, #0B1F33 0%, #1d3a24 60%, #4B5D2E 100%); background-size: cover; background-position: center;
    border: 1px solid rgba(201,162,39,0.6); box-shadow: 0 4px 14px rgba(0,0,0,0.18); }
.mission-banner .mb-label { font-family: 'Oswald', sans-serif; color: #C9A227; font-size: 0.78rem; letter-spacing: 0.18em; }
.mission-banner .mb-quote { color: #fff; font-size: 1.05rem; font-weight: 600; margin-top: 0.15rem; }
.mission-banner .mb-sub { color: #d9d4c3; font-size: 0.8rem; margin-top: 0.2rem; }
</style>
""", unsafe_allow_html=True)

# ── TIMEZONE ──────────────────────────────────────────────────────────────────
IST = pytz.timezone("Asia/Kolkata")
def now_ist():
    return datetime.now(IST)
def today_ist():
    return now_ist().date()
def time_str():
    return now_ist().strftime("%I:%M %p")
def date_str():
    return today_ist().strftime("%Y-%m-%d")

MISSION_QUOTES = [
    "The only easy day was yesterday.",
    "Discipline beats motivation. Start the timer, finish the mission.",
    "Every order on time. Every bill checked. No one left behind.",
    "Precision today, trust tomorrow.",
    "Small missions, done right, win the war.",
    "Stay sharp. Stay ready. Deliver.",
    "Train hard, work smart, win together.",
]

def mission_banner(sub=""):
    """Commando-style banner. Uses background.jpg from the repo if present (dark overlay keeps text readable)."""
    bg = ""
    try:
        if os.path.exists("background.jpg"):
            import base64
            if "_bg_b64" not in st.session_state:
                with open("background.jpg", "rb") as f:
                    st.session_state["_bg_b64"] = base64.b64encode(f.read()).decode()
            bg = (" style=\"background-image: linear-gradient(120deg, rgba(11,31,51,0.88), rgba(75,93,46,0.72)), "
                  f"url('data:image/jpeg;base64,{st.session_state['_bg_b64']}');\"")
    except Exception:
        bg = ""
    q = MISSION_QUOTES[today_ist().weekday()]
    st.markdown(f'<div class="mission-banner"{bg}><div class="mb-label">🎯 MISSION OF THE DAY</div>'
                f'<div class="mb-quote">“{q}”</div>' + (f'<div class="mb-sub">{sub}</div>' if sub else "") + '</div>',
                unsafe_allow_html=True)

def parse_task_time(s):
    """Read a task start/end time saved as '07:39:12 PM' (new) or '07:39 PM' (old)"""
    for fmt in ("%I:%M:%S %p", "%I:%M %p"):
        try:
            return datetime.strptime(str(s).strip(), fmt)
        except Exception:
            pass
    return None

def task_secs(row):
    """Duration of a task in seconds (exact for new records, whole minutes for old ones)"""
    s = parse_task_time(row.get("start_time",""))
    e = parse_task_time(row.get("end_time",""))
    if s and e:
        diff = (e - s).total_seconds()
        if diff < 0:
            diff += 24*3600   # crossed midnight
        return int(diff)
    try:
        return int(float(row.get("duration_mins",0) or 0) * 60)
    except Exception:
        return 0

def fmt_secs(secs):
    """45 -> '45 secs', 125 -> '2 min 5 secs', 3720 -> '1 hr 2 min'"""
    secs = int(round(secs or 0))
    if secs < 60:
        return f"{secs} secs"
    if secs < 3600:
        m, s = divmod(secs, 60)
        return f"{m} min {s} secs" if s else f"{m} min"
    h, rem = divmod(secs, 3600)
    return f"{h} hr {rem//60} min"

# ── SUPABASE ──────────────────────────────────────────────────────────────────
# Keys stored in Streamlit secrets or environment variables only
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_SECRET = st.secrets["SUPABASE_SECRET"]
except:
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_SECRET = os.getenv("SUPABASE_SECRET", "")

if not SUPABASE_URL or not SUPABASE_SECRET:
    st.error("⚠️ Supabase credentials not found!")
    st.stop()

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_SECRET)
supabase = init_supabase()

@st.cache_data(ttl=300)
def load_warehouses():
    try:
        resp = supabase.table("warehouses").select("*").eq("active", True).execute()
        return [w["name"] for w in resp.data] if resp.data else ["Warehouse 1","Warehouse 2","Warehouse 3"]
    except:
        return ["Warehouse 1","Warehouse 2","Warehouse 3"]

@st.cache_data(ttl=300)
def load_areas():
    try:
        resp = supabase.table("areas").select("*").eq("active", True).execute()
        return [a["name"] for a in resp.data] if resp.data else ["Gaur City","Sector 78","Indirapuram"]
    except:
        return ["Gaur City","Sector 78","Indirapuram"]

# ── USERS ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_users():
    try:
        resp = supabase.table("app_users").select("*").eq("active", True).execute()
        users = {}
        for u in resp.data:
            users[u["username"]] = {
                "password": u["password"],
                "name": u["name"],
                "team": u["team"],
                "role": u["role"],
                "phone": u.get("phone") or ""
            }
        return users
    except:
        return {}

USERS = load_users()

_OLD_DISTRIBUTORS = [
    "Acorns Health Solutions Private Limited","Admire Enterprises","Zone Ventures Put Ltd",
    "Amar Drugs Distributors","Amarjeet Medical Hall","Ankit Enterprises",
    "Ar Kay Medicos Private Limited","Bawa Medical Store","Bhakti Enterprises",
    "D. C. Agencies Private Limited","Digipharms","Evara Life Sciences Llp",
    "Goel Medical Agencies","Guru Ji Medicos","Harikul Pharma",
    "Health And Wellness Pharmacy","Hindustan Pharma","J B G Distributors",
    "Jayanti Medical Agency Llp","Krishna Medical Agencies","M/s Jai Medical Agency",
    "M/s Shri Hari Pharma","M/s Bawa Medical Agencies","M/s Medi Science",
    "M/s Mediways Vaccine Company","M/s Premier Medical Agency","M/s Satyam Medicos",
    "M/s Sehgal Pharma","M/s Star Pharma","M/s Stupa Enterprises",
    "Retailer Shakti","M/s Universal Medical Agency",
    "Maypri Healthcare Private Limited","Mediways Agencies","Mediways Vaccine",
    "Mukesh Pharma Private Limited","Narayan Medical Agency",
    "Neelkanth Pharma Logistics Private Limited","New Brahmroop Medicare",
    "Olr Pharmacy","Om Distributors","Pawan Agencies","Pharmacype Enterprises",
    "Sastasundar Healthbuddy Limited","Satyam Distributors","Sharma Medical Agency",
    "Shivshakti Enterprises","Shree Maruti Nandan Pharmaceuticals Pvt Ltd",
    "Shri Radhey Krishan Trading Co.","Shri Rudram Enterprises","Silvertone Networks",
    "Trisha Pharma","Vashudev Enterprises","Vijaydeep Medicose",
    "Vtc Tradewings Pvt Ltd","Xcelent Pharmaceuticals Private Limited","Unnati",
]

@st.cache_data(ttl=300)
def load_distributors():
    """Distributor master from Supabase (Settings -> Distributors)"""
    try:
        return supabase.table("distributors").select("*").order("name").execute().data or []
    except Exception:
        return []

# the master list once normal_order_setup.sql has been run; the old built-in list until then
DISTRIBUTORS = [d["name"] for d in load_distributors() if d.get("active", True)] or _OLD_DISTRIBUTORS

IMG_FOLDER = "images"
os.makedirs(IMG_FOLDER, exist_ok=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
for k,v in [("logged_in",False),("username",""),("name",""),("team",""),("role",""),("work_area",""),("stock_active_form",None),("purchase_active_form",None),("show_pipeline",None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── PERSISTENT LOGIN via Query Params ─────────────────────────────────────────
# Auto login if credentials stored in query params
if not st.session_state.logged_in:
    try:
        params = st.query_params
        if "u" in params and "t" in params:
            username = params["u"]
            token    = params["t"]
            # Verify token matches (simple hash)
            import hashlib
            USERS_temp = load_users()
            if username in USERS_temp:
                expected = hashlib.md5(
                    (username + USERS_temp[username]["password"]).encode()
                ).hexdigest()[:8]
                if token == expected:
                    st.session_state.logged_in = True
                    st.session_state.username  = username
                    st.session_state.name      = USERS_temp[username]["name"]
                    st.session_state.team      = USERS_temp[username]["team"]
                    st.session_state.role      = USERS_temp[username]["role"]
    except:
        pass

# ── IMAGE UPLOAD ──────────────────────────────────────────────────────────────
def calc_actual_duration(df):
    """Calculate actual working time by merging overlapping task periods"""
    try:
        from datetime import datetime as dt
        periods = []
        for _, row in df.iterrows():
            try:
                s = parse_task_time(row.get("start_time",""))
                e = parse_task_time(row.get("end_time",""))
                if e > s:
                    periods.append((s, e))
            except:
                pass
        if not periods:
            return 0
        periods.sort()
        merged = [list(periods[0])]
        for start, end in periods[1:]:
            if start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        return sum([int((e-s).total_seconds()/60) for s,e in merged])
    except:
        return 0

def upload_image(file, prefix="img"):
    if file is None:
        return ""
    base = st.session_state.get("_photo_bases", {}).pop(getattr(file, "file_id", id(file)), None)
    if base:   # photo-first box: clear it for the next entry
        st.session_state[base + "_v"] = st.session_state.get(base + "_v", 0) + 1
    try:
        name = f"{prefix}_{now_ist().strftime('%Y%m%d_%H%M%S')}.jpg"
        supabase.storage.from_("Images").upload(
            path=name,
            file=file.getbuffer().tobytes(),
            file_options={"content-type": "image/jpeg"}
        )
        return name
    except Exception as e:
        st.error(f"Image upload error: {e}")
        return ""

def photo_key(base):
    """uploader key that changes after a successful save -> next entry starts with an empty photo box"""
    return f"{base}_{st.session_state.get(base + '_v', 0)}"

def remember_photo(file, base):
    st.session_state.setdefault("_photo_bases", {})[getattr(file, "file_id", id(file))] = base

# ── LOGIN ─────────────────────────────────────────────────────────────────────
def show_login():
    st.markdown("""
    <style>
    .main {background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);}
    .login-card {background:white; padding:2.5rem; border-radius:16px; 
                 box-shadow:0 20px 60px rgba(0,0,0,0.3); max-width:400px; margin:auto;}
    </style>
    """, unsafe_allow_html=True)
    
    col1,col2,col3 = st.columns([1,2,1])
    with col2:
        st.markdown("---")
        st.markdown("# 💊 RapidSurge")
        st.markdown("### Warehouse Mission Control")
        mission_banner("Log in to report for duty.")
        st.markdown("---")
        username = st.text_input("👤 Username", placeholder="Enter username")
        password = st.text_input("🔒 Password", type="password", placeholder="Enter password")
        if st.button("🚀 Login", width='stretch', type="primary"):
            if username in USERS and USERS[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.name = USERS[username]["name"]
                st.session_state.team = USERS[username]["team"]
                st.session_state.role = USERS[username]["role"]
                st.session_state.work_area = ""
                st.session_state["fresh_login"] = True     # Stock: ask the area again after a real login
                # Store login in URL for persistence
                import hashlib
                token = hashlib.md5((username + password).encode()).hexdigest()[:8]
                st.query_params["u"] = username
                st.query_params["t"] = token
                st.rerun()
            else:
                st.error("❌ Wrong username or password!")
        st.caption("Contact Ankit if you forgot your password.")

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
def show_sidebar():
    with st.sidebar:
        # Time based greeting
        hour = now_ist().hour
        if hour < 12:
            greeting = "🌅 Good Morning"
        elif hour < 17:
            greeting = "🌞 Good Afternoon"
        else:
            greeting = "🌙 Good Evening"

        st.markdown(f"## {greeting}, {st.session_state.name}!")

        # Daily quote by day of week
        quotes = ["🪖 " + q for q in MISSION_QUOTES]
        st.info(quotes[today_ist().weekday()])
        st.divider()

        # Personal stats
        try:
            from datetime import timedelta
            yesterday = (today_ist() - timedelta(days=1)).strftime("%Y-%m-%d")
            yest_resp = supabase.table("daily_tasks").select("id,status")\
                .eq("person", st.session_state.name)\
                .eq("date", yesterday).execute()
            yest_count = len([t for t in (yest_resp.data or []) if t.get("status") != "In Progress"])
            today_resp = supabase.table("daily_tasks").select("id,status")\
                .eq("person", st.session_state.name)\
                .eq("date", date_str()).execute()
            today_count = len([t for t in (today_resp.data or []) if t.get("status") != "In Progress"])
            st.markdown("**🎖️ Missions Completed:**")
            c1,c2 = st.columns(2)
            with c1: st.metric("Yesterday", yest_count)
            with c2:
                delta = today_count - yest_count
                st.metric("Today", today_count, f"{'+' if delta>=0 else ''}{delta}")
        except:
            pass

        st.divider()
        st.markdown(f"📅 **{today_ist().strftime('%d %B %Y')}**")
        st.markdown(f"🕐 **{time_str()}**")
        st.markdown(f"**Team:** {st.session_state.team}")
        if st.session_state.role == "admin":
            st.success("👑 Admin")
        # Show current work area for Stock team
        if st.session_state.team == "Stock" and st.session_state.work_area:
            st.markdown(f"📍 **Area:** {st.session_state.work_area}")
            st.caption("To change area: Logout and log in again")
            st.divider()

                        # Pipeline buttons
            st.markdown("**📋 View Pipeline:**")
            if st.button("🧾 Normal Order Pipeline", width='stretch', key="btn_normal_pipe"):
                st.session_state["show_pipeline"] = "normal"
                st.rerun()
            if st.button("📦 Arrangement Pipeline", width='stretch', key="btn_arr_pipe"):
                st.session_state["show_pipeline"] = "arrangement"
                st.rerun()
            if st.session_state.get("show_pipeline"):
                if st.button("❌ Close Pipeline", width='stretch', key="btn_close_pipe"):
                    st.session_state["show_pipeline"] = None
                    st.rerun()
            st.divider()

        if st.button("🚪 Logout", width='stretch'):
            for k in ["logged_in","username","name","team","role","work_area"]:
                st.session_state[k] = False if k=="logged_in" else ""
            st.query_params.clear()
            st.rerun()

# ── TIMER BUTTON ──────────────────────────────────────────────────────────────
def get_active_timer():
    """Check if any timer is currently running"""
    timer_keys = [
        "purchase_order","purchase_return","pharmarack","bounce",
        "arrangement_order","bill_crosscheck","bill_upload","bill_upload_normal",
        "stock_placement","rack_cleaning","inventory",
        "call_log","medicine_search","delivery","other_task","pickup","sheet_order"
    ]
    for k in timer_keys:
        if st.session_state.get(f"{k}_start"):
            return k, st.session_state[f"{k}_start"]
    return None, None

def timer_button(key, task_name=None):
    sk = f"{key}_start"
    if sk not in st.session_state:
        st.session_state[sk] = None

    if st.session_state[sk] is None and restore_timer(key, task_name):
        st.toast("⏱️ Timer restored after refresh", icon="🔄")
    if st.session_state[sk] is None:
        # Check if another task is running
        active_key, active_start = get_active_timer()
        if active_key and active_key != key:
            active_name = active_key.replace("_"," ").title()
            elapsed = int((now_ist() - active_start).total_seconds() / 60)
            st.warning(f"⚠️ **{active_name}** is already in progress ({elapsed} mins)! Please complete it first before starting a new task.")
            return None

        st.info("👆 Click START when you begin this task")
        if st.button("▶️ Start", key=f"btn_{key}", type="primary"):
            st.session_state[sk] = now_ist()
            # Save In Progress record to daily_tasks
            try:
                result = supabase.table("daily_tasks").insert({
                    "date": date_str(),
                    "time": time_str(),
                    "person": st.session_state.name,
                    "team": st.session_state.team,
                    "task_type": task_name or key.replace("_"," ").title(),
                    "status": "In Progress",
                    "start_time": now_ist().strftime("%I:%M:%S %p"),
                    "details": {}
                }).execute()
                if result.data:
                    st.session_state[f"{key}_task_id"] = result.data[0]["id"]
            except:
                pass
            st.rerun()
        return None
    else:
        elapsed = int((now_ist() - st.session_state[sk]).total_seconds() / 60)
        st.success(f"⏱️ Started at {st.session_state[sk].strftime('%I:%M %p')} — {elapsed} mins elapsed")
        c1,c2 = st.columns([3,1])
        with c2:
            if st.button("❌ Cancel Task", key=f"cancel_{key}", type="secondary"):
                st.session_state[sk] = None
                # Remove the unfinished "In Progress" record so it doesn't count as a task
                cancel_id = st.session_state.get(f"{key}_task_id")
                if cancel_id:
                    try:
                        supabase.table("daily_tasks").delete()\
                            .eq("id", cancel_id).eq("status", "In Progress").execute()
                    except:
                        pass
                    st.session_state[f"{key}_task_id"] = None
                st.rerun()
        return st.session_state[sk]

def end_timer(key, start_time, keep_record=False):
    end = now_ist()
    duration = int((end - start_time).total_seconds() / 60)
    st.session_state["mission_done"] = int((end - start_time).total_seconds())
    st.session_state[f"{key}_start"] = None
    task_id = st.session_state.get(f"{key}_task_id")
    if task_id:
        try:
            if keep_record:
                # Form has no row of its own -> turn the In Progress record into the final one
                supabase.table("daily_tasks").update({
                    "end_time": end.strftime("%I:%M:%S %p"),
                    "duration_mins": str(duration),
                    "status": "Completed"
                }).eq("id", task_id).execute()
            else:
                # Form saves its own full row -> remove the empty In Progress placeholder
                # (this was creating a duplicate empty entry for every task)
                supabase.table("daily_tasks").delete()\
                    .eq("id", task_id).eq("status", "In Progress").execute()
        except:
            pass
        st.session_state[f"{key}_task_id"] = None
    return end.strftime("%I:%M:%S %p"), duration

# ── PURCHASE TEAM FORMS ───────────────────────────────────────────────────────
def form_purchase_order():
    st.subheader("🛒 Purchase Order")
    st.caption("For orders NOT in the order sheet (e.g. phone orders). Sheet medicines → use 📑 **Order Sheet**.")
    start = timer_button("purchase_order")
    if start is None: return
    with st.form("purchase_order_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            distributor = st.selectbox("Distributor *", DISTRIBUTORS, key="po_dist")
            po_area     = st.selectbox("Area / Store *", ["— Select Area —"] + load_areas(), key="po_area")
            order_type  = st.selectbox("Order Type", ["Regular","Arrangement"], key="po_type")
            no_sku      = st.number_input("No of SKUs", min_value=0, step=1)
        with c2:
            mode        = st.selectbox("Mode", ["Through Call","Pharma Rack","Excel Send"], key="po_mode")
            urgency     = st.selectbox("Urgency", ["Normal","Urgent","Very Urgent"], key="po_urgency")
        remarks = st.text_input("Remarks")
        if st.form_submit_button("Submit ✅", type="primary", width='stretch'):
            if po_area == "— Select Area —":
                st.error("Select the Area / Store for this order!")
                return
            if no_sku < 1:
                st.error("Enter No of SKUs (at least 1)!")
                return
            end_time, duration = end_timer("purchase_order", start)
            try:
                supabase.table("daily_tasks").insert({
                    "date": date_str(), "time": time_str(),
                    "person": st.session_state.name, "team": "Purchase",
                    "task_type": "Purchase Order",
                    "details": {"distributor": distributor, "area": po_area, "order_type": order_type,
                               "no_sku": str(no_sku), "mode": mode, "urgency": urgency,
                               "remarks": remarks},
                    "start_time": start.strftime("%I:%M:%S %p"),
                    "end_time": end_time, "duration_mins": str(duration),
                    "status": "Completed"
                }).execute()
                # Delete the In Progress duplicate if exists
                task_id = st.session_state.get("purchase_order_task_id")
                if task_id:
                    supabase.table("daily_tasks").delete().eq("id", task_id).execute()
                    st.session_state["purchase_order_task_id"] = None
                st.success("✅ Purchase Order submitted!")
                st.balloons()
            except Exception as e:
                st.error(f"Error: {e}")

def form_purchase_return():
    st.subheader("↩️ Purchase Return")
    start = timer_button("purchase_return")
    if start is None: return
    with st.form("purchase_return_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            distributor = st.selectbox("Distributor *", DISTRIBUTORS, key="pr_dist")
            bill_no     = st.text_input("Bill Number *")
        with c2:
            no_items    = st.number_input("No of Items Returned", min_value=0, step=1)
            reason      = st.selectbox("Return Reason", ["Expired","Damaged","Wrong Item","Excess Stock","Other"], key="pr_reason")
        items    = st.text_area("Items Returned")
        remarks  = st.text_input("Remarks")
        if st.form_submit_button("Submit ✅", type="primary", width='stretch'):
            if not bill_no:
                st.error("Fill Bill Number!")
            else:
                end_time, duration = end_timer("purchase_return", start)
                try:
                    supabase.table("daily_tasks").insert({
                        "date": date_str(), "time": time_str(),
                        "person": st.session_state.name, "team": "Purchase",
                        "task_type": "Purchase Return",
                        "details": {"distributor": distributor, "bill_no": bill_no,
                                   "no_items": str(no_items), "reason": reason,
                                   "items": items, "remarks": remarks},
                        "start_time": start.strftime("%I:%M:%S %p"),
                        "end_time": end_time, "duration_mins": str(duration)
                    }).execute()
                    st.success("✅ Purchase Return submitted!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")

def form_pharmarack():
    st.subheader("💊 Medicine Search on PharmaRack")
    start = timer_button("pharmarack")
    if start is None: return
    with st.form("pharmarack_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            no_searched  = st.number_input("No of Medicines Searched", min_value=0, step=1)
            no_found     = st.number_input("No of Medicines Found", min_value=0, step=1)
        with c2:
            no_not_found = st.number_input("No of Medicines Not Found", min_value=0, step=1)
            no_ordered   = st.number_input("No of Medicines Ordered", min_value=0, step=1)
        remarks = st.text_input("Remarks")
        if st.form_submit_button("Submit ✅", type="primary", width='stretch'):
            end_time, duration = end_timer("pharmarack", start)
            try:
                supabase.table("daily_tasks").insert({
                    "date": date_str(), "time": time_str(),
                    "person": st.session_state.name, "team": "Purchase",
                    "task_type": "PharmaRack Search",
                    "details": {"no_searched": str(no_searched), "no_found": str(no_found),
                               "no_not_found": str(no_not_found), "no_ordered": str(no_ordered),
                               "remarks": remarks},
                    "start_time": start.strftime("%I:%M:%S %p"),
                    "end_time": end_time, "duration_mins": str(duration)
                }).execute()
                st.success("✅ PharmaRack Search submitted!")
                st.balloons()
            except Exception as e:
                st.error(f"Error: {e}")

def form_bounce_medicine():
    st.subheader("📋 Understand Bounce Medicine")
    start = timer_button("bounce")
    if start is None: return
    with st.form("bounce_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            no_bounced  = st.number_input("No of Medicines Bounced", min_value=0, step=1)
            no_useful   = st.number_input("No of New Useful Medicines Found", min_value=0, step=1)
        with c2:
            st.markdown("📸 **Image of Medicine List**")
        img = st.file_uploader("📷 Take photo or choose file", type=["jpg","jpeg","png"], key="bounce_upload")
        remarks = st.text_input("Remarks")
        if st.form_submit_button("Submit ✅", type="primary", width='stretch'):
            end_time, duration = end_timer("bounce", start)
            img_name = upload_image(img, "bounce") if img else ""
            try:
                supabase.table("daily_tasks").insert({
                    "date": date_str(), "time": time_str(),
                    "person": st.session_state.name, "team": "Purchase",
                    "task_type": "Bounce Medicine Study",
                    "details": {"no_bounced": str(no_bounced), "no_useful": str(no_useful),
                               "image": img_name, "remarks": remarks},
                    "start_time": start.strftime("%I:%M:%S %p"),
                    "end_time": end_time, "duration_mins": str(duration)
                }).execute()
                st.success("✅ Bounce Medicine Study submitted!")
                st.balloons()
            except Exception as e:
                st.error(f"Error: {e}")

# ── ARRANGEMENT FORM ──────────────────────────────────────────────────────────
def form_arrangement():
    st.subheader("📋 New Arrangement Order")
    start = timer_button("arrangement_order", "Arrangement Order")
    if start is None:
        return

    AREAS = load_areas() + load_warehouses() + ["Other"]

    # Auto generate arrangement number
    try:
        today_prefix = today_ist().strftime("%Y%m%d")
        existing = supabase.table("arrangements").select("arrangement_no")\
            .like("arrangement_no", f"ARR-{today_prefix}-%").execute()
        next_no = len(existing.data) + 1 if existing.data else 1
        auto_arr_no = f"ARR-{today_prefix}-{str(next_no).zfill(3)}"
    except:
        auto_arr_no = f"ARR-{today_ist().strftime('%Y%m%d')}-001"

    st.info(f"🔢 Auto Arrangement No: **{auto_arr_no}**")

    # Customer order items to link (optional)
    link_area, picked_lines = arrangement_line_picker()
    picked_lines = [p for p in picked_lines if _to_float(p.get("Order Qty"), 0) > 0]

    # form keys change after each saved order -> fresh form; they do NOT change on an error,
    # so a missing photo no longer resets the distributor / area
    fv = st.session_state.get("arr_form_ver", 0)
    area_default = link_area if link_area in AREAS else None
    with st.form(f"arrangement_form_{fv}", clear_on_submit=False):
        c1,c2 = st.columns(2)
        with c1:
            arr_no        = st.text_input("Arrangement No", value=auto_arr_no, disabled=True)
            distributor   = st.selectbox("Distributor *", DISTRIBUTORS, key=f"arr_dist_{fv}")
            area          = st.selectbox("Customer Area *", AREAS,
                                         index=AREAS.index(area_default) if area_default else 0,
                                         key=f"arr_area_{fv}_{area_default}",
                                         disabled=bool(picked_lines),
                                         help="Filled from the customer-order area above" if picked_lines else None)
            bill_order_id = st.text_input("Bill Number / Order ID", key=f"arr_bill_{fv}")
        with c2:
            urgency       = st.selectbox("Urgency", ["Normal","Urgent","Very Urgent"], key=f"arr_urgency_{fv}")
            pickup_type   = st.selectbox("Pickup Type", ["Self Pick","Porter","Distributor Delivers"], key=f"arr_pickup_{fv}")
            no_medicines  = st.number_input("No of Medicines to Pick *", min_value=0, max_value=200, step=1,
                                            value=len(picked_lines),
                                            key=f"arr_nmed_{fv}_{len(picked_lines)}",
                                            help="Filled from the ticked customer items — add any extra medicines. Max 200.")
            order_time    = st.text_input("Order Time", value=time_str(), key=f"arr_time_{fv}")
        remarks = st.text_input("Remarks", key=f"arr_remarks_{fv}")
        st.markdown("📸 **Image of Order ***")
        arr_img = st.file_uploader("Select or Take Photo", type=["jpg","jpeg","png"], key=f"arr_upload_{fv}")

        if st.form_submit_button("Submit ✅", type="primary", width='stretch'):
            medicines = ""
            if picked_lines:
                # Ticked customer items: area comes from them, medicines added automatically
                area = link_area
                medicines = "\n".join(
                    f"{p.get('Item','')} {('(' + str(p.get('Pack')) + ')') if p.get('Pack') else ''}".strip()
                    + f" - {_qty_txt(min(_to_float(p.get('Order Qty'),0), _to_float(p.get('Needed'),0)))}"
                    for p in picked_lines)
            if not no_medicines:
                st.error("Enter No of Medicines to Pick!")
            elif arr_img is None:
                st.error("⚠️ Image of order is mandatory! Please upload or take photo (just above Submit).")
            else:
                # Check duplicate arrangement number
                try:
                    check = supabase.table("arrangements")\
                        .select("id")\
                        .eq("arrangement_no", arr_no)\
                        .execute()
                    if check.data:
                        st.error(f"❌ Arrangement No #{arr_no} already exists! Please use a different number.")
                    else:
                        img_name = upload_image(arr_img, "arr")
                        result = supabase.table("arrangements").insert({
                            "arrangement_no": arr_no,
                            "distributor": distributor,
                            "area": area,
                            "bill_order_id": bill_order_id,
                            "no_medicines": str(no_medicines),
                            "order_placed_date": date_str(),
                            "order_placed_time": order_time,
                            "order_by": st.session_state.name,
                            "urgency": urgency,
                            "pickup_type": pickup_type,
                            "order_image": img_name,
                            "status": "Pending"
                        }).execute()
                        arr_id = result.data[0]["id"]
                        if picked_lines:
                            save_arrangement_links(arr_id, arr_no, distributor, area, picked_lines)
                        for med in medicines.strip().split("\n"):
                            if med.strip():
                                parts = med.rsplit(" - ", 1)
                                med_name = parts[0].strip()
                                qty = parts[1].strip() if len(parts) > 1 else "1"
                                supabase.table("arrangement_medicines").insert({
                                    "arrangement_id": arr_id,
                                    "medicine_name": med_name,
                                    "quantity": qty
                                }).execute()
                        end_time, duration = end_timer("arrangement_order", start, keep_record=True)
                        # Update task with medicines count - find by person and date
                        try:
                            task_resp = supabase.table("daily_tasks").select("id")\
                                .eq("task_type", "Arrangement Order")\
                                .eq("person", st.session_state.name)\
                                .eq("date", date_str())\
                                .eq("status", "Completed")\
                                .order("id", desc=True)\
                                .limit(1).execute()
                            if task_resp.data:
                                supabase.table("daily_tasks").update({
                                    "details": {
                                        "arrangement_no": arr_no,
                                        "distributor": distributor,
                                        "no_medicines": str(no_medicines),
                                        "area": area,
                                        "customer_lines": str(len(picked_lines)),
                                        "remarks": remarks
                                    }
                                }).eq("id", task_resp.data[0]["id"]).execute()
                        except:
                            pass
                        st.session_state["arr_form_ver"] = fv + 1
                        st.success(f"✅ Arrangement #{arr_no} placed successfully!")
                        st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")

# ── STOCK TEAM FORMS ──────────────────────────────────────────────────────────
def form_bill_upload():
    st.subheader("🧾 Bill Upload")
    start = timer_button("bill_upload_normal", "Bill Upload")
    if start is None:
        return
    st.markdown("📸 **Bill Image (Mandatory)**")
    img = st.file_uploader("📷 Take photo or choose file", type=["jpg","jpeg","png","pdf"], key=photo_key("bu_upload"))
    if img is None:
        st.info("📷 **Step 1: take the photo (or choose a file).** The form opens after that.")
        return
    remember_photo(img, "bu_upload")
    with st.form("bill_upload_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            distributor  = st.selectbox("Distributor *", DISTRIBUTORS, key="bu_dist")
            bill_no      = st.text_input("Bill Number *")
            bill_date    = st.date_input("Bill Date")
        with c2:
            delivery_by  = st.selectbox("Delivery By", ["Porter","Naresh","Sandeep","Distributor"], key="bu_del")
            order_type   = st.selectbox("Order Type", ["Regular","Arrangement"], key="bu_type")
        remarks = st.text_input("Remarks")
        if st.form_submit_button("Submit ✅", type="primary", width='stretch'):
            if not bill_no:
                st.error("Fill Bill Number!")
            else:
                img_name = upload_image(img, "bill") if img else ""
                end_time, duration = end_timer("bill_upload_normal", start)
                try:
                    supabase.table("daily_tasks").insert({
                        "date": date_str(), "time": time_str(),
                        "person": st.session_state.name, "team": "Stock",
                        "task_type": "Bill Upload",
                        "duration_mins": str(duration), "status": "Completed",
                        "details": {"distributor": distributor, "bill_no": bill_no,
                                   "bill_date": str(bill_date), "delivery_by": delivery_by,
                                   "order_type": order_type, "image": img_name,
                                   "remarks": remarks, "check_status": "Unchecked"},
                        "start_time": start.strftime("%I:%M:%S %p"), "end_time": end_time
                    }).execute()
                    st.success("✅ Bill uploaded successfully!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")

def form_rack_cleaning():
    st.subheader("🧹 Rack Cleaning")
    start = timer_button("rack_cleaning")
    if start is None: return
    with st.form("rack_cleaning_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            rack_no      = st.text_input("Rack No / Location *")
            no_racks     = st.number_input("No of Racks Cleaned", min_value=0, step=1)
        with c2:
            expiry_found = st.selectbox("Expiry Items Found?", ["No","Yes"], key="rc_exp")
            expiry_items = st.text_input("Expiry Items (if any)")
        remarks = st.text_input("Remarks")
        if st.form_submit_button("Submit ✅", type="primary", width='stretch'):
            if not rack_no:
                st.error("Fill Rack No!")
            else:
                end_time, duration = end_timer("rack_cleaning", start)
                try:
                    supabase.table("daily_tasks").insert({
                        "date": date_str(), "time": time_str(),
                        "person": st.session_state.name, "team": "Stock",
                        "task_type": "Rack Cleaning",
                        "details": {"rack_no": rack_no, "no_racks": str(no_racks),
                                   "expiry_found": expiry_found, "expiry_items": expiry_items,
                                   "remarks": remarks},
                        "start_time": start.strftime("%I:%M:%S %p"),
                        "end_time": end_time, "duration_mins": str(duration)
                    }).execute()
                    st.success("✅ Rack Cleaning submitted!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")

def form_inventory_check():
    st.subheader("📊 Inventory Check")
    start = timer_button("inventory")
    if start is None: return
    with st.form("inventory_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            location     = st.text_input("Location / Rack No *")
            no_items     = st.number_input("No of Items Checked", min_value=0, step=1)
            no_shortage  = st.number_input("No of Shortage Items", min_value=0, step=1)
        with c2:
            no_expiry    = st.number_input("No of Near Expiry Items", min_value=0, step=1)
            no_wrong     = st.number_input("No of Wrong Batch Items", min_value=0, step=1)
        shortage_items = st.text_area("Shortage Items List")
        remarks        = st.text_input("Remarks")
        if st.form_submit_button("Submit ✅", type="primary", width='stretch'):
            if not location:
                st.error("Fill Location!")
            else:
                end_time, duration = end_timer("inventory", start)
                try:
                    supabase.table("daily_tasks").insert({
                        "date": date_str(), "time": time_str(),
                        "person": st.session_state.name, "team": "Stock",
                        "task_type": "Inventory Check",
                        "details": {"location": location, "no_items": str(no_items),
                                   "no_shortage": str(no_shortage), "no_expiry": str(no_expiry),
                                   "no_wrong": str(no_wrong), "shortage_items": shortage_items,
                                   "remarks": remarks},
                        "start_time": start.strftime("%I:%M:%S %p"),
                        "end_time": end_time, "duration_mins": str(duration)
                    }).execute()
                    st.success("✅ Inventory Check submitted!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")

# ── CALL TEAM FORMS ───────────────────────────────────────────────────────────

def form_medicine_search():
    st.subheader("🔍 Medicine Search")
    st.caption("Track time spent searching for medicines in warehouse")

    start = timer_button("medicine_search", "Medicine Search")
    if start is None:
        return

    with st.form("medicine_search_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            no_searched  = st.number_input("No of Medicines Searched", min_value=0, step=1)
            no_found     = st.number_input("No Found in Warehouse", min_value=0, step=1)
        with c2:
            no_not_found = st.number_input("No NOT Found", min_value=0, step=1)
            no_ordered   = st.number_input("No Ordered After Search", min_value=0, step=1)
        remarks = st.text_input("Remarks")

        if st.form_submit_button("Submit ✅", type="primary", width='stretch'):
            end_time, duration = end_timer("medicine_search", start)
            avg_per_sku = round(duration/no_searched, 2) if no_searched > 0 else 0
            try:
                supabase.table("daily_tasks").insert({
                    "date": date_str(), "time": time_str(),
                    "person": st.session_state.name, "team": "Call",
                    "task_type": "Medicine Search",
                    "details": {
                        "no_searched": str(no_searched),
                        "no_found": str(no_found),
                        "no_not_found": str(no_not_found),
                        "no_ordered": str(no_ordered),
                        "avg_per_sku": str(avg_per_sku),
                        "remarks": remarks
                    },
                    "start_time": start.strftime("%I:%M:%S %p"),
                    "end_time": end_time,
                    "duration_mins": str(duration),
                    "status": "Completed"
                }).execute()
                st.success(f"✅ Medicine Search submitted! Avg time/SKU: {avg_per_sku} mins")
                st.balloons()
                st.session_state["medicine_search_start"] = None
            except Exception as e:
                st.error(f"Error: {e}")

# ── CALL TEAM FORM ────────────────────────────────────────────────────────────
def form_call_log():
    st.subheader("📞 Daily Call Log")

    start = timer_button("call_log")
    if start is None:
        return

    with st.form("call_log_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            calls_made   = st.number_input("Total Calls Made", min_value=0, step=1)
            calls_picked = st.number_input("Calls Picked", min_value=0, step=1)
        with c2:
            orders_del   = st.number_input("Orders Delivered", min_value=0, step=1)
        remarks = st.text_input("Remarks")
        if st.form_submit_button("Submit ✅", type="primary", width='stretch'):
            calls_not_picked = max(0, calls_made - calls_picked)
            end_time, duration = end_timer("call_log", start)
            try:
                supabase.table("daily_tasks").insert({
                    "date": date_str(), "time": time_str(),
                    "person": st.session_state.name, "team": "Call",
                    "task_type": "Call Log",
                    "details": {"calls_made": str(calls_made), "calls_picked": str(calls_picked),
                               "calls_not_picked": str(calls_not_picked), "orders_delivered": str(orders_del),
                               "remarks": remarks},
                    "start_time": start.strftime("%I:%M:%S %p"),
                    "end_time": end_time,
                    "duration_mins": str(duration)
                }).execute()
                st.success(f"✅ Call Log submitted! Duration: {duration} mins | Calls not picked: {calls_not_picked}")
                st.balloons()
                st.session_state["call_log_start"] = None
            except Exception as e:
                st.error(f"Error: {e}")

# ── PICKUP FORM ──────────────────────────────────────────────────────────────
def form_pickup():
    st.subheader("📋 Pickup Log")

    # Simple date filter for Naresh
    from datetime import timedelta
    pickup_date = st.date_input("Filter by Order Date",
        value=today_ist(),
        key="naresh_date_filter",
        min_value=today_ist() - timedelta(days=2),
        max_value=today_ist())

    try:
        resp = supabase.table("arrangements").select("*")\
            .eq("status", "Pending")\
            .eq("pickup_type", "Self Pick")\
            .eq("order_placed_date", pickup_date.strftime("%Y-%m-%d"))\
            .execute()
        arrangements = resp.data if resp.data else []
    except Exception as e:
        st.error(f"Error: {e}")
        arrangements = []

    if not arrangements:
        st.info("No pending arrangements!")
        return

    # Show pending summary
    pending = [a for a in arrangements if a.get("status") == "Pending"]

    if pending:
        st.markdown(f"**🔴 {len(pending)} Pending Arrangements:**")
        for arr in pending:
            urgency_color = "🔴" if arr.get("urgency") == "Very Urgent" else "🟡" if arr.get("urgency") == "Urgent" else "🟢"
            st.markdown(f"{urgency_color} **#{arr.get('arrangement_no')}** — {arr.get('distributor')} — Area: {arr.get('area','')} — Medicines: {arr.get('no_medicines','')} — {arr.get('urgency')}")

    st.divider()
    st.subheader("➕ Add Pickup Entry")

    arr_options = {f"#{a.get('arrangement_no')} — {a.get('distributor')} — {a.get('area','')}": a for a in arrangements}

    # Show invoice image OUTSIDE form so it stays visible
    if "selected_pickup_arr" not in st.session_state:
        st.session_state.selected_pickup_arr = None

    arr_keys = ["—"] + list(arr_options.keys())
    selected_preview = st.selectbox("Preview Arrangement", arr_keys, key="pu_preview")
    if selected_preview != "—":
        preview_arr = arr_options[selected_preview]
        st.session_state.selected_pickup_arr = selected_preview
        # Store for auto-fill in form
        st.session_state["pickup_auto_dist"] = preview_arr.get("distributor","")
        st.session_state["pickup_auto_arr"]  = selected_preview

        c1,c2,c3 = st.columns(3)
        with c1: st.info(f"📍 Area: **{preview_arr.get('area','N/A')}**")
        with c2: st.info(f"🧾 Bill/Order ID: **{preview_arr.get('bill_order_id','N/A')}**")
        with c3: st.info(f"💊 Medicines to Pick: **{preview_arr.get('no_medicines','N/A')}**")
        order_img = preview_arr.get("order_image","")
        if order_img and order_img.strip():
            st.markdown("**📄 Invoice Image from Purchase Team:**")
            try:
                img_data = supabase.storage.from_("Images").download(order_img.strip())
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(img_data))
                st.image(img, caption="Invoice (Download to zoom)", width='stretch')
                st.download_button(
                    "🔍 Download to Zoom",
                    img_data,
                    file_name=f"invoice_{preview_arr.get('arrangement_no','')}.jpg",
                    mime="image/jpeg",
                    key=f"dl_inv_{preview_arr.get('arrangement_no','')}"
                )
            except Exception as img_err:
                st.warning(f"⚠️ Image error: {img_err}")
        else:
            st.warning("⚠️ No invoice image uploaded by Purchase Team for this arrangement")

    # Auto fill from preview
    auto_dist = st.session_state.get("pickup_auto_dist","")
    auto_arr  = st.session_state.get("pickup_auto_arr","")
    arr_keys  = ["—"] + list(arr_options.keys())

    # Show selected info above form
    if auto_dist:
        st.success(f"✅ Auto-filled: **{auto_dist}** | **{auto_arr}**")

    st.markdown("**📸 Image of Medicine Received**")
    medicine_img = st.file_uploader("📷 Take photo or choose file", type=["jpg","jpeg","png"], key=photo_key("pu_upload"))
    if medicine_img is None:
        st.info("📷 **Step 1: take the photo (or choose a file).** The form opens after that.")
    else:
        remember_photo(medicine_img, "pu_upload")
        with st.form("pickup_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                # Show auto-filled values as text info
                st.markdown(f"**Distributor:** {auto_dist if auto_dist else 'Select below'}")
                distributor = st.selectbox("Change Distributor (if needed)",
                    dist_options(auto_dist),
                    index=dist_options(auto_dist).index(auto_dist) if auto_dist else 0,
                    key="pu_dist")
                st.markdown(f"**Arrangement:** {auto_arr if auto_arr else 'Select below'}")
                arr_select = st.selectbox("Change Arrangement (if needed)",
                    arr_keys,
                    index=arr_keys.index(auto_arr) if auto_arr in arr_keys else 0,
                    key="pu_arr")
                delivery_by = st.selectbox("Delivery By", ["Self Pick","Distributor"], key="pu_delby")
            with c2:
                no_sku_received = st.number_input("No of SKUs Actually Received", min_value=0, step=1)
                time_reached    = st.time_input("Time Reached Distributor", key="pu_reached")
                time_handover   = st.time_input("Handover Received Time", key="pu_handover")

            # Show invoice image if arrangement selected
            if arr_select != "—":
                selected_arr = arr_options[arr_select]
                no_medicines = selected_arr.get("no_medicines", "N/A")
                bill_id      = selected_arr.get("bill_order_id", "N/A")
                area         = selected_arr.get("area", "N/A")
                st.info(f"📋 Area: **{area}** | Bill/Order ID: **{bill_id}** | Medicines to Pick: **{no_medicines}**")

            # Porter details
            st.markdown("**Porter Details (if applicable)**")
            c3, c4 = st.columns(2)
            with c3:
                porter_no     = st.text_input("Porter No", placeholder="Leave blank if not applicable")
            with c4:
                porter_pickup = st.time_input("Porter Pickup Time", key="pu_porter")

            # Medicine received image

            remarks = st.text_input("Remarks")

            if st.form_submit_button("Submit ✅", type="primary", width='stretch'):
                if not medicine_img:
                    st.error("⚠️ Image of medicine received is mandatory! Please upload or take photo.")
                else:
                    arr_id = None
                    arr_no = None
                    if arr_select != "—":
                        selected_arr = arr_options[arr_select]
                        arr_id = selected_arr["id"]
                        arr_no = selected_arr.get("arrangement_no")

                    med_img_name = upload_image(medicine_img, "pickup") if medicine_img else ""

                    try:
                        supabase.table("daily_tasks").insert({
                            "date": date_str(),
                            "time": time_str(),
                            "person": st.session_state.name,
                            "team": "Delivery",
                            "task_type": "Pickup",
                            "details": {
                                "distributor": distributor,
                                "arrangement_no": str(arr_no) if arr_no else "",
                                "delivery_by": delivery_by,
                                "pickup_by": st.session_state.name,
                                "no_sku_received": str(no_sku_received),
                                "time_reached": str(time_reached),
                                "time_handover": str(time_handover),
                                "porter_no": porter_no,
                                "porter_pickup_time": str(porter_pickup) if porter_no else "",
                            "medicine_image": med_img_name,
                                "remarks": remarks
                            },
                            "start_time": str(time_reached),
                            "end_time": str(time_handover),
                        }).execute()

                        if arr_id:
                            supabase.table("arrangements").update({
                                "status": "Picked Up - In Transit",
                                "pickup_by": st.session_state.name,
                                "pickup_time": str(time_reached),
                                "handover_type": delivery_by,
                                "porter_no": porter_no,
                                "no_sku_received": str(no_sku_received),
                            }).eq("id", arr_id).execute()

                        st.success("✅ Pickup entry submitted!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

# ── DELIVERY FORM ─────────────────────────────────────────────────────────────
def form_delivery():
    st.subheader("🚚 Delivery Trip Log")
    LOCATIONS = load_warehouses() + DISTRIBUTORS
    TRIP_TYPES = ["Waiting for Medicine","Picked and Going to Another Distributor",
                  "Picked and Going to Warehouse","Going to Distributor","Waiting for Porter"]

    if "delivery_trip_id" not in st.session_state:
        st.session_state.delivery_trip_id = None
    if "delivery_start_time" not in st.session_state:
        st.session_state.delivery_start_time = None

    if st.session_state.delivery_trip_id is None:
        st.info("📍 Select location and activity then click Start Trip")
        with st.form("delivery_start_form"):
            c1,c2 = st.columns(2)
            with c1:
                loc_a     = st.selectbox("Current Location *", LOCATIONS, key="d_loc_a")
                trip_type = st.selectbox("Activity Type *", TRIP_TYPES, key="d_type")
            with c2:
                loc_b     = st.selectbox("Going To", ["—"]+LOCATIONS, key="d_loc_b")
            if trip_type == "Waiting for Medicine":
                c3,c4 = st.columns(2)
                with c3: no_bills = st.number_input("No of Bills", min_value=0, step=1)
                with c4: no_sku   = st.number_input("No of SKUs", min_value=0, step=1)
            else:
                no_bills, no_sku = 0, 0
            remarks = st.text_input("Remarks")
            if st.form_submit_button("▶️ Start Trip", type="primary", width='stretch'):
                start_t = time_str()
                try:
                    result = supabase.table("daily_tasks").insert({
                        "date": date_str(), "time": time_str(),
                        "person": st.session_state.name, "team": "Delivery",
                        "task_type": "Delivery Trip",
                        "details": {"location_a": loc_a, "trip_type": trip_type,
                                   "location_b": loc_b, "no_bills": str(no_bills),
                                   "no_sku": str(no_sku), "remarks": remarks},
                        "start_time": start_t, "end_time": "In Progress",
                        "status": "In Progress"
                    }).execute()
                    st.session_state.delivery_trip_id = result.data[0]["id"]
                    st.session_state.delivery_start_time = now_ist()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        elapsed = int((now_ist() - st.session_state.delivery_start_time).total_seconds() / 60)
        st.success(f"⏱️ Trip in progress — {elapsed} minutes elapsed")
        st.info("Click Complete when activity is done")
        if st.button("✅ Complete This Activity", type="primary", width='stretch'):
            end_t    = time_str()
            duration = elapsed
            try:
                supabase.table("daily_tasks").update({
                    "end_time": end_t,
                    "duration_mins": str(duration),
                    "status": "Completed"
                }).eq("id", st.session_state.delivery_trip_id).execute()
                st.session_state.delivery_trip_id   = None
                st.session_state.delivery_start_time = None
                st.success("✅ Trip completed!")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# ── OTHER TASK FORM ───────────────────────────────────────────────────────────
def form_other_task():
    st.subheader("✏️ Other Task")
    start = timer_button("other_task")
    if start is None: return
    with st.form("other_task_form", clear_on_submit=True):
        task_name = st.text_input("Task Name *", placeholder="What did you do?")
        details   = st.text_area("Task Details", placeholder="Describe the task...")
        remarks   = st.text_input("Remarks")
        if st.form_submit_button("Submit ✅", type="primary", width='stretch'):
            if not task_name:
                st.error("Fill Task Name!")
            else:
                end_time, duration = end_timer("other_task", start)
                try:
                    supabase.table("daily_tasks").insert({
                        "date": date_str(), "time": time_str(),
                        "person": st.session_state.name, "team": st.session_state.team,
                        "task_type": "Other",
                        "details": {"task_name": task_name, "details": details, "remarks": remarks},
                        "start_time": start.strftime("%I:%M:%S %p"),
                        "end_time": end_time, "duration_mins": str(duration)
                    }).execute()
                    st.success("✅ Task submitted!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")

# ── STOCK PLACEMENT & CROSS CHECK FORMS ──────────────────────────────────────

def form_stock_placement():
    st.subheader("📍 Stock Placement")

    # Area and date filter
    from datetime import timedelta
    c1,c2 = st.columns(2)
    with c1:
        try:
            areas_resp = supabase.table("areas").select("name").eq("active",True).execute()
            area_list = ["All Areas"] + [a["name"] for a in (areas_resp.data or [])]
        except:
            area_list = ["All Areas"]
        default_sp_area_idx = 0
        if st.session_state.get("work_area") and st.session_state.work_area in area_list:
            default_sp_area_idx = area_list.index(st.session_state.work_area)
        sp_area = st.selectbox("Filter by Area", area_list, index=default_sp_area_idx, key="sp_area_filter")
    with c2:
        sp_date = st.date_input("Filter by Date", value=today_ist(), key="sp_date_filter",
            min_value=today_ist()-timedelta(days=7), max_value=today_ist())

    # Load Bill Uploaded arrangements
    try:
        two_days_ago = (sp_date - timedelta(days=2)).strftime("%Y-%m-%d")
        sp_date_str  = sp_date.strftime("%Y-%m-%d")
        arr_resp = supabase.table("arrangements").select("*")\
            .eq("status", "Bill Uploaded")\
            .gte("order_placed_date", two_days_ago)\
            .lte("order_placed_date", sp_date_str)\
            .execute()
        arrangements = arr_resp.data if arr_resp.data else []
        if sp_area != "All Areas":
            arrangements = [a for a in arrangements if a.get("area","") == sp_area]
    except Exception as e:
        st.error(f"Error: {e}")
        arrangements = []

    # Load Normal Orders with bill uploaded
    try:
        from datetime import timedelta
        two_days_ago = (sp_date - timedelta(days=2)).strftime("%Y-%m-%d")
        normal_resp = supabase.table("daily_tasks").select("*")\
            .eq("task_type", "Bill Upload (Software)")\
            .gte("date", two_days_ago)\
            .lte("date", sp_date.strftime("%Y-%m-%d"))\
            .execute()
        normal_orders = []
        for t in (normal_resp.data or []):
            d = t.get("details",{})
            area_match = sp_area == "All Areas" or d.get("area","") == sp_area or d.get("area","") == ""
            if not d.get("arrangement_no","") and not d.get("placement_done") and area_match:
                normal_orders.append(t)
    except:
        normal_orders = []

    if not arrangements and not normal_orders:
        st.info("No items pending placement!")
        return

    st.markdown(f"**Pending:** {len(arrangements)} Arrangements + {len(normal_orders)} Normal Orders")

    # Build combined options
    all_options = {}
    for a in arrangements:
        all_options[f"ARR: #{a.get('arrangement_no')} — {a.get('distributor','')} — {a.get('area','')}"] = {"type": "arrangement", "data": a}
    for n in normal_orders:
        d = n.get("details",{})
        all_options[f"NORMAL: {d.get('distributor','')} — Bill: {d.get('bill_no','')} — Items: {d.get('no_items','')}"] = {"type": "normal", "data": n}

    start = timer_button("stock_placement")
    if start is None:
        return

    selected_label = st.selectbox("Select Item *", list(all_options.keys()), key="sp_arr")
    selected_item  = all_options[selected_label]
    item_type      = selected_item["type"]
    selected_data  = selected_item["data"]

    if item_type == "arrangement":
        st.info(f"📋 Distributor: **{selected_data.get('distributor','')}** | Area: **{selected_data.get('area','')}** | Arrangement: **{selected_data.get('arrangement_no','')}**")
        # Load medicines for arrangement
        try:
            meds_resp = supabase.table("arrangement_medicines").select("*")\
                .eq("arrangement_id", selected_data["id"]).execute()
            medicines = meds_resp.data if meds_resp.data else []
        except:
            medicines = []
    else:
        d = selected_data.get("details",{})
        st.info(f"📋 Distributor: **{d.get('distributor','')}** | Bill: **{d.get('bill_no','')}** | Items: **{d.get('no_items','')}**")
        medicines = []

    with st.form("stock_placement_form", clear_on_submit=True):
        st.markdown("**Enter Box/Rack Location for Each Medicine:**")

        placement_data = {}
        if medicines:
            for med in medicines:
                c1,c2,c3 = st.columns([3,2,2])
                with c1:
                    st.markdown(f"💊 **{med.get('medicine_name','')}** (Qty: {med.get('quantity','')})")
                with c2:
                    location = st.text_input(f"Box/Rack", key=f"loc_{med['id']}", placeholder="e.g. A-1-3-2")
                with c3:
                    qty_placed = st.text_input(f"Qty Placed", key=f"qty_{med['id']}", value=str(med.get('quantity','')))
                placement_data[med['id']] = {
                    "medicine_name": med.get('medicine_name',''),
                    "quantity": med.get('quantity',''),
                    "location": location,
                    "qty_placed": qty_placed
                }
        else:
            if item_type == "arrangement":
                st.warning("No medicines found for this arrangement — they may not have been entered during order placement!")
            total_items = st.number_input("Total Items Placed", min_value=0, step=1)

        st.divider()
        st.markdown("**📸 Photo of Placement Area**")
        placement_img = st.file_uploader("📷 Take photo or choose file",
                type=["jpg","jpeg","png"], key="sp_upload")

        remarks = st.text_input("Remarks")

        if st.form_submit_button("Submit Placement ✅", type="primary", width='stretch'):
            end_time, duration = end_timer("stock_placement", start)
            img_name = upload_image(placement_img, "placement") if placement_img else ""

            try:
                import random
                import json

                # Save placement data
                if item_type == "arrangement":
                    supabase.table("arrangements").update({
                        "status": "Stock Placed",
                        "placed_by": st.session_state.name,
                        "placement_time": end_time,
                        "placement_image": img_name,
                        "placement_data": json.dumps(placement_data),
                    }).eq("id", selected_data["id"]).execute()
                else:
                    d = selected_data.get("details",{})
                    d["placement_done"] = True
                    d["placed_by"] = st.session_state.name
                    d["placement_time"] = end_time
                    d["placement_image"] = img_name
                    supabase.table("daily_tasks").update({
                        "details": d
                    }).eq("id", selected_data["id"]).execute()

                # Randomly select 2 medicines for cross check (only for arrangements)
                if item_type == "arrangement":
                    if medicines and len(medicines) >= 2:
                        check_meds = random.sample(medicines, 2)
                    elif medicines and len(medicines) == 1:
                        check_meds = medicines
                    else:
                        check_meds = []
                else:
                    check_meds = []

                check_list = [{"medicine_name": m.get("medicine_name",""),
                              "quantity": m.get("quantity",""),
                              "location": placement_data.get(m["id"],{}).get("location","")}
                             for m in check_meds]

                if item_type == "arrangement" and check_meds:
                    supabase.table("arrangements").update({
                        "cross_check_medicines": json.dumps(check_list),
                        "cross_check_status": "Pending"
                    }).eq("id", selected_data["id"]).execute()

                # Log daily task
                supabase.table("daily_tasks").insert({
                    "date": date_str(), "time": time_str(),
                    "person": st.session_state.name, "team": st.session_state.team,
                    "task_type": "Stock Placement",
                    "details": {
                        "arrangement_no": selected_data.get("arrangement_no","") if item_type=="arrangement" else "",
                        "bill_no": "" if item_type=="arrangement" else selected_data.get("details",{}).get("bill_no",""),
                        "distributor": selected_data.get("distributor","") if item_type=="arrangement" else selected_data.get("details",{}).get("distributor",""),
                        "no_medicines": str(len(medicines)) if medicines else str(total_items),
                        "placement_image": img_name,
                        "remarks": remarks
                    },
                    "start_time": start.strftime("%I:%M:%S %p"),
                    "end_time": end_time,
                    "duration_mins": str(duration)
                }).execute()

                if check_meds:
                    check_names = " & ".join([m.get("medicine_name","") for m in check_meds])
                    st.success(f"✅ Placement done! Cross check needed for: **{check_names}**")
                else:
                    st.success("✅ Placement done!")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

def form_placement_crosscheck():
    st.subheader("🔍 Placement Cross Check")

    # Load arrangements pending cross check
    try:
        from datetime import timedelta
        two_days_ago = (today_ist() - timedelta(days=2)).strftime("%Y-%m-%d")
        resp = supabase.table("arrangements").select("*")\
            .eq("status", "Stock Placed")\
            .eq("cross_check_status", "Pending")\
            .gte("order_placed_date", two_days_ago)\
            .execute()
        arrangements = resp.data if resp.data else []
    except Exception as e:
        st.error(f"Error: {e}")
        arrangements = []

    if not arrangements:
        st.info("No arrangements pending placement cross check!")
        return

    # Filter out arrangements placed by current user
    others_arrangements = [
        a for a in arrangements
        if a.get("placed_by") != st.session_state.name
    ]

    if not others_arrangements:
        st.warning("⚠️ You placed all pending arrangements! Another team member needs to cross check.")
        return

    arr_options = {
        f"#{a.get('arrangement_no')} — {a.get('distributor','')} — Placed by: {a.get('placed_by','')}": a
        for a in others_arrangements
    }

    with st.form("placement_crosscheck_form", clear_on_submit=True):
        selected_label = st.selectbox("Select Arrangement *", list(arr_options.keys()), key="pc_arr")
        selected_arr   = arr_options[selected_label]

        st.info(f"📋 Placed by: **{selected_arr.get('placed_by','')}** | Arrangement: **{selected_arr.get('arrangement_no','')}**")

        # Show medicines to cross check
        import json
        check_meds = []
        try:
            check_meds = json.loads(selected_arr.get("cross_check_medicines","[]"))
        except:
            check_meds = []

        if check_meds:
            st.markdown("**🔍 Verify these 2 medicines:**")
            results = {}
            for med in check_meds:
                st.markdown(f"💊 **{med.get('medicine_name','')}** | Expected Location: **{med.get('location','')}** | Qty: **{med.get('quantity','')}**")
                c1,c2 = st.columns(2)
                with c1:
                    correct = st.selectbox(
                        f"Is it in correct location?",
                        ["Yes ✅","No ❌"],
                        key=f"cc_{med.get('medicine_name','')}"
                    )
                with c2:
                    qty_ok = st.selectbox(
                        f"Is quantity correct?",
                        ["Yes ✅","No ❌"],
                        key=f"qq_{med.get('medicine_name','')}"
                    )
                results[med.get("medicine_name","")] = {
                    "location_correct": correct,
                    "quantity_correct": qty_ok
                }
                st.divider()

        remarks = st.text_input("Remarks")

        if st.form_submit_button("Submit Cross Check ✅", type="primary", width='stretch'):
            try:
                # Check if any issues found
                issues = [k for k,v in results.items()
                         if "No" in v.get("location_correct","") or "No" in v.get("quantity_correct","")]

                if issues:
                    new_status = "Placement Issue Found"
                    st.warning(f"⚠️ Issues found with: {', '.join(issues)}")
                else:
                    new_status = "Completed"

                supabase.table("arrangements").update({
                    "status": new_status,
                    "cross_check_status": "Done",
                    "cross_checked_by_placement": st.session_state.name,
                    "cross_check_result": json.dumps(results),
                }).eq("id", selected_arr["id"]).execute()

                supabase.table("daily_tasks").insert({
                    "date": date_str(), "time": time_str(),
                    "person": st.session_state.name, "team": st.session_state.team,
                    "task_type": "Placement Cross Check",
                    "details": {
                        "arrangement_no": selected_arr.get("arrangement_no"),
                        "placed_by": selected_arr.get("placed_by"),
                        "results": json.dumps(results),
                        "issues": str(issues),
                        "remarks": remarks
                    },
                    "start_time": time_str(),
                    "end_time": time_str(),
                }).execute()

                if issues:
                    st.error(f"❌ Issues found! Admin has been notified.")
                else:
                    st.success("✅ Cross check passed! Arrangement Completed!")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# ── REGISTER ENTRY FORM ──────────────────────────────────────────────────────

def form_edit_register_entry():
    st.subheader("✏️ Edit Register Entry")
    st.caption("You can edit your own entries within 30 mins. After 30 mins only Admin can edit.")
    try:
        resp = supabase.table("daily_tasks").select("*")\
            .eq("task_type", "Register Entry")\
            .eq("person", st.session_state.name)\
            .eq("date", date_str()).execute()
        entries = resp.data or []
    except Exception as e:
        st.error(f"Error: {e}")
        entries = []

    if not entries:
        st.info("No register entries today!")
        return

    from datetime import datetime as dt
    editable = []
    non_editable = []
    for e in entries:
        try:
            entry_time = dt.strptime(e.get("time",""), "%I:%M %p")
            now_time   = dt.strptime(time_str(), "%I:%M %p")
            diff = int((now_time - entry_time).total_seconds() / 60)
            if diff <= 30:
                editable.append(e)
            else:
                non_editable.append(e)
        except:
            non_editable.append(e)

    if editable:
        st.markdown("**✅ Editable (within 30 mins):**")
        for entry in editable:
            d = entry.get("details",{}) or {}
            with st.expander(f"📒 {d.get('distributor','')} | Bill: {d.get('bill_no','')} | Items: {d.get('no_items','')} | {entry.get('time','')}"):
                with st.form(f"edit_form_{entry['id']}", clear_on_submit=False):
                    c1,c2 = st.columns(2)
                    with c1:
                        new_dist  = st.selectbox("Distributor", dist_options(d.get("distributor","")),
                            index=dist_options(d.get("distributor","")).index(d.get("distributor","")) if d.get("distributor","") else 0,
                            key=f"ed_dist_{entry['id']}")
                        new_bill  = st.text_input("Bill Number", value=d.get("bill_no",""), key=f"ed_bill_{entry['id']}")
                        new_items = st.number_input("No of Items", value=int(float(d.get("no_items",0) or 0)), min_value=0, step=1, key=f"ed_items_{entry['id']}")
                    with c2:
                        new_amount = st.number_input("Bill Amount (₹)", value=float(d.get("bill_amount",0) or 0), min_value=0.0, step=100.0, key=f"ed_amount_{entry['id']}")
                        new_delby  = st.selectbox("Delivered By", ["Distributor","Porter","Naresh","Sandeep","Other"],
                            index=["Distributor","Porter","Naresh","Sandeep","Other"].index(d.get("delivery_by","Distributor")) if d.get("delivery_by","") in ["Distributor","Porter","Naresh","Sandeep","Other"] else 0,
                            key=f"ed_delby_{entry['id']}")
                    edit_reason = st.text_input("Reason for Edit *", key=f"ed_reason_{entry['id']}")
                    if st.form_submit_button("Save Changes ✅", type="primary"):
                        if not edit_reason:
                            st.error("Enter reason for edit!")
                        else:
                            try:
                                supabase.table("daily_tasks").update({
                                    "details": {
                                        "distributor": new_dist,
                                        "bill_no": new_bill,
                                        "no_items": str(new_items),
                                        "bill_amount": str(new_amount),
                                        "delivery_by": new_delby,
                                        "edited": True,
                                        "edit_reason": edit_reason,
                                        "edited_by": st.session_state.name,
                                        "edit_time": time_str(),
                                        "original": d
                                    }
                                }).eq("id", entry["id"]).execute()
                                st.success("✅ Entry updated!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
    else:
        st.warning("⏰ 30 min window passed! Contact Admin to edit.")

    if non_editable:
        st.divider()
        st.markdown("**🔒 Locked entries:**")
        for entry in non_editable:
            d = entry.get("details",{}) or {}
            st.markdown(f"- {entry.get('time','')} | {d.get('distributor','')} | Bill: {d.get('bill_no','')} | Items: {d.get('no_items','')} | ₹{d.get('bill_amount','')}")

def form_register_entry():
    st.subheader("📒 Register Entry")
    st.caption("Quick entry when stock arrives — no need to make distributor/porter wait!")

    # Order type + arrangement picker OUTSIDE the form so the ARR list appears immediately
    order_type = st.radio("Order Type *", ["Normal Order","Arrangement"], horizontal=True, key="re_type")
    arr_no, arr_dist, arr_area = "", None, None
    if order_type == "Arrangement":
        try:
            from datetime import timedelta
            two_days_ago = (today_ist() - timedelta(days=2)).strftime("%Y-%m-%d")
            resp = supabase.table("arrangements").select("*")\
                .eq("status", "Reached Warehouse")\
                .gte("order_placed_date", two_days_ago)\
                .execute()
            reg_done = supabase.table("daily_tasks").select("details")\
                .eq("task_type", "Register Entry").gte("date", two_days_ago).execute()
            registered = set(str((t.get("details") or {}).get("arrangement_no","")) for t in (reg_done.data or []))
            arr_list = [a for a in (resp.data or []) if str(a.get("arrangement_no","")) not in registered]
            if arr_list:
                arr_map = {f"#{a.get('arrangement_no')} — {a.get('distributor','')} — {a.get('area','')}": a for a in arr_list}
                arr_select = st.selectbox("Arrangement No *", ["— Select Arrangement —"] + list(arr_map.keys()), key="re_arr")
                if arr_select in arr_map:
                    arr_no   = str(arr_map[arr_select].get("arrangement_no",""))
                    arr_dist = arr_map[arr_select].get("distributor")
                    arr_area = arr_map[arr_select].get("area")
            else:
                st.warning("No arrangements waiting for register entry. The ARR must first be marked "
                           "'Reached Warehouse' in 📦 Receive Porter.")
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("📸 **Image of Packet/Box (Mandatory — take photo BEFORE opening)**")
    st.caption("⚠️ Take photo of sealed packet/box before opening — prevents disputes later!")
    invoice_img = st.file_uploader("📷 Take photo or choose file", type=["jpg","jpeg","png"], key=photo_key("re_upload"))
    if invoice_img is None:
        st.info("📷 **Step 1: take the photo (or choose a file).** The form opens after that.")
    else:
        remember_photo(invoice_img, "re_upload")
        with st.form("register_entry_form", clear_on_submit=True):
            c1,c2 = st.columns(2)
            with c1:
                dist_idx    = dist_options(arr_dist).index(arr_dist) if arr_dist else 0
                distributor = st.selectbox("Distributor *", dist_options(arr_dist), index=dist_idx, key=f"re_dist_{arr_no}")
                bill_no     = st.text_input("Bill Number *")
            with c2:
                no_items    = st.number_input("No of Items Received *", min_value=0, step=1)
                delivery_by = st.selectbox("Delivered By", ["Distributor","Porter","Naresh","Sandeep","Other"], key="re_delby")
                try:
                    areas_resp = supabase.table("areas").select("name").eq("active",True).execute()
                    area_options = [a["name"] for a in (areas_resp.data or [])]
                except:
                    area_options = ["Gaur City","Sector 78","Indirapuram"]
                default_re_area = 0
                if arr_area and arr_area in area_options:
                    default_re_area = area_options.index(arr_area)
                elif st.session_state.get("work_area") and st.session_state.work_area in area_options:
                    default_re_area = area_options.index(st.session_state.work_area)
                re_area = st.selectbox("Warehouse/Area *", area_options, index=default_re_area, key=f"re_area_{arr_no}")


            bill_amount = st.number_input("Bill Amount (₹)", min_value=0.0, step=100.0, key="re_amount")
            remarks = st.text_input("Remarks", placeholder="Any notes about delivery condition...")

            if st.form_submit_button("Submit Entry ✅", type="primary", width='stretch'):
                if not bill_no or no_items == 0:
                    st.error("Fill Bill Number and No of Items!")
                elif order_type == "Arrangement" and not arr_no:
                    st.error("Select the Arrangement No at the top — so this bill is linked to its ARR!")
                elif not invoice_img:
                    st.error("⚠️ Invoice image is mandatory! Please upload or take photo.")
                else:
                    img_name = upload_image(invoice_img, "invoice") if invoice_img else ""
                    # Check duplicate bill number - show warning
                    try:
                        dup_check = supabase.table("daily_tasks").select("*")\
                            .eq("task_type", "Register Entry")\
                            .eq("date", date_str())\
                            .execute()
                        existing_bills = [t.get("details",{}).get("bill_no","").strip()
                                         for t in (dup_check.data or [])]
                        if bill_no.strip() in existing_bills:
                            st.warning(f"⚠️ Bill No **{bill_no}** already entered today!")
                    except:
                        pass
                    try:
                        supabase.table("daily_tasks").insert({
                            "date": date_str(),
                            "time": time_str(),
                            "person": st.session_state.name,
                            "team": st.session_state.team,
                            "task_type": "Register Entry",
                            "details": {
                                "order_type": order_type,
                                "distributor": distributor,
                                "bill_no": bill_no,
                                "bill_amount": str(bill_amount),
                                "no_items": str(no_items),
                                "delivery_by": delivery_by,
                                "arrangement_no": arr_no,
                                "area": re_area,
                                "invoice_image": img_name,
                                "remarks": remarks
                            },
                            "start_time": time_str(),
                            "end_time": time_str(),
                        }).execute()
                        st.success(f"✅ Register entry done! {no_items} items from {distributor} received!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Error: {e}")

# ── BILL CROSS CHECK & UPLOAD FORMS ──────────────────────────────────────────

def form_bill_crosscheck():
    st.subheader("✔️ Bill Cross Check")

    # Area and date filter FIRST - before summary
    from datetime import timedelta, datetime as dt
    c1,c2 = st.columns(2)
    with c1:
        try:
            areas_resp = supabase.table("areas").select("name").eq("active",True).execute()
            area_list = ["All Areas"] + [a["name"] for a in (areas_resp.data or [])]
        except:
            area_list = ["All Areas"]
        # Default to work area
        default_area_idx = 0
        work_area = st.session_state.get("work_area","")
        if work_area and work_area in area_list:
            default_area_idx = area_list.index(work_area)
        bc_area = st.selectbox("Filter by Area", area_list, index=default_area_idx, key="bc_area_filter")
    with c2:
        bc_date = st.date_input("Filter by Date", value=today_ist(), key="bc_date_filter",
            min_value=today_ist()-timedelta(days=7), max_value=today_ist(),
            help="Select yesterday to see bills entered last night")

    # ── PENDING BILLS SUMMARY ─────────────────────────────────────────────────
    try:
        two_days_ago = (bc_date - timedelta(days=2)).strftime("%Y-%m-%d")

        # Pending arrangements
        arr_pending = supabase.table("arrangements").select("*")\
            .eq("status", "Reached Warehouse")\
            .gte("order_placed_date", two_days_ago)\
            .execute()

        # Pending normal orders (last 2 days)
        reg_pending = supabase.table("daily_tasks").select("*")\
            .eq("task_type", "Register Entry")\
            .eq("date", bc_date.strftime("%Y-%m-%d"))\
            .execute()

        # Cross checked bills
        crossed = supabase.table("daily_tasks").select("*")\
            .eq("task_type", "Bill Cross Check")\
            .gte("date", two_days_ago)\
            .execute()
        crossed_bills = [t.get("details",{}).get("bill_no","") for t in (crossed.data or [])]

        # Normal orders pending cross check
        normal_pending = [t for t in (reg_pending.data or [])
            if not t.get("details",{}).get("cross_checked")
            and not t.get("details",{}).get("arrangement_no")      # arrangement bills are checked via their ARR
            and t.get("details",{}).get("bill_no","") not in crossed_bills]

        # Apply work area filter from session state
        work_area = st.session_state.get("work_area","All Areas")
        if work_area != "All Areas":
            arr_pending_data = [a for a in (arr_pending.data or []) if a.get("area","") == work_area]
            normal_pending = [t for t in normal_pending if t.get("details",{}).get("area","") == work_area]
        else:
            arr_pending_data = arr_pending.data or []

        # Build area wise summary
        area_summary = {}
        now_time = dt.strptime(time_str(), "%I:%M %p")

        # From arrangements
        for arr in arr_pending_data:
            area = arr.get("area","Unknown")
            if area not in area_summary:
                area_summary[area] = {"count": 0, "oldest_wait": 0, "total_wait": 0}
            area_summary[area]["count"] += 1
            try:
                arr_time = dt.strptime(arr.get("order_placed_time",""), "%I:%M %p")
                wait = int((now_time - arr_time).total_seconds() / 60)
                if wait > area_summary[area]["oldest_wait"]:
                    area_summary[area]["oldest_wait"] = wait
                area_summary[area]["total_wait"] += wait
            except:
                pass

        # From normal orders
        for n in normal_pending:
            area = n.get("details",{}).get("area","Unknown")
            if area not in area_summary:
                area_summary[area] = {"count": 0, "oldest_wait": 0, "total_wait": 0}
            area_summary[area]["count"] += 1
            try:
                reg_time = dt.strptime(n.get("time",""), "%I:%M %p")
                wait = int((now_time - reg_time).total_seconds() / 60)
                if wait > area_summary[area]["oldest_wait"]:
                    area_summary[area]["oldest_wait"] = wait
                area_summary[area]["total_wait"] += wait
            except:
                pass

        if area_summary:
            total_pending = sum([v["count"] for v in area_summary.values()])
            st.warning(f"⚠️ **{total_pending} bills pending cross check!**")

            # Show table
            summary_rows = []
            for area, data in area_summary.items():
                oldest = data["oldest_wait"]
                avg_wait = round(data["total_wait"] / data["count"], 0) if data["count"] > 0 else 0
                if oldest > 60:
                    oldest_str = f"🔴 {oldest//60}h {oldest%60}m"
                elif oldest > 30:
                    oldest_str = f"🟡 {oldest} mins"
                else:
                    oldest_str = f"🟢 {oldest} mins"
                summary_rows.append({
                    "Area": area,
                    "Pending Bills": data["count"],
                    "Oldest Waiting": oldest_str,
                    "Avg Wait (mins)": int(avg_wait)
                })

            import pandas as pd
            st.dataframe(pd.DataFrame(summary_rows), width='stretch')
            st.divider()
        else:
            st.success("✅ No bills pending cross check!")

    except Exception as e:
        st.error(f"Error loading summary: {e}")

    # Start timer at TOP so they dont have to scroll
    start = timer_button("bill_crosscheck", "Bill Cross Check")
    if start is None:
        return


    # Load arrangements that reached warehouse
    try:
        two_days_ago = (bc_date - timedelta(days=2)).strftime("%Y-%m-%d")
        resp = supabase.table("arrangements").select("*")\
            .eq("status", "Reached Warehouse")\
            .gte("order_placed_date", two_days_ago)\
            .lte("order_placed_date", bc_date.strftime("%Y-%m-%d"))\
            .execute()
        arrangements = resp.data if resp.data else []
        if bc_area != "All Areas":
            arrangements = [a for a in arrangements if a.get("area","") == bc_area]
    except Exception as e:
        st.error(f"Error: {e}")
        arrangements = []

    # Load normal orders from register entry
    try:
        # Show register entries from bc_date and day before
        normal_resp = supabase.table("daily_tasks").select("*")\
            .eq("task_type", "Register Entry")\
            .gte("date", (bc_date - timedelta(days=1)).strftime("%Y-%m-%d"))\
            .lte("date", bc_date.strftime("%Y-%m-%d"))\
            .execute()
        normal_orders = normal_resp.data if normal_resp.data else []
        # Filter out already cross checked
        normal_orders = [n for n in normal_orders
                        if not n.get("details",{}).get("cross_checked")
                        and not n.get("details",{}).get("arrangement_no")]   # arrangement bills are checked via their ARR
        # Apply area filter
        if bc_area != "All Areas":
            normal_orders = [n for n in normal_orders 
                           if n.get("details",{}).get("area","") == bc_area]
    except:
        normal_orders = []

    if not arrangements and not normal_orders:
        st.info("No items pending cross check!")
        return

    # Show pending items
    if normal_orders:
        st.markdown("### 📦 Normal Orders Pending Cross Check")
        for n in normal_orders:
            d = n.get("details",{})
            st.markdown(f"🧾 **{d.get('distributor','')}** | Bill: **{d.get('bill_no','')}** | Items: **{d.get('no_items','')}** | Amount: ₹**{d.get('bill_amount','')}**")
        st.divider()

    # Combine options
    arr_options = {}
    for a in arrangements:
        arr_options[f"ARR: #{a.get('arrangement_no')} — {a.get('distributor','')} — {a.get('area','')}"] = {"type": "arrangement", "data": a}
    for n in normal_orders:
        d = n.get("details",{})
        arr_options[f"NORMAL: {d.get('distributor','')} — Bill: {d.get('bill_no','')} — Items: {d.get('no_items','')}"] = {"type": "normal", "data": n}

    # Selection OUTSIDE the form so details + bill number update when a different bill is picked
    selected_label = st.selectbox("Select Item *", list(arr_options.keys()), key="bc_arr")
    selected_item  = arr_options[selected_label]
    item_type      = selected_item["type"]
    selected_data  = selected_item["data"]

    if item_type == "arrangement":
        st.info(f"📋 Distributor: **{selected_data.get('distributor','')}** | Area: **{selected_data.get('area','')}** | Arrangement: **{selected_data.get('arrangement_no','')}**")
        # Bill number from Register Entry of this ARR (fallback: bill/order id typed at ARR creation)
        default_bill = selected_data.get("bill_order_id","") or ""
        try:
            re_rows = supabase.table("daily_tasks").select("details")\
                .eq("task_type", "Register Entry")\
                .gte("date", (bc_date - timedelta(days=3)).strftime("%Y-%m-%d")).execute().data or []
            for t in re_rows:
                dd = t.get("details") or {}
                if str(dd.get("arrangement_no","")) == str(selected_data.get("arrangement_no","")) and dd.get("bill_no"):
                    default_bill = dd.get("bill_no")
                    break
        except Exception:
            pass
    else:
        d = selected_data.get("details",{})
        st.info(f"📋 Distributor: **{d.get('distributor','')}** | Bill: **{d.get('bill_no','')}** | Items: **{d.get('no_items','')}** | Amount: ₹**{d.get('bill_amount','')}**")
        default_bill = d.get("bill_no","")

    # Customer order items linked to this arrangement -> confirm received qty here
    cust_items = customer_items_editor(selected_data) if item_type == "arrangement" else None

    st.markdown("📸 **Image of Physical Bill After Cross Check (Mandatory)**")
    st.caption("⚠️ Take photo of bill after you have checked and marked it — this is your proof of checking!")
    bill_check_img = st.file_uploader("📷 Take photo or choose file", type=["jpg","jpeg","png"], key=photo_key("cc_img_upload"))
    if bill_check_img is None:
        st.info("📷 **Step 1: take the photo (or choose a file).** The form opens after that.")
    else:
        remember_photo(bill_check_img, "cc_img_upload")
        with st.form("bill_crosscheck_form", clear_on_submit=True):
            bill_no = st.text_input("Bill Number", value=default_bill, key=f"bc_billno_{item_type}_{selected_data.get('id','')}")

            c1,c2,c3 = st.columns(3)
            with c1:
                no_items     = st.number_input("No of Items Checked *", min_value=0, step=1)
                near_expiry  = st.number_input("Near Expiry Items", min_value=0, step=1)
                damaged      = st.number_input("Damaged Items", min_value=0, step=1)
            with c2:
                contra       = st.number_input("Contra Items (Wrong Medicine)", min_value=0, step=1)
                wrong_batch  = st.number_input("Wrong Batch", min_value=0, step=1)
                wrong_disc   = st.number_input("Wrong Discount", min_value=0, step=1)
            with c3:
                wrong_calc   = st.number_input("Wrong Calculation", min_value=0, step=1)
                shortage     = st.number_input("Shortage Items", min_value=0, step=1)

            st.divider()

            st.markdown("📝 **Comments/Notes on Bill**")
            bill_comments = st.text_area("Write any comments, notes or issues found on bill",
                placeholder="e.g. Batch no written incorrectly, discount not matching, item substituted...")

            st.markdown("---")
            st.markdown("📹 **Video Evidence (Optional)**")
            st.markdown("[📁 Open RapidSurge Stock Videos Folder](https://drive.google.com/drive/folders/1DbkuKSFeftMVpVFqVwcRRDssc49X9YJQ)")
            st.caption("Record video → Upload to folder → Copy link → Paste below")
            video_link = st.text_input("Paste Video Link", placeholder="https://drive.google.com/file/d/...")
            remarks = st.text_input("Remarks")

            if st.form_submit_button("Submit Cross Check ✅", type="primary", width='stretch'):
                if no_items < 1:
                    st.error("Enter No of Items Checked (at least 1)!")
                    return
                end_time, duration = end_timer("bill_crosscheck", start)
                # Calculate avg time per item
                avg_time = round(duration / no_items, 2) if no_items > 0 else 0

                try:
                    # Update status based on type
                    if item_type == "arrangement":
                        supabase.table("arrangements").update({
                            "status": "Bill Cross Checked",
                            "cross_checked_by": st.session_state.name,
                            "cross_check_time": end_time,
                        }).eq("id", selected_data["id"]).execute()
                        dist = selected_data.get("distributor","")
                        arr_no = selected_data.get("arrangement_no","")
                        if cust_items is not None and not cust_items.empty:
                            n_ok, n_short = save_customer_receipts(cust_items)
                            st.info(f"🧾 Customer items: {n_ok} received · {n_short} short")
                    else:
                        # Mark normal order as cross checked
                        d = selected_data.get("details",{})
                        d["cross_checked"] = True
                        d["cross_checked_by"] = st.session_state.name
                        d["cross_check_time"] = end_time
                        supabase.table("daily_tasks").update({
                            "details": d
                        }).eq("id", selected_data["id"]).execute()
                        dist = d.get("distributor","")
                        arr_no = ""

                    # Save to daily tasks
                    supabase.table("daily_tasks").insert({
                        "date": date_str(), "time": time_str(),
                        "person": st.session_state.name, "team": st.session_state.team,
                        "task_type": "Bill Cross Check",
                        "details": {
                            "arrangement_no": arr_no,
                            "bill_no": bill_no,
                            "no_items": str(no_items),
                            "near_expiry": str(near_expiry),
                            "damaged": str(damaged),
                            "contra": str(contra),
                            "wrong_batch": str(wrong_batch),
                            "wrong_discount": str(wrong_disc),
                            "wrong_calculation": str(wrong_calc),
                            "shortage": str(shortage),
                            "avg_time_per_item": str(avg_time),
                            "remarks": remarks,
                            "bill_comments": bill_comments,
                            "video_link": video_link,
                            "bill_check_image": upload_image(bill_check_img, "bill_check") if bill_check_img else "",
                            "area": bc_area if bc_area != "All Areas" else "",
                            "distributor": selected_data.get("distributor","") if item_type=="arrangement" else selected_data.get("details",{}).get("distributor","")
                        },
                        "start_time": start.strftime("%I:%M:%S %p"),
                        "end_time": end_time,
                        "duration_mins": str(duration)
                    }).execute()

                    st.success(f"✅ Bill Cross Check done! Avg time per item: {avg_time} mins")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

def form_bill_upload_arrangement():
    st.subheader("📤 Bill Upload (Software Screenshot)")
    st.info("📌 Upload screenshot of bill from your **billing software** — NOT the physical bill from distributor!")

    # Area and date filter
    from datetime import timedelta
    c1,c2,c3 = st.columns(3)
    with c1:
        try:
            areas_resp = supabase.table("areas").select("name").eq("active",True).execute()
            area_list = ["All Areas"] + [a["name"] for a in (areas_resp.data or [])]
        except:
            area_list = ["All Areas"]
        default_bu_area_idx = 0
        if st.session_state.get("work_area") and st.session_state.work_area in area_list:
            default_bu_area_idx = area_list.index(st.session_state.work_area)
        bu_area = st.selectbox("Filter by Area", area_list, index=default_bu_area_idx, key="bu_area_filter")
    with c2:
        bu_date = st.date_input("Filter by Date", value=today_ist(), key="bu_date_filter",
            min_value=today_ist()-timedelta(days=7), max_value=today_ist())
    with c3:
        order_type_filter = st.selectbox("Order Type", ["All","Arrangement","Normal Order"], key="bu_type_filter")

    start = timer_button("bill_upload", "Bill Upload")
    if start is None:
        return

    # Load cross checked arrangements
    try:
        two_days_ago = (bu_date - timedelta(days=2)).strftime("%Y-%m-%d")
        arr_resp = supabase.table("arrangements").select("*")\
            .eq("status", "Bill Cross Checked")\
            .gte("order_placed_date", two_days_ago)\
            .lte("order_placed_date", bu_date.strftime("%Y-%m-%d"))\
            .execute()
        arrangements = arr_resp.data if arr_resp.data else []
        if bu_area != "All Areas":
            arrangements = [a for a in arrangements if a.get("area","") == bu_area]
    except Exception as e:
        st.error(f"Error: {e}")
        arrangements = []

    # Load cross checked normal orders
    try:
        normal_resp = supabase.table("daily_tasks").select("*")\
            .eq("task_type", "Bill Cross Check")\
            .eq("date", bu_date.strftime("%Y-%m-%d"))\
            .execute()
        cross_checked_normal = []
        for t in (normal_resp.data or []):
            d = t.get("details",{})
            area_match = bu_area == "All Areas" or d.get("area","") == bu_area or d.get("area","") == ""
            if not d.get("arrangement_no","") and not d.get("bill_uploaded") and area_match:
                cross_checked_normal.append(t)
    except:
        cross_checked_normal = []

    # Apply order type filter
    if order_type_filter == "Arrangement":
        cross_checked_normal = []
    elif order_type_filter == "Normal Order":
        arrangements = []

    if not arrangements and not cross_checked_normal:
        st.info("No items pending bill upload!")
        return

    st.markdown(f"**Pending:** {len(arrangements)} Arrangements + {len(cross_checked_normal)} Normal Orders")

    # Build combined options
    all_options = {}
    for a in arrangements:
        all_options[f"ARR: #{a.get('arrangement_no')} — {a.get('distributor','')} — {a.get('area','')}"] = {"type": "arrangement", "data": a}
    for n in cross_checked_normal:
        d = n.get("details",{})
        all_options[f"NORMAL: {d.get('distributor','')} — Bill: {d.get('bill_no','')} — Items: {d.get('no_items','')}"] = {"type": "normal", "data": n}

    st.markdown("📸 **Software Bill Screenshot (Mandatory)**")
    bill_img = st.file_uploader("📷 Take photo or choose file",
            type=["jpg","jpeg","png","pdf"], key=photo_key("ba_upload"))
    if bill_img is None:
        st.info("📷 **Step 1: take the photo (or choose a file).** The form opens after that.")
    else:
        remember_photo(bill_img, "ba_upload")
        with st.form("bill_upload_arr_form", clear_on_submit=True):
            selected_label = st.selectbox("Select Item *", list(all_options.keys()), key="ba_arr")
            selected_item  = all_options[selected_label]
            item_type      = selected_item["type"]
            selected_data  = selected_item["data"]

            if item_type == "arrangement":
                auto_bill_no = selected_data.get("bill_order_id","")
                auto_dist    = selected_data.get("distributor","")
                auto_area    = selected_data.get("area","")
                auto_items   = 0
                auto_amount  = 0.0
                st.info(f"📋 Distributor: **{auto_dist}** | Area: **{auto_area}** | Type: **Arrangement**")
            else:
                d = selected_data.get("details",{})
                auto_bill_no = d.get("bill_no","")
                auto_dist    = d.get("distributor","")
                auto_area    = d.get("area","")
                auto_items   = int(float(d.get("no_items",0) or 0))
                auto_amount  = float(d.get("bill_amount",0) or 0)
                st.info(f"📋 Distributor: **{auto_dist}** | Bill: **{auto_bill_no}** | Items: **{auto_items}** | Type: **Normal Order**")

            c1,c2 = st.columns(2)
            with c1:
                bill_no   = st.text_input("Bill Number *", value=auto_bill_no)
                bill_date = st.date_input("Bill Date")
                bill_amt  = st.number_input("Bill Amount (₹)", min_value=0.0, step=100.0, value=auto_amount)
            with c2:
                no_items  = st.number_input("No of Items", min_value=0, step=1, value=auto_items)


            remarks = st.text_input("Remarks")

            if st.form_submit_button("Upload Bill ✅", type="primary", width='stretch'):
                if not bill_no:
                    st.error("Enter Bill Number!")
                elif not bill_img:
                    st.error("⚠️ Bill screenshot is mandatory!")
                else:
                    end_time, duration = end_timer("bill_upload", start)
                    img_name = upload_image(bill_img, "bill_arr") if bill_img else ""
                    try:
                        if item_type == "arrangement":
                            supabase.table("arrangements").update({
                                "status": "Bill Uploaded",
                                "bill_uploaded_by": st.session_state.name,
                                "bill_upload_time": time_str(),
                                "bill_image_arr": img_name,
                            }).eq("id", selected_data["id"]).execute()
                            arr_no = selected_data.get("arrangement_no","")
                            dist   = selected_data.get("distributor","")
                        else:
                            d = selected_data.get("details",{})
                            d["bill_uploaded"] = True
                            d["bill_uploaded_by"] = st.session_state.name
                            d["bill_upload_time"] = time_str()
                            supabase.table("daily_tasks").update({
                                "details": d
                            }).eq("id", selected_data["id"]).execute()
                            arr_no = ""
                            dist   = d.get("distributor","")

                        supabase.table("daily_tasks").insert({
                            "date": date_str(), "time": time_str(),
                            "person": st.session_state.name, "team": st.session_state.team,
                            "task_type": "Bill Upload (Software)",
                            "details": {
                                "arrangement_no": arr_no,
                                "distributor": dist,
                                "bill_no": bill_no,
                                "bill_date": str(bill_date),
                                "bill_amount": str(bill_amt),
                                "no_items": str(no_items),
                                "order_type": item_type,
                                "bill_image": img_name,
                                "remarks": remarks
                            },
                            "start_time": start.strftime("%I:%M:%S %p"),
                            "end_time": end_time,
                            "duration_mins": str(duration),
                            "status": "Completed"
                        }).execute()

                        st.success("✅ Bill uploaded successfully!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")


def show_pickup_images():
    st.subheader("📸 Pickup Images from Naresh/Sandeep")
    try:
        from datetime import timedelta
        two_days_ago = (today_ist() - timedelta(days=2)).strftime("%Y-%m-%d")
        resp = supabase.table("daily_tasks").select("*")\
            .eq("task_type", "Pickup")\
            .eq("team", "Delivery")\
            .gte("date", two_days_ago)\
            .execute()
        pickups = resp.data if resp.data else []
    except Exception as e:
        st.error(f"Error: {e}")
        pickups = []

    if not pickups:
        st.info("No pickup images found for last 2 days!")
        return

    c1,c2,c3 = st.columns(3)
    with c1:
        filter_date = st.date_input("Filter by Date", value=today_ist(), key="pi_date")
    with c2:
        filter_dist = st.text_input("Search Distributor", placeholder="Type to search...", key="pi_dist")
    with c3:
        filter_arr = st.text_input("Arrangement No", placeholder="e.g. ARR-001", key="pi_arr")

    filter_date_str = filter_date.strftime("%Y-%m-%d")
    filtered = [p for p in pickups if p.get("date","") == filter_date_str]
    if filter_dist:
        filtered = [p for p in filtered if filter_dist.lower() in p.get("details",{}).get("distributor","").lower()]
    if filter_arr:
        filtered = [p for p in filtered if filter_arr.lower() in p.get("details",{}).get("arrangement_no","").lower()]

    st.markdown(f"**{len(filtered)} pickup entries found**")

    for p in filtered:
        d = p.get("details",{})
        img_name = d.get("medicine_image","")
        with st.expander(f"📦 {d.get('distributor','')} | Arr: {d.get('arrangement_no','')} | By: {p.get('person','')} | {p.get('start_time','')}"):
            c1,c2 = st.columns([2,1])
            with c1:
                if img_name:
                    try:
                        img_data = supabase.storage.from_("Images").download(img_name)
                        from PIL import Image
                        import io as io_module
                        img = Image.open(io_module.BytesIO(img_data))
                        st.image(img, width='stretch')
                        st.download_button("🔍 Download",
                            img_data,
                            file_name=f"pickup_{d.get('arrangement_no','')}.jpg",
                            mime="image/jpeg",
                            key=f"dl_pickup_{p['id']}")
                    except:
                        st.warning("Image not available")
                else:
                    st.warning("⚠️ No image uploaded!")
            with c2:
                st.markdown(f"**Distributor:** {d.get('distributor','')}")
                st.markdown(f"**Arrangement:** {d.get('arrangement_no','')}")
                st.markdown(f"**Picked by:** {p.get('person','')}")
                st.markdown(f"**Time:** {p.get('start_time','')}")
                st.markdown(f"**SKUs:** {d.get('no_sku_received','')}")

def form_book_porter():
    st.subheader("🚛 Book Porter")

    # Load pending arrangements
    try:
        from datetime import timedelta
        two_days_ago = (today_ist() - timedelta(days=2)).strftime("%Y-%m-%d")
        resp = supabase.table("arrangements").select("*")\
            .in_("status", ["Pending", "Picked Up - In Transit"])\
            .gte("order_placed_date", two_days_ago)\
            .execute()
        arrangements = resp.data if resp.data else []
    except Exception as e:
        st.error(f"Error loading arrangements: {e}")
        arrangements = []

    with st.form("book_porter_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            # Auto-generate System Porter ID
            try:
                today_str = date_str()
                existing = supabase.table("porter_bookings").select("porter_no")\
                    .like("porter_no", f"PRT-{today_str}-%")\
                    .execute()
                next_num = len(existing.data or []) + 1
                auto_porter_no = f"PRT-{today_str}-{next_num:03d}"
            except:
                auto_porter_no = f"PRT-{date_str()}-001"
            porter_no    = st.text_input("System Porter ID", value=auto_porter_no,
                help="Auto-generated ID for tracking")
            porter_phone = st.text_input("Porter Phone Number *",
                placeholder="e.g. 9876543210",
                help="Actual porter contact number")
            vehicle_no   = st.text_input("Vehicle Number", placeholder="e.g. UP16 AB 1234")
            pickup_point = st.text_input("Pickup Point *", placeholder="Distributor name/address")
        with c2:
            delivery_point = st.selectbox("Delivery Point *", load_warehouses(), key="pb_delivery")
            booked_via     = st.selectbox("Booked Via", ["Phone Call","Porter App","WhatsApp","Other"], key="pb_via")

        # Select multiple arrangements
        if arrangements:
            arr_options = [f"#{a.get('arrangement_no')} — {a.get('distributor')} — {a.get('area','')}" for a in arrangements]
            selected_arrs = st.multiselect("Link Arrangements *", arr_options, key="pb_arrs")
        else:
            st.warning("No pending arrangements found!")
            selected_arrs = []

        remarks = st.text_input("Remarks")

        if st.form_submit_button("Book Porter ✅", type="primary", width='stretch'):
            if not porter_phone or not pickup_point or not delivery_point:
                st.error("Fill Porter Phone, Pickup and Delivery Point!")
            elif not selected_arrs:
                st.error("Select at least one arrangement!")
            else:
                try:
                    # Extract arrangement nos
                    arr_nos = [a.split("—")[0].replace("#","").strip() for a in selected_arrs]
                    arr_ids = [a["id"] for a in arrangements if str(a.get("arrangement_no")) in arr_nos]

                    # Save porter booking
                    result = supabase.table("porter_bookings").insert({
                        "date": date_str(),
                        "time": time_str(),
                        "booked_by": st.session_state.name,
                        "porter_no": porter_no,
                        "porter_phone": porter_phone,
                        "vehicle_no": vehicle_no,
                        "pickup_point": pickup_point,
                        "delivery_point": delivery_point,
                        "booked_via": booked_via,
                        "arrangement_nos": ", ".join(arr_nos),
                        "status": "Booked",
                        "remarks": remarks
                    }).execute()
                    porter_id = result.data[0]["id"]

                    # Update arrangement status
                    for arr_id in arr_ids:
                        supabase.table("arrangements").update({
                            "status": "Porter Booked",
                            "porter_no": porter_no,
                        }).eq("id", arr_id).execute()

                    st.success(f"✅ Porter {porter_no} booked successfully!")
                    st.info(f"Arrangements linked: {', '.join(arr_nos)}")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")

def form_porter_handover():
    st.subheader("🚛 Handover to Porter")

    # Date filter
    from datetime import timedelta
    handover_date = st.date_input("Filter by Date", value=today_ist(), key="handover_date",
        min_value=today_ist()-timedelta(days=7), max_value=today_ist())

    # Load porter booked arrangements
    try:
        resp = supabase.table("porter_bookings").select("*")\
            .eq("status", "Booked")\
            .eq("date", handover_date.strftime("%Y-%m-%d"))\
            .execute()
        bookings = resp.data if resp.data else []
    except Exception as e:
        st.error(f"Error: {e}")
        bookings = []

    if not bookings:
        st.info("No porter bookings pending handover!")
        return

    # Show pending bookings
    st.markdown(f"**{len(bookings)} porter booking(s) pending handover:**")
    for b in bookings:
        st.markdown(f"🚛 Porter: **{b.get('porter_no')}** | Vehicle: **{b.get('vehicle_no','')}** | Arrangements: **{b.get('arrangement_nos','')}** | Pickup: **{b.get('pickup_point','')}** | Delivery: **{b.get('delivery_point','')}**")
    st.divider()

    # Build label showing arrangement + area/warehouse
    def get_arr_label(arr_nos_str):
        arr_nos = [a.strip() for a in arr_nos_str.split(",")]
        labels = []
        for arr_no in arr_nos:
            try:
                resp = supabase.table("arrangements").select("arrangement_no,area")\
                    .eq("arrangement_no", arr_no.strip()).execute()
                if resp.data:
                    area = resp.data[0].get("area","")
                    labels.append(f"{arr_no}({area})")
                else:
                    labels.append(arr_no)
            except:
                labels.append(arr_no)
        return ", ".join(labels)

    booking_options = {
        f"Porter:{b.get('porter_no')} | {get_arr_label(b.get('arrangement_nos',''))}": b
        for b in bookings
    }

    with st.form("porter_handover_form", clear_on_submit=True):
        selected_booking_label = st.selectbox("Select Porter Booking *", list(booking_options.keys()), key="ph_select")
        selected_booking = booking_options[selected_booking_label]

        st.info(f"🚛 Porter: **{selected_booking.get('porter_no')}** | Vehicle: **{selected_booking.get('vehicle_no','')}** | Going to: **{selected_booking.get('delivery_point','')}**")

        c1,c2 = st.columns(2)
        with c1:
            no_bills     = st.number_input("No of Bills Given to Porter", min_value=0, step=1)
            no_polythene = st.number_input("No of Polythene Given", min_value=0, step=1)
        with c2:
            handover_time = st.time_input("Handover Time", key="ph_time")

        st.markdown("📸 **Image of Handover**")
        handover_img = st.file_uploader("📷 Take photo or choose file", type=["jpg","jpeg","png"], key="ph_upload")

        remarks = st.text_input("Remarks")

        if st.form_submit_button("Submit Handover ✅", type="primary", width='stretch'):
            img_name = upload_image(handover_img, "handover") if handover_img else ""
            try:
                # Update porter booking
                supabase.table("porter_bookings").update({
                    "status": "Handed Over",
                    "no_bills": str(no_bills),
                    "no_polythene": str(no_polythene),
                    "handover_time": str(handover_time),
                    "handover_by": st.session_state.name,
                    "handover_image": img_name,
                }).eq("id", selected_booking["id"]).execute()

                # Update arrangement status
                arr_nos = [a.strip() for a in selected_booking.get("arrangement_nos","").split(",")]
                for arr_no in arr_nos:
                    supabase.table("arrangements").update({
                        "status": "Given to Porter - In Transit",
                    }).eq("arrangement_no", arr_no.strip()).execute()

                # Log in daily tasks
                supabase.table("daily_tasks").insert({
                    "date": date_str(), "time": time_str(),
                    "person": st.session_state.name, "team": "Delivery",
                    "task_type": "Porter Handover",
                    "details": {
                        "porter_no": selected_booking.get("porter_no"),
                        "arrangement_nos": selected_booking.get("arrangement_nos"),
                        "no_bills": str(no_bills),
                        "no_polythene": str(no_polythene),
                        "handover_image": img_name,
                        "remarks": remarks
                    },
                    "start_time": str(handover_time),
                    "end_time": time_str(),
                }).execute()

                st.success("✅ Handover recorded!")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

def form_porter_receive():
    st.subheader("📦 Receive Stock")

    # ── INCOMING STOCK DASHBOARD ─────────────────────────────────────────────
    st.markdown("### 📊 All Incoming Stock Today")

    # Date filter
    from datetime import timedelta
    receive_date = st.date_input("Filter by Date", value=today_ist(), key="receive_date",
        min_value=today_ist()-timedelta(days=7), max_value=today_ist())

    try:
        receive_date_str = receive_date.strftime("%Y-%m-%d")
        two_days_ago = receive_date_str  # Use selected date only

        # All arrangements not yet received
        all_resp = supabase.table("arrangements").select("*")\
            .not_.in_("status", ["Reached Warehouse","Bill Cross Checked",
                                  "Bill Uploaded","Stock Placed","Completed",
                                  "Placement Issue Found"])\
            .gte("order_placed_date", two_days_ago)\
            .lte("order_placed_date", receive_date_str)\
            .execute()
        all_incoming = all_resp.data if all_resp.data else []

    except Exception as e:
        st.error(f"Error: {e}")
        all_incoming = []

    if all_incoming:
        # Area filter
        all_areas = list(set([a.get("area","") for a in all_incoming if a.get("area","")]))
        all_areas.sort()
        
        c1,c2 = st.columns(2)
        with c1:
            # Default to work area if set
            area_options = ["All Areas"] + all_areas
            default_area_idx = 0
            work_area = st.session_state.get("work_area","")
            if work_area and work_area in area_options:
                default_area_idx = area_options.index(work_area)
            selected_area = st.selectbox("Filter by Area/Warehouse",
                area_options, index=default_area_idx, key="incoming_area_filter")
        with c2:
            selected_status = st.selectbox("Filter by Status",
                ["All Status","Pending","In Transit","Porter Booked","Porter On Way"],
                key="incoming_status_filter")

        # Apply filters
        filtered_incoming = all_incoming
        if selected_area != "All Areas":
            filtered_incoming = [a for a in filtered_incoming if a.get("area","") == selected_area]
        if selected_status != "All Status":
            if selected_status == "Pending":
                filtered_incoming = [a for a in filtered_incoming if a.get("status","") == "Pending"]
            elif selected_status == "In Transit":
                filtered_incoming = [a for a in filtered_incoming if a.get("status","") == "Picked Up - In Transit"]
            elif selected_status == "Porter Booked":
                filtered_incoming = [a for a in filtered_incoming if a.get("status","") == "Porter Booked"]
            elif selected_status == "Porter On Way":
                filtered_incoming = [a for a in filtered_incoming if "Porter" in a.get("status","") and "Transit" in a.get("status","")]

        st.markdown(f"**Showing {len(filtered_incoming)} of {len(all_incoming)} incoming stocks**")

        for arr in filtered_incoming:
            status = arr.get("status","")
            pickup_type = arr.get("pickup_type","")

            # Status emoji
            if status == "Pending":
                if pickup_type == "Self Pick":
                    status_icon = "🔴 Waiting for Naresh to Pick"
                elif pickup_type == "Porter":
                    status_icon = "🔴 Waiting for Porter Booking"
                elif pickup_type == "Distributor Delivers":
                    status_icon = "🚚 Distributor will Deliver Directly"
            elif status == "Picked Up - In Transit":
                status_icon = "🚚 Naresh Picked — Coming to Warehouse"
            elif status == "Porter Booked":
                status_icon = "🚛 Porter Booked — In Transit"
            elif status == "Given to Porter - In Transit":
                status_icon = "🚛 Porter On The Way"
            else:
                status_icon = status

            c1,c2,c3,c4 = st.columns([2,2,2,2])
            with c1: st.markdown(f"**#{arr.get('arrangement_no','')}**")
            with c2: st.markdown(f"🏪 {arr.get('distributor','')}")
            with c3: st.markdown(f"📍 {arr.get('area','')}")
            with c4: st.markdown(f"{status_icon}")

        if not filtered_incoming:
            st.info(f"No incoming stock for selected filter!")
        st.divider()
    else:
        st.info("No incoming stock at the moment!")
        st.divider()

    # Load handed over porter bookings OR delivered by distributor
    try:
        # Porter handed over
        porter_resp = supabase.table("porter_bookings").select("*")\
            .eq("status", "Handed Over").execute()
        bookings = porter_resp.data if porter_resp.data else []

        # Also check Distributor Delivers arrangements
        from datetime import timedelta
        two_days_ago = (today_ist() - timedelta(days=2)).strftime("%Y-%m-%d")
        dist_resp = supabase.table("arrangements").select("*")\
            .eq("pickup_type", "Distributor Delivers")\
            .eq("status", "Pending")\
            .gte("order_placed_date", two_days_ago)\
            .execute()
        dist_arrangements = dist_resp.data if dist_resp.data else []

    except Exception as e:
        st.error(f"Error: {e}")
        bookings = []
        dist_arrangements = []

    if not bookings and not dist_arrangements:
        st.info("No stock pending receipt!")
        return

    # Show Distributor Delivers section
    if dist_arrangements:
        st.markdown("### 🚚 Distributor Direct Delivery")
        for arr in dist_arrangements:
            st.markdown(f"📦 **#{arr.get('arrangement_no')}** — {arr.get('distributor','')} — {arr.get('area','')} — Medicines: {arr.get('no_medicines','')}")

        st.divider()
        dist_options = {
            f"#{a.get('arrangement_no')} — {a.get('distributor','')} — {a.get('area','')}": a
            for a in dist_arrangements
        }

        with st.form("dist_receive_form", clear_on_submit=True):
            selected_dist_label = st.selectbox("Select Arrangement *", list(dist_options.keys()), key="dr_select")
            selected_dist_arr   = dist_options[selected_dist_label]

            c1,c2 = st.columns(2)
            with c1:
                bills_received = st.number_input("No of Bills Received", min_value=0, step=1, key="dr_bills")
            with c2:
                receive_time = st.time_input("Receive Time", key="dr_time")

            st.markdown("📸 **Image of Stock Received**")
            recv_img = st.file_uploader("📷 Take photo or choose file", type=["jpg","jpeg","png"], key="dr_upload")

            remarks = st.text_input("Remarks", key="dr_remarks")

            if st.form_submit_button("Confirm Receipt ✅", type="primary", width='stretch'):
                img_name = upload_image(recv_img, "dist_recv") if recv_img else ""
                try:
                    supabase.table("arrangements").update({
                        "status": "Reached Warehouse",
                        "pickup_by": "Distributor",
                        "pickup_time": str(receive_time),
                    }).eq("id", selected_dist_arr["id"]).execute()

                    supabase.table("daily_tasks").insert({
                        "date": date_str(), "time": time_str(),
                        "person": st.session_state.name, "team": st.session_state.team,
                        "task_type": "Distributor Delivery Receipt",
                        "details": {
                            "arrangement_no": selected_dist_arr.get("arrangement_no"),
                            "distributor": selected_dist_arr.get("distributor"),
                            "bills_received": str(bills_received),
                            "image": img_name,
                            "remarks": remarks
                        },
                        "start_time": str(receive_time),
                        "end_time": time_str(),
                    }).execute()

                    st.success("✅ Distributor delivery received!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        st.divider()

    if not bookings:
        return

    st.markdown(f"**{len(bookings)} porter delivery(s) incoming:**")
    for b in bookings:
        st.markdown(f"🚛 Porter: **{b.get('porter_no')}** | Bills: **{b.get('no_bills',0)}** | Polythene: **{b.get('no_polythene',0)}** | Arrangements: **{b.get('arrangement_nos','')}**")
    st.divider()

    # Build label showing arrangement + area/warehouse
    def get_arr_label(arr_nos_str):
        arr_nos = [a.strip() for a in arr_nos_str.split(",")]
        labels = []
        for arr_no in arr_nos:
            try:
                resp = supabase.table("arrangements").select("arrangement_no,area")\
                    .eq("arrangement_no", arr_no.strip()).execute()
                if resp.data:
                    area = resp.data[0].get("area","")
                    labels.append(f"{arr_no}({area})")
                else:
                    labels.append(arr_no)
            except:
                labels.append(arr_no)
        return ", ".join(labels)

    booking_options = {
        f"Porter:{b.get('porter_no')} | {get_arr_label(b.get('arrangement_nos',''))}": b
        for b in bookings
    }

    with st.form("porter_receive_form", clear_on_submit=True):
        selected_label   = st.selectbox("Select Porter *", list(booking_options.keys()), key="pr_select")
        selected_booking = booking_options[selected_label]

        st.info(f"Expected — Bills: **{selected_booking.get('no_bills',0)}** | Polythene: **{selected_booking.get('no_polythene',0)}**")

        c1,c2 = st.columns(2)
        with c1:
            bills_received     = st.number_input("No of Bills Received", min_value=0, step=1)
            polythene_received = st.number_input("No of Polythene Received", min_value=0, step=1)
        with c2:
            receive_time = st.time_input("Receive Time", key="pr_time")
            shortage     = st.text_input("Shortage (if any)")

        # Image per arrangement
        arr_nos = [a.strip() for a in selected_booking.get("arrangement_nos","").split(",")]
        st.markdown(f"**📸 Upload Image for Each Arrangement ({len(arr_nos)} arrangements)**")
        arr_images = {}
        for arr_no in arr_nos:
            st.markdown(f"Arrangement #{arr_no}")
            img = st.file_uploader(f"📷 Photo for #{arr_no} — take photo or choose file",
                    type=["jpg","jpeg","png"], key=f"pr_upload_{arr_no}")
            arr_images[arr_no] = img

        remarks = st.text_input("Remarks")

        if st.form_submit_button("Confirm Receipt ✅", type="primary", width='stretch'):
            try:
                # Upload images
                uploaded_images = {}
                for arr_no, img in arr_images.items():
                    if img:
                        uploaded_images[arr_no] = upload_image(img, f"receipt_{arr_no}")

                # Update porter booking
                supabase.table("porter_bookings").update({
                    "status": "Delivered",
                    "bills_received": str(bills_received),
                    "polythene_received": str(polythene_received),
                    "receive_time": str(receive_time),
                    "received_by": st.session_state.name,
                    "shortage": shortage,
                    "receipt_images": str(uploaded_images),
                }).eq("id", selected_booking["id"]).execute()

                # Update arrangement status
                for arr_no in arr_nos:
                    supabase.table("arrangements").update({
                        "status": "Reached Warehouse",
                    }).eq("arrangement_no", arr_no.strip()).execute()

                # Log in daily tasks
                supabase.table("daily_tasks").insert({
                    "date": date_str(), "time": time_str(),
                    "person": st.session_state.name, "team": "Stock",
                    "task_type": "Porter Receipt",
                    "details": {
                        "porter_no": selected_booking.get("porter_no"),
                        "arrangement_nos": selected_booking.get("arrangement_nos"),
                        "bills_received": str(bills_received),
                        "polythene_received": str(polythene_received),
                        "shortage": shortage,
                        "images": str(uploaded_images),
                        "remarks": remarks
                    },
                    "start_time": str(receive_time),
                    "end_time": time_str(),
                }).execute()

                st.success("✅ Receipt confirmed! Arrangements marked as Reached Warehouse!")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

def form_porter_payment():
    st.subheader("💰 Porter Payment")

    # Load delivered porter bookings without payment
    try:
        resp = supabase.table("porter_bookings").select("*")\
            .eq("status", "Delivered").execute()
        bookings = resp.data if resp.data else []
    except Exception as e:
        st.error(f"Error: {e}")
        bookings = []

    if not bookings:
        st.info("No pending porter payments!")
        return

    booking_options = {
        f"Porter: {b.get('porter_no')} | {b.get('arrangement_nos','')} | {b.get('date','')}": b
        for b in bookings
    }

    with st.form("porter_payment_form", clear_on_submit=True):
        selected_label   = st.selectbox("Select Porter *", list(booking_options.keys()), key="pp_select")
        selected_booking = booking_options[selected_label]

        c1,c2 = st.columns(2)
        with c1:
            amount       = st.number_input("Porter Cost (₹) *", min_value=0.0, step=10.0)
            payment_mode = st.selectbox("Payment Mode", ["Cash","UPI","Online"], key="pp_mode")
        with c2:
            payment_time = st.time_input("Payment Time", key="pp_time")

        st.markdown("📸 **Payment Bill Image**")
        bill_img = st.file_uploader("📷 Take photo or choose file", type=["jpg","jpeg","png"], key="pp_upload")

        remarks = st.text_input("Remarks")

        if st.form_submit_button("Submit Payment ✅", type="primary", width='stretch'):
            if amount <= 0:
                st.error("Enter valid amount!")
            else:
                img_name = upload_image(bill_img, "payment") if bill_img else ""
                try:
                    supabase.table("porter_bookings").update({
                        "status": "Payment Done",
                        "porter_cost": str(amount),
                        "payment_mode": payment_mode,
                        "payment_time": str(payment_time),
                        "payment_by": st.session_state.name,
                        "payment_image": img_name,
                    }).eq("id", selected_booking["id"]).execute()

                    st.success(f"✅ Payment of ₹{amount} recorded!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# ── USER PAGE ─────────────────────────────────────────────────────────────────
def show_user_page():
    team = st.session_state.team
    sync_form_with_link(team)

    # Stock area is locked on the server for 6 hours -> survives refresh / re-login
    if team == "Stock":
        lock = get_area_lock(st.session_state.name)
        st.session_state["area_lock"] = lock
        if st.session_state.get("fresh_login") and not st.session_state.work_area:
            pass                                            # just logged in -> choose area
        elif lock and lock.get("area") and lock["area"] != st.session_state.work_area:
            st.session_state.work_area = lock["area"]       # refresh / admin change

    # Area selection for Stock team
    if team == "Stock" and not st.session_state.work_area:
        st.title("📍 Select Your Work Area")
        st.markdown(f"### Welcome {st.session_state.name}! Which area are you working in today?")
        st.divider()
        try:
            areas_resp = supabase.table("areas").select("name").eq("active",True).execute()
            area_options = [a["name"] for a in (areas_resp.data or [])] + ["All Areas"]
        except:
            area_options = ["Gaur City","Sector 78","Indirapuram","All Areas"]

        cols = st.columns(len(area_options))
        for i, area in enumerate(area_options):
            with cols[i]:
                if st.button(f"📍 {area}", width='stretch', type="primary"):
                    set_area_lock(st.session_state.name, area, st.session_state.name)
                    st.session_state.work_area = area
                    st.session_state["fresh_login"] = False
                    st.rerun()
        st.caption("Your area stays fixed for the day, even if the page refreshes. "
                   "To change it: Logout and log in again.")
        return

    c1,c2 = st.columns([4,1])
    with c1:
        st.title(f"💊 RapidSurge — {team} Team")
        mission_banner(f"👤 {st.session_state.name} · {team} Team · 📅 {today_ist().strftime('%A, %d %B %Y')}")
    with c2:
        st.write("")
        if st.button("🚪 Logout", key="mobile_logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.query_params.clear()
            st.rerun()
    st.divider()

    show_my_shift()
    done_secs = st.session_state.pop("mission_done", None)
    if done_secs is not None:
        st.toast(f"🎖️ Mission complete — {fmt_secs(done_secs)}", icon="✅")

    # ── MANAGER: switch between own work and team view ───────────────────────
    if st.session_state.get("role") == "manager":
        mode = st.radio("View", ["🧑‍💼 My Work", "👥 Team View"], horizontal=True,
                        key="mgr_mode", label_visibility="collapsed")
        if mode == "👥 Team View":
            show_manager_team_view()
            return

    # ── ATTENDANCE: clock in first; no tasks while on a break ────────────────
    if not attendance_gate():
        return

    # ── TASKS FROM ADMIN ──────────────────────────────────────────────────────
    show_my_assigned_tasks()

    # ── PIPELINE VIEW ─────────────────────────────────────────────────────────
    if team == "Stock" and st.session_state.get("show_pipeline"):
        work_area = st.session_state.get("work_area","All Areas")
        if st.button("⬅️ Back to menu", key="pipe_back", type="primary"):
            st.session_state["show_pipeline"] = None
            st.rerun()

        if st.session_state["show_pipeline"] == "normal":
            st.subheader("🧾 Normal Order Pipeline")
            try:
                reg_resp = supabase.table("daily_tasks").select("*")\
                    .eq("task_type", "Register Entry")\
                    .eq("date", date_str()).execute()
                reg_entries = [t for t in (reg_resp.data or [])
                    if work_area == "All Areas" or t.get("details",{}).get("area","") == work_area]

                cross_resp = supabase.table("daily_tasks").select("*")\
                    .eq("task_type", "Bill Cross Check")\
                    .eq("date", date_str()).execute()
                cross_dict = {t.get("details",{}).get("bill_no",""):t for t in (cross_resp.data or [])}

                upload_resp = supabase.table("daily_tasks").select("*")\
                    .eq("task_type", "Bill Upload (Software)")\
                    .eq("date", date_str()).execute()
                upload_dict = {t.get("details",{}).get("bill_no",""):t for t in (upload_resp.data or [])}

                place_resp = supabase.table("daily_tasks").select("*")\
                    .eq("task_type", "Stock Placement")\
                    .eq("date", date_str()).execute()
                place_dict = {t.get("details",{}).get("bill_no",""):t for t in (place_resp.data or [])}

                if not reg_entries:
                    st.info(f"No bills found for {work_area} today!")
                else:
                    rows = []
                    for i, r in enumerate(reg_entries):
                        d      = r.get("details",{})
                        bill_no = d.get("bill_no","")
                        cross  = cross_dict.get(bill_no)
                        upload = upload_dict.get(bill_no)
                        place  = place_dict.get(bill_no)

                        if place:
                            status = "✅ Placed"
                        elif upload:
                            status = "📍 Placement Pending"
                        elif cross:
                            status = "📤 Upload Pending"
                        else:
                            status = "✔️ Cross Check Pending"

                        # Calculate total time from register to placement
                        try:
                            from datetime import datetime as dt
                            reg_t   = dt.strptime(r.get("time",""), "%I:%M %p")
                            if place:
                                end_t = parse_task_time(place.get("end_time",""))
                            elif upload:
                                end_t = parse_task_time(upload.get("end_time",""))
                            elif cross:
                                end_t = parse_task_time(cross.get("end_time",""))
                            else:
                                end_t = dt.strptime(time_str(), "%I:%M %p")
                            total_mins = int((end_t - reg_t).total_seconds() / 60)
                        except:
                            total_mins = "-"

                        rows.append({
                            "S.No": i+1,
                            "Bill No": bill_no,
                            "Distributor": d.get("distributor",""),
                            "Items": int(float(d.get("no_items",0) or 0)),
                            "Amount": f"₹{float(d.get('bill_amount',0) or 0):,.0f}",
                            "Reg Time": r.get("time",""),
                            "Reg By": r.get("person",""),
                            "Check By": cross.get("person","") if cross else "⏳",
                            "Check Start": cross.get("start_time","") if cross else "⏳",
                            "Check End": cross.get("end_time","") if cross else "⏳",
                            "Check Mins": int(float(cross.get("duration_mins",0) or 0)) if cross else 0,
                            "Upload By": upload.get("person","") if upload else "⏳",
                            "Upload Start": upload.get("start_time","") if upload else "⏳",
                            "Upload End": upload.get("end_time","") if upload else "⏳",
                            "Upload Mins": int(float(upload.get("duration_mins",0) or 0)) if upload else 0,
                            "Place By": place.get("person","") if place else "⏳",
                            "Place Start": place.get("start_time","") if place else "⏳",
                            "Place End": place.get("end_time","") if place else "⏳",
                            "Place Mins": int(float(place.get("duration_mins",0) or 0)) if place else 0,
                            "Total Mins": total_mins,
                            "Status": status
                        })

                    pipeline_df = pd.DataFrame(rows)
                    st.dataframe(pipeline_df, width='stretch')

                    # Download
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine="openpyxl") as w:
                        pipeline_df.to_excel(w, index=False)
                    st.download_button("⬇️ Download Excel", buf.getvalue(),
                        f"stock_pipeline_{date_str()}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="stock_pipeline_dl")

            except Exception as e:
                st.error(f"Error: {e}")

        elif st.session_state["show_pipeline"] == "arrangement":
            show_incoming_arrangements(work_area, full=True)
        # ── MAIN AREA ─────────────────────────────────────────────────────
        else:
            # ── DASHBOARD ─────────────────────────────────────────────────
            work_area = st.session_state.get("work_area","All Areas")
            st.markdown(f"### 📊 Today's Summary — {work_area}")

            try:
                from datetime import timedelta
                # Load today's data
                reg_resp = supabase.table("daily_tasks").select("*")\
                    .eq("task_type","Register Entry").eq("date",date_str()).execute()
                reg_entries = [t for t in (reg_resp.data or [])
                    if work_area=="All Areas" or t.get("details",{}).get("area","")==work_area]

                cross_resp = supabase.table("daily_tasks").select("*")\
                    .eq("task_type","Bill Cross Check").eq("date",date_str()).execute()
                cross_tasks = cross_resp.data or []
                crossed_bills = [t.get("details",{}).get("bill_no","") for t in cross_tasks]

                upload_resp = supabase.table("daily_tasks").select("*")\
                    .eq("task_type","Bill Upload (Software)").eq("date",date_str()).execute()
                upload_tasks = upload_resp.data or []
                uploaded_bills = [t.get("details",{}).get("bill_no","") for t in upload_tasks]

                place_resp = supabase.table("daily_tasks").select("*")\
                    .eq("task_type","Stock Placement").eq("date",date_str()).execute()
                place_tasks = place_resp.data or []
                placed_bills = [t.get("details",{}).get("bill_no","") for t in place_tasks]

                # Normal orders
                normal_entries = [t for t in reg_entries
                    if t.get("details",{}).get("order_type","") == "Normal Order"]

                normal_cross_pending  = len([t for t in normal_entries
                    if t.get("details",{}).get("bill_no","") not in crossed_bills])
                normal_upload_pending = len([t for t in normal_entries
                    if t.get("details",{}).get("bill_no","") in crossed_bills
                    and t.get("details",{}).get("bill_no","") not in uploaded_bills])
                normal_place_pending  = len([t for t in normal_entries
                    if t.get("details",{}).get("bill_no","") in uploaded_bills
                    and t.get("details",{}).get("bill_no","") not in placed_bills])

                # Avg times for normal orders
                normal_cross_tasks  = [t for t in cross_tasks if not t.get("details",{}).get("arrangement_no","")]
                normal_upload_tasks = [t for t in upload_tasks if not t.get("details",{}).get("arrangement_no","")]
                normal_place_tasks  = [t for t in place_tasks if not t.get("details",{}).get("arrangement_no","")]

                def avg_time_per_sku(tasks, sku_field="no_items"):
                    total_dur = sum([int(float(t.get("duration_mins",0) or 0)) for t in tasks])
                    total_sku = sum([int(float((t.get("details") or {}).get(sku_field,0) or 0)) for t in tasks])
                    return round(total_dur/total_sku, 2) if total_sku > 0 else 0

                # Arrangement orders
                arr_resp = supabase.table("arrangements").select("*")\
                    .eq("order_placed_date", date_str()).execute()
                arr_today = arr_resp.data or []
                if work_area != "All Areas":
                    arr_today = [a for a in arr_today if a.get("area","") == work_area]

                arr_reached   = [a for a in arr_today if a.get("status") in ["Reached Warehouse","Bill Cross Checked","Bill Uploaded","Stock Placed","Completed"]]
                arr_cross_pend= len([a for a in arr_today if a.get("status")=="Reached Warehouse"])
                arr_upload_pend=len([a for a in arr_today if a.get("status")=="Bill Cross Checked"])
                arr_place_pend = len([a for a in arr_today if a.get("status")=="Bill Uploaded"])

                arr_cross_tasks  = [t for t in cross_tasks if t.get("details",{}).get("arrangement_no","")]
                arr_upload_tasks = [t for t in upload_tasks if t.get("details",{}).get("arrangement_no","")]
                arr_place_tasks  = [t for t in place_tasks if t.get("details",{}).get("arrangement_no","")]

                # ── NORMAL ORDERS TABLE ───────────────────────────────────
                st.markdown("#### 🧾 Normal Orders")
                normal_data = [{
                    "Bills Received": len(normal_entries),
                    "Cross Check Pending": normal_cross_pending,
                    "Upload Pending": normal_upload_pending,
                    "Avg Check/SKU": f"{avg_time_per_sku(normal_cross_tasks)} mins",
                    "Avg Upload/SKU": f"{avg_time_per_sku(normal_upload_tasks)} mins",
                }]
                st.dataframe(pd.DataFrame(normal_data), width='stretch', hide_index=True)

                st.divider()

                # ── ARRANGEMENT ORDERS TABLE ──────────────────────────────
                st.markdown("#### 📦 Arrangement Orders")
                arr_data = [{
                    "Bills Received": len(arr_reached),
                    "Cross Check Pending": arr_cross_pend,
                    "Upload Pending": arr_upload_pend,
                    "Avg Check/SKU": f"{avg_time_per_sku(arr_cross_tasks)} mins",
                    "Avg Upload/SKU": f"{avg_time_per_sku(arr_upload_tasks)} mins",
                }]
                st.dataframe(pd.DataFrame(arr_data), width='stretch', hide_index=True)

            except Exception as e:
                st.error(f"Dashboard error: {e}")
        return   # pipeline is its own screen (⬅️ Back to menu at the top)

    elif team == "Call":
        if "call_active_form" not in st.session_state:
            st.session_state.call_active_form = None

        with st.sidebar:
            st.divider()
            st.markdown("### 📞 Calls")
            if st.button("📞 Call Log", width='stretch', key="c_calllog",
                type="primary" if st.session_state.call_active_form=="calllog" else "secondary"):
                st.session_state.call_active_form = "calllog"
                st.rerun()
            if st.button("📞 Customer Delivery", width='stretch', key="c_custdel",
                type="primary" if st.session_state.call_active_form=="custdel" else "secondary"):
                st.session_state.call_active_form = "custdel"
                st.rerun()
            if st.button("🔍 Medicine Search", width='stretch', key="c_medsearch",
                type="primary" if st.session_state.call_active_form=="medsearch" else "secondary"):
                st.session_state.call_active_form = "medsearch"
                st.rerun()

            st.markdown("### 🚛 Logistics")
            if st.button("🚛 Book Porter", width='stretch', key="c_porter",
                type="primary" if st.session_state.call_active_form=="porter" else "secondary"):
                st.session_state.call_active_form = "porter"
                st.rerun()
            if st.button("✏️ Other", width='stretch', key="c_other",
                type="primary" if st.session_state.call_active_form=="other" else "secondary"):
                st.session_state.call_active_form = "other"
                st.rerun()

            if st.session_state.call_active_form:
                st.divider()
                if st.button("✖️ Close Form", width='stretch', key="c_close"):
                    st.session_state.call_active_form = None
                    st.rerun()

            # My Tasks Today in sidebar
            st.divider()
            st.markdown("**📋 My Tasks Today:**")
            try:
                resp = supabase.table("daily_tasks").select("*")\
                    .eq("person", st.session_state.name)\
                    .eq("date", date_str()).execute()
                tasks = resp.data or []
                if tasks:
                    for t in sorted(tasks, key=lambda x: x.get("time","")):
                        status_icon = "🔄" if t.get("status")=="In Progress" else "✅"
                        st.markdown(f"{status_icon} {t.get('time','')} — **{t.get('task_type','')}**")
                else:
                    st.caption("No tasks yet today!")
            except:
                st.caption("Error loading tasks")

        # Main area
        if st.session_state.call_active_form:
            form_map = {
                "calllog":   form_call_log,
                "custdel":   form_customer_delivery,
                "medsearch": form_medicine_search,
                "porter":    form_book_porter,
                "other":     form_other_task,
            }
            if st.session_state.call_active_form in form_map:
                form_map[st.session_state.call_active_form]()
        else:
            # Mobile task buttons
            st.markdown("### 📋 Select Task:")
            st.markdown("#### 📞 Calls")
            c1,c2 = st.columns(2)
            with c1:
                if st.button("📞 Call Log", key="mc_calllog", type="primary", use_container_width=True):
                    st.session_state.call_active_form = "calllog"
                    st.rerun()
            with c2:
                if st.button("🔍 Medicine Search", key="mc_medsearch", type="primary", use_container_width=True):
                    st.session_state.call_active_form = "medsearch"
                    st.rerun()
            if st.button("📞 Customer Delivery Status", key="mc_custdel", type="primary", use_container_width=True):
                st.session_state.call_active_form = "custdel"
                st.rerun()
            st.markdown("#### 🚛 Logistics")
            c1,c2 = st.columns(2)
            with c1:
                if st.button("🚛 Book Porter", key="mc_porter", use_container_width=True):
                    st.session_state.call_active_form = "porter"
                    st.rerun()
            with c2:
                if st.button("✏️ Other", key="mc_other", use_container_width=True):
                    st.session_state.call_active_form = "other"
                    st.rerun()
            st.divider()
            # Dashboard
            st.markdown("### 📊 Today's Call Summary")
            try:
                    tasks_resp = supabase.table("daily_tasks").select("*")\
                    .eq("person", st.session_state.name)\
                    .eq("date", date_str()).execute()
                    tasks = tasks_resp.data or []

                    call_logs    = [t for t in tasks if t.get("task_type") == "Call Log"]
                    med_searches = [t for t in tasks if t.get("task_type") == "Medicine Search"]

                    total_calls   = sum([int(float((t.get("details") or {}).get("calls_made",0) or 0)) for t in call_logs])
                    total_picked  = sum([int(float((t.get("details") or {}).get("calls_picked",0) or 0)) for t in call_logs])
                    total_orders  = sum([int(float((t.get("details") or {}).get("orders_delivered",0) or 0)) for t in call_logs])
                    pickup_rate   = round((total_picked/total_calls)*100, 1) if total_calls > 0 else 0

                    total_searched  = sum([int(float((t.get("details") or {}).get("no_searched",0) or 0)) for t in med_searches])
                    total_found     = sum([int(float((t.get("details") or {}).get("no_found",0) or 0)) for t in med_searches])
                    total_not_found = sum([int(float((t.get("details") or {}).get("no_not_found",0) or 0)) for t in med_searches])
                    search_dur      = sum([int(float(t.get("duration_mins",0) or 0)) for t in med_searches])
                    avg_search_sku  = round(search_dur/total_searched, 2) if total_searched > 0 else 0

                    # Call metrics
                    st.markdown("#### 📞 Call Log")
                    c1,c2,c3,c4 = st.columns(4)
                    with c1: st.metric("Total Calls", total_calls)
                    with c2: st.metric("Picked", total_picked)
                    with c3: st.metric("Not Picked", total_calls - total_picked)
                    with c4: st.metric("📊 Pickup Rate", f"{pickup_rate}%")

                    st.divider()
                    c1,c2 = st.columns(2)
                    with c1: st.metric("🛒 Orders Delivered", total_orders)
                    with c2: st.metric("⏱️ Total Sessions", len(call_logs))

                    if med_searches:
                        st.divider()
                        st.markdown("#### 🔍 Medicine Search")
                        s1,s2,s3,s4 = st.columns(4)
                        with s1: st.metric("Searched", total_searched)
                        with s2: st.metric("Found", total_found)
                        with s3: st.metric("Not Found", total_not_found)
                        with s4: st.metric("Avg mins/SKU", avg_search_sku)

            except Exception as e:
                st.error(f"Dashboard error: {e}")

    elif team == "Delivery":
        if "delivery_active_form" not in st.session_state:
            st.session_state.delivery_active_form = None

        if st.session_state.delivery_active_form:
            if st.button("← Back", key="del_back"):
                st.session_state.delivery_active_form = None
                st.rerun()
            st.divider()
            form_map = {
                "pickup":   form_pickup,
                "handover": form_porter_handover,
                "delivery": form_delivery,
                "other":    form_other_task,
            }
            if st.session_state.delivery_active_form in form_map:
                form_map[st.session_state.delivery_active_form]()
        else:
            try:
                pending_resp = supabase.table("arrangements").select("*")\
                    .eq("status","Pending")\
                    .eq("pickup_type","Self Pick")\
                    .eq("order_placed_date", date_str()).execute()
                pending_count = len(pending_resp.data or [])
            except:
                pending_count = 0
            if pending_count > 0:
                st.error(f"🔴 {pending_count} Pickup(s) Pending Today!")
            else:
                st.success("✅ No pending pickups!")
            st.divider()
            st.markdown("### What do you want to do?")
            c1,c2 = st.columns(2)
            with c1:
                if st.button("📋 View & Pickup", width='stretch', key="d_pickup", type="primary"):
                    st.session_state.delivery_active_form = "pickup"
                    st.rerun()
            with c2:
                if st.button("🚛 Porter Handover", width='stretch', key="d_handover", type="primary"):
                    st.session_state.delivery_active_form = "handover"
                    st.rerun()
            c1,c2 = st.columns(2)
            with c1:
                if st.button("🚚 Delivery Trip", width='stretch', key="d_delivery"):
                    st.session_state.delivery_active_form = "delivery"
                    st.rerun()
            with c2:
                if st.button("✏️ Other Task", width='stretch', key="d_other"):
                    st.session_state.delivery_active_form = "other"
                    st.rerun()
            st.divider()
            st.markdown("### 📊 Today's Summary")
            try:
                tasks_resp = supabase.table("daily_tasks").select("*")\
                    .eq("person", st.session_state.name)\
                    .eq("date", date_str()).execute()
                tasks = tasks_resp.data or []
                pickups  = len([t for t in tasks if t.get("task_type")=="Pickup"])
                trips    = len([t for t in tasks if t.get("task_type")=="Delivery Trip"])
                handover = len([t for t in tasks if t.get("task_type")=="Porter Handover"])
                c1,c2,c3 = st.columns(3)
                with c1: st.metric("📋 Pickups", pickups)
                with c2: st.metric("🚚 Trips", trips)
                with c3: st.metric("🚛 Handovers", handover)
                if tasks:
                    st.markdown("**Recent tasks:**")
                    for t in sorted(tasks, key=lambda x: x.get("time",""), reverse=True)[:5]:
                        st.markdown(f"✅ {t.get('time','')} — {t.get('task_type','')}")
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()

    # ── MY PERFORMANCE TODAY (Stock: shown at the bottom) ────────────────────
    if team != "Stock":
        show_my_performance()
        st.divider()

    # ── ARRANGEMENT PIPELINE (not for Stock: they see the simple incoming list) ──
    with (st.container() if team == "Stock" else st.expander("🔄 View Today's Arrangement Pipeline", expanded=False)):
      if team != "Stock":
        try:
            arr_resp = supabase.table("arrangements").select("*")\
                .eq("order_placed_date", date_str()).execute()
            arr_today = arr_resp.data if arr_resp.data else []
        except:
            arr_today = []

        if not arr_today:
            st.info("No arrangements today!")
        else:
            st.markdown(f"**{len(arr_today)} arrangements today**")
            for arr in arr_today:
                status  = arr.get("status","")
                urgency = arr.get("urgency","Normal")
                urgency_color = "🔴" if urgency == "Very Urgent" else "🟡" if urgency == "Urgent" else "🟢"
                pickup_type = arr.get("pickup_type","")
                if pickup_type == "Self Pick":
                    pickup_icon = "🚚 Naresh/Sandeep"
                elif pickup_type == "Porter":
                    pickup_icon = "🚛 Porter"
                elif pickup_type == "Distributor Delivers":
                    pickup_icon = "🏪 Distributor Delivers"
                else:
                    pickup_icon = pickup_type

                st.markdown(f"{urgency_color} **#{arr.get('arrangement_no','')}** | {arr.get('distributor','')} | {arr.get('area','')} | {pickup_icon} | **{status}**")

    # ── TEAM FORMS ───────────────────────────────────────────────────────────
    if team == "Purchase":
        if "purchase_active_form" not in st.session_state:
            st.session_state.purchase_active_form = None

        with st.sidebar:
            st.divider()
            st.markdown("### 📦 Ordering")
            if st.button("📑 Order Sheet", width='stretch', key="p_sheet",
                type="primary" if st.session_state.purchase_active_form=="sheet" else "secondary"):
                st.session_state.purchase_active_form = "sheet"
                st.rerun()
            if st.button("🛒 Purchase Order", width='stretch', key="p_purchase",
                type="primary" if st.session_state.purchase_active_form=="purchase" else "secondary"):
                st.session_state.purchase_active_form = "purchase"
                st.rerun()
            if st.button("↩️ Purchase Return", width='stretch', key="p_return",
                type="primary" if st.session_state.purchase_active_form=="return" else "secondary"):
                st.session_state.purchase_active_form = "return"
                st.rerun()
            if st.button("📦 Arrangement Order", width='stretch', key="p_arrangement",
                type="primary" if st.session_state.purchase_active_form=="arrangement" else "secondary"):
                st.session_state.purchase_active_form = "arrangement"
                st.rerun()

            st.markdown("### 🧾 Customer Orders")
            if st.button("📥 Import Orders", width='stretch', key="p_import",
                type="primary" if st.session_state.purchase_active_form=="import" else "secondary"):
                st.session_state.purchase_active_form = "import"
                st.rerun()
            if st.button("🧾 Pending Items", width='stretch', key="p_pending_items",
                type="primary" if st.session_state.purchase_active_form=="pending_items" else "secondary"):
                st.session_state.purchase_active_form = "pending_items"
                st.rerun()
            if st.button("📊 Order Tracker", width='stretch', key="p_tracker",
                type="primary" if st.session_state.purchase_active_form=="tracker" else "secondary"):
                st.session_state.purchase_active_form = "tracker"
                st.rerun()
            if st.button("🧾 Bills Register", width='stretch', key="p_bills",
                type="primary" if st.session_state.purchase_active_form=="bills" else "secondary"):
                st.session_state.purchase_active_form = "bills"
                st.rerun()

            st.markdown("### 🔍 Research")
            if st.button("💊 PharmaRack Search", width='stretch', key="p_pharma",
                type="primary" if st.session_state.purchase_active_form=="pharma" else "secondary"):
                st.session_state.purchase_active_form = "pharma"
                st.rerun()
            if st.button("📋 Bounce Medicine", width='stretch', key="p_bounce",
                type="primary" if st.session_state.purchase_active_form=="bounce" else "secondary"):
                st.session_state.purchase_active_form = "bounce"
                st.rerun()

            st.markdown("### 🚛 Logistics")
            if st.button("🚛 Book Porter", width='stretch', key="p_porter",
                type="primary" if st.session_state.purchase_active_form=="porter" else "secondary"):
                st.session_state.purchase_active_form = "porter"
                st.rerun()
            if st.button("💰 Porter Payment", width='stretch', key="p_payment",
                type="primary" if st.session_state.purchase_active_form=="payment" else "secondary"):
                st.session_state.purchase_active_form = "payment"
                st.rerun()
            if st.button("📸 Pickup Images", width='stretch', key="p_pickup",
                type="primary" if st.session_state.purchase_active_form=="pickup" else "secondary"):
                st.session_state.purchase_active_form = "pickup"
                st.rerun()

            st.markdown("### 📦 Stock Work")
            if st.button("📒 Register Entry", width='stretch', key="p_register",
                type="primary" if st.session_state.purchase_active_form=="register" else "secondary"):
                st.session_state.purchase_active_form = "register"
                st.rerun()
            if st.button("✔️ Bill Cross Check", width='stretch', key="p_crosscheck",
                type="primary" if st.session_state.purchase_active_form=="crosscheck" else "secondary"):
                st.session_state.purchase_active_form = "crosscheck"
                st.rerun()
            if st.button("✏️ Other", width='stretch', key="p_other",
                type="primary" if st.session_state.purchase_active_form=="other" else "secondary"):
                st.session_state.purchase_active_form = "other"
                st.rerun()

            if st.session_state.purchase_active_form:
                st.divider()
                if st.button("✖️ Close Form", width='stretch', key="p_close"):
                    st.session_state.purchase_active_form = None
                    st.rerun()

            # My Tasks Today in sidebar
            st.divider()
            st.markdown("**📋 My Tasks Today:**")
            try:
                resp = supabase.table("daily_tasks").select("*")\
                    .eq("person", st.session_state.name)\
                    .eq("date", date_str()).execute()
                tasks = resp.data or []
                if tasks:
                    for t in sorted(tasks, key=lambda x: x.get("time","")):
                        status_icon = "🔄" if t.get("status")=="In Progress" else "✅"
                        st.markdown(f"{status_icon} {t.get('time','')} — **{t.get('task_type','')}**")
                else:
                    st.caption("No tasks yet today!")
            except:
                st.caption("Error loading tasks")

        # Main area
        if st.session_state.purchase_active_form:
            form_map = {
                "purchase":    form_purchase_order,
                "sheet":       form_order_sheet,
                "return":      form_purchase_return,
                "arrangement": form_arrangement,
                "pharma":      form_pharmarack,
                "bounce":      form_bounce_medicine,
                "porter":      form_book_porter,
                "payment":     form_porter_payment,
                "pickup":      show_pickup_images,
                "register":    form_register_entry,
                "crosscheck":  form_bill_crosscheck,
                "placement":   form_stock_placement,
                "import":      form_import_orders,
                "pending_items": form_pending_items,
                "tracker":     show_customer_order_tracker,
                "bills":       show_bills_register,
                "other":       form_other_task,
            }
            if st.session_state.purchase_active_form in form_map:
                form_map[st.session_state.purchase_active_form]()
        else:
            # Mobile task buttons
            st.markdown("### 📋 Select Task:")
            st.markdown("#### 📦 Ordering")
            if st.button("📑 Order Sheet", key="mp_sheet", type="primary", use_container_width=True):
                st.session_state.purchase_active_form = "sheet"
                st.rerun()
            c1,c2 = st.columns(2)
            with c1:
                if st.button("🛒 Purchase Order", key="mp_purchase", type="primary", use_container_width=True):
                    st.session_state.purchase_active_form = "purchase"
                    st.rerun()
            with c2:
                if st.button("📦 Arrangement", key="mp_arrangement", type="primary", use_container_width=True):
                    st.session_state.purchase_active_form = "arrangement"
                    st.rerun()
            c1,c2 = st.columns(2)
            with c1:
                if st.button("↩️ Return", key="mp_return", use_container_width=True):
                    st.session_state.purchase_active_form = "return"
                    st.rerun()
            with c2:
                if st.button("💊 PharmaRack", key="mp_pharma", use_container_width=True):
                    st.session_state.purchase_active_form = "pharma"
                    st.rerun()
            st.markdown("#### 🧾 Customer Orders")
            c1,c2,c3 = st.columns(3)
            with c1:
                if st.button("📥 Import", key="mp_import", use_container_width=True):
                    st.session_state.purchase_active_form = "import"
                    st.rerun()
            with c2:
                if st.button("🧾 Pending", key="mp_pending_items", use_container_width=True):
                    st.session_state.purchase_active_form = "pending_items"
                    st.rerun()
            with c3:
                if st.button("📊 Tracker", key="mp_tracker", use_container_width=True):
                    st.session_state.purchase_active_form = "tracker"
                    st.rerun()
            if st.button("🧾 Bills Register", key="mp_bills", use_container_width=True):
                st.session_state.purchase_active_form = "bills"
                st.rerun()
            st.markdown("#### 🚛 Logistics")
            c1,c2 = st.columns(2)
            with c1:
                if st.button("🚛 Book Porter", key="mp_porter", use_container_width=True):
                    st.session_state.purchase_active_form = "porter"
                    st.rerun()
            with c2:
                if st.button("💰 Porter Payment", key="mp_payment", use_container_width=True):
                    st.session_state.purchase_active_form = "payment"
                    st.rerun()
            st.markdown("#### 📦 Stock Work")
            c1,c2 = st.columns(2)
            with c1:
                if st.button("📒 Register Entry", key="mp_register", use_container_width=True):
                    st.session_state.purchase_active_form = "register"
                    st.rerun()
            with c2:
                if st.button("✔️ Bill Check", key="mp_crosscheck", use_container_width=True):
                    st.session_state.purchase_active_form = "crosscheck"
                    st.rerun()
            c1,c2 = st.columns(2)
            with c1:
                if st.button("✏️ Other", key="mp_other", use_container_width=True):
                    st.session_state.purchase_active_form = "other"
                    st.rerun()
            st.divider()
            # Dashboard
            st.markdown("### 📊 Today's Purchase Summary")
            try:
                tasks_resp = supabase.table("daily_tasks").select("*")\
                    .eq("person", st.session_state.name)\
                    .eq("date", date_str()).execute()
                tasks = [t for t in (tasks_resp.data or []) if t.get("status") != "In Progress"]

                purchase_orders  = [t for t in tasks if t.get("task_type") == "Purchase Order"]
                returns          = [t for t in tasks if t.get("task_type") == "Purchase Return"]
                pharmarack       = [t for t in tasks if t.get("task_type") == "PharmaRack Search"]
                arr_timer        = [t for t in tasks if t.get("task_type") == "Arrangement Order"]
                # Load arrangements from arrangements table
                try:
                    arr_db_resp = supabase.table("arrangements").select("*")\
                        .eq("order_placed_date", date_str())\
                        .eq("order_by", st.session_state.name).execute()
                    arrangements = arr_db_resp.data if arr_db_resp.data else arr_timer
                except Exception as arr_err:
                    st.warning(f"Arr load error: {arr_err}")
                    arrangements = arr_timer
                total_medicines = sum([int(float(a.get("no_medicines",0) or 0)) for a in arrangements])
                arr_duration = sum([int(float(t.get("duration_mins",0) or 0)) for t in arr_timer])
                avg_arr = round(arr_duration/len(arr_timer), 1) if arr_timer else 0
                total_skus  = sum([int(float((t.get("details") or {}).get("no_sku",0) or 0)) for t in purchase_orders])
                po_duration = sum([int(float(t.get("duration_mins",0) or 0)) for t in purchase_orders])
                avg_po_sku  = round(po_duration/total_skus, 2) if total_skus > 0 else 0

                c1,c2,c3,c4 = st.columns(4)
                with c1: st.metric("🛒 Purchase Orders", len(purchase_orders))
                with c2: st.metric("📦 Arrangements", len(arrangements))
                with c3: st.metric("↩️ Returns", len(returns))
                with c4: st.metric("💊 PharmaRack", len(pharmarack))

                st.divider()
                st.markdown("#### 📋 Order Details")
                st.dataframe(pd.DataFrame([{
                    "Purchase Orders": len(purchase_orders),
                    "Total SKUs Ordered": total_skus,
                    "Avg mins/SKU": avg_po_sku,
                    "Arrangements": len(arrangements),
                    "Total Medicines": total_medicines,
                    "Avg mins/Arrangement": avg_arr,
                    "Returns": len(returns),
                    "PharmaRack Searches": len(pharmarack),
                }]), width='stretch', hide_index=True)

                # Arrangement pipeline
                st.divider()
                st.markdown("#### 📦 Today's Arrangements")
                try:
                    arr_resp = supabase.table("arrangements").select("*")\
                        .eq("order_placed_date", date_str())\
                        .eq("order_by", st.session_state.name).execute()
                    my_arrangements = arr_resp.data or []
                    if my_arrangements:
                        for arr in my_arrangements:
                            status = arr.get("status","")
                            urgency = arr.get("urgency","Normal")
                            icon = "🔴" if urgency=="Very Urgent" else "🟡" if urgency=="Urgent" else "🟢"
                            st.markdown(f"{icon} **#{arr.get('arrangement_no','')}** | {arr.get('distributor','')} | **{status}**")
                    else:
                        st.info("No arrangements placed today!")
                except:
                    pass

            except Exception as e:
                st.error(f"Dashboard error: {e}")

    elif team == "Stock":
        if "stock_active_form" not in st.session_state:
            st.session_state.stock_active_form = None

        with st.sidebar:
            st.divider()
            st.markdown("### 📥 Incoming Stock")
            if st.button("📒 Register Entry", width='stretch', key="s_register",
                type="primary" if st.session_state.stock_active_form=="register" else "secondary"):
                st.session_state.stock_active_form = "register"
                st.rerun()
            if st.button("📦 Receive Porter", width='stretch', key="s_receive",
                type="primary" if st.session_state.stock_active_form=="receive" else "secondary"):
                st.session_state.stock_active_form = "receive"
                st.rerun()
            if st.button("🧾 Bills Register", width='stretch', key="s_bills",
                type="primary" if st.session_state.stock_active_form=="bills" else "secondary"):
                st.session_state.stock_active_form = "bills"
                st.rerun()
            st.markdown("### ✅ Processing")
            if st.button("✔️ Bill Cross Check", width='stretch', key="s_crosscheck",
                type="primary" if st.session_state.stock_active_form=="crosscheck" else "secondary"):
                st.session_state.stock_active_form = "crosscheck"
                st.rerun()
            if st.button("📤 Bill Upload", width='stretch', key="s_upload",
                type="primary" if st.session_state.stock_active_form=="upload" else "secondary"):
                st.session_state.stock_active_form = "upload"
                st.rerun()
            st.markdown("### 🔧 Other Work")
            if st.button("↩️ Purchase Return", width='stretch', key="s_return",
                type="primary" if st.session_state.stock_active_form=="return" else "secondary"):
                st.session_state.stock_active_form = "return"
                st.rerun()
            if st.button("🧹 Rack Cleaning", width='stretch', key="s_rack",
                type="primary" if st.session_state.stock_active_form=="rack" else "secondary"):
                st.session_state.stock_active_form = "rack"
                st.rerun()
            if st.button("📊 Inventory Check", width='stretch', key="s_inventory",
                type="primary" if st.session_state.stock_active_form=="inventory" else "secondary"):
                st.session_state.stock_active_form = "inventory"
                st.rerun()
            if st.button("✏️ Edit Entry", width='stretch', key="s_edit",
                type="primary" if st.session_state.stock_active_form=="edit" else "secondary"):
                st.session_state.stock_active_form = "edit"
                st.rerun()
            if st.button("✏️ Other", width='stretch', key="s_other",
                type="primary" if st.session_state.stock_active_form=="other" else "secondary"):
                st.session_state.stock_active_form = "other"
                st.rerun()

            if st.session_state.stock_active_form:
                st.divider()
                if st.button("✖️ Close Form", width='stretch', key="s_close"):
                    st.session_state.stock_active_form = None
                    st.rerun()

            # My Tasks Today in sidebar
            st.divider()
            st.markdown("**📋 My Tasks Today:**")
            try:
                resp = supabase.table("daily_tasks").select("*")\
                    .eq("person", st.session_state.name)\
                    .eq("date", date_str()).execute()
                tasks = resp.data or []
                if tasks:
                    for t in sorted(tasks, key=lambda x: x.get("time","")):
                        status_icon = "🔄" if t.get("status")=="In Progress" else "✅"
                        st.markdown(f"{status_icon} {t.get('time','')} — **{t.get('task_type','')}**")
                else:
                    st.caption("No tasks yet today!")
            except:
                st.caption("Error loading tasks")

        # Main area (sidebar is hidden on phones -> everything reachable from here)
        show_area_status("stk_area")
        if st.session_state.stock_active_form:
            if st.button("⬅️ Back to menu", key="s_back", type="primary"):
                st.session_state.stock_active_form = None
                st.rerun()
            form_map = {
                "register":    form_register_entry,
                "receive":     form_porter_receive,
                "bills":       lambda: show_bills_register("stk_bills", default_area=st.session_state.get("work_area")),
                "crosscheck":  form_bill_crosscheck,
                "upload":      form_bill_upload_arrangement,
                "placement":   form_stock_placement,
                "plcheck":     form_placement_crosscheck,
                "return":      form_purchase_return,
                "rack":        form_rack_cleaning,
                "inventory":   form_inventory_check,
                "porter":      form_book_porter,
                "purchase":    form_purchase_order,
                "arrangement": form_arrangement,
                "edit":        form_edit_register_entry,
                "other":       form_other_task,
            }
            if st.session_state.stock_active_form in form_map:
                form_map[st.session_state.stock_active_form]()
        else:
            stock_main_menu()
            # Dashboard
            work_area = st.session_state.get("work_area","All Areas")
            show_live_pending_bills(work_area, f"#### ⏳ Pending bills — {work_area}")
            st.caption("Full journey of every bill (pending and placed): 🧾 Bills Register in the menu.")
            st.divider()
            show_incoming_arrangements(work_area)
            st.divider()
            _summary = st.expander(f"📊 Today's Summary — {work_area}", expanded=False)
            try:
              with _summary:
                reg_resp = supabase.table("daily_tasks").select("*")\
                    .eq("task_type","Register Entry").eq("date",date_str()).execute()
                reg_entries = [t for t in (reg_resp.data or [])
                    if work_area=="All Areas" or t.get("details",{}).get("area","")==work_area]
                cross_resp = supabase.table("daily_tasks").select("*")\
                    .eq("task_type","Bill Cross Check").eq("date",date_str()).execute()
                cross_tasks = cross_resp.data or []
                upload_resp = supabase.table("daily_tasks").select("*")\
                    .eq("task_type","Bill Upload (Software)").eq("date",date_str()).execute()
                upload_tasks = upload_resp.data or []
                place_resp = supabase.table("daily_tasks").select("*")\
                    .eq("task_type","Stock Placement").eq("date",date_str()).execute()
                place_tasks = place_resp.data or []
                crossed_bills = [t.get("details",{}).get("bill_no","") for t in cross_tasks]
                uploaded_bills = [t.get("details",{}).get("bill_no","") for t in upload_tasks]
                placed_bills = [t.get("details",{}).get("bill_no","") for t in place_tasks]
                normal_entries = [t for t in reg_entries if t.get("details",{}).get("order_type","") == "Normal Order"]
                normal_cross_pending  = len([t for t in normal_entries if t.get("details",{}).get("bill_no","") not in crossed_bills])
                normal_upload_pending = len([t for t in normal_entries if t.get("details",{}).get("bill_no","") in crossed_bills and t.get("details",{}).get("bill_no","") not in uploaded_bills])
                normal_place_pending  = len([t for t in normal_entries if t.get("details",{}).get("bill_no","") in uploaded_bills and t.get("details",{}).get("bill_no","") not in placed_bills])
                normal_cross_tasks  = [t for t in cross_tasks if not t.get("details",{}).get("arrangement_no","")]
                normal_upload_tasks = [t for t in upload_tasks if not t.get("details",{}).get("arrangement_no","")]
                normal_place_tasks  = [t for t in place_tasks if not t.get("details",{}).get("arrangement_no","")]
                def avg_sku(tasks, field="no_items"):
                    dur = sum([int(float(t.get("duration_mins",0) or 0)) for t in tasks])
                    sku = sum([int(float((t.get("details") or {}).get(field,0) or 0)) for t in tasks])
                    return round(dur/sku, 2) if sku > 0 else 0
                arr_resp = supabase.table("arrangements").select("*").eq("order_placed_date", date_str()).execute()
                arr_today = arr_resp.data or []
                if work_area != "All Areas":
                    arr_today = [a for a in arr_today if a.get("area","") == work_area]
                arr_reached    = [a for a in arr_today if a.get("status") in ["Reached Warehouse","Bill Cross Checked","Bill Uploaded","Stock Placed","Completed"]]
                arr_cross_pend = len([a for a in arr_today if a.get("status")=="Reached Warehouse"])
                arr_upload_pend= len([a for a in arr_today if a.get("status")=="Bill Cross Checked"])
                arr_place_pend = len([a for a in arr_today if a.get("status")=="Bill Uploaded"])
                arr_cross_tasks  = [t for t in cross_tasks if t.get("details",{}).get("arrangement_no","")]
                arr_upload_tasks = [t for t in upload_tasks if t.get("details",{}).get("arrangement_no","")]
                arr_place_tasks  = [t for t in place_tasks if t.get("details",{}).get("arrangement_no","")]
                st.markdown("#### 🧾 Normal Orders")
                st.dataframe(pd.DataFrame([{
                    "Bills Received": len(normal_entries),
                    "Cross Check Pending": normal_cross_pending,
                    "Upload Pending": normal_upload_pending,
                    "Avg Check/SKU": f"{avg_sku(normal_cross_tasks)} mins",
                    "Avg Upload/SKU": f"{avg_sku(normal_upload_tasks)} mins",
                }]), width='stretch', hide_index=True)
                st.divider()
                st.markdown("#### 📦 Arrangement Orders")
                st.dataframe(pd.DataFrame([{
                    "Bills Received": len(arr_reached),
                    "Cross Check Pending": arr_cross_pend,
                    "Upload Pending": arr_upload_pend,
                    "Avg Check/SKU": f"{avg_sku(arr_cross_tasks)} mins",
                    "Avg Upload/SKU": f"{avg_sku(arr_upload_tasks)} mins",
                }]), width='stretch', hide_index=True)
            except Exception as e:
                st.error(f"Dashboard error: {e}")





    if st.session_state.team == "Stock":
        st.divider()
        show_my_performance()
    st.divider()
    c1,c2 = st.columns([3,1])
    with c1: st.subheader("📋 My Tasks Today")
    with c2:
        if st.button("🔄 Refresh", key="refresh_tasks"):
            st.rerun()

    # Show In Progress tasks from session state
    in_progress = []
    # Show only relevant tasks per team
    team = st.session_state.team
    if team == "Purchase":
        timer_keys = {
            "purchase_order": "Purchase Order",
            "purchase_return": "Purchase Return",
            "pharmarack": "PharmaRack Search",
            "bounce": "Bounce Medicine Study",
            "arrangement_order": "Arrangement Order",
            "other_task": "Other Task",
        }
    elif team == "Stock":
        timer_keys = {
            "bill_crosscheck": "Bill Cross Check",
            "bill_upload": "Bill Upload",
            "bill_upload_normal": "Bill Upload",
            "stock_placement": "Stock Placement",
            "rack_cleaning": "Rack Cleaning",
            "inventory": "Inventory Check",
            "other_task": "Other Task",
        }
    elif team == "Call":
        timer_keys = {
            "call_log": "Call Log",
            "medicine_search": "Medicine Search",
            "other_task": "Other Task",
        }
    elif team == "Delivery":
        timer_keys = {
            "delivery": "Delivery Trip",
            "pickup": "Pickup",
            "other_task": "Other Task",
        }
    else:
        timer_keys = {
            "other_task": "Other Task",
        }
    timer_keys.update({"bill_crosscheck": "Bill Cross Check", "bill_upload": "Bill Upload",
                       "bill_upload_normal": "Bill Upload", "stock_placement": "Stock Placement",
                       "purchase_order": "Purchase Order", "arrangement_order": "Arrangement Order",
                       "purchase_return": "Purchase Return", "other_task": "Other Task"})
    active_task_ids = set()
    for key, task_name in timer_keys.items():
        start_time = st.session_state.get(f"{key}_start")
        if start_time and st.session_state.get(f"{key}_task_id"):
            active_task_ids.add(st.session_state.get(f"{key}_task_id"))
        if start_time:
            elapsed = int((now_ist() - start_time).total_seconds() / 60)
            in_progress.append({
                "Time": start_time.strftime("%I:%M %p"),
                "Task": task_name,
                "Details": "🔄 In Progress...",
                "Start": start_time.strftime("%I:%M %p"),
                "End": "In Progress",
                "Duration": f"{elapsed} mins",
            })

    if in_progress:
        st.warning(f"⏳ {len(in_progress)} task(s) in progress:")
        st.dataframe(pd.DataFrame(in_progress), width='stretch')
    try:
        resp = supabase.table("daily_tasks").select("*")\
            .eq("person", st.session_state.name)\
            .eq("date", date_str()).execute()

        # Also load In Progress tasks from yesterday (not completed)
        inprogress_resp = supabase.table("daily_tasks").select("*")\
            .eq("person", st.session_state.name)\
            .eq("status", "In Progress")\
            .execute()
        # Unfinished = started but never submitted (any day), except timers running right now
        unfinished = [t for t in (inprogress_resp.data or []) if t.get("id") not in active_task_ids]
        inprogress_data = []
        if unfinished:
            with st.expander(f"⚠️ {len(unfinished)} unfinished task(s) — started but never submitted (not counted)"):
                st.caption("These timers were started but the form was never submitted (page closed, logged out, etc.). "
                           "Discard them to clean up — they are not counted in your totals.")
                st.dataframe(pd.DataFrame([{"Date": t.get("date",""), "Started": t.get("start_time",""),
                                            "Task": t.get("task_type","")} for t in unfinished]),
                             hide_index=True, width='stretch')
                if st.button("🗑️ Discard all unfinished", key="discard_unfinished"):
                    try:
                        for part in _chunks([t["id"] for t in unfinished], 100):
                            supabase.table("daily_tasks").delete().in_("id", part)\
                                .eq("status", "In Progress").execute()
                        st.success("✅ Discarded")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        # Also load arrangement orders placed by this person
        arr_resp = supabase.table("arrangements").select("*")\
            .eq("order_by", st.session_state.name)\
            .eq("order_placed_date", date_str()).execute()
        
        # Convert arrangements to daily_tasks format
        arr_tasks = []
        for a in (arr_resp.data or []):
            arr_tasks.append({
                "time": a.get("order_placed_time",""),
                "task_type": "Arrangement",
                "details": {
                    "distributor": a.get("distributor",""),
                    "arrangement_no": a.get("arrangement_no",""),
                    "no_medicines": a.get("no_medicines","0"),
                    "urgency": a.get("urgency",""),
                    "pickup_type": a.get("pickup_type",""),
                },
                "start_time": a.get("order_placed_time",""),
                "end_time": "",
                "duration_mins": 0,
                "status": a.get("status","Pending")
            })
        
        arr_meds_lookup = {str(a.get("arrangement_no","")): a.get("no_medicines","0") for a in (arr_resp.data or [])}
        arr_area_lookup = {str(a.get("arrangement_no","")): a.get("area","") for a in (arr_resp.data or [])}

        # Only finished tasks are shown and counted
        all_data = [t for t in (resp.data or []) if t.get("status") != "In Progress"] + inprogress_data
        if all_data:
            df = pd.DataFrame(all_data)
            # Sort by time
            try:
                df["sort_time"] = pd.to_datetime(df["time"], format="%I:%M %p", errors="coerce")
                df = df.sort_values("sort_time").drop(columns=["sort_time"])
            except:
                pass
            display_rows = []
            total_sku = 0
            total_duration = 0

            for _, row in df.iterrows():
                details = row.get("details", {}) or {}
                secs = task_secs(row)
                duration = round(secs/60, 1)

                # Get SKU based on task type
                if row.get("task_type") == "Purchase Order":
                    try:
                        sku = int(float(details.get("no_sku",0) or 0))
                    except:
                        sku = 0
                    po_dist = details.get("distributor","")
                    po_area_txt = details.get("area","")
                    parts = [p for p in [po_dist, po_area_txt] if p]
                    extra = " | ".join(parts + [f"SKUs: {sku}"])
                elif row.get("task_type") in ("Bill Cross Check", "Stock Placement", "Bill Upload (Software)"):
                    sku, extra = task_qty_detail(row)
                elif row.get("task_type") == "Call Log":
                    sku = int(float(details.get("calls_made",0) or 0))
                    picked = int(details.get("calls_picked",0) or 0)
                    not_picked = sku - picked
                    orders = details.get("orders_delivered",0)
                    extra = f"Made:{sku} | Picked:{picked} | Not Picked:{not_picked} | Orders:{orders}"
                elif row.get("task_type") == "Medicine Search":
                    sku = int(float(details.get("no_searched",0) or 0))
                    found = details.get("no_found",0)
                    not_found = details.get("no_not_found",0)
                    extra = f"Searched:{sku} | Found:{found} | Not Found:{not_found}"
                elif row.get("task_type") == "Register Entry":
                    sku, extra = task_qty_detail(row)
                elif row.get("task_type") in ["Order Import","Customer Items Check","Customer Items Received","Customer Delivery Update"]:
                    try:
                        sku = int(float(details.get("lines",0) or 0))
                    except:
                        sku = 0
                    if row.get("task_type") == "Order Import":
                        extra = f"{details.get('area','')} | {sku} new items ({details.get('file_lines','')} in file)"
                    elif row.get("task_type") == "Customer Items Check":
                        extra = f"{details.get('area','')} | In Store: {details.get('in_store',0)} | Not Available: {details.get('not_available',0)}"
                    elif row.get("task_type") == "Customer Delivery Update":
                        extra = f"Order {details.get('order','')} | Delivered: {details.get('delivered',0)} | Not delivered: {details.get('not_delivered',0)}"
                    else:
                        extra = f"{details.get('arrangement_no','')} | Received: {details.get('received',0)} | Short: {details.get('short',0)}"
                elif row.get("task_type") == "Arrangement Order":
                    arr_no_row = str(details.get("arrangement_no",""))
                    try:
                        sku = int(float(arr_meds_lookup.get(arr_no_row, details.get("no_medicines",0)) or 0))
                    except:
                        sku = 0
                    arr_area_txt = arr_area_lookup.get(arr_no_row) or details.get("area","")
                    parts = [f"#{arr_no_row}" if arr_no_row else "", details.get("distributor",""), arr_area_txt]
                    extra = " | ".join([p for p in parts if p])
                else:
                    sku = 0
                    extra = details.get("distributor","") or details.get("task_name","")

                avg = round(duration/sku, 1) if sku > 0 and duration > 0 else 0
                per_med_types = ["Stock Placement","Arrangement Order","Purchase Order"]
                avg_secs = round(secs/sku, 1) if sku > 0 and secs > 0 else 0
                total_sku += sku
                total_duration += duration

                display_rows.append({
                    "Time": row.get("time",""),
                    "Task": row.get("task_type",""),
                    "Details": extra,
                    "Start": row.get("start_time",""),
                    "End": row.get("end_time",""),
                    "Duration": fmt_secs(secs) if row.get("end_time") else "In Progress",
                    "Qty": str(sku) if sku > 0 else "",
                    "Avg secs/unit": f"{avg_secs} secs" if avg_secs else "",
                })

            st.dataframe(pd.DataFrame(display_rows), width='stretch', hide_index=True)
            st.caption("Qty = SKUs (Purchase Order) · medicines (Arrangement / Placement) · items (Register / Cross Check) · calls (Call Log)")
            total_duration = round(total_duration, 1)

            # Smart Summary based on team
            overall_avg = round(total_duration/total_sku, 1) if total_sku > 0 else 0
            team = st.session_state.team

            c1,c2,c3,c4 = st.columns(4)
            with c1: st.metric("Total Tasks", len(display_rows))
            if team != "Purchase":
                with c3: st.metric("Total Time", f"{total_duration} mins")

            if team == "Call":
                call_rows = [row for _, row in df.iterrows() if row.get("task_type") == "Call Log"]
                search_rows = [row for _, row in df.iterrows() if row.get("task_type") == "Medicine Search"]

                total_calls  = sum([int((row.get("details") or {}).get("calls_made",0) or 0) for row in call_rows])
                total_picked = sum([int((row.get("details") or {}).get("calls_picked",0) or 0) for row in call_rows])
                total_orders = sum([int((row.get("details") or {}).get("orders_delivered",0) or 0) for row in call_rows])

                # Medicine search stats
                total_searched  = sum([int((row.get("details") or {}).get("no_searched",0) or 0) for row in search_rows])
                total_found     = sum([int((row.get("details") or {}).get("no_found",0) or 0) for row in search_rows])
                total_not_found = sum([int((row.get("details") or {}).get("no_not_found",0) or 0) for row in search_rows])
                search_duration = sum([int(float(row.get("duration_mins",0) or 0)) for row in search_rows])
                avg_search_sku  = round(search_duration/total_searched, 2) if total_searched > 0 else 0
                
                # Calculate averages per hour
                total_hours = round(total_duration/60, 2) if total_duration > 0 else 0
                avg_calls_per_hour = round(total_calls/total_hours, 1) if total_hours > 0 else 0
                avg_orders_per_hour = round(total_orders/total_hours, 1) if total_hours > 0 else 0

                pickup_rate = round((total_picked/total_calls)*100, 1) if total_calls > 0 else 0

                with c2: st.metric("Total Calls", total_calls)
                with c4: st.metric("Total Orders", total_orders)

                st.divider()
                r1,r2,r3,r4 = st.columns(4)
                with r1: st.metric("📞 Picked", total_picked)
                with r2: st.metric("📵 Not Picked", total_calls - total_picked)
                with r3: st.metric("📊 Pickup Rate", f"{pickup_rate}%")
                with r4: st.metric("⏱️ Total Time", f"{total_duration} mins")

                if search_rows:
                    st.divider()
                    st.markdown("**🔍 Medicine Search:**")
                    s1,s2,s3,s4 = st.columns(4)
                    with s1: st.metric("Searched", total_searched)
                    with s2: st.metric("Found", total_found)
                    with s3: st.metric("Not Found", total_not_found)
                    with s4: st.metric("Avg mins/SKU", avg_search_sku)
            elif team == "Purchase":
                # Calculate purchase metrics
                normal_orders = [row for _, row in df.iterrows() if row.get("task_type") == "Purchase Order"]
                arrangements  = [row for _, row in df.iterrows() if row.get("task_type") == "Arrangement Order" and row.get("status") != "In Progress"]
                pharmarack    = [row for _, row in df.iterrows() if row.get("task_type") == "PharmaRack Search"]
                returns       = [row for _, row in df.iterrows() if row.get("task_type") == "Purchase Return"]

                # Only real work: skip empty/unfinished rows
                normal_orders = [r for r in normal_orders if int(float((r.get("details") or {}).get("no_sku",0) or 0)) > 0]
                arrangements  = [r for r in arrangements if (r.get("details") or {}).get("arrangement_no")]

                def _meds(r):
                    d = r.get("details") or {}
                    try:
                        return int(float(arr_meds_lookup.get(str(d.get("arrangement_no","")), d.get("no_medicines",0)) or 0))
                    except Exception:
                        return 0

                total_skus  = sum([int(float((r.get("details") or {}).get("no_sku",0) or 0)) for r in normal_orders])
                total_meds  = sum([_meds(r) for r in arrangements])
                normal_secs = sum([task_secs(r) for r in normal_orders])
                arr_secs    = sum([task_secs(r) for r in arrangements])
                all_secs    = sum([task_secs(r) for _, r in df.iterrows() if r.get("end_time")])

                avg_normal_secs = normal_secs/len(normal_orders) if normal_orders else 0
                avg_arr_secs    = arr_secs/len(arrangements) if arrangements else 0
                secs_per_sku    = round(normal_secs/total_skus, 1) if total_skus else 0
                secs_per_med    = round(arr_secs/total_meds, 1) if total_meds else 0

                with c2: st.metric("📦 Total SKUs", total_skus)
                with c3: st.metric("💊 Total Medicines", total_meds)
                with c4: st.metric("⏱️ Total Time", fmt_secs(all_secs))

                # Show only sections with activity today
                if normal_orders:
                    st.divider()
                    st.markdown("**🛒 Normal Orders**")
                    n1,n2,n3,n4 = st.columns(4)
                    with n1: st.metric("Orders", len(normal_orders))
                    with n2: st.metric("Total Time", fmt_secs(normal_secs))
                    with n3: st.metric("Avg Time/Order", fmt_secs(avg_normal_secs))
                    with n4: st.metric("Avg secs/SKU", f"{secs_per_sku} secs")

                if arrangements:
                    st.divider()
                    st.markdown("**📋 Arrangement Orders**")
                    a1,a2,a3,a4 = st.columns(4)
                    with a1: st.metric("Arrangements", len(arrangements))
                    with a2: st.metric("Total Time", fmt_secs(arr_secs))
                    with a3: st.metric("Avg Time/Arr", fmt_secs(avg_arr_secs))
                    with a4: st.metric("Avg secs/Medicine", f"{secs_per_med} secs")

                if pharmarack or returns:
                    st.divider()
                    r5,r6,r7,r8 = st.columns(4)
                    with r5: st.metric("💊 PharmaRack", len(pharmarack))
                    with r6: st.metric("↩️ Returns", len(returns))

                # Stock work done by Purchase people
                reg_rows   = [r for _, r in df.iterrows() if r.get("task_type") == "Register Entry"]
                cc_rows    = [r for _, r in df.iterrows() if r.get("task_type") == "Bill Cross Check"]
                up_rows    = [r for _, r in df.iterrows() if r.get("task_type") in ["Bill Upload (Software)","Bill Upload"]]
                place_rows = [r for _, r in df.iterrows() if r.get("task_type") == "Stock Placement"]
                if reg_rows or cc_rows or up_rows or place_rows:
                    reg_items = sum([int(_to_float((r.get("details") or {}).get("no_items"), 0)) for r in reg_rows])
                    cc_items  = sum([int(_to_float((r.get("details") or {}).get("no_items"), 0)) for r in cc_rows])
                    cc_secs   = sum([task_secs(r) for r in cc_rows])
                    st.divider()
                    st.markdown("**📦 Stock Work**")
                    s1,s2,s3,s4 = st.columns(4)
                    with s1: st.metric("📒 Register Entries", f"{len(reg_rows)} | {reg_items} items")
                    with s2: st.metric("✔️ Bills Cross Checked", f"{len(cc_rows)} | {cc_items} items")
                    with s3: st.metric("📤 Uploads | 📍 Placements", f"{len(up_rows)} | {len(place_rows)}")
                    with s4: st.metric("⏱️ Avg secs/item (check)", f"{round(cc_secs/cc_items,1) if cc_items else 0} secs")
            elif team == "Stock":
                # Calculate stock metrics
                reg_entries   = [row for _, row in df.iterrows() if row.get("task_type") == "Register Entry"]
                cross_checks  = [row for _, row in df.iterrows() if row.get("task_type") == "Bill Cross Check"]
                bill_uploads  = [row for _, row in df.iterrows() if row.get("task_type") in ["Bill Upload","Bill Upload (Arrangement)"]]
                placements    = [row for _, row in df.iterrows() if row.get("task_type") == "Stock Placement"]
                place_checks  = [row for _, row in df.iterrows() if row.get("task_type") == "Placement Cross Check"]
                rack_cleaning = [row for _, row in df.iterrows() if row.get("task_type") == "Rack Cleaning"]
                inventory     = [row for _, row in df.iterrows() if row.get("task_type") == "Inventory Check"]

                # Items metrics
                items_received = sum([int(float((row.get("details") or {}).get("no_items",0) or 0)) for row in reg_entries])
                items_checked  = sum([int(float((row.get("details") or {}).get("no_items",0) or 0)) for row in cross_checks])
                meds_placed    = sum([int(float((row.get("details") or {}).get("no_medicines",0) or 0)) for row in placements])

                # Avg time metrics
                cross_dur = sum([int(row.get("duration_mins",0) or 0) for row in cross_checks])
                place_dur = sum([int(row.get("duration_mins",0) or 0) for row in placements])
                avg_cross = round(cross_dur/items_checked, 2) if items_checked > 0 else 0
                avg_place = round(place_dur/meds_placed, 2) if meds_placed > 0 else 0

                # Issues found
                issues = sum([1 for row in place_checks if "No" in str((row.get("details") or {}).get("placement_issues",""))])

                with c2: st.metric("Total Items Handled", items_received + items_checked + meds_placed)
                with c4: st.metric("Avg mins/Item (Check)", f"{avg_cross} mins")

                st.divider()
                r1,r2,r3,r4 = st.columns(4)
                with r1: st.metric("📒 Register Entry", f"{len(reg_entries)} | {items_received} items")
                with r2: st.metric("✔️ Bill Cross Check", f"{len(cross_checks)} | {items_checked} items")
                with r3: st.metric("📤 Bill Upload", len(bill_uploads))
                with r4: st.metric("📍 Stock Placed", f"{len(placements)} | {meds_placed} meds")

                st.divider()
                r5,r6,r7,r8 = st.columns(4)
                with r5: st.metric("⏱️ Avg mins/Med (Place)", f"{avg_place} mins")
                with r6: st.metric("🔍 Placement Checks", len(place_checks))
                with r7: st.metric("⚠️ Issues Found", issues)
                with r8: st.metric("🧹 Rack Cleaning", len(rack_cleaning))
            else:
                with c2: st.metric("Total Count", total_sku)
                with c4: st.metric("Avg/Item", f"{overall_avg} mins")
        else:
            st.info("No tasks submitted today yet.")
    except Exception as e:
        st.error(f"Error: {e}")

# ── CUSTOMER ORDER LINKING ────────────────────────────────────────────────────
# Backend order-schedule file -> item lines -> Purchase decides (In Store / Not Available / Arrange)
# -> Stock receives arranged lines -> order is Ready. 3-hour clock starts at upload time.

OPEN_LINE_STATUSES = ["Pending", "Partly Arranged"]
SELECT_AREA = "— Select Area —"

BACKEND_COLS = {
    "scheduleddate": "scheduled_date", "date": "scheduled_date",
    "order": "order_no", "orderno": "order_no", "ordernumber": "order_no", "orderid": "order_no",
    "customername": "customer_name", "customer": "customer_name",
    "customerphone": "customer_phone", "phone": "customer_phone", "mobile": "customer_phone",
    "itemname": "item_name", "medicinename": "item_name", "item": "item_name",
    "packsize": "pack_size", "pack": "pack_size",
    "qty": "qty", "quantity": "qty",
    "rx": "rx", "unitprice": "unit_price", "linetotal": "line_total",
}

def now_iso():
    return now_ist().isoformat()

def to_ist(ts):
    """Supabase timestamp -> IST datetime (or None)"""
    try:
        if ts is None or str(ts) in ("", "None", "nan", "NaT"):
            return None
        t = pd.to_datetime(ts, utc=True)
        return t.tz_convert("Asia/Kolkata").to_pydatetime()
    except Exception:
        return None

def age_mins(ts, now=None):
    t = to_ist(ts)
    if not t:
        return 0
    return max(0, int(((now or now_ist()) - t).total_seconds() // 60))

def fmt_age(mins):
    mins = int(mins or 0)
    return f"{mins//60}h {mins%60}m" if mins >= 60 else f"{mins}m"

def age_flag(mins):
    return "🔴" if mins >= 180 else ("🟡" if mins >= 120 else "🟢")

def _norm_col(s):
    return "".join(ch for ch in str(s).lower() if ch.isalnum())

def _clean_str(v):
    s = str(v if v is not None else "").strip()
    if s.lower() in ("nan", "none", "nat"):
        return ""
    if s.endswith(".0") and s[:-2].isdigit():
        s = s[:-2]
    return s

def _to_float(v, default=0.0):
    try:
        f = float(str(v).replace(",", "").strip())
        return default if f != f else f
    except Exception:
        return default

def _qty_txt(q):
    q = float(q or 0)
    return str(int(q)) if q == int(q) else str(q)

def parse_backend_file(uploaded):
    """Read the backend order-schedule file (.xlsx / .csv) into clean item lines"""
    name = uploaded.name.lower()
    if name.endswith((".xlsx", ".xls")):
        raw = pd.read_excel(uploaded, dtype=str)
    else:
        raw = pd.read_csv(uploaded, dtype=str)
    rename = {}
    for c in raw.columns:
        k = BACKEND_COLS.get(_norm_col(c))
        if k and k not in rename.values():
            rename[c] = k
    df = raw.rename(columns=rename)
    missing = [c for c in ["order_no", "item_name"] if c not in df.columns]
    if missing:
        return [], ("File is missing column(s): " + ", ".join(missing) +
                    ". Expected headers like: Scheduled Date, Order #, Customer Name, Customer Phone, Item Name, Pack Size, Qty")
    lines = {}
    for _, r in df.iterrows():
        order_no = _clean_str(r.get("order_no"))
        item = _clean_str(r.get("item_name"))
        if not order_no or not item:
            continue
        pack = _clean_str(r.get("pack_size"))
        key = f"{order_no}|{item.lower()}|{pack.lower()}"
        qty = _to_float(r.get("qty"), 1) or 1
        if key in lines:                       # same item twice in one order -> add qty
            lines[key]["qty"] += qty
            continue
        lines[key] = {
            "line_key": key,
            "order_no": order_no,
            "scheduled_date": _clean_str(r.get("scheduled_date"))[:10],
            "customer_name": _clean_str(r.get("customer_name")),
            "customer_phone": _clean_str(r.get("customer_phone")),
            "item_name": item,
            "pack_size": pack,
            "qty": qty,
            "rx": _clean_str(r.get("rx")),
            "unit_price": _to_float(r.get("unit_price"), 0),
            "line_total": _to_float(r.get("line_total"), 0),
        }
    return list(lines.values()), None

def _chunks(seq, n):
    seq = list(seq)
    for i in range(0, len(seq), n):
        yield seq[i:i+n]

def log_simple_task(task_type, details):
    """Record an instant task (no timer) so it shows in My Tasks / performance"""
    try:
        t = now_ist().strftime("%I:%M:%S %p")
        supabase.table("daily_tasks").insert({
            "date": date_str(), "time": time_str(),
            "person": st.session_state.name, "team": st.session_state.team,
            "task_type": task_type, "details": details,
            "start_time": t, "end_time": t, "duration_mins": "0",
            "status": "Completed"
        }).execute()
    except Exception:
        pass

def import_order_lines(lines, area):
    """Insert new lines, keep existing ones untouched, flag lines that disappeared"""
    now = now_iso()
    keys = [l["line_key"] for l in lines]
    existing = {}
    for part in _chunks(keys, 80):
        resp = supabase.table("customer_order_lines")\
            .select("id,line_key,area,status,removed,qty").in_("line_key", part).execute()
        for r in resp.data or []:
            existing[r["line_key"]] = r

    new_rows, seen_ids, wrong_area = [], [], []
    restored = qty_changed = 0
    for l in lines:
        ex = existing.get(l["line_key"])
        if not ex:
            row = dict(l)
            row.update({"area": area, "status": "Pending", "qty_arranged": 0, "qty_received": 0,
                        "imported_at": now, "imported_by": st.session_state.name,
                        "last_seen_at": now, "removed": False})
            new_rows.append(row)
            continue
        if ex.get("area") and ex.get("area") != area:
            wrong_area.append(f"#{l['order_no']} ({ex.get('area')})")
            continue
        if ex.get("removed"):
            supabase.table("customer_order_lines").update(
                {"removed": False, "status": "Pending", "last_seen_at": now}).eq("id", ex["id"]).execute()
            restored += 1
        elif ex.get("status") == "Pending" and _to_float(ex.get("qty"), 0) != l["qty"]:
            supabase.table("customer_order_lines").update(
                {"qty": l["qty"], "last_seen_at": now}).eq("id", ex["id"]).execute()
            qty_changed += 1
        else:
            seen_ids.append(ex["id"])

    for part in _chunks(seen_ids, 100):
        supabase.table("customer_order_lines").update({"last_seen_at": now}).in_("id", part).execute()
    for part in _chunks(new_rows, 200):
        supabase.table("customer_order_lines").insert(part).execute()

    # Lines of the same area + scheduled dates that are no longer in the file -> Removed
    removed = 0
    dates = sorted(set(l["scheduled_date"] for l in lines if l["scheduled_date"]))
    if dates:
        resp = supabase.table("customer_order_lines").select("id,line_key")\
            .eq("area", area).eq("status", "Pending").eq("removed", False)\
            .in_("scheduled_date", dates).execute()
        file_keys = set(keys)
        gone = [r["id"] for r in (resp.data or []) if r["line_key"] not in file_keys]
        for part in _chunks(gone, 100):
            supabase.table("customer_order_lines").update(
                {"removed": True, "status": "Removed"}).in_("id", part).execute()
        removed = len(gone)

    return {"new": len(new_rows), "existing": len(seen_ids), "restored": restored,
            "qty_changed": qty_changed, "removed": removed, "wrong_area": wrong_area}

def get_open_lines(area=None):
    q = supabase.table("customer_order_lines").select("*")\
        .in_("status", OPEN_LINE_STATUSES).eq("removed", False)
    if area and area not in ("All Areas", SELECT_AREA):
        q = q.eq("area", area)
    return q.order("imported_at").order("order_no").execute().data or []

def remaining_qty(line):
    return max(0.0, _to_float(line.get("qty"), 0) - _to_float(line.get("qty_arranged"), 0))

def refresh_line_status(line_id):
    """Recalculate a line's status from its arrangement lines"""
    lr = supabase.table("customer_order_lines").select("*").eq("id", line_id).execute().data
    if not lr:
        return
    line = lr[0]
    als = supabase.table("arrangement_lines").select("*").eq("line_id", line_id).execute().data or []
    if not als:
        return
    qty = _to_float(line.get("qty"), 0)
    ordered = sum(_to_float(a.get("qty_ordered"), 0) for a in als)
    received = sum(_to_float(a.get("qty_received"), 0) for a in als if a.get("status") != "Ordered")
    waiting = any(a.get("status") == "Ordered" for a in als)
    upd = {"qty_arranged": ordered, "qty_received": received}
    if ordered < qty and not line.get("remainder_note"):
        upd["status"] = "Partly Arranged"
    elif waiting:
        upd["status"] = "Arranged"
    else:
        upd["status"] = "Received" if received >= ordered else "Short"
        upd["completed_at"] = now_iso()
    supabase.table("customer_order_lines").update(upd).eq("id", line_id).execute()

# ── PURCHASE: IMPORT ──────────────────────────────────────────────────────────
def form_import_orders():
    st.subheader("📥 Import Customer Orders")
    st.caption("Upload the order-schedule file from backend — one area at a time. "
               "Re-uploading the same or a newer file is safe: only new items are added.")
    area = st.selectbox("Which area / store is this file for? *", [SELECT_AREA] + load_areas(), key="imp_area")
    up = st.file_uploader("Backend file (.xlsx or .csv)", type=["xlsx", "xls", "csv"],
                          key=f"imp_file_{st.session_state.get('imp_ver', 0)}")
    if not up:
        return
    try:
        lines, err = parse_backend_file(up)
    except Exception as e:
        st.error(f"Could not read file: {e}")
        return
    if err:
        st.error(err)
        return
    if not lines:
        st.warning("No item lines found in this file.")
        return
    n_orders = len(set(l["order_no"] for l in lines))
    st.info(f"📄 File has **{len(lines)} item lines** in **{n_orders} orders**")
    prev = pd.DataFrame(lines)[["scheduled_date", "order_no", "customer_name", "item_name", "pack_size", "qty"]]
    prev.columns = ["Date", "Order #", "Customer", "Item", "Pack", "Qty"]
    st.dataframe(prev, hide_index=True, width='stretch', height=250)

    if st.button("📥 Import", type="primary", key="imp_go", width='stretch'):
        if area == SELECT_AREA:
            st.error("Select the area / store for this file first!")
            return
        try:
            res = import_order_lines(lines, area)
        except Exception as e:
            st.error(f"Import failed: {e}")
            return
        st.success(f"✅ **{area}**: {res['new']} new items added · {res['existing']} already imported"
                   + (f" · {res['qty_changed']} qty updated" if res['qty_changed'] else "")
                   + (f" · {res['restored']} restored" if res['restored'] else ""))
        if res["removed"]:
            st.warning(f"🗑️ {res['removed']} pending item(s) are no longer in the backend file — marked **Removed** (cancelled/changed orders).")
        if res["wrong_area"]:
            st.error("⚠️ These orders were already imported under a DIFFERENT area and were skipped — "
                     "check you selected the right area: " + ", ".join(sorted(set(res["wrong_area"]))[:15]))
        log_simple_task("Order Import", {"area": area, "lines": str(res["new"]),
                                          "file_lines": str(len(lines)), "orders": str(n_orders)})
        st.session_state["imp_ver"] = st.session_state.get("imp_ver", 0) + 1

# ── PURCHASE: PENDING ITEMS ───────────────────────────────────────────────────
DELIVERY_TIMES = [""] + [datetime(2000, 1, 1, h, m).strftime("%I:%M %p") for h in range(7, 24) for m in (0, 30)]

def due_info(line, now=None):
    """(flag, minutes_left, label) from scheduled date + promised delivery time; None if no time"""
    t = (line.get("delivery_time") or "").strip()
    d = (line.get("scheduled_date") or "").strip()
    if not t or not d:
        return None
    try:
        due = IST.localize(datetime.strptime(f"{d} {t}", "%Y-%m-%d %I:%M %p"))
    except Exception:
        return None
    left = int(((due - (now or now_ist())).total_seconds()) // 60)
    flag = "🔴" if left <= 60 else ("🟡" if left <= 180 else "🟢")
    label = f"overdue {fmt_age(-left)}" if left < 0 else f"in {fmt_age(left)}"
    return flag, left, label

def _sched_label(d):
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%d %b")
    except Exception:
        return d or ""

def form_pending_items():
    st.subheader("🧾 Pending Customer Items")
    st.caption("For each item: 🏪 **In Store** (available, nothing to buy) or ❌ **Not Available** (can't be sourced). "
               "Items to buy from a distributor → tick them in **📦 Arrangement Order**. "
               "Set **Deliver by** (time promised to the customer) — it applies to the whole order.")
    try:
        all_lines = get_open_lines(None)
    except Exception as e:
        st.error(f"Could not load items — has the setup SQL been run in Supabase? ({e})")
        return
    c1, c2 = st.columns(2)
    with c1:
        area = st.selectbox("Area", ["All Areas"] + load_areas(), key="pi_area")
    dates = sorted(set(l.get("scheduled_date") or "" for l in all_lines))
    with c2:
        sched = st.selectbox("Scheduled date", ["All dates"] + [d for d in dates if d], key="pi_sched",
                             format_func=lambda d: d if d == "All dates" else _sched_label(d))
    lines = [l for l in all_lines
             if (area == "All Areas" or l.get("area") == area) and (sched == "All dates" or l.get("scheduled_date") == sched)]
    if not lines:
        st.success("🎉 No pending customer items for this filter!")
        return

    now = now_ist()
    def sort_key(l):
        di = due_info(l, now)
        return (l.get("scheduled_date") or "9999", di[1] if di else 10**9, str(l.get("imported_at") or ""), str(l.get("order_no")))
    lines = sorted(lines, key=sort_key)
    rows = []
    for l in lines:
        a = age_mins(l.get("imported_at"), now)
        di = due_info(l, now)
        rows.append({
            "id": l["id"],
            "⏰": di[0] if di else age_flag(a),
            "Sched": _sched_label(l.get("scheduled_date")),
            "Deliver by": l.get("delivery_time") or "",
            "Due": di[2] if di else "",
            "Age": fmt_age(a),
            "Order #": l.get("order_no", ""),
            "Customer": l.get("customer_name", ""),
            "Area": l.get("area", ""),
            "Item": l.get("item_name", ""),
            "Pack": l.get("pack_size", ""),
            "Qty": _qty_txt(remaining_qty(l)),
            "Status": l.get("status", ""),
            "Action": "—",
        })
    df = pd.DataFrame(rows)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Pending Items", len(rows))
    with c2: st.metric("Orders", df["Order #"].nunique())
    with c3: st.metric("🔴 Due within 1 hr / overdue", sum(1 for l in lines if (due_info(l, now) or (None, 10**9))[1] <= 60))
    with c4: st.metric("⏱️ No delivery time set", df[df["Deliver by"] == ""]["Order #"].nunique())

    ver = st.session_state.get("pi_ver", 0)
    edited = st.data_editor(
        df, key=f"pi_editor_{ver}", hide_index=True, width='stretch',
        disabled=[c for c in df.columns if c not in ("Action", "Deliver by")],
        column_config={
            "id": None,
            "Deliver by": st.column_config.SelectboxColumn("Deliver by", options=DELIVERY_TIMES,
                                                           help="Time promised to the customer (whole order)"),
            "Action": st.column_config.SelectboxColumn(
                "Action", options=["—", "🏪 In Store", "❌ Not Available"], required=True),
        })
    st.caption("⏰ with a delivery time: 🔴 due within 1 hr or overdue · 🟡 within 3 hrs · 🟢 later. "
               "Without a time: age since upload.")
    chosen = edited[edited["Action"] != "—"]
    old_time = {r["id"]: r["Deliver by"] for r in rows}
    time_changes = {}
    for _, r in edited.iterrows():
        if (r["Deliver by"] or "") != (old_time.get(r["id"]) or ""):
            time_changes[str(r["Order #"])] = r["Deliver by"] or None
    n_changes = len(chosen) + len(time_changes)
    if st.button(f"💾 Save ({len(chosen)} decision(s), {len(time_changes)} delivery time(s))", type="primary",
                 key="pi_save", disabled=n_changes == 0, width='stretch'):
        by_id = {l["id"]: l for l in lines}
        n_store = n_na = 0
        now_s = now_iso()
        try:
            for order_no, t in time_changes.items():
                supabase.table("customer_order_lines").update({"delivery_time": t})\
                    .eq("order_no", order_no).eq("removed", False).execute()
            for _, r in chosen.iterrows():
                line = by_id.get(int(r["id"]))
                if not line:
                    continue
                decision = "In Store" if "In Store" in r["Action"] else "Not Available"
                if line.get("status") == "Partly Arranged":
                    supabase.table("customer_order_lines").update({
                        "remainder_note": decision, "decided_by": st.session_state.name,
                        "decided_at": now_s}).eq("id", line["id"]).execute()
                    refresh_line_status(line["id"])
                else:
                    supabase.table("customer_order_lines").update({
                        "status": decision, "decided_by": st.session_state.name,
                        "decided_at": now_s, "completed_at": now_s}).eq("id", line["id"]).execute()
                if decision == "In Store":
                    n_store += 1
                else:
                    n_na += 1
            if n_store + n_na:
                log_simple_task("Customer Items Check", {"area": area, "lines": str(n_store + n_na),
                                                         "in_store": str(n_store), "not_available": str(n_na)})
            st.session_state["pi_ver"] = ver + 1
            st.success(f"✅ Saved: {n_store} In Store · {n_na} Not Available · {len(time_changes)} delivery time(s)")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e} — has delivery_time_setup.sql been run in Supabase?")

# ── ARRANGEMENT FORM: pick customer lines ────────────────────────────────────
def arrangement_line_picker():
    """Shown above the arrangement form. Returns (area, [selected rows])"""
    ver = st.session_state.get("arr_link_ver", 0)
    with st.expander("🔗 Customer order items for this distributor", expanded=True):
        link_area = st.selectbox("Area of customer orders", [SELECT_AREA] + load_areas(), key=f"arr_link_area_{ver}")
        if link_area == SELECT_AREA:
            st.caption("Select an area to see its pending customer items. (Or skip this and just enter the number of medicines below.)")
            return None, []
        try:
            open_lines = get_open_lines(link_area)
        except Exception as e:
            st.warning(f"Could not load customer items ({e})")
            return None, []
        if not open_lines:
            st.info("No pending customer items for this area.")
            return link_area, []
        now = now_ist()
        open_lines = sorted(open_lines, key=lambda l: (l.get("scheduled_date") or "9999",
                                                       (due_info(l, now) or (None, 10**9))[1],
                                                       str(l.get("imported_at") or "")))
        ldf = pd.DataFrame([{
            "id": l["id"],
            "Order?": False,
            "⏰": (due_info(l, now) or (age_flag(age_mins(l.get("imported_at"), now)),))[0],
            "Deliver by": (f"{_sched_label(l.get('scheduled_date'))} {l.get('delivery_time')}"
                           if l.get("delivery_time") else _sched_label(l.get("scheduled_date"))),
            "Order #": l.get("order_no", ""),
            "Customer": l.get("customer_name", ""),
            "Item": l.get("item_name", ""),
            "Pack": l.get("pack_size", ""),
            "Needed": remaining_qty(l),
            "Order Qty": remaining_qty(l),
        } for l in open_lines])
        ed = st.data_editor(
            ldf, key=f"arr_link_editor_{ver}", hide_index=True, width='stretch',
            disabled=["⏰", "Deliver by", "Order #", "Customer", "Item", "Pack", "Needed"],
            column_config={
                "id": None,
                "Order?": st.column_config.CheckboxColumn("Order?", help="Tick items you are ordering from this distributor"),
                "Order Qty": st.column_config.NumberColumn("Order Qty", min_value=0, step=1,
                                                           help="Change only if this item is split between 2 distributors"),
            })
        picked = ed[ed["Order?"] == True].to_dict("records")
        if picked:
            st.success(f"✅ {len(picked)} item(s) selected — they will be linked to this arrangement")
        return link_area, picked

def save_arrangement_links(arr_id, arr_no, distributor, area, picked):
    now_s = now_iso()
    for p in picked:
        qty = min(_to_float(p.get("Order Qty"), 0), _to_float(p.get("Needed"), 0))
        if qty <= 0:
            continue
        supabase.table("arrangement_lines").insert({
            "arrangement_id": arr_id, "arrangement_no": arr_no, "distributor": distributor,
            "area": area, "line_id": int(p["id"]), "order_no": str(p.get("Order #", "")),
            "item_name": p.get("Item", ""), "qty_ordered": qty, "status": "Ordered",
            "ordered_by": st.session_state.name, "ordered_at": now_s
        }).execute()
        refresh_line_status(int(p["id"]))
    st.session_state["arr_link_ver"] = st.session_state.get("arr_link_ver", 0) + 1

# ── STOCK: CONFIRM CUSTOMER ITEMS (inside Bill Cross Check) ───────────────────
def customer_items_editor(arr):
    """Show customer items linked to this ARR; returns the edited table (or None)"""
    try:
        als = supabase.table("arrangement_lines").select("*")\
            .eq("arrangement_no", str(arr.get("arrangement_no",""))).eq("status", "Ordered").execute().data or []
    except Exception:
        return None
    if not als:
        return None
    st.markdown(f"🧾 **Customer order items in this arrangement ({len(als)})** — change *Received* only if less arrived")
    df = pd.DataFrame([{
        "id": a["id"], "line_id": a.get("line_id"),
        "Order #": a.get("order_no", ""), "Item": a.get("item_name", ""),
        "Ordered": _to_float(a.get("qty_ordered"), 0),
        "Received": _to_float(a.get("qty_ordered"), 0),
    } for a in als])
    return st.data_editor(df, key=f"bc_cust_{arr.get('id','')}", hide_index=True, width='stretch',
                          disabled=["Order #", "Item", "Ordered"],
                          column_config={"id": None, "line_id": None,
                                         "Received": st.column_config.NumberColumn("Received", min_value=0, step=1)})

def save_customer_receipts(ed):
    """Save received qty for each customer item: full = Received, less = Short"""
    now_s = now_iso()
    n_ok = n_short = 0
    for _, r in ed.iterrows():
        rec = _to_float(r["Received"], 0)
        status = "Received" if rec >= _to_float(r["Ordered"], 0) else "Short"
        supabase.table("arrangement_lines").update({
            "qty_received": rec, "status": status,
            "received_by": st.session_state.name, "received_at": now_s
        }).eq("id", int(r["id"])).execute()
        if r.get("line_id") is not None and str(r.get("line_id")) != "nan":
            refresh_line_status(int(r["line_id"]))
        if status == "Received":
            n_ok += 1
        else:
            n_short += 1
    return n_ok, n_short

# ── ORDER TRACKER ─────────────────────────────────────────────────────────────
LINE_ICON = {"Pending": "⏳ Pending", "Partly Arranged": "📦 Part-arranged", "Arranged": "📦 Arranged",
             "In Store": "🏪 In Store", "Received": "✅ Received", "Short": "⚠️ Short",
             "Not Available": "❌ Not Available"}

def order_status(statuses):
    s = list(statuses)
    if all(x == "Pending" for x in s):
        return "⚪ Not Started"
    if any(x in ("Pending", "Partly Arranged", "Arranged") for x in s):
        return "🔄 In Progress"
    if any(x in ("Not Available", "Short") for x in s):
        return "⚠️ Done – Partial"
    return "✅ Ready"

def show_customer_order_tracker(kp="trk", show_phone=False):
    st.subheader("📦 Customer Order Tracker")
    c0, c1, c2, c3 = st.columns(4)
    with c0:
        date_by = st.selectbox("Date type", ["Scheduled date", "Imported on"], key=f"{kp}_dateby")
    with c1:
        day = st.date_input(date_by, value=today_ist(), key=f"{kp}_day")
    with c2:
        area = st.selectbox("Area", ["All Areas"] + load_areas(), key=f"{kp}_area")
    with c3:
        deliv_f = st.selectbox("Delivery", ["All", "✅ Delivered", "❌ Not delivered", "🟡 Partly", "📞 Awaiting call"],
                               key=f"{kp}_deliv")
    start = IST.localize(datetime(day.year, day.month, day.day))
    from datetime import timedelta
    end = start + timedelta(days=1)
    try:
        q = supabase.table("customer_order_lines").select("*").eq("removed", False)
        if date_by == "Scheduled date":
            q = q.eq("scheduled_date", day.strftime("%Y-%m-%d"))
        else:
            q = q.gte("imported_at", start.isoformat()).lt("imported_at", end.isoformat())
        if area != "All Areas":
            q = q.eq("area", area)
        lines = q.execute().data or []
    except Exception as e:
        st.error(f"Could not load — has the setup SQL been run in Supabase? ({e})")
        return

    def _order_delivery(ls):
        if all(l.get("delivery_status") == "Delivered" for l in ls):
            return "✅ Delivered"
        if all(l.get("delivery_status") == "Not Delivered" for l in ls):
            return "❌ Not delivered"
        if any(l.get("delivery_status") for l in ls):
            return "🟡 Partly"
        return "📞 Awaiting call"
    if deliv_f != "All" and lines:
        by_o = {}
        for l in lines:
            by_o.setdefault(l.get("order_no"), []).append(l)
        keep = {o for o, ls in by_o.items() if _order_delivery(ls) == deliv_f}
        lines = [l for l in lines if l.get("order_no") in keep]
    if not lines:
        st.info(f"No customer orders for this {date_by.lower()} / area / delivery filter.")
        return

    customer_order_summary(lines)
    st.divider()

    # arrangement links for distributor names
    links = {}
    for part in _chunks([l["id"] for l in lines], 100):
        for a in supabase.table("arrangement_lines").select("line_id,arrangement_no,distributor,ordered_by,ordered_at")\
                .in_("line_id", part).execute().data or []:
            links.setdefault(a["line_id"], []).append(a)

    now = now_ist()
    orders = {}
    for l in lines:
        orders.setdefault(l["order_no"], []).append(l)

    order_rows = []
    for ono, ls in orders.items():
        statuses = [l.get("status", "Pending") for l in ls]
        stt = order_status(statuses)
        t0 = min([to_ist(l.get("imported_at")) for l in ls if to_ist(l.get("imported_at"))] or [now])
        done = stt in ("✅ Ready", "⚠️ Done – Partial")
        t_end = max([to_ist(l.get("completed_at")) for l in ls if to_ist(l.get("completed_at"))] or [now]) if done else now
        mins = max(0, int((t_end - t0).total_seconds() // 60))
        row = {
            "⏰": "🔴" if mins >= 180 else ("🟢" if done else age_flag(mins)),
            "Order #": ono,
            "Customer": ls[0].get("customer_name", ""),
        }
        if show_phone:
            row["Phone"] = ls[0].get("customer_phone", "")
        di = due_info(ls[0], now)
        row.update({
            "Area": ls[0].get("area", ""),
            "Sched": _sched_label(ls[0].get("scheduled_date")),
            "Deliver by": (f"{di[0]} {ls[0].get('delivery_time')} ({di[2]})" if di and not done
                           else (ls[0].get("delivery_time") or "")),
            "Items": len(ls),
            "🏪 Store": statuses.count("In Store"),
            "📦 Arranged": sum(1 for s in statuses if s in ("Arranged", "Partly Arranged")),
            "✅ Received": statuses.count("Received"),
            "⏳ Pending": statuses.count("Pending"),
            "❌ N/A": statuses.count("Not Available") + statuses.count("Short"),
            "Status": stt,
            "🚚 Delivery": _order_delivery(ls),
            "Imported": t0.strftime("%I:%M %p"),
            "Time": fmt_age(mins) + ("" if done else " (running)"),
            "_mins": mins, "_done": done,
        })
        order_rows.append(row)

    odf = pd.DataFrame(order_rows).sort_values(["_done", "_mins"], ascending=[True, False])
    done_df = odf[odf["_done"]]
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: st.metric("Orders", len(odf))
    with m2: st.metric("✅ Ready", int((odf["Status"] == "✅ Ready").sum()))
    with m3: st.metric("🔄 Open", int((~odf["_done"]).sum()))
    with m4: st.metric("🔴 Over 3 hrs", int((odf["_mins"] >= 180).sum()))
    with m5: st.metric("Avg Time to Ready", fmt_age(done_df["_mins"].mean()) if not done_df.empty else "—")

    f1, f2 = st.columns([3, 2])
    with f1:
        search = st.text_input("🔍 Search — mobile no, order #, customer name or medicine", key=f"{kp}_search",
                               placeholder="e.g. 98716  ·  158213  ·  Shivam  ·  Glizina").strip().lower()
    with f2:
        status_filter = st.multiselect("Show status", sorted(odf["Status"].unique()), default=[], key=f"{kp}_st",
                                       placeholder="All statuses")
    match_orders = None
    if search:
        s_digits = "".join(ch for ch in search if ch.isdigit())
        match_orders = set()
        for l in lines:
            phone = "".join(ch for ch in str(l.get("customer_phone", "")) if ch.isdigit())
            if (search in str(l.get("order_no", "")).lower()
                    or search in str(l.get("customer_name", "")).lower()
                    or search in str(l.get("item_name", "")).lower()
                    or (s_digits and len(s_digits) >= 4 and s_digits in phone)):
                match_orders.add(str(l.get("order_no", "")))
    view = odf if not status_filter else odf[odf["Status"].isin(status_filter)]
    if match_orders is not None:
        view = view[view["Order #"].astype(str).isin(match_orders)]
        st.caption(f"🔍 {len(view)} order(s) match “{search}”")
    st.dataframe(view.drop(columns=["_mins", "_done"]), hide_index=True, width='stretch')

    # line level + export
    line_rows = []
    for l in sorted(lines, key=lambda x: (x.get("order_no", ""), x.get("item_name", ""))):
        ls = links.get(l["id"], [])
        line_rows.append({
            "Scheduled Date": l.get("scheduled_date", ""),
            "Order #": l.get("order_no", ""),
            "Customer Name": l.get("customer_name", ""),
            "Customer Phone": l.get("customer_phone", "") if show_phone else "",
            "Item Name": l.get("item_name", ""),
            "Pack Size": l.get("pack_size", ""),
            "Qty": _qty_txt(l.get("qty")),
            "Deliver by": l.get("delivery_time") or "",
            "Distributor Name": ", ".join(sorted(set(a.get("distributor", "") for a in ls))),
            "ARR No": ", ".join(sorted(set(a.get("arrangement_no", "") for a in ls))),
            "Arranged By": ", ".join(sorted(set(a.get("ordered_by", "") or "" for a in ls))),
            "Arranged At": ", ".join(sorted(set(to_ist(a.get("ordered_at")).strftime("%d %b %I:%M %p")
                                                for a in ls if to_ist(a.get("ordered_at"))))),
            "Area": l.get("area", ""),
            "Status": LINE_ICON.get(l.get("status", ""), l.get("status", "")),
            "Checked By": l.get("decided_by", "") or "",
            "Delivery": l.get("delivery_status") or "",
            "Not Delivered Reason": l.get("delivery_reason") or "",
        })
    ldf = pd.DataFrame(line_rows)
    if not show_phone:
        ldf = ldf.drop(columns=["Customer Phone"])
    if match_orders is not None:
        # show the matching orders' lines; if the search is a medicine name, only those medicines
        med_hit = ldf["Item Name"].str.lower().str.contains(search, regex=False)
        ldf = ldf[ldf["Order #"].astype(str).isin(match_orders) & (med_hit if med_hit.any() else True)]
    with st.expander(f"🔍 Item-level detail ({len(ldf)} medicines)", expanded=bool(search)):
        st.dataframe(ldf, hide_index=True, width='stretch')
    st.download_button("⬇️ Download (with Distributor Name filled)", ldf.to_csv(index=False).encode("utf-8"),
                       file_name=f"customer-orders-{'sched' if date_by == 'Scheduled date' else 'imported'}-{day}-{area.replace(' ', '_')}.csv", mime="text/csv",
                       key=f"{kp}_dl")


# ── CUSTOMER DELIVERY STATUS (Call team) ──────────────────────────────────────
NOT_DELIVERED_REASONS = [
    "A) Already purchased from outside",
    "B) Doesn't want an alternative medicine",
    "C) Valid prescription not shared",
    "D) Was only enquiring, doesn't need medicine",
    "E) Wants a freebie to buy",
    "F) Wants more discount",
]
DELIVERY_CHOICES = ["—", "✅ Delivered", "❌ Not Delivered"]

def customer_order_summary(lines):
    """Summary block in the format asked for by Ankit"""
    ls = [l for l in lines if not l.get("removed")]
    orders = {}
    for l in ls:
        orders.setdefault(l.get("order_no"), []).append(l)
    st_ = lambda l: l.get("status", "Pending")
    in_store = [l for l in ls if st_(l) == "In Store"]
    to_arrange = [l for l in ls if st_(l) != "In Store"]
    placed = [l for l in to_arrange if st_(l) in ("Arranged", "Partly Arranged", "Received", "Short")]
    not_placed = [l for l in to_arrange if l not in placed]
    pend_dec = [l for l in not_placed if st_(l) == "Pending"]
    not_avail = [l for l in not_placed if st_(l) == "Not Available"]
    deliv = [l for l in ls if l.get("delivery_status") == "Delivered"]
    notdeliv = [l for l in ls if l.get("delivery_status") == "Not Delivered"]
    ord_deliv = [o for o, x in orders.items() if x and all(l.get("delivery_status") == "Delivered" for l in x)]
    ord_nd = [o for o, x in orders.items() if x and all(l.get("delivery_status") == "Not Delivered" for l in x)]
    ord_part = [o for o, x in orders.items() if any(l.get("delivery_status") == "Delivered" for l in x)
                and any(l.get("delivery_status") != "Delivered" for l in x)]
    ord_wait = [o for o in orders if o not in ord_deliv and o not in ord_nd and o not in ord_part]

    st.markdown(f"#### 📦 Customer orders (arrangement): **{len(orders)} orders · {len(ls)} medicines**")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**💊 Medicines**")
        st.markdown(
            f"- 🏪 Already in store: **{len(in_store)}**\n"
            f"- 📦 To be arranged: **{len(to_arrange)}**\n"
            f"    - ✅ Order placed with distributor: **{len(placed)}**\n"
            f"    - ⏳ Order not placed: **{len(not_placed)}**"
            + (f" (awaiting decision {len(pend_dec)} · not available {len(not_avail)})" if not_placed else ""))
    with c2:
        st.markdown("**🚚 Delivery to customer**")
        md = (f"- ✅ Delivered: **{len(ord_deliv)} orders** · {len(deliv)} medicines\n"
              + (f"- 🟡 Partly delivered: **{len(ord_part)} orders**\n" if ord_part else "")
              + f"- ❌ Not delivered: **{len(ord_nd)} orders** · {len(notdeliv)} medicines\n")
        reasons = {}
        for l in notdeliv:
            reasons[l.get("delivery_reason") or "No reason given"] = reasons.get(l.get("delivery_reason") or "No reason given", 0) + 1
        for r in NOT_DELIVERED_REASONS + [k for k in reasons if k not in NOT_DELIVERED_REASONS]:
            if reasons.get(r):
                md += f"    - {r}: **{reasons[r]}**\n"
        md += f"- 📞 Awaiting call: **{len(ord_wait)} orders**"
        st.markdown(md)

def form_customer_delivery():
    """Call team: after calling the customer, mark each order delivered / not delivered with reason"""
    from datetime import timedelta
    st.subheader("📞 Customer Delivery Status")
    st.caption("Call the customer, then mark the order ✅ Delivered or ❌ Not Delivered with the reason. "
               "Use the table to mark individual medicines if only part of the order was taken.")
    c1, c2 = st.columns(2)
    with c1: area = st.selectbox("Area", ["All Areas"] + load_areas(), key="cd_area")
    with c2: show_done = st.toggle("Show already-marked orders", key="cd_done")
    since = IST.localize(datetime.combine(today_ist() - timedelta(days=7), datetime.min.time())).isoformat()
    try:
        q = supabase.table("customer_order_lines").select("*").eq("removed", False).gte("imported_at", since)
        if area != "All Areas":
            q = q.eq("area", area)
        lines = q.execute().data or []
    except Exception as e:
        st.error(f"Could not load customer orders ({e})")
        return
    if lines and "delivery_status" not in lines[0]:
        st.error("Run delivery_status_setup.sql in Supabase first.")
        return
    orders = {}
    for l in lines:
        orders.setdefault(l.get("order_no"), []).append(l)
    if not show_done:
        orders = {o: x for o, x in orders.items() if any(not l.get("delivery_status") for l in x)}
    if not orders:
        st.success("✅ No orders waiting for a call.")
        return

    def ready(x):
        return all(l.get("status") in ("In Store", "Received", "Not Available", "Short") for l in x)
    olist = sorted(orders.items(), key=lambda kv: (not ready(kv[1]), str(min(l.get("imported_at", "") for l in kv[1]))))
    st.markdown(f"**{len(olist)} orders** · 🟢 ready = all medicines in store / received")

    # quick whole-order action
    labels = {f"{'🟢' if ready(x) else '⏳'} #{o} — {x[0].get('customer_name','')} — {x[0].get('customer_phone','')} — {len(x)} medicine(s)": o
              for o, x in olist}
    pick = st.selectbox("Order", list(labels.keys()), key="cd_pick")
    o = labels[pick]
    x = orders[o]
    ph = "".join(ch for ch in str(x[0].get("customer_phone", "")) if ch.isdigit())
    if ph:
        st.markdown(f"📞 [Call {x[0].get('customer_name','')} ({ph})](tel:{ph})")
    st.dataframe(pd.DataFrame([{"Medicine": l.get("item_name", ""), "Pack": l.get("pack_size", ""),
                                "Qty": _qty_txt(l.get("qty")), "Stock": LINE_ICON.get(l.get("status"), l.get("status")),
                                "Delivery": l.get("delivery_status") or "",
                                "Reason": l.get("delivery_reason") or ""} for l in x]),
                 hide_index=True, width='stretch')
    b1, b2, b3 = st.columns([1, 2, 1])
    with b1:
        if st.button("✅ Whole order delivered", key=f"cd_all_ok_{o}", type="primary", width='stretch'):
            save_delivery([(l["id"], "Delivered", None) for l in x], o)
    with b2:
        reason = st.selectbox("Reason", NOT_DELIVERED_REASONS, key=f"cd_reason_{o}", label_visibility="collapsed")
    with b3:
        if st.button("❌ Whole order not delivered", key=f"cd_all_no_{o}", width='stretch'):
            save_delivery([(l["id"], "Not Delivered", reason) for l in x], o)

    # per-medicine marking (all waiting orders)
    with st.expander("✏️ Mark individual medicines (all waiting orders)"):
        rows = [{"id": l["id"], "Order #": oo, "Customer": l.get("customer_name", ""), "Medicine": l.get("item_name", ""),
                 "Stock": LINE_ICON.get(l.get("status"), l.get("status")),
                 "Delivery": {"Delivered": "✅ Delivered", "Not Delivered": "❌ Not Delivered"}.get(l.get("delivery_status"), "—"),
                 "Reason": l.get("delivery_reason") or ""}
                for oo, xx in olist for l in xx]
        ver = st.session_state.get("cd_ver", 0)
        ed = st.data_editor(pd.DataFrame(rows), key=f"cd_editor_{ver}", hide_index=True, width='stretch',
                            disabled=["Order #", "Customer", "Medicine", "Stock"],
                            column_config={"id": None,
                                           "Delivery": st.column_config.SelectboxColumn("Delivery", options=DELIVERY_CHOICES, required=True),
                                           "Reason": st.column_config.SelectboxColumn("Reason (if not delivered)", options=[""] + NOT_DELIVERED_REASONS)})
        if st.button("💾 Save medicine-wise", key="cd_save_lines", type="primary"):
            old = {r["id"]: (r["Delivery"], r["Reason"]) for r in rows}
            changes, missing = [], 0
            for _, r in ed.iterrows():
                if (r["Delivery"], r["Reason"]) == old.get(r["id"]) or r["Delivery"] == "—":
                    continue
                if r["Delivery"] == "❌ Not Delivered" and not r["Reason"]:
                    missing += 1
                    continue
                changes.append((int(r["id"]), "Delivered" if r["Delivery"].startswith("✅") else "Not Delivered",
                                None if r["Delivery"].startswith("✅") else r["Reason"]))
            if missing:
                st.error(f"{missing} medicine(s) marked Not Delivered without a reason — pick a reason.")
            elif changes:
                st.session_state["cd_ver"] = ver + 1
                save_delivery(changes, "medicine-wise")
            else:
                st.info("Nothing changed.")

def save_delivery(changes, label):
    """changes: [(line_id, 'Delivered'/'Not Delivered', reason)]"""
    now_s = now_iso()
    try:
        for lid, stt, reason in changes:
            supabase.table("customer_order_lines").update({
                "delivery_status": stt, "delivery_reason": reason,
                "delivery_by": st.session_state.name, "delivery_at": now_s}).eq("id", lid).execute()
        ok = sum(1 for c in changes if c[1] == "Delivered")
        log_simple_task("Customer Delivery Update", {"lines": str(len(changes)), "delivered": str(ok),
                                                      "not_delivered": str(len(changes) - ok), "order": str(label)})
        st.rerun()
    except Exception as e:
        st.error(f"Could not save: {e}")

# ── LOAD ALL ROWS (Supabase returns max 1000 per request) ─────────────────────
def fetch_all(table, build=None, page=1000, max_rows=50000):
    """Fetch every matching row in pages. build(query) adds filters."""
    rows, start = [], 0
    while start < max_rows:
        q = supabase.table(table).select("*")
        if build:
            q = build(q)
        data = q.range(start, start + page - 1).execute().data or []
        rows += data
        if len(data) < page:
            break
        start += page
    return rows

# ── BILLS REGISTER ────────────────────────────────────────────────────────────
ISSUE_FIELDS = [("near_expiry", "Near expiry"), ("damaged", "Damaged"), ("contra", "Wrong medicine"),
                ("wrong_batch", "Wrong batch"), ("wrong_discount", "Wrong discount"),
                ("wrong_calculation", "Wrong calc"), ("shortage", "Shortage")]

def _bill_key(d):
    """Match tasks of the same bill: arrangement bills by ARR no, normal bills by bill no + distributor"""
    arr = str((d or {}).get("arrangement_no", "") or "").strip()
    if arr:
        return ("ARR", arr)
    return ("BILL", str((d or {}).get("bill_no", "")).strip().lower(),
            str((d or {}).get("distributor", "")).strip().lower())

def _task_dt(task, field="end_time"):
    """date + time of a task as a datetime (None if unreadable)"""
    try:
        t = parse_task_time(task.get(field) or task.get("time", ""))
        d = datetime.strptime(str(task.get("date", ""))[:10], "%Y-%m-%d")
        return d.replace(hour=t.hour, minute=t.minute, second=t.second) if t else None
    except Exception:
        return None

def build_bill_journeys(reg_from, reg_to, later_to):
    """One record per bill (Register Entry) with every stage: who / start / end / took / waited"""
    regs = fetch_all("daily_tasks", lambda q: q.eq("task_type", "Register Entry").gte("date", reg_from).lte("date", reg_to))
    later = fetch_all("daily_tasks", lambda q: q.in_("task_type", ["Bill Cross Check", "Bill Upload (Software)", "Stock Placement"])
                      .gte("date", reg_from).lte("date", later_to))
    idx = {"Bill Cross Check": {}, "Bill Upload (Software)": {}, "Stock Placement": {}}
    for task in sorted(later, key=lambda x: (str(x.get("date", "")), str(_task_dt(x) or ""))):
        if task.get("status") == "In Progress":
            continue
        idx.setdefault(task.get("task_type"), {}).setdefault(_bill_key(task.get("details")), task)
    out = []
    for r in regs:
        d = r.get("details") or {}
        k = _bill_key(d)
        arrived = _task_dt(r, "time")
        rec = {"reg": r, "d": d, "arrived": arrived, "stages": []}
        prev_end = arrived
        for label, ttype in [("✔️ Cross Check", "Bill Cross Check"), ("📤 Upload", "Bill Upload (Software)"),
                             ("📍 Placement", "Stock Placement")]:
            t = idx[ttype].get(k)
            if not t:
                rec["stages"].append({"label": label, "task": None})
                continue
            s_, e_ = _task_dt(t, "start_time"), _task_dt(t, "end_time")
            if s_ and e_ and e_ < s_:
                e_ = e_ + (datetime(2000, 1, 2) - datetime(2000, 1, 1))
            rec["stages"].append({"label": label, "task": t, "by": t.get("person", ""), "start": s_, "end": e_,
                                  "took": (e_ - s_).total_seconds() if s_ and e_ else None,
                                  "waited": (s_ - prev_end).total_seconds() if s_ and prev_end else None})
            prev_end = e_ or prev_end
        done = [s for s in rec["stages"] if s["task"]]
        rec["next"] = next((s["label"] for s in rec["stages"]
                            if not s["task"] and (PLACEMENT_STEP or s["label"] != "📍 Placement")), None)
        rec["checked"], rec["uploaded"], rec["placed"] = [s.get("end") if s["task"] else None for s in rec["stages"]]
        if not PLACEMENT_STEP and not rec["placed"]:
            rec["placed"] = rec["uploaded"]          # journey ends at bill upload
        out.append(rec)
    return out

def _fmt_when(dt_, ref):
    """'11:45 AM', or '28 Sep 10:05 AM' when it is on a later day than ref"""
    if not dt_:
        return ""
    if ref and dt_.date() != ref.date():
        return dt_.strftime("%d %b %I:%M %p")
    return dt_.strftime("%I:%M %p")

def _mins(secs):
    return fmt_age(int(secs // 60)) if secs is not None and secs >= 0 else ""

def _stage_wait_mins(b, now_n):
    """Minutes the bill has been waiting in its current stage (since the previous step finished)"""
    last = b["arrived"]
    for s in b["stages"]:
        if s["task"] and s.get("end"):
            last = s["end"]
    return int((now_n - last).total_seconds() // 60) if last else 0

def _wait_flag(mins):
    return "🔴" if mins >= 120 else ("🟡" if mins >= 60 else "🟢")

def _issues(task):
    ccd = (task or {}).get("details") or {}
    out = []
    for fld, label in ISSUE_FIELDS:
        n = _to_float(ccd.get(fld), 0)
        if n > 0:
            out.append(f"{label} {int(n)}")
    return ", ".join(out)

PLACEMENT_STEP = False   # stock placement is done in the new billing software, not in this app

def show_live_pending_bills(area="All Areas", title="#### ⏳ Live — bills not yet uploaded"):
    """Bills of the last 7 days that are not placed yet, oldest first, for one area or all"""
    from datetime import timedelta
    now_n = now_ist().replace(tzinfo=None)
    try:
        live = build_bill_journeys((today_ist() - timedelta(days=7)).strftime("%Y-%m-%d"), date_str(), date_str())
    except Exception as e:
        st.error(f"Could not load bills: {e}")
        return

    pend = [b for b in live if b["next"] and (area in ("All Areas", None) or b["d"].get("area", "") == area)]
    st.markdown(title)
    if not pend:
        st.success("✅ No pending bills — everything that arrived is checked and uploaded.")
    else:
        stage_of = {"✔️ Cross Check": "✔️ Waiting Check", "📤 Upload": "📤 Waiting Upload", "📍 Placement": "📍 Waiting Placement"}
        m = st.columns(3)
        with m[0]: st.metric("✔️ Waiting Check", sum(1 for b in pend if b["next"] == "✔️ Cross Check"))
        with m[1]: st.metric("📤 Waiting Upload", sum(1 for b in pend if b["next"] == "📤 Upload"))
        with m[2]: st.metric("📅 From previous days", sum(1 for b in pend if b["arrived"] and b["arrived"].date() < now_n.date()))
        lrows = []
        for b in sorted(pend, key=lambda x: x["arrived"] or now_n):
            age = int((now_n - b["arrived"]).total_seconds() // 60) if b["arrived"] else 0
            flag = "🔴" if age >= 360 or (b["arrived"] and b["arrived"].date() < now_n.date()) else ("🟡" if age >= 120 else "🟢")
            sw = _stage_wait_mins(b, now_n)
            lrows.append({"⏰": flag, "Arrived": _fmt_when(b["arrived"], now_n), "Since arrival": fmt_age(age),
                          "Stage": f"{_wait_flag(sw)} {stage_of.get(b['next'], b['next'])} — {fmt_age(sw)}",
                          "Area": b["d"].get("area", ""),
                          "Distributor": b["d"].get("distributor", ""), "Bill No": b["d"].get("bill_no", ""),
                          "Items": int(_to_float(b["d"].get("no_items"), 0)),
                          "Type": (b["d"].get("order_type") or "Normal Order") + (f" · {b['d'].get('arrangement_no')}" if b["d"].get("arrangement_no") else ""),
                          "Entered By": b["reg"].get("person", "")})
        st.caption("⏰ since arrival: 🟢 under 2h · 🟡 2–6h · 🔴 over 6h or arrived on an earlier day  |  "
                   "Stage time: how long it has waited for this step — 🟢 under 1h · 🟡 1–2h · 🔴 over 2h")
        st.dataframe(pd.DataFrame(lrows), hide_index=True, width='stretch')


def show_bills_register(kp="bills", default_area=None):
    from datetime import timedelta
    st.subheader("🧾 Bills Register")
    now_n = now_ist().replace(tzinfo=None)

    areas_all = ["All Areas"] + load_areas()
    area = st.selectbox("Area", areas_all, key=f"{kp}_area",
                        index=areas_all.index(default_area) if default_area in areas_all else 0)
    show_live_pending_bills(area)

    st.divider()
    # ── HISTORY: bills that arrived in a date range ──
    st.markdown("#### 📜 Bills by arrival date")
    c1, c2, c4, c5 = st.columns(4)
    with c1: d_from = st.date_input("From", value=today_ist(), key=f"{kp}_from")
    with c2: d_to   = st.date_input("To", value=today_ist(), key=f"{kp}_to")
    with c4: otype  = st.selectbox("Type", ["All", "Normal Order", "Arrangement"], key=f"{kp}_type")
    with c5: dist   = st.selectbox("Distributor", ["All"] + DISTRIBUTORS, key=f"{kp}_dist")
    if d_to < d_from:
        st.error("'To' date is before 'From' date")
        return
    f, t = d_from.strftime("%Y-%m-%d"), d_to.strftime("%Y-%m-%d")
    try:
        bills = build_bill_journeys(f, t, (d_to + timedelta(days=7)).strftime("%Y-%m-%d"))
    except Exception as e:
        st.error(f"Could not load bills: {e}")
        return
    sel = []
    for b in bills:
        d = b["d"]
        typ = d.get("order_type", "") or "Normal Order"
        if (area != "All Areas" and d.get("area", "") != area) or (otype != "All" and typ != otype) \
                or (dist != "All" and d.get("distributor", "") != dist):
            continue
        sel.append(b)
    if not sel:
        st.info("No bills entered for this period / filter.")
        return

    rows = []
    for b in sorted(sel, key=lambda x: x["arrived"] or now_n, reverse=True):
        d, a = b["d"], b["arrived"]
        cc, up, pl = b["stages"]
        if not b["next"]:
            status = "✅ Placed" if PLACEMENT_STEP else "✅ Done"
        else:
            sw = _stage_wait_mins(b, now_n)
            status = f"{_wait_flag(sw)} " + {"✔️ Cross Check": "Waiting Check", "📤 Upload": "Waiting Upload",
                                              "📍 Placement": "Waiting Placement"}[b["next"]] + f" — {fmt_age(sw)}"
        typ = "Arrangement" if (d.get("order_type") == "Arrangement" or d.get("arrangement_no")) else "Normal"
        row = {"Arrival Date": a.strftime("%d %b") if a else b["reg"].get("date", ""),
               "Arrival Time": a.strftime("%I:%M %p") if a else "",
               "Bill No": d.get("bill_no", ""), "No of SKU": int(_to_float(d.get("no_items"), 0)),
               "Bill Type": typ, "Distributor": d.get("distributor", ""), "Area": d.get("area", ""),
               "Cross Check Time": _fmt_when(cc.get("end"), a) if cc["task"] else "",
               "Checked By": cc.get("by", "") if cc["task"] else "",
               "Upload Time": _fmt_when(up.get("end"), a) if up["task"] else "",
               "Uploaded By": up.get("by", "") if up["task"] else "",
               "Placement Time": _fmt_when(pl.get("end"), a) if pl["task"] else "",
               "Placed By": pl.get("by", "") if pl["task"] else "",
               "Current Status": status,
               "Total Time Taken": (_mins((b["placed"] - a).total_seconds()) if b["placed"] and a
                                    else (f"⏳ {fmt_age(int((now_n - a).total_seconds() // 60))} (running)" if a else "")),
               "Amount ₹": _to_float(d.get("bill_amount"), 0), "ARR No": d.get("arrangement_no", "") or "",
               "Entered By": b["reg"].get("person", "")}
        for s, short in [(cc, "Check"), (up, "Upload"), (pl, "Place")]:
            row[f"{short} By"] = s.get("by", "") if s["task"] else ""
            row[f"{short} Start"] = _fmt_when(s.get("start"), a) if s["task"] else ""
            row[f"{short} End"] = _fmt_when(s.get("end"), a) if s["task"] else ""
            row[f"{short} Took"] = _mins(s.get("took")) if s["task"] else ""
            row[f"Wait → {short}"] = _mins(s.get("waited")) if s["task"] else ""
        row["Arrival → Upload"] = _mins((b["uploaded"] - a).total_seconds()) if b["uploaded"] and a else ""
        row["Arrival → Placed"] = _mins((b["placed"] - a).total_seconds()) if b["placed"] and a else ""
        row["Issues"] = _issues(cc["task"])
        row["_up_m"] = (b["uploaded"] - a).total_seconds() / 60 if b["uploaded"] and a else None
        row["_pl_m"] = (b["placed"] - a).total_seconds() / 60 if b["placed"] and a else None
        row["_nextday"] = bool(b["uploaded"] and a and b["uploaded"].date() > a.date())
        rows.append(row)
    df = pd.DataFrame(rows)

    up_m, pl_m = df["_up_m"].dropna(), df["_pl_m"].dropna()
    m = st.columns(4)
    with m[0]: st.metric("🧾 Bills Arrived", len(df))
    with m[1]: st.metric("💰 Total Amount", f"₹{df['Amount ₹'].sum():,.0f}")
    with m[2]: st.metric("⏱️ Avg Arrival → Upload", fmt_age(up_m.mean()) if not up_m.empty else "—")
    with m[3]: st.metric("⏱️ Avg Arrival → Placed" if PLACEMENT_STEP else "📅 Pending now",
                         fmt_age(pl_m.mean()) if PLACEMENT_STEP and not pl_m.empty
                         else (int(df["Current Status"].str.contains("Waiting").sum()) if not PLACEMENT_STEP else "—"))
    m = st.columns(4)
    with m[0]: st.metric("📦 Total SKUs", int(df["No of SKU"].sum()))
    with m[1]: st.metric("📅 Uploaded next day or later", int(df["_nextday"].sum()))
    with m[2]: st.metric("✅ Fully placed" if PLACEMENT_STEP else "✅ Done (uploaded)",
                         int(df["Current Status"].isin(["✅ Placed", "✅ Done"]).sum()))
    with m[3]: st.metric("⚠️ Bills with issues", int((df["Issues"] != "").sum()))

    show_all = st.toggle("Show extra columns (amount, entered by, start / took / wait of every stage, issues)", key=f"{kp}_all")
    base_cols = ["Arrival Date", "Arrival Time", "Bill No", "No of SKU", "Bill Type", "Distributor", "Area",
                 "Cross Check Time", "Checked By", "Upload Time", "Uploaded By"]
    base_cols += (["Placement Time", "Placed By"] if PLACEMENT_STEP else []) + ["Current Status", "Total Time Taken"]
    full = df.drop(columns=["_up_m", "_pl_m", "_nextday"])
    st.dataframe(full if show_all else full[base_cols], hide_index=True, width='stretch')
    st.caption("Times on a later day than arrival show the date, e.g. '28 Sep 10:05 AM'. "
               "Waiting time in Current Status: 🟢 under 1h · 🟡 1–2h · 🔴 over 2h.")

    # ── ONE BILL'S JOURNEY ──
    with st.expander("🔍 Journey of one bill"):
        labels = {f"{r['Bill No'] or '(no bill no)'} — {r['Distributor']} — {r['Arrival Date']} {r['Arrival Time']}": i
                  for i, r in enumerate(rows)}
        pick = st.selectbox("Bill", list(labels.keys()), key=f"{kp}_pick")
        b = sorted(sel, key=lambda x: x["arrived"] or now_n, reverse=True)[labels[pick]]
        a = b["arrived"]
        jr = [{"Stage": "📒 Arrived (Register Entry)", "By": b["reg"].get("person", ""), "Start": _fmt_when(a, a),
               "End": _fmt_when(a, a), "Took": "", "Waited before": "",
               "Details": f"{b['d'].get('distributor','')} · Bill {b['d'].get('bill_no','')} · {int(_to_float(b['d'].get('no_items'),0))} items · ₹{_to_float(b['d'].get('bill_amount'),0):,.0f}"}]
        for s in b["stages"]:
            if s["task"]:
                jr.append({"Stage": s["label"], "By": s["by"], "Start": _fmt_when(s["start"], a), "End": _fmt_when(s["end"], a),
                           "Took": _mins(s["took"]), "Waited before": _mins(s["waited"]),
                           "Details": _issues(s["task"]) if s["label"].startswith("✔️") else ""})
            else:
                jr.append({"Stage": s["label"], "By": "", "Start": "", "End": "", "Took": "",
                           "Waited before": "", "Details": "⏳ not done yet"})
        st.dataframe(pd.DataFrame(jr), hide_index=True, width='stretch')
        if b["placed"] and a:
            st.markdown(f"**Total: arrival → placed {_mins((b['placed'] - a).total_seconds())}**")
        elif a:
            st.markdown(f"**⏳ Open for {fmt_age(int((now_n - a).total_seconds() // 60))} — next step: {b['next']}**")

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        full.to_excel(w, index=False, sheet_name="Bills")
    st.download_button("⬇️ Download Excel (all stage columns)", buf.getvalue(), f"bills-register-{f}-to-{t}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"{kp}_dl")

# ── SHIFT PLANNER ─────────────────────────────────────────────────────────────
SHIFT_TIMES = [""] + [datetime(2000, 1, 1, h, m).strftime("%I:%M %p") for h in range(6, 24) for m in (0, 30)]
SHIFT_STATUS = ["Working", "Off", "Leave"]
SHIFT_ICON = {"Off": "🏖️ Off", "Leave": "🤒 Leave"}

def load_roster(date_s, person=None):
    try:
        q = supabase.table("shift_roster").select("*").eq("date", date_s)
        if person:
            q = q.eq("person", person)
        return {r["person"]: r for r in (q.execute().data or [])}
    except Exception:
        return {}

def shift_text(r):
    if not r:
        return ""
    if r.get("status") in SHIFT_ICON:
        return SHIFT_ICON[r["status"]] + (f" ({r['note']})" if r.get("note") else "")
    t = f"{r.get('start_time') or '?'} – {r.get('end_time') or '?'}"
    return t + (f" · {r['area']}" if r.get("area") else "")

def show_my_shift():
    """Staff: today's and tomorrow's planned shift, one line"""
    from datetime import timedelta
    t, tm = date_str(), (today_ist() + timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        rows = supabase.table("shift_roster").select("*").eq("person", st.session_state.name)\
            .in_("date", [t, tm]).execute().data or []
    except Exception:
        return
    by = {r["date"]: r for r in rows}
    parts = []
    if t in by:
        parts.append(f"📅 **Today:** {shift_text(by[t])}")
    if tm in by:
        parts.append(f"📅 **Tomorrow:** {shift_text(by[tm])}")
    if parts:
        st.markdown("  ·  ".join(parts))

def show_shift_planner(kp="shift"):
    from datetime import timedelta
    st.subheader("📅 Shift Planner")
    users = [u for u in (load_users() or {}).values() if u.get("role") != "admin"]
    team_of = {u["name"]: u.get("team", "") for u in users}
    phones = {u["name"]: u.get("phone", "") for u in users}
    c1, c2 = st.columns(2)
    with c1: day = st.date_input("Shift date", value=today_ist() + timedelta(days=1), key=f"{kp}_day")
    with c2: team_f = st.selectbox("Team", ["All"] + sorted(set(team_of.values()) - {""}), key=f"{kp}_team")
    d = day.strftime("%Y-%m-%d")
    prev = (day - timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        supabase.table("shift_roster").select("id").limit(1).execute()
    except Exception as e:
        st.error(f"Run shift_setup.sql in Supabase first ({e})")
        return
    current = load_roster(d)
    src_key = f"{kp}_src_{d}"
    if st.button(f"📋 Copy from {(day - timedelta(days=1)).strftime('%d %b')}", key=f"{kp}_copy"):
        st.session_state[src_key] = "prev"
        st.session_state[f"{kp}_ver"] = st.session_state.get(f"{kp}_ver", 0) + 1
    base = load_roster(prev) if st.session_state.get(src_key) == "prev" else current
    people = sorted([p for p in team_of if team_f == "All" or team_of[p] == team_f],
                    key=lambda p: (team_of[p], p))
    areas = [""] + load_areas()
    rows = []
    for p in people:
        r = base.get(p, {})
        rows.append({"Person": p, "Team": team_of.get(p, ""),
                     "Status": r.get("status") or "Working",
                     "Start": r.get("start_time") or "", "End": r.get("end_time") or "",
                     "Area": r.get("area") or "", "Note": r.get("note") or ""})
    if not rows:
        st.info("No team members.")
        return
    if st.session_state.get(src_key) == "prev":
        st.info(f"Filled from {prev} — change what's different, then Save.")
    elif not current:
        st.caption("Nothing saved for this date yet.")
    ed = st.data_editor(pd.DataFrame(rows), key=f"{kp}_ed_{d}_{st.session_state.get(f'{kp}_ver', 0)}",
                        hide_index=True, width='stretch', disabled=["Person", "Team"],
                        column_config={
                            "Status": st.column_config.SelectboxColumn("Status", options=SHIFT_STATUS, required=True),
                            "Start": st.column_config.SelectboxColumn("Start", options=SHIFT_TIMES),
                            "End": st.column_config.SelectboxColumn("End", options=SHIFT_TIMES),
                            "Area": st.column_config.SelectboxColumn("Area", options=areas),
                        })
    if st.button("💾 Save shifts", type="primary", key=f"{kp}_save", width='stretch'):
        payload = [{"date": d, "person": r["Person"], "team": r["Team"], "status": r["Status"] or "Working",
                    "start_time": (r["Start"] or None) if r["Status"] == "Working" else None,
                    "end_time": (r["End"] or None) if r["Status"] == "Working" else None,
                    "area": (r["Area"] or None) if r["Status"] == "Working" else None,
                    "note": str(r["Note"] or "").strip() or None,
                    "set_by": st.session_state.name, "updated_at": now_iso()} for _, r in ed.iterrows()]
        try:
            supabase.table("shift_roster").upsert(payload, on_conflict="date,person").execute()
            st.session_state.pop(src_key, None)
            st.success(f"✅ Shifts saved for {day.strftime('%d %b')} ({len(payload)} people)")
            current = load_roster(d)
        except Exception as e:
            st.error(f"Could not save: {e}")

    if current:
        lines = [f"{p}: {shift_text(current[p])}" for p in people if p in current]
        with st.expander("📋 WhatsApp message for team group"):
            st.code(f"Shifts for {day.strftime('%a %d %b')}:\n" + "\n".join(lines), language=None)
        with st.expander("📲 Send to one person"):
            for p in [p for p in people if p in current]:
                c1, c2 = st.columns([3, 2])
                with c1: st.markdown(f"**{p}** — {shift_text(current[p])}")
                with c2:
                    msg = f"Hi {p}, your shift on {day.strftime('%a %d %b')}: {shift_text(current[p])}. Thank you."
                    if not wa_buttons(phones.get(p), msg, f"{kp}_wa_{p}"):
                        st.caption("No mobile saved")

# ── ATTENDANCE (clock in / breaks / clock out) ────────────────────────────────
BREAK_TYPES = [("🍱 Lunch", "Lunch"), ("☕ Tea", "Tea"), ("🚶 Personal", "Personal")]

def att_log(event, break_type=None):
    supabase.table("attendance_log").insert({
        "person": st.session_state.name, "team": st.session_state.team,
        "area": st.session_state.get("work_area", "") or "",
        "date": date_str(), "event": event, "break_type": break_type, "at": now_iso()
    }).execute()

def att_state(events):
    """From a person's events of one day (sorted): current state + totals"""
    st_ = {"login": None, "clock_in": None, "clock_out": None, "on_break": None,
           "break_secs": 0, "breaks": 0, "working": False}
    brk_start = None
    for e in events:
        t = to_ist(e.get("at"))
        ev = e.get("event")
        if ev == "login" and not st_["login"]:
            st_["login"] = t
        elif ev == "clock_in":
            if not st_["clock_in"]:
                st_["clock_in"] = t
            st_["clock_out"] = None
            st_["working"] = True
        elif ev == "break_start":
            brk_start = (t, e.get("break_type") or "Break")
            st_["breaks"] += 1
        elif ev == "break_end" and brk_start:
            st_["break_secs"] += max(0, (t - brk_start[0]).total_seconds())
            brk_start = None
        elif ev == "clock_out":
            if brk_start:                       # clocked out during a break -> close it
                st_["break_secs"] += max(0, (t - brk_start[0]).total_seconds())
                brk_start = None
            st_["clock_out"] = t
            st_["working"] = False
    st_["on_break"] = brk_start
    return st_

def attendance_gate():
    """Top-of-page attendance bar. Returns True when the person may work on tasks."""
    try:
        events = supabase.table("attendance_log").select("*")\
            .eq("person", st.session_state.name).eq("date", date_str()).order("at").execute().data or []
    except Exception:
        return True          # table not created yet -> never block work
    if not any(e.get("event") == "login" for e in events):
        try:
            att_log("login")
        except Exception:
            pass
    s = att_state(events)
    now = now_ist()

    if not s["clock_in"] or (s["clock_out"] and not s["working"]):
        if s["clock_out"]:
            st.info(f"🔴 You clocked out at **{s['clock_out'].strftime('%I:%M %p')}**. Came back? Clock in again to continue.")
        else:
            st.markdown(f"### 🪖 Report for duty, {st.session_state.name}!")
            st.caption("Clock in to start today's mission.")
        if st.button("🟢 Clock In — Report for Duty", type="primary", width='stretch', key="att_in"):
            att_log("clock_in")
            st.rerun()
        return False

    if s["on_break"]:
        b_start, b_type = s["on_break"]
        mins = int((now - b_start).total_seconds() // 60)
        st.warning(f"☕ On **{b_type}** break since {b_start.strftime('%I:%M %p')} — {fmt_age(mins)}")
        if st.button("▶️ End Break — back to work", type="primary", width='stretch', key="att_break_end"):
            att_log("break_end", b_type)
            st.rerun()
        return False

    # Working: compact bar
    worked = int((now - s["clock_in"]).total_seconds() // 60)
    c0, c1, c2, c3, c4 = st.columns([3, 1, 1, 1, 1])
    with c0:
        st.caption(f"🟢 In since **{s['clock_in'].strftime('%I:%M %p')}** · {fmt_age(worked)} · "
                   f"Breaks: {s['breaks']} ({fmt_age(int(s['break_secs'] // 60))})")
    active_key, _ = get_active_timer()
    for col, (label, btype) in zip([c1, c2, c3], BREAK_TYPES):
        with col:
            if st.button(label, key=f"att_brk_{btype}", width='stretch'):
                if active_key:
                    st.error("Finish or cancel your running task first.")
                else:
                    att_log("break_start", btype)
                    st.rerun()
    with c4:
        if st.session_state.get("att_confirm_out"):
            if st.button("✅ Confirm Out", key="att_out_yes", type="primary", width='stretch'):
                if active_key:
                    st.error("Finish or cancel your running task first.")
                else:
                    att_log("clock_out")
                    st.session_state["att_confirm_out"] = False
                    st.rerun()
        elif st.button("🔴 Clock Out", key="att_out", width='stretch'):
            st.session_state["att_confirm_out"] = True
            st.rerun()
    return True

def _merged_secs(periods):
    """Total seconds covered by (start, end) periods, overlaps counted once"""
    periods = sorted(p for p in periods if p[0] and p[1] and p[1] > p[0])
    total, cur_s, cur_e = 0, None, None
    for s, e in periods:
        if cur_e is None or s > cur_e:
            if cur_e is not None:
                total += (cur_e - cur_s).total_seconds()
            cur_s, cur_e = s, e
        else:
            cur_e = max(cur_e, e)
    if cur_e is not None:
        total += (cur_e - cur_s).total_seconds()
    return total

def _vs_plan(cin, rr, day_dt):
    """' (+20m)' / ' (-10m)' / ' (on time)' vs planned start; '' if no plan"""
    try:
        tt = datetime.strptime((rr or {}).get("start_time") or "", "%I:%M %p")
    except Exception:
        return ""
    diff = int((cin - day_dt.replace(hour=tt.hour, minute=tt.minute)).total_seconds() // 60)
    if abs(diff) <= 5:
        return " (on time)"
    return f" ({'+' if diff > 0 else '-'}{fmt_age(abs(diff))})"

def show_attendance_admin(kp="att"):
    st.subheader("🕐 Attendance & Active Time")
    show_staff_areas(kp + "_areas")
    st.caption("For efficiency only (not salary). Active % = task time ÷ (time present − breaks). "
               "Task time only counts work done with task timers, so 70–80% is a good score.")
    c1, c2 = st.columns(2)
    with c1: day = st.date_input("Date", value=today_ist(), key=f"{kp}_day")
    with c2: team_f = st.selectbox("Team", ["All", "Purchase", "Stock", "Call", "Delivery"], key=f"{kp}_team")
    d = day.strftime("%Y-%m-%d")
    is_today = d == date_str()
    try:
        events = fetch_all("attendance_log", lambda q: q.eq("date", d).order("at"))
        tasks  = fetch_all("daily_tasks", lambda q: q.eq("date", d))
    except Exception as e:
        st.error(f"Could not load — has the attendance SQL been run in Supabase? ({e})")
        return
    running = set(t.get("person") for t in tasks if t.get("status") == "In Progress")
    tasks = [t for t in tasks if t.get("status") != "In Progress"]
    phones = {u.get("name"): u.get("phone", "") for u in (load_users() or {}).values()}
    reminders = []
    roster = load_roster(d)

    # everyone (non-admin) + anyone with activity that day
    people = {}
    for u in (load_users() or {}).values():
        if u.get("role") != "admin":
            people[u["name"]] = u.get("team", "")
    for e in events:
        people.setdefault(e.get("person"), e.get("team", ""))
    for t in tasks:
        people.setdefault(t.get("person"), t.get("team", ""))

    day_dt = datetime.strptime(d, "%Y-%m-%d")
    def on_day(tstr):
        tt = parse_task_time(tstr)
        return day_dt.replace(hour=tt.hour, minute=tt.minute, second=tt.second) if tt else None

    rows = []
    now_naive = now_ist().replace(tzinfo=None)
    for person, team in sorted(people.items(), key=lambda x: (str(x[1]), str(x[0]))):
        if not person or (team_f != "All" and team != team_f):
            continue
        evs = [e for e in events if e.get("person") == person]
        tks = [t for t in tasks if t.get("person") == person]
        s = att_state(evs)
        periods = [(on_day(t.get("start_time")), on_day(t.get("end_time"))) for t in tks]
        periods = [p for p in periods if p[0] and p[1]]
        task_secs_total = _merged_secs(periods)
        first_task = min([p[0] for p in periods]) if periods else None
        last_task  = max([p[1] for p in periods]) if periods else None
        cin = s["clock_in"].replace(tzinfo=None) if s["clock_in"] else None
        cout = s["clock_out"].replace(tzinfo=None) if s["clock_out"] else None
        auto_out = False
        if cin and not cout:
            if is_today:
                cout_calc = now_naive          # still in
            else:
                last_ev = max([to_ist(e.get("at")).replace(tzinfo=None) for e in evs if to_ist(e.get("at"))] + ([last_task] if last_task else []))
                cout_calc, auto_out = last_ev, True
        else:
            cout_calc = cout
        present = (cout_calc - cin).total_seconds() if cin and cout_calc and cout_calc > cin else 0
        work_base = max(0, present - s["break_secs"])
        active = round(task_secs_total / work_base * 100) if work_base > 0 else None
        gap = int((first_task - cin).total_seconds() // 60) if cin and first_task and first_task > cin else None
        login = s["login"].replace(tzinfo=None) if s["login"] else None
        rr = roster.get(person) or {}
        off_today = rr.get("status") in ("Off", "Leave")
        if not evs and not tks:
            status = SHIFT_ICON[rr["status"]] if off_today else "⚪ Not seen"
        elif not cin:
            status = "⚠️ No clock-in"
        elif s["on_break"]:
            status = "☕ On break"
        elif cout:
            status = "🔴 Out"
        elif is_today:
            status = "🟢 Working"
        else:
            status = "🔴 Out (auto)"
        # reminder candidates (today only, friendly wording)
        if is_today:
            now_ist_naive = now_naive
            plan_start = None
            if rr.get("start_time"):
                try:
                    tt = datetime.strptime(rr["start_time"], "%I:%M %p")
                    plan_start = day_dt.replace(hour=tt.hour, minute=tt.minute)
                except Exception:
                    plan_start = None
            not_due_yet = plan_start is not None and now_ist_naive < plan_start
            if status in ("⚪ Not seen", "⚠️ No clock-in") and not off_today and not not_due_yet:
                reminders.append((person, "Not clocked in" + (f" (shift {rr['start_time']})" if rr.get("start_time") else ""),
                    f"Hi {person}, you haven't clocked in on the RapidSurge app today. Please tap Clock In and log your tasks. Thank you."))
            elif status == "☕ On break":
                b_mins = int((now_ist_naive - s["on_break"][0].replace(tzinfo=None)).total_seconds() // 60)
                if b_mins >= 45:
                    reminders.append((person, f"{s['on_break'][1]} break {fmt_age(b_mins)}",
                        f"Hi {person}, your {s['on_break'][1].lower()} break has been running for {fmt_age(b_mins)} on the RapidSurge app. If you're back, please tap End Break. Thank you."))
            elif status == "🟢 Working" and person not in running:
                acts = [cin] + ([last_task] if last_task else [])
                acts += [to_ist(e.get("at")).replace(tzinfo=None) for e in evs
                         if e.get("event") == "break_end" and to_ist(e.get("at"))]
                idle = int((now_ist_naive - max(acts)).total_seconds() // 60)
                if idle >= 60:
                    reminders.append((person, f"No task for {fmt_age(idle)}",
                        f"Hi {person}, no task has been logged on the RapidSurge app for the last {fmt_age(idle)}. If you're working on something, please start its task timer. Thank you."))
        rows.append({
            "Person": person, "Team": team, "Status": status,
            "App Opened": login.strftime("%I:%M %p") if login else "",
            "Planned": shift_text(rr),
            "Clock In": (cin.strftime("%I:%M %p") + _vs_plan(cin, rr, day_dt)) if cin else "",
            "First Task": first_task.strftime("%I:%M %p") if first_task else "",
            "Gap to 1st Task": fmt_age(gap) if gap is not None else "",
            "Breaks": f"{s['breaks']} · {fmt_age(int(s['break_secs'] // 60))}" if s["breaks"] else "",
            "Task Time": fmt_secs(task_secs_total) if task_secs_total else "",
            "Tasks": len(tks),
            "Last Task": last_task.strftime("%I:%M %p") if last_task else "",
            "Clock Out": (cout_calc.strftime("%I:%M %p") + (" (auto)" if auto_out else "")) if cin and cout_calc and not (is_today and not cout) else "",
            "Present": fmt_age(int(present // 60)) if present else "",
            "Active %": f"{active}%" if active is not None else "",
        })
    if not rows:
        st.info("No team members found.")
        return
    df = pd.DataFrame(rows)
    m = st.columns(4)
    with m[0]: st.metric("🟢 Clocked in", int(df["Clock In"].ne("").sum()))
    with m[1]: st.metric("⚪ Not seen", int((df["Status"] == "⚪ Not seen").sum()),
                         help="Off / on leave (from Shift Planner) are not counted here")
    with m[2]: st.metric("⚠️ Worked without clock-in", int((df["Status"] == "⚠️ No clock-in").sum()))
    act = [int(x[:-1]) for x in df["Active %"] if x]
    with m[3]: st.metric("📊 Avg Active %", f"{round(sum(act)/len(act))}%" if act else "—")
    st.dataframe(df, hide_index=True, width='stretch')

    # ── WhatsApp reminders (opens WhatsApp with the message typed; you press Send) ──
    if is_today:
        st.markdown("#### 📲 Reminders")
        if not reminders:
            st.success("✅ Everyone is clocked in and active — no reminders needed.")
        else:
            st.caption("📱 App = WhatsApp app (phone) · 💻 Web = WhatsApp Web (computer). The message opens ready — you press Send.")
            for person, reason, msg in reminders:
                c1, c2, c3 = st.columns([2, 2, 2])
                with c1: st.markdown(f"**{person}**")
                with c2: st.markdown(reason)
                with c3:
                    if not wa_buttons(phones.get(person, ""), msg, f"rem_{person}"):
                        st.caption("Add mobile in Settings → Manage Users")
            not_in = [p for p, r, _ in reminders if r == "Not clocked in"]
            if not_in:
                with st.expander("📋 Message for team group"):
                    st.code("Good morning team. Please clock in on the RapidSurge app: " + ", ".join(not_in), language=None)

    with st.expander("🔍 Timeline of one person"):
        who = st.selectbox("Person", [r["Person"] for r in rows], key=f"{kp}_who")
        tl = []
        for e in [e for e in events if e.get("person") == who]:
            t = to_ist(e.get("at"))
            label = {"login": "📱 Opened app", "clock_in": "🟢 Clock In", "clock_out": "🔴 Clock Out",
                     "break_start": f"☕ {e.get('break_type','')} break start", "break_end": "▶️ Break end"}.get(e.get("event"), e.get("event"))
            tl.append({"Time": t.strftime("%I:%M:%S %p") if t else "", "What": label, "_t": t.replace(tzinfo=None) if t else None})
        for t in [t for t in tasks if t.get("person") == who]:
            s_ = on_day(t.get("start_time"))
            tl.append({"Time": s_.strftime("%I:%M:%S %p") if s_ else t.get("time", ""),
                       "What": f"🧾 {t.get('task_type','')} ({fmt_secs(task_secs(t))})", "_t": s_})
        tl = sorted(tl, key=lambda x: x["_t"] or datetime.min)
        if tl:
            st.dataframe(pd.DataFrame(tl).drop(columns=["_t"]), hide_index=True, width='stretch')
        else:
            st.caption("No activity.")

# ── TASKS ASSIGNED BY ADMIN ───────────────────────────────────────────────────
PRIORITY_ICON = {"Urgent": "🔴", "High": "🟡", "Normal": "🟢"}

def wa_buttons(phone, msg, key):
    """Two WhatsApp buttons: phone app / WhatsApp Web. Returns False if no valid number."""
    from urllib.parse import quote
    digits = "".join(ch for ch in str(phone or "") if ch.isdigit())
    if len(digits) == 10:
        digits = "91" + digits
    if len(digits) < 11:
        return False
    b1, b2 = st.columns(2)
    with b1: st.link_button("📱 App", f"https://api.whatsapp.com/send?phone={digits}&text={quote(msg)}", width='stretch')
    with b2: st.link_button("💻 Web", f"https://web.whatsapp.com/send?phone={digits}&text={quote(msg)}", width='stretch')
    return True

def ensure_daily_copies(person=None):
    """Create today's copy of every 'repeat daily' task (once per person per day)"""
    try:
        q = supabase.table("assigned_tasks").select("*").eq("is_template", True).eq("active", True)
        if person:
            q = q.eq("assigned_to", person)
        temps = q.execute().data or []
        if not temps:
            return
        have = supabase.table("assigned_tasks").select("template_id")\
            .eq("due_date", date_str()).in_("template_id", [t["id"] for t in temps]).execute().data or []
        have_ids = set(h.get("template_id") for h in have)
        new = [{"title": t["title"], "details": t.get("details"), "assigned_to": t["assigned_to"], "team": t.get("team"),
                "due_date": date_str(), "priority": t.get("priority", "Normal"), "status": "Pending",
                "is_template": False, "template_id": t["id"], "active": True,
                "assigned_by": t.get("assigned_by"), "assigned_at": now_iso()}
               for t in temps if t["id"] not in have_ids and str(t.get("due_date", "")) <= date_str()]
        if new:
            supabase.table("assigned_tasks").insert(new).execute()
    except Exception:
        pass

def show_my_assigned_tasks():
    """Staff: tasks from admin, shown at the top of their page"""
    try:
        ensure_daily_copies(st.session_state.name)
        rows = supabase.table("assigned_tasks").select("*")\
            .eq("assigned_to", st.session_state.name).eq("is_template", False).eq("active", True)\
            .lte("due_date", date_str()).in_("status", ["Pending", "In Progress"]).execute().data or []
    except Exception:
        return          # table not created yet
    if not rows:
        return
    order = {"Urgent": 0, "High": 1, "Normal": 2}
    rows.sort(key=lambda r: (order.get(r.get("priority"), 3), str(r.get("due_date")), r["id"]))
    overdue = sum(1 for r in rows if str(r.get("due_date")) < date_str())
    title = f"📌 Tasks from Admin ({len(rows)})" + (f" · ⚠️ {overdue} overdue" if overdue else "")
    with st.expander(title, expanded=True):
        for r in rows:
            icon = PRIORITY_ICON.get(r.get("priority"), "🟢")
            due = "Today" if r.get("due_date") == date_str() else f"⚠️ Due {r.get('due_date')}"
            c1, c2 = st.columns([3, 2])
            with c1:
                st.markdown(f"{icon} **{r.get('title','')}**  \n<small>{due} · from {r.get('assigned_by','')}</small>", unsafe_allow_html=True)
                if r.get("details"):
                    st.caption(r["details"])
            with c2:
                if r.get("status") == "Pending":
                    if st.button("▶️ Start", key=f"at_start_{r['id']}", width='stretch'):
                        supabase.table("assigned_tasks").update({"status": "In Progress", "started_at": now_iso()}).eq("id", r["id"]).execute()
                        st.rerun()
                else:
                    t0 = to_ist(r.get("started_at"))
                    if t0:
                        st.caption(f"🔄 Started {t0.strftime('%I:%M %p')}")
                note = st.text_input("Note (optional)", key=f"at_note_{r['id']}", label_visibility="collapsed",
                                     placeholder="Note / reason (optional)")
                d1, d2 = st.columns(2)
                with d1:
                    if st.button("✅ Done", key=f"at_done_{r['id']}", type="primary", width='stretch'):
                        finish_assigned_task(r, "Done", note)
                with d2:
                    if st.button("❌ Can't", key=f"at_cant_{r['id']}", width='stretch'):
                        if not note.strip():
                            st.error("Write the reason in the note box")
                        else:
                            finish_assigned_task(r, "Cannot Do", note)
            st.divider()

def finish_assigned_task(r, status, note):
    now = now_ist()
    supabase.table("assigned_tasks").update({"status": status, "done_at": now.isoformat(),
                                             "note": note.strip() or None}).eq("id", r["id"]).execute()
    if status == "Done":
        st.session_state["mission_done"] = int((now - (to_ist(r.get("started_at")) or now)).total_seconds())
        # count the work in My Tasks / Active % (from Start, if started today)
        t0 = to_ist(r.get("started_at"))
        start = t0 if t0 and t0.date() == now.date() else now
        try:
            supabase.table("daily_tasks").insert({
                "date": date_str(), "time": time_str(),
                "person": st.session_state.name, "team": st.session_state.team,
                "task_type": "Assigned Task",
                "details": {"task_name": r.get("title", ""), "assigned_by": r.get("assigned_by", ""),
                            "note": note.strip()},
                "start_time": start.strftime("%I:%M:%S %p"), "end_time": now.strftime("%I:%M:%S %p"),
                "duration_mins": str(int((now - start).total_seconds() // 60)), "status": "Completed"
            }).execute()
        except Exception:
            pass
    st.rerun()

def show_assign_tasks_admin(kp="asg"):
    st.subheader("📌 Assign Tasks")
    users = [u for u in (load_users() or {}).values() if u.get("role") != "admin"]
    people = sorted(u["name"] for u in users)
    team_of = {u["name"]: u.get("team", "") for u in users}
    phones = {u["name"]: u.get("phone", "") for u in users}
    teams = sorted(set(team_of.values()) - {""})

    with st.expander("➕ New task", expanded=True):
        who_mode = st.radio("Assign to", ["People", "Whole team"], horizontal=True, key=f"{kp}_mode")
        if who_mode == "People":
            who = st.multiselect("Person / people *", people, key=f"{kp}_who")
        else:
            tsel = st.multiselect("Team(s) *", teams, key=f"{kp}_teams")
            who = [p for p in people if team_of.get(p) in tsel]
            if who:
                st.caption("Will be assigned to: " + ", ".join(who))
        with st.form(f"{kp}_form", clear_on_submit=True):
            title = st.text_input("Task *", placeholder="e.g. Clean rack A1–A5, check expiry of cough syrups")
            details = st.text_area("Details (optional)", height=70)
            c1, c2, c3 = st.columns(3)
            with c1: due = st.date_input("Due date", value=today_ist(), key=f"{kp}_due")
            with c2: pri = st.selectbox("Priority", ["Normal", "High", "Urgent"], key=f"{kp}_pri")
            with c3: rep = st.checkbox("🔁 Repeat daily", key=f"{kp}_rep", help="A fresh copy appears every day until you stop it")
            if st.form_submit_button("📌 Assign", type="primary", width='stretch'):
                if not who or not title.strip():
                    st.error("Choose who and write the task!")
                else:
                    base = {"title": title.strip(), "details": details.strip() or None, "priority": pri,
                            "due_date": due.strftime("%Y-%m-%d"), "active": True,
                            "assigned_by": st.session_state.name, "assigned_at": now_iso()}
                    try:
                        if rep:
                            temps = supabase.table("assigned_tasks").insert(
                                [{**base, "assigned_to": p, "team": team_of.get(p, ""), "is_template": True,
                                  "status": "Template"} for p in who]).execute().data or []
                            ensure_daily_copies()
                        else:
                            supabase.table("assigned_tasks").insert(
                                [{**base, "assigned_to": p, "team": team_of.get(p, ""), "is_template": False,
                                  "status": "Pending"} for p in who]).execute()
                        st.success(f"✅ Assigned to {len(who)} person(s)" + (" — repeats daily" if rep else ""))
                    except Exception as e:
                        st.error(f"Could not save — has assigned_tasks_setup.sql been run in Supabase? ({e})")

    # ── Status board ──
    ensure_daily_copies()
    c1, c2, c3 = st.columns(3)
    with c1: day = st.date_input("Tasks due on", value=today_ist(), key=f"{kp}_day")
    with c2: pf = st.selectbox("Person", ["All"] + people, key=f"{kp}_pf")
    with c3: sf = st.selectbox("Status", ["All", "Pending", "In Progress", "Done", "Cannot Do"], key=f"{kp}_sf")
    try:
        d = day.strftime("%Y-%m-%d")
        rows = supabase.table("assigned_tasks").select("*").eq("is_template", False).eq("active", True)\
            .eq("due_date", d).execute().data or []
        # also carry forward unfinished older tasks when looking at today
        if d == date_str():
            rows += supabase.table("assigned_tasks").select("*").eq("is_template", False).eq("active", True)\
                .lt("due_date", d).in_("status", ["Pending", "In Progress"]).execute().data or []
    except Exception as e:
        st.error(f"Could not load — has assigned_tasks_setup.sql been run in Supabase? ({e})")
        return
    if pf != "All":
        rows = [r for r in rows if r.get("assigned_to") == pf]
    if sf != "All":
        rows = [r for r in rows if r.get("status") == sf]

    m = st.columns(4)
    with m[0]: st.metric("📌 Tasks", len(rows))
    with m[1]: st.metric("✅ Done", sum(1 for r in rows if r.get("status") == "Done"))
    with m[2]: st.metric("⏳ Open", sum(1 for r in rows if r.get("status") in ("Pending", "In Progress")))
    with m[3]: st.metric("❌ Can't do", sum(1 for r in rows if r.get("status") == "Cannot Do"))

    status_icon = {"Pending": "⏳ Pending", "In Progress": "🔄 In Progress", "Done": "✅ Done", "Cannot Do": "❌ Can't do"}
    order = {"Urgent": 0, "High": 1, "Normal": 2}
    for r in sorted(rows, key=lambda x: (x.get("status") == "Done", order.get(x.get("priority"), 3), str(x.get("assigned_to")))):
        c1, c2, c3 = st.columns([3, 2, 2])
        with c1:
            late = " · ⚠️ overdue" if str(r.get("due_date")) < date_str() and r.get("status") in ("Pending", "In Progress") else ""
            rep = " · 🔁" if r.get("template_id") else ""
            st.markdown(f"{PRIORITY_ICON.get(r.get('priority'),'🟢')} **{r.get('title','')}**{rep}  \n"
                        f"<small>👤 {r.get('assigned_to','')} · due {r.get('due_date','')}{late}</small>", unsafe_allow_html=True)
            if r.get("note"):
                st.caption(f"📝 {r['note']}")
        with c2:
            txt = status_icon.get(r.get("status"), r.get("status"))
            t = to_ist(r.get("done_at")) or to_ist(r.get("started_at"))
            st.markdown(txt + (f"  \n<small>{t.strftime('%I:%M %p')}</small>" if t else ""), unsafe_allow_html=True)
        with c3:
            if r.get("status") in ("Pending", "In Progress"):
                msg = f"Hi {r.get('assigned_to','')}, new task from {r.get('assigned_by','')} on the RapidSurge app: {r.get('title','')}. Please check your dashboard. Thank you."
                if not wa_buttons(phones.get(r.get("assigned_to")), msg, f"{kp}_wa_{r['id']}"):
                    st.caption("No mobile saved")
                if st.button("🗑️ Cancel task", key=f"{kp}_del_{r['id']}", width='stretch'):
                    supabase.table("assigned_tasks").update({"active": False}).eq("id", r["id"]).execute()
                    st.rerun()

    # ── Repeating tasks ──
    try:
        temps = supabase.table("assigned_tasks").select("*").eq("is_template", True).eq("active", True).execute().data or []
    except Exception:
        temps = []
    if temps:
        with st.expander(f"🔁 Repeating daily tasks ({len(temps)})"):
            for t in sorted(temps, key=lambda x: (str(x.get("assigned_to")), str(x.get("title")))):
                c1, c2 = st.columns([4, 1])
                with c1: st.markdown(f"**{t.get('title','')}** — {t.get('assigned_to','')} · since {t.get('due_date','')}")
                with c2:
                    if st.button("⏹️ Stop", key=f"{kp}_stop_{t['id']}", width='stretch'):
                        supabase.table("assigned_tasks").update({"active": False}).eq("id", t["id"]).execute()
                        st.rerun()

# ── FULL DAY VIEW OF ONE PERSON (admin) ───────────────────────────────────────
def task_qty_detail(t):
    """(qty, details text) for any task type"""
    d = t.get("details") or {}
    tt = t.get("task_type", "")
    num = lambda k: int(_to_float(d.get(k), 0))
    join = lambda *p: " | ".join([str(x) for x in p if x not in (None, "", "0")])
    if tt == "Purchase Order":
        return num("no_sku"), join(d.get("distributor"), d.get("area"), f"SKUs: {num('no_sku')}")
    if tt == "Arrangement Order":
        n = d.get("arrangement_no", "")
        return num("no_medicines"), join(f"#{n}" if n else "", d.get("distributor"), d.get("area"))
    if tt in ("Register Entry", "Bill Cross Check", "Bill Upload (Software)", "Bill Upload", "Purchase Return"):
        return num("no_items"), join(f"Bill {d.get('bill_no')}" if d.get("bill_no") else "", d.get("arrangement_no"),
                                     d.get("distributor"), f"Items: {num('no_items')}")
    if tt == "Stock Placement":
        return num("no_medicines"), join(d.get("arrangement_no"), f"Bill {d.get('bill_no')}" if d.get("bill_no") else "",
                                         d.get("distributor"), f"Medicines: {num('no_medicines')}")
    if tt == "Call Log":
        return num("calls_made"), f"Made {num('calls_made')} | Picked {num('calls_picked')} | Orders {d.get('orders_delivered', 0)}"
    if tt == "Medicine Search":
        return num("no_searched"), f"Searched {num('no_searched')} | Found {d.get('no_found', 0)}"
    if tt == "Customer Delivery Update":
        return num("lines"), f"Order {d.get('order','')} | Delivered {d.get('delivered',0)} | Not delivered {d.get('not_delivered',0)}"
    if tt in ("Order Import", "Customer Items Check", "Customer Items Received"):
        return num("lines"), join(d.get("area"), d.get("arrangement_no"), f"{num('lines')} items")
    return 0, join(d.get("task_name"), d.get("distributor"), d.get("remarks"))

def show_person_day(person, day):
    """Everything one person did on one day: attendance + every task + breaks + idle gaps"""
    from datetime import timedelta
    d = day.strftime("%Y-%m-%d")
    is_today = d == date_str()
    try:
        tasks = fetch_all("daily_tasks", lambda q: q.eq("person", person).eq("date", d))
    except Exception as e:
        st.error(f"Could not load tasks: {e}")
        return
    try:
        events = supabase.table("attendance_log").select("*").eq("person", person).eq("date", d).order("at").execute().data or []
    except Exception:
        events = []
    day_dt = datetime.strptime(d, "%Y-%m-%d")
    def on_day(tstr):
        tt = parse_task_time(tstr)
        return day_dt.replace(hour=tt.hour, minute=tt.minute, second=tt.second) if tt else None
    naive = lambda x: x.replace(tzinfo=None) if x else None

    s = att_state(events)
    cin, cout = naive(s["clock_in"]), naive(s["clock_out"])
    items = []   # (start, end, what, details, qty, kind)
    for t in tasks:
        stt, end = on_day(t.get("start_time")), on_day(t.get("end_time"))
        if not stt:
            stt = on_day(t.get("time"))
        if t.get("status") == "In Progress":
            items.append((stt, None, f"🔄 {t.get('task_type','')} (started, not submitted)", "", 0, "open"))
            continue
        if stt and end and end < stt:
            end = end + timedelta(days=1)
        q, det = task_qty_detail(t)
        items.append((stt, end or stt, t.get("task_type", ""), det, q, "task"))
    brk = None
    for e in events:
        t = naive(to_ist(e.get("at")))
        ev = e.get("event")
        if ev == "login":
            items.append((t, t, "📱 Opened app", "", 0, "mark"))
        elif ev == "clock_in":
            items.append((t, t, "🟢 Clock In", "", 0, "mark"))
        elif ev == "clock_out":
            if brk:
                items.append((brk[0], t, f"☕ {brk[1]} break", "", 0, "break")); brk = None
            items.append((t, t, "🔴 Clock Out", "", 0, "mark"))
        elif ev == "break_start":
            brk = (t, e.get("break_type") or "Break")
        elif ev == "break_end" and brk:
            items.append((brk[0], t, f"☕ {brk[1]} break", "", 0, "break")); brk = None
    now_n = naive(now_ist())
    if brk:
        items.append((brk[0], now_n if is_today else brk[0], f"☕ {brk[1]} break (running)", "", 0, "break"))
    items = [i for i in items if i[0]]
    items.sort(key=lambda i: (i[0], 0 if i[5] == "mark" else 1))

    task_items = [i for i in items if i[5] == "task"]
    task_secs_total = _merged_secs([(i[0], i[1]) for i in task_items])
    if not items:
        st.info(f"No activity recorded for {person} on {d}.")
        return

    # idle gaps (15+ min with no task / break) between clock-in (or first task) and clock-out (or now)
    GAP = 15 * 60
    day_start = cin or (task_items[0][0] if task_items else None)
    day_end = cout or (now_n if is_today and cin else (max(i[1] for i in task_items) if task_items else None))
    rows, cursor = [], day_start
    for st_, en, what, det, q, kind in items:
        is_out = kind == "mark" and "Clock Out" in what
        if (kind in ("task", "break") or is_out) and cursor and st_ and (st_ - cursor).total_seconds() >= GAP and (not day_end or st_ <= day_end):
            rows.append({"Time": cursor.strftime("%I:%M %p"), "What": "💤 No activity", "Details": "",
                         "Start": cursor.strftime("%I:%M %p"), "End": st_.strftime("%I:%M %p"),
                         "Duration": fmt_age(int((st_ - cursor).total_seconds() // 60)), "Qty": "", "Avg secs/unit": ""})
        secs = int((en - st_).total_seconds()) if (en and st_ and kind in ("task", "break")) else None
        rows.append({
            "Time": st_.strftime("%I:%M %p"), "What": what, "Details": det,
            "Start": st_.strftime("%I:%M:%S %p") if kind != "mark" else "",
            "End": en.strftime("%I:%M:%S %p") if (en and kind in ("task", "break")) else "",
            "Duration": fmt_secs(secs) if secs is not None else "",
            "Qty": str(q) if q else "",
            "Avg secs/unit": f"{round(secs / q, 1)} secs" if (q and secs) else "",
        })
        if kind in ("task", "break") and en and (cursor is None or en > cursor):
            cursor = en
        if is_out:
            cursor = None          # nothing counted after clock-out
    if cursor and day_end and not cout and (day_end - cursor).total_seconds() >= GAP:
        rows.append({"Time": cursor.strftime("%I:%M %p"), "What": "💤 No activity" + (" (so far)" if is_today and not cout else ""),
                     "Details": "", "Start": cursor.strftime("%I:%M %p"), "End": day_end.strftime("%I:%M %p"),
                     "Duration": fmt_age(int((day_end - cursor).total_seconds() // 60)), "Qty": "", "Avg secs/unit": ""})

    rows.sort(key=lambda r: datetime.strptime(r["Time"], "%I:%M %p"))   # keep time order

    # summary line
    present = (day_end - cin).total_seconds() if cin and day_end and day_end > cin else 0
    base = max(0, present - s["break_secs"])
    active = f"{round(task_secs_total / base * 100)}%" if base > 0 else "—"
    idle_mins = sum(int((datetime.strptime(r["End"], "%I:%M %p") - datetime.strptime(r["Start"], "%I:%M %p")).total_seconds() // 60) % 1440
                    for r in rows if r["What"].startswith("💤"))
    parts = [f"🟢 In {cin.strftime('%I:%M %p')}" if cin else "⚠️ No clock-in",
             f"🔴 Out {cout.strftime('%I:%M %p')}" if cout else ("still in" if is_today and cin else ""),
             f"Present {fmt_age(int(present // 60))}" if present else "",
             f"Breaks {s['breaks']} ({fmt_age(int(s['break_secs'] // 60))})" if s["breaks"] else "",
             f"Task time {fmt_secs(task_secs_total)}", f"Active {active}",
             f"{len(task_items)} tasks", f"💤 {fmt_age(idle_mins)} no activity" if idle_mins else ""]
    st.markdown("**" + " · ".join([p for p in parts if p]) + "**")
    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, width='stretch')
    st.caption("💤 No activity = 15+ minutes with no task and no break recorded.")
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name=person[:30])
    st.download_button("⬇️ Download this day (Excel)", buf.getvalue(), f"{person}-{d}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"day_dl_{person}_{d}")

# ── ALL STAFF WORK (admin / manager) ──────────────────────────────────────────
def show_all_staff_work(kp="asw"):
    st.subheader("👥 All Staff Work")
    users = [u for u in (load_users() or {}).values() if u.get("role") != "admin"]
    team_of = {u["name"]: u.get("team", "") for u in users}
    c1, c2, c3 = st.columns(3)
    with c1: day = st.date_input("Date", value=today_ist(), key=f"{kp}_day")
    with c2: team_f = st.selectbox("Team", ["All"] + sorted(set(team_of.values()) - {""}), key=f"{kp}_team")
    d = day.strftime("%Y-%m-%d")
    try:
        tasks = [t for t in fetch_all("daily_tasks", lambda q: q.eq("date", d)) if t.get("status") != "In Progress"]
    except Exception as e:
        st.error(f"Could not load tasks: {e}")
        return
    for t in tasks:
        team_of.setdefault(t.get("person"), t.get("team", ""))
    tasks = [t for t in tasks if team_f == "All" or team_of.get(t.get("person")) == team_f]
    people = sorted(set(t.get("person") for t in tasks if t.get("person")))
    types = sorted(set(t.get("task_type", "") for t in tasks))
    with c3: who = st.multiselect("Person", people, key=f"{kp}_who", placeholder="All people")
    ttype = st.multiselect("Task type", types, key=f"{kp}_tt", placeholder="All task types")
    if who:
        tasks = [t for t in tasks if t.get("person") in who]
    if ttype:
        tasks = [t for t in tasks if t.get("task_type") in ttype]
    if not tasks:
        st.info("No finished tasks for this selection.")
        return

    rows = []
    for t in tasks:
        secs = task_secs(t)
        q, det = task_qty_detail(t)
        rows.append({"Person": t.get("person", ""), "Team": team_of.get(t.get("person"), ""),
                     "Task": t.get("task_type", ""), "Details": det,
                     "Start": t.get("start_time", "") or t.get("time", ""), "End": t.get("end_time", ""),
                     "Duration": fmt_secs(secs), "Qty": _qty_txt(q) if q else "", "_secs": secs,
                     "_spu": (secs / q) if q and secs else None,
                     "_sort": parse_task_time(t.get("start_time") or t.get("time")) or datetime.min})
    df = pd.DataFrame(rows)

    # speed vs the day's typical (median) for the same task type
    med = df.dropna(subset=["_spu"]).groupby("Task")["_spu"].median().to_dict()
    def speed(r):
        if r["_spu"] is None or pd.isna(r["_spu"]):
            return ""
        m = med.get(r["Task"])
        flag = " 🐢" if m and r["_spu"] > 2 * m else (" ⚡" if m and r["_spu"] < 0.5 * m else "")
        return f"{round(r['_spu'], 1)} secs{flag}"
    df["Avg secs/unit"] = df.apply(speed, axis=1)

    # per-person summary
    summ = df.groupby(["Person", "Team"]).agg(Tasks=("Task", "count"), Secs=("_secs", "sum"),
                                              First=("_sort", "min"), Last=("_sort", "max")).reset_index()
    summ["Task Time"] = summ["Secs"].map(fmt_secs)
    summ["First Task"] = summ["First"].map(lambda x: x.strftime("%I:%M %p") if x and x != datetime.min else "")
    summ["Last Task"] = summ["Last"].map(lambda x: x.strftime("%I:%M %p") if x and x != datetime.min else "")
    summ["🐢 Slow"] = summ["Person"].map(lambda p: int(df[(df["Person"] == p) & df["Avg secs/unit"].str.contains("🐢")].shape[0]))
    m = st.columns(3)
    with m[0]: st.metric("👥 People", len(summ))
    with m[1]: st.metric("🧾 Tasks", len(df))
    with m[2]: st.metric("⏱️ Total task time", fmt_secs(df["_secs"].sum()))
    st.markdown("**Per person**")
    st.dataframe(summ[["Person", "Team", "Tasks", "Task Time", "First Task", "Last Task", "🐢 Slow"]]
                 .sort_values(["Team", "Person"]), hide_index=True, width='stretch')

    only_slow = st.toggle("Show only slow tasks 🐢 (more than 2× the day's typical speed for that task)", key=f"{kp}_slow")
    view = df[df["Avg secs/unit"].str.contains("🐢")] if only_slow else df
    view = view.sort_values(["Person", "_sort"])
    st.markdown("**Every task**")
    st.dataframe(view[["Person", "Team", "Start", "End", "Task", "Details", "Duration", "Qty", "Avg secs/unit"]],
                 hide_index=True, width='stretch')
    st.caption("🐢 slower than 2× and ⚡ faster than half the day's typical secs/unit for the same task type. "
               "Pick one person and open 📋 Full Day to see breaks and idle gaps too.")
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        view.drop(columns=["_secs", "_spu", "_sort"]).to_excel(w, index=False, sheet_name="Tasks")
        summ.drop(columns=["Secs", "First", "Last"]).to_excel(w, index=False, sheet_name="Per person")
    st.download_button("⬇️ Download Excel", buf.getvalue(), f"staff-work-{d}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"{kp}_dl")

# ── MANAGER: TEAM VIEW ────────────────────────────────────────────────────────
def show_full_day_picker(kp="fd"):
    users = [u for u in (load_users() or {}).values() if u.get("role") != "admin"]
    people = sorted(u["name"] for u in users)
    c1, c2 = st.columns(2)
    with c1: day = st.date_input("Date", value=today_ist(), key=f"{kp}_day")
    with c2: who = st.selectbox("Person", people, key=f"{kp}_who") if people else None
    if who:
        show_person_day(who, day)

def show_manager_team_view():
    st.markdown("## 👥 Team View")
    t0, t1, t2, t3, t4, t5, t6, t7, t8 = st.tabs(["👥 All Staff Work", "🕐 Attendance", "📋 Full Day", "📌 Assign Tasks", "📅 Shift Planner", "🧾 Bills Register", "📦 Customer Orders", "🛒 Normal Orders", "🚚 Distributors"])
    with t0: show_all_staff_work("mgr_asw")
    with t1: show_attendance_admin("mgr_att")
    with t2: show_full_day_picker("mgr_fd")
    with t3: show_assign_tasks_admin("mgr_asg")
    with t4: show_shift_planner("mgr_shift")
    with t5: show_bills_register("mgr_bills")
    with t6: show_customer_order_tracker("mgr_trk", show_phone=True)
    with t7: show_order_sheet_report("mgr_osr")
    with t8: show_distributors_admin("mgr_dist")

# ── DISTRIBUTOR LIST (master) ─────────────────────────────────────────────────
DIST_XL_COLS = ["Name", "Address", "GST No", "Mobile", "Email", "Usual Margin %", "Active"]

def dist_options(current=""):
    """Distributor dropdown list; keeps an old name visible so editing never silently changes it"""
    return DISTRIBUTORS + ([current] if current and current not in DISTRIBUTORS else [])

def show_distributors_admin(kp="dist"):
    st.subheader("🏭 Distributors")
    st.caption("This list feeds every distributor dropdown in the app. The name must match the column header "
               "in the Order Sheet exactly.")
    try:
        rows = supabase.table("distributors").select("*").order("name").execute().data or []
    except Exception as e:
        st.error(f"Could not load distributors — has normal_order_setup.sql been run in Supabase? ({e})")
        return
    names_lc = {r["name"].strip().lower(): r for r in rows}

    c1, c2 = st.columns(2)
    with c1:
        with st.expander("➕ Add a distributor", expanded=False):
            with st.form(f"{kp}_add", clear_on_submit=True):
                name = st.text_input("Name *")
                a1, a2 = st.columns(2)
                with a1:
                    mobile = st.text_input("Mobile")
                    gst = st.text_input("GST No")
                with a2:
                    email = st.text_input("Email")
                    margin = st.number_input("Usual margin %", min_value=0.0, max_value=100.0, step=0.5, value=0.0)
                address = st.text_area("Address", height=70)
                if st.form_submit_button("Add ✅", type="primary"):
                    n = name.strip()
                    if not n:
                        st.error("Enter the distributor name.")
                    elif n.lower() in names_lc:
                        st.error(f"'{names_lc[n.lower()]['name']}' is already in the list.")
                    else:
                        try:
                            supabase.table("distributors").insert({
                                "name": n, "mobile": mobile.strip(), "email": email.strip(), "gst_no": gst.strip().upper(),
                                "address": address.strip(), "usual_margin": margin or None, "active": True}).execute()
                            load_distributors.clear()
                            st.success(f"✅ {n} added")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
    with c2:
        with st.expander("📤 Upload list from Excel", expanded=False):
            buf = io.BytesIO()
            pd.DataFrame(columns=DIST_XL_COLS).to_excel(buf, index=False)
            st.download_button("⬇️ Download format", buf.getvalue(), "distributors-format.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"{kp}_fmt")
            up = st.file_uploader("Filled distributor sheet (.xlsx)", type=["xlsx", "xls"],
                                  key=f"{kp}_up_{st.session_state.get(kp + '_upv', 0)}")
            if up:
                try:
                    df = pd.read_excel(up, dtype=str)
                    cm = {_norm_col(c): c for c in df.columns}
                    if "name" not in cm:
                        st.error("The sheet needs a 'Name' column — use the format above.")
                    else:
                        recs = []
                        for _, r in df.iterrows():
                            n = _clean_str(r.get(cm["name"]))
                            if not n:
                                continue
                            g = lambda k: _clean_str(r.get(cm[k])) if k in cm else ""
                            rec = {"name": names_lc.get(n.lower(), {}).get("name", n)}
                            for col, key in [("address", "address"), ("gstno", "gst_no"), ("mobile", "mobile"), ("email", "email")]:
                                if g(col):
                                    rec[key] = g(col).upper() if key == "gst_no" else g(col)
                            if g("usualmargin"):
                                rec["usual_margin"] = _to_float(g("usualmargin"), None)
                            if g("active"):
                                rec["active"] = g("active").lower() not in ("no", "n", "false", "0", "inactive")
                            recs.append(rec)
                        new = sum(1 for x in recs if x["name"].lower() not in names_lc)
                        st.info(f"📄 {len(recs)} distributors in file · {new} new · {len(recs) - new} to update")
                        if st.button("💾 Save list", key=f"{kp}_up_save", type="primary"):
                            for x in recs:
                                if x["name"].lower() in names_lc:
                                    upd = {k: v for k, v in x.items() if k != "name"}
                                    if upd:
                                        supabase.table("distributors").update(upd).eq("id", names_lc[x["name"].lower()]["id"]).execute()
                                else:
                                    supabase.table("distributors").insert({"active": True, **x}).execute()
                            load_distributors.clear()
                            st.session_state[kp + "_upv"] = st.session_state.get(kp + "_upv", 0) + 1
                            st.success("✅ Distributor list saved")
                            st.rerun()
                except Exception as e:
                    st.error(f"Could not read the file: {e}")

    if not rows:
        st.info("No distributors yet — add them above.")
        return
    act = [r for r in rows if r.get("active", True)]
    missing = sum(1 for r in act if not (r.get("mobile") and r.get("gst_no")))
    st.markdown(f"**{len(act)} active distributors**" + (f" · ⚠️ {missing} missing mobile / GST" if missing else ""))
    df = pd.DataFrame([{"id": r["id"], "Name": r["name"], "Mobile": r.get("mobile") or "", "Email": r.get("email") or "",
                        "GST No": r.get("gst_no") or "", "Address": r.get("address") or "",
                        "Usual Margin %": r.get("usual_margin"), "Active": bool(r.get("active", True))} for r in rows])
    ver = st.session_state.get(kp + "_ver", 0)
    ed = st.data_editor(df, key=f"{kp}_ed_{ver}", hide_index=True, width='stretch', disabled=["Name"],
                        column_config={"id": None,
                                       "Usual Margin %": st.column_config.NumberColumn("Usual Margin %", min_value=0, max_value=100, format="%.2f"),
                                       "Active": st.column_config.CheckboxColumn("Active")})
    st.caption("Edit details in the table, then save. Names can't be edited here (old bills keep the old name) — "
               "untick Active and add the new name instead.")
    old = {r["id"]: r for r in df.to_dict("records")}
    changes = []
    for r in ed.to_dict("records"):
        o = old.get(r["id"])
        diff = {}
        for col, key in [("Mobile", "mobile"), ("Email", "email"), ("GST No", "gst_no"), ("Address", "address"), ("Active", "active")]:
            if (r[col] or "") != (o[col] or ""):
                diff[key] = r[col]
        a, b = r["Usual Margin %"], o["Usual Margin %"]
        if not ((a is None or pd.isna(a)) and (b is None or pd.isna(b))) and a != b:
            diff["usual_margin"] = None if a is None or pd.isna(a) else float(a)
        if diff:
            changes.append((r["id"], diff))
    if st.button(f"💾 Save changes ({len(changes)})", key=f"{kp}_save", type="primary", disabled=not changes):
        try:
            for i, diff in changes:
                supabase.table("distributors").update(diff).eq("id", i).execute()
            load_distributors.clear()
            st.session_state[kp + "_ver"] = ver + 1
            st.success(f"✅ {len(changes)} distributor(s) updated")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")


# ── NORMAL ORDER SHEET (Purchase) ─────────────────────────────────────────────
NOT_ORDERED_REASONS = [
    "A) Not available with any distributor",
    "B) Margin too low",
    "C) Enough stock already",
    "D) Minimum order value not met",
    "E) Short expiry",
    "F) Distributor credit / payment hold",
    "G) Duplicate item",
    "H) Other",
]
OFF_TOP_REASONS = ["Not available with top distributors", "Needed urgently", "Payment issue", "Other"]
MED_TYPE_ORDER = ["Fast", "Average", "Slow Regular", "Very Slow Regular", "Rare", "New"]
SHEET_BASE_COLS = {"itemname": "item_name", "packsize": "pack_size", "closingstock": "closing_stock",
                   "closingstrip": "closing_strip", "combine": None, "type": "item_type", "medtype": "med_type",
                   "order": "order_qty", "bestdist1": "best1", "bestdist2": "best2", "bestdist3": "best3"}
SHEET_TEMPLATE_COLS = ["Item Name", "Pack Size", "Closing Stock", "Closing (Strip)", "combine", "Type", "Med Type",
                       "Order", "Best Dist 1", "Best Dist 2", "Best Dist 3"]

def _cell_lines(v):
    s = "" if v is None else str(v)
    if s.strip().lower() in ("", "nan", "none", "-", "—"):
        return []
    return [p.strip() for p in s.splitlines() if p.strip()]

def _parse_best(v):
    """'Jai Medical Agency\\n 30.29% -'  ->  {name, margin, scheme}"""
    parts = _cell_lines(v)
    if not parts:
        return None
    rest = " ".join(parts[1:])
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*%", rest)
    scheme = (rest[m.end():] if m else rest).strip()
    return {"name": parts[0], "margin": float(m.group(1)) if m else None,
            "scheme": "" if scheme in ("-", "—") else scheme}

def _parse_offer(v):
    """distributor column cell '5+1\\n Mgn 39.64%\\n Qty 62'  ->  {margin, qty, scheme}"""
    parts = _cell_lines(v)
    if not parts:
        return None
    s = " ".join(parts)
    m = re.search(r"mgn\s*(-?\d+(?:\.\d+)?)\s*%", s, re.I)
    q = re.search(r"qty\s*(-?\d+(?:\.\d+)?)", s, re.I)
    if not m and not q:
        return None
    scheme = parts[0] if not parts[0].lower().startswith(("mgn", "qty")) else ""
    return {"margin": float(m.group(1)) if m else None, "qty": float(q.group(1)) if q else None,
            "scheme": "" if scheme in ("-", "—") else scheme}

def parse_order_sheet(uploaded):
    """-> (lines, distributor column names, rows skipped (order 0), error)"""
    name = uploaded.name.lower()
    raw = pd.read_excel(uploaded, dtype=str) if name.endswith((".xlsx", ".xls")) else pd.read_csv(uploaded, dtype=str)
    colmap, dist_cols = {}, []
    for c in raw.columns:
        k = _norm_col(c)
        if k in SHEET_BASE_COLS:
            if SHEET_BASE_COLS[k] and SHEET_BASE_COLS[k] not in colmap.values():
                colmap[c] = SHEET_BASE_COLS[k]
        elif k and not k.startswith("unnamed"):
            dist_cols.append(c)
    inv = {v: k for k, v in colmap.items()}
    if "item_name" not in inv or "order_qty" not in inv:
        return [], [], 0, "The file needs 'Item Name' and 'Order' columns — download the format and compare the headers."
    lines, seen, skipped = [], {}, 0
    for _, r in raw.iterrows():
        g = lambda k: r.get(inv[k]) if k in inv else None
        item = _clean_str(g("item_name"))
        if not item:
            continue
        oq = _to_float(g("order_qty"), 0)
        if oq <= 0:
            skipped += 1
            continue
        pack = _clean_str(g("pack_size"))
        key = f"{item.lower()}|{pack.lower()}"
        if key in seen:                           # same medicine twice in one sheet -> add qty
            seen[key]["order_qty"] += oq
            continue
        offers = {}
        for c in dist_cols:
            o = _parse_offer(r.get(c))
            if o:
                offers[str(c).strip()] = o
        line = {"item_key": key, "item_name": item, "pack_size": pack,
                "closing_stock": _to_float(g("closing_stock"), 0), "closing_strip": _to_float(g("closing_strip"), 0),
                "item_type": _clean_str(g("item_type")) or "Ok", "med_type": _clean_str(g("med_type")),
                "order_qty": oq, "best": [b for b in (_parse_best(g(f"best{i}")) for i in (1, 2, 3)) if b],
                "offers": offers}
        seen[key] = line
        lines.append(line)
    return lines, [str(c).strip() for c in dist_cols], skipped, None

def order_sheet_template():
    names = [d for d in DISTRIBUTORS]
    ex = {"Item Name": "Atorva 20 Tablet", "Pack Size": "15 Tablet", "Closing Stock": "30", "Closing (Strip)": "2",
          "combine": "Atorva 20 Tablet15 Tablet", "Type": "Ok", "Med Type": "Fast", "Order": "6",
          "Best Dist 1": "Jai Medical Agency\n 30.29% -", "Best Dist 2": "Sehgal pharma\n 30.07% -",
          "Best Dist 3": "Zonne Ventures Pvt Ltd\n 29.3% -"}
    cols = SHEET_TEMPLATE_COLS + names
    df = pd.DataFrame([{c: ex.get(c, "") for c in cols}])
    for n, cell in [("Jai Medical Agency", "—\n Mgn 30.29%\n Qty 51"), ("Sehgal pharma", "—\n Mgn 30.07%\n Qty 22")]:
        if n in df.columns:
            df.loc[0, n] = cell
    notes = pd.DataFrame({"How to fill": [
        "One row per medicine. Row 2 is an example — delete it before uploading.",
        "Order = strips to order (not loose). Rows with Order 0 are ignored.",
        "Type: Ok / Discontinued / Duplicate / JIT.  Med Type: Fast / Average / Slow Regular / Very Slow Regular / Rare / New.",
        "Best Dist 1-3: distributor name on line 1, then 'margin% scheme' on line 2 (e.g. 30.29% 5+1). Use - if none.",
        "Distributor columns: scheme on line 1 (— if none), then 'Mgn 28.5%' and 'Qty 198'. Leave blank if the distributor doesn't have it.",
        "Distributor column headers must match names in the app's distributor list exactly.",
    ]})
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Order Sheet")
        notes.to_excel(w, index=False, sheet_name="How to fill")
    return buf.getvalue()

def import_order_sheet(lines, area, fname):
    d = date_str()
    now_s = now_iso()
    prev = supabase.table("order_sheets").select("*").eq("area", area).eq("sheet_date", d).execute().data or []
    rnd = max([int(p.get("round") or 0) for p in prev] + [0]) + 1
    sheet = supabase.table("order_sheets").insert({
        "area": area, "sheet_date": d, "round": rnd, "file_name": fname, "lines": len(lines),
        "uploaded_by": st.session_state.name, "uploaded_at": now_s}).execute().data[0]
    earlier = fetch_all("order_sheet_lines", lambda q: q.eq("area", area).eq("sheet_date", d)) if prev else []
    ordered_before, pending_before = {}, {}
    for l in earlier:
        if l.get("status") == "Ordered":
            ordered_before.setdefault(l.get("item_key"), l)
        elif l.get("status") == "Pending":
            pending_before.setdefault(l.get("item_key"), []).append(l)
    keys = set(l["item_key"] for l in lines)
    superseded = [x["id"] for k, xs in pending_before.items() if k in keys for x in xs]
    for ch in _chunks(superseded, 200):
        supabase.table("order_sheet_lines").update({"status": "Superseded", "superseded_by": sheet["id"]})\
            .in_("id", ch).execute()
    rows = [{**l, "sheet_id": sheet["id"], "area": area, "sheet_date": d, "round": rnd, "status": "Pending",
             "repeat_of": (ordered_before.get(l["item_key"]) or {}).get("id"), "uploaded_at": now_s} for l in lines]
    for ch in _chunks(rows, 200):
        supabase.table("order_sheet_lines").insert(ch).execute()
    return {"round": rnd, "lines": len(rows), "repeats": sum(1 for r in rows if r["repeat_of"]),
            "superseded": len(superseded)}

def delete_order_sheet(sheet_id):
    """Undo a wrong upload: remove its lines and bring back the lines it replaced"""
    supabase.table("order_sheet_lines").delete().eq("sheet_id", sheet_id).execute()
    supabase.table("order_sheet_lines").update({"status": "Pending", "superseded_by": None})\
        .eq("superseded_by", sheet_id).execute()
    supabase.table("order_sheets").delete().eq("id", sheet_id).execute()

def _usual_margins():
    return {d["name"]: d.get("usual_margin") for d in load_distributors()}

def dist_rank_info(l, dist, usual=None):
    """rank of `dist` for this medicine (1-3 = Best Dist, 4+ by margin), its margin/scheme/stock, best margin"""
    best = l.get("best") or []
    offers = l.get("offers") or {}
    names = [b.get("name") for b in best]
    o = offers.get(dist) or {}
    ranked = [k for k, _ in sorted(offers.items(), key=lambda kv: -(kv[1].get("margin") or -1)) if k not in names]
    order = names + ranked
    rank = order.index(dist) + 1 if dist in order else None
    if dist in names:
        b = best[names.index(dist)]
        margin = b.get("margin") if b.get("margin") is not None else o.get("margin")
        scheme = b.get("scheme") or o.get("scheme") or ""
    else:
        margin, scheme = o.get("margin"), o.get("scheme") or ""
    usual_used = False
    if margin is None and usual and usual.get(dist) is not None:
        margin, usual_used = float(usual[dist]), True
    best_margin = best[0].get("margin") if best else None
    return {"rank": rank, "margin": margin, "scheme": scheme, "qty": o.get("qty"), "best_margin": best_margin,
            "usual": usual_used, "top3": dist in names}

def _best_txt(l):
    b = (l.get("best") or [None])[0]
    if not b:
        return "— none —"
    return f"{b.get('name')} {b.get('margin')}%" + (f" {b['scheme']}" if b.get("scheme") else "")

def _mt_sort(m):
    return MED_TYPE_ORDER.index(m) if m in MED_TYPE_ORDER else len(MED_TYPE_ORDER)

def _suggest_reason(l):
    if "dup" in str(l.get("item_type", "")).lower():
        return "G) Duplicate item"
    if not l.get("best") and not l.get("offers"):
        return "A) Not available with any distributor"
    return ""

def _repeat_txt(l, by_id):
    p = by_id.get(l.get("repeat_of"))
    if not p:
        return ""
    return f"🔁 R{p.get('round')}: {_qty_txt(p.get('ordered_qty'))} from {p.get('distributor','')} ({p.get('marked_by','')})"

def load_sheet_lines(area, d):
    q = lambda q: q.eq("sheet_date", d) if area in ("All Areas", None) else q.eq("sheet_date", d).eq("area", area)
    return fetch_all("order_sheet_lines", q)

def form_order_sheet():
    st.subheader("📑 Normal Order Sheet")
    view = st.radio("View", ["🛒 Order by distributor", "❌ Not ordered", "📤 Upload sheet"], horizontal=True,
                    key="os_view", label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        area = st.selectbox("Area *", [SELECT_AREA] + load_areas(), key="os_area")
    day = today_ist()
    if view != "📤 Upload sheet":
        with c2:
            day = st.date_input("Sheet date", value=today_ist(), key="os_date")
    if area == SELECT_AREA:
        st.info("Select the area first.")
        return
    if view == "📤 Upload sheet":
        _order_sheet_upload(area)
        return
    d = day.strftime("%Y-%m-%d")
    try:
        all_lines = load_sheet_lines(area, d)
    except Exception as e:
        st.error(f"Could not load the order sheet — has normal_order_setup.sql been run in Supabase? ({e})")
        return
    live = [l for l in all_lines if l.get("status") != "Superseded"]
    if not live:
        st.info(f"No order sheet uploaded for {area} on {day.strftime('%d %b')}. Use 📤 Upload sheet.")
        return
    cnt = lambda s: sum(1 for l in live if l.get("status") == s)
    m = st.columns(4)
    with m[0]: st.metric("📋 To order", len(live))
    with m[1]: st.metric("✅ Ordered", cnt("Ordered"))
    with m[2]: st.metric("❌ Not ordered", cnt("Not Ordered"))
    with m[3]: st.metric("⏳ Not marked", cnt("Pending"))
    by_id = {l["id"]: l for l in all_lines}
    pending = [l for l in live if l.get("status") == "Pending"]
    if view == "🛒 Order by distributor":
        _order_by_distributor(area, d, pending, by_id)
    else:
        _mark_not_ordered(area, d, pending, live, by_id)

def _order_sheet_upload(area):
    st.caption("Upload the order sheet from the software for this area. Up to 3 rounds a day — each upload is a new round. "
               "Medicines still pending from an earlier round move to the new round.")
    st.download_button("⬇️ Download blank format", order_sheet_template(), "order-sheet-format.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="os_fmt")
    try:
        today_sheets = supabase.table("order_sheets").select("*").eq("area", area).eq("sheet_date", date_str())\
            .order("round").execute().data or []
    except Exception as e:
        st.error(f"Could not load uploads — has normal_order_setup.sql been run in Supabase? ({e})")
        return
    nxt = max([int(s.get("round") or 0) for s in today_sheets] + [0]) + 1
    up = st.file_uploader("Order sheet (.xlsx or .csv)", type=["xlsx", "xls", "csv"],
                          key=f"os_file_{st.session_state.get('os_upv', 0)}")
    if up:
        try:
            lines, dcols, skipped, err = parse_order_sheet(up)
        except Exception as e:
            st.error(f"Could not read file: {e}")
            lines, err = [], None
        if err:
            st.error(err)
        elif lines:
            known = {n.lower() for n in DISTRIBUTORS}
            found = set(dcols) | {b["name"] for l in lines for b in l["best"]}
            new_d = sorted(n for n in found if n.lower() not in known)
            no_dist = sum(1 for l in lines if not l["best"] and not l["offers"])
            st.info(f"📄 **{len(lines)} medicines** to order · {sum(l['order_qty'] for l in lines):,.0f} strips"
                    + (f" · {no_dist} with no distributor" if no_dist else "")
                    + (f" · {skipped} rows with Order 0 skipped" if skipped else "")
                    + f"  →  this will be **Round {nxt}** for {area} today")
            if nxt > 3:
                st.warning(f"⚠️ {area} already has {nxt - 1} uploads today. Continue only if this is really a new round.")
            if new_d:
                st.warning("🏭 New distributor(s) not in the distributor list: " + ", ".join(new_d))
                if st.button(f"➕ Add {len(new_d)} to distributor list", key="os_add_dist"):
                    try:
                        for n in new_d:
                            supabase.table("distributors").insert({"name": n, "active": True}).execute()
                        load_distributors.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            prev = pd.DataFrame([{"Medicine": l["item_name"], "Pack": l["pack_size"], "Type": l["item_type"],
                                  "Med Type": l["med_type"], "Stock (strips)": _qty_txt(l["closing_strip"]),
                                  "Order": _qty_txt(l["order_qty"]), "Best #1": _best_txt(l)} for l in lines])
            st.dataframe(prev, hide_index=True, width='stretch', height=250)
            if st.button(f"📥 Upload as Round {nxt}", type="primary", key="os_go", width='stretch'):
                try:
                    res = import_order_sheet(lines, area, up.name)
                except Exception as e:
                    st.error(f"Upload failed: {e}")
                    return
                log_simple_task("Order Sheet Upload", {"area": area, "round": str(res["round"]), "lines": str(res["lines"])})
                st.session_state["os_upv"] = st.session_state.get("os_upv", 0) + 1
                st.session_state["os_msg"] = (f"✅ Round {res['round']} uploaded: {res['lines']} medicines"
                    + (f" · {res['superseded']} still-pending medicines moved from the earlier round" if res["superseded"] else "")
                    + (f" · 🔁 {res['repeats']} were already ordered earlier today" if res["repeats"] else ""))
                st.rerun()
        else:
            st.warning("No medicines with Order above 0 found in this file.")
    msg = st.session_state.pop("os_msg", None)
    if msg:
        st.success(msg)
    if today_sheets:
        st.markdown(f"**Today's uploads — {area}**")
        for s in today_sheets:
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"Round {s.get('round')} · {s.get('lines')} medicines · {s.get('uploaded_by','')} · "
                            f"{(to_ist(s.get('uploaded_at')) or now_ist()).strftime('%I:%M %p')} · {s.get('file_name','')}")
            with c2:
                if st.button("🗑️ Delete", key=f"os_del_{s['id']}", help="Wrong file? Delete it (only before any medicine is marked)"):
                    marked = supabase.table("order_sheet_lines").select("id").eq("sheet_id", s["id"])\
                        .in_("status", ["Ordered", "Not Ordered"]).execute().data or []
                    if marked:
                        st.error(f"Can't delete — {len(marked)} medicine(s) of this round are already marked.")
                    else:
                        delete_order_sheet(s["id"])
                        st.rerun()

def _order_by_distributor(area, d, pending, by_id):
    msg = st.session_state.pop("os_msg2", None)
    if msg:
        st.success(msg)
    if not pending:
        st.success("🎉 Every medicine in this sheet is marked.")
        return
    usual = _usual_margins()
    top_count = {}
    for l in pending:
        for b in l.get("best") or []:
            top_count[b.get("name")] = top_count.get(b.get("name"), 0) + 1
    names = sorted(set(DISTRIBUTORS) | set(top_count), key=lambda n: (-top_count.get(n, 0), n.lower()))
    c1, c2 = st.columns([3, 1])
    with c1:
        dist = st.selectbox("Distributor *", names, key="os_dist",
                            format_func=lambda n: f"{n} — {top_count[n]} medicine(s) in top 3" if top_count.get(n) else n)
    with c2:
        mode = st.selectbox("Mode", ["Through Call", "Pharma Rack", "Excel Send"], key="os_mode")
    show_all = st.toggle(f"Also show medicines where {dist} is NOT in the top 3", key="os_all")
    start = timer_button("sheet_order", "Purchase Order")
    if start is None:
        return
    rows = []
    for l in pending:
        ri = dist_rank_info(l, dist, usual)
        if not ri["top3"] and not show_all:
            continue
        rows.append({
            "id": l["id"], "Order?": False, "Rnd": l.get("round"),
            "Medicine": l.get("item_name", ""), "Pack": l.get("pack_size", ""), "Type": l.get("item_type", ""),
            "Med Type": l.get("med_type", ""), "Stock": _qty_txt(l.get("closing_strip")), "Order": _qty_txt(l.get("order_qty")),
            "Rank": f"#{ri['rank']}" if ri["rank"] else "not offered",
            "Margin": (f"{ri['margin']}%" + (" (usual)" if ri["usual"] else "")) if ri["margin"] is not None else "",
            "Scheme": ri["scheme"], "Dist Qty": _qty_txt(ri["qty"]) if ri["qty"] is not None else "",
            "Best #1": _best_txt(l), "🔁": _repeat_txt(l, by_id),
            "Order Qty": float(l.get("order_qty") or 0), "Why not top 3?": "", "Note": "",
            "_top": ri["top3"], "_r": ri["rank"] or 99, "_mt": _mt_sort(l.get("med_type"))})
    if not rows:
        st.info(f"{dist} is not in the top 3 for any pending medicine. Switch on the toggle above to see all medicines.")
        return
    rows.sort(key=lambda r: (not r["_top"], r["_r"], r["_mt"], r["Medicine"]))
    df = pd.DataFrame(rows)
    meta = {r["id"]: r for r in rows}
    ver = st.session_state.get("os_ver", 0)
    ed = st.data_editor(
        df.drop(columns=["_top", "_r", "_mt"]), key=f"os_ed_{ver}", hide_index=True, width='stretch',
        disabled=["Rnd", "Medicine", "Pack", "Type", "Med Type", "Stock", "Order", "Rank", "Margin", "Scheme",
                  "Dist Qty", "Best #1", "🔁"],
        column_config={
            "id": None,
            "Order?": st.column_config.CheckboxColumn("Order?", help="Tick medicines you are ordering from this distributor"),
            "Stock": st.column_config.TextColumn("Stock", help="Closing stock in strips"),
            "Order": st.column_config.TextColumn("Order", help="Strips to order (from the sheet)"),
            "Order Qty": st.column_config.NumberColumn("Order Qty", min_value=0, step=1, help="Strips you are ordering"),
            "Why not top 3?": st.column_config.SelectboxColumn("Why not top 3?", options=[""] + OFF_TOP_REASONS,
                                                                help="Needed only when this distributor is not Best Dist 1-3"),
        })
    st.caption("Rank #1-#3 = Best Dist 1-3 in the sheet; #4 and below are ranked by margin. "
               "Margin is this distributor's margin for that medicine.")
    picked = ed[ed["Order?"] == True]
    n = len(picked)
    strips = float(picked["Order Qty"].fillna(0).sum()) if n else 0
    if st.button(f"💾 Save order — {dist} ({n} SKUs, {_qty_txt(strips)} strips)", type="primary", key="os_save",
                 disabled=n == 0, width='stretch'):
        errs = []
        for _, r in picked.iterrows():
            mt = meta[r["id"]]
            if not (r["Order Qty"] and r["Order Qty"] > 0):
                errs.append(f"{r['Medicine']}: enter Order Qty")
            if not mt["_top"] and not r["Why not top 3?"]:
                errs.append(f"{r['Medicine']}: {dist} is not in the top 3 — pick 'Why not top 3?'")
            if r["Why not top 3?"] == "Other" and not str(r["Note"] or "").strip():
                errs.append(f"{r['Medicine']}: write a note for 'Other'")
        if errs:
            st.error("Fix these before saving:\n\n- " + "\n- ".join(errs[:10]))
            return
        end_time, duration = end_timer("sheet_order", start)
        now_s = now_iso()
        try:
            off_top = int(sum(1 for _, r in picked.iterrows() if not meta[r["id"]]["_top"]))
            task = supabase.table("daily_tasks").insert({
                "date": date_str(), "time": time_str(), "person": st.session_state.name, "team": "Purchase",
                "task_type": "Purchase Order",
                "details": {"distributor": dist, "area": area, "order_type": "Regular", "no_sku": str(n),
                            "strips": _qty_txt(strips), "mode": mode, "urgency": "Normal", "source": "Order Sheet",
                            "sheet_date": d, "off_top3": str(off_top), "remarks": ""},
                "start_time": start.strftime("%I:%M:%S %p"), "end_time": end_time,
                "duration_mins": str(duration), "status": "Completed"}).execute().data
            task_id = task[0]["id"] if task else None
            usual = _usual_margins()
            for _, r in picked.iterrows():
                l = by_id[int(r["id"])]
                ri = dist_rank_info(l, dist, usual)
                supabase.table("order_sheet_lines").update({
                    "status": "Ordered", "ordered_qty": float(r["Order Qty"]), "distributor": dist,
                    "dist_rank": ri["rank"], "dist_margin": ri["margin"], "best_margin": ri["best_margin"],
                    "off_top_reason": r["Why not top 3?"] or None, "note": str(r["Note"] or "").strip() or None,
                    "po_task_id": task_id, "marked_by": st.session_state.name, "marked_at": now_s}).eq("id", l["id"]).execute()
            st.session_state["os_ver"] = ver + 1
            st.session_state["os_msg2"] = f"✅ Order saved — {dist}: {n} SKUs, {_qty_txt(strips)} strips"
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

def _mark_not_ordered(area, d, pending, live, by_id):
    st.caption("Medicines you are NOT ordering — pick a reason for each. Suggested reasons are pre-filled; check them before saving.")
    if pending:
        rows = [{"id": l["id"], "Rnd": l.get("round"), "Medicine": l.get("item_name", ""), "Pack": l.get("pack_size", ""),
                 "Type": l.get("item_type", ""), "Med Type": l.get("med_type", ""),
                 "Stock": _qty_txt(l.get("closing_strip")), "Order": _qty_txt(l.get("order_qty")),
                 "Best #1": _best_txt(l), "🔁": _repeat_txt(l, by_id),
                 "Reason": _suggest_reason(l), "Note": "", "_mt": _mt_sort(l.get("med_type"))} for l in pending]
        rows.sort(key=lambda r: (r["Reason"] == "", r["_mt"], r["Medicine"]))
        df = pd.DataFrame(rows).drop(columns=["_mt"])
        ver = st.session_state.get("os_nver", 0)
        ed = st.data_editor(df, key=f"os_ned_{ver}", hide_index=True, width='stretch',
                            disabled=[c for c in df.columns if c not in ("Reason", "Note")],
                            column_config={"id": None,
                                           "Reason": st.column_config.SelectboxColumn("Reason", options=[""] + NOT_ORDERED_REASONS)})
        chosen = ed[ed["Reason"].fillna("") != ""]
        if st.button(f"💾 Save {len(chosen)} as Not ordered", type="primary", key="os_nsave",
                     disabled=len(chosen) == 0, width='stretch'):
            bad = [r["Medicine"] for _, r in chosen.iterrows() if r["Reason"].startswith("H)") and not str(r["Note"] or "").strip()]
            if bad:
                st.error("Write a note for 'Other': " + ", ".join(bad[:10]))
                return
            now_s = now_iso()
            try:
                for _, r in chosen.iterrows():
                    supabase.table("order_sheet_lines").update({
                        "status": "Not Ordered", "not_ordered_reason": r["Reason"],
                        "note": str(r["Note"] or "").strip() or None,
                        "marked_by": st.session_state.name, "marked_at": now_s}).eq("id", int(r["id"])).execute()
                log_simple_task("Order Sheet - Not Ordered", {"area": area, "lines": str(len(chosen)), "sheet_date": d})
                st.session_state["os_nver"] = ver + 1
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.success("🎉 Nothing left to mark.")
    done = [l for l in live if l.get("status") == "Not Ordered"]
    if done:
        with st.expander(f"↩️ Undo — {len(done)} medicine(s) marked Not ordered"):
            opts = {f"{l.get('item_name')} — {l.get('not_ordered_reason')} ({l.get('marked_by','')})": l["id"] for l in done}
            back = st.multiselect("Move back to pending", list(opts.keys()), key="os_undo")
            if st.button("↩️ Move back", key="os_undo_go", disabled=not back):
                for k in back:
                    supabase.table("order_sheet_lines").update({"status": "Pending", "not_ordered_reason": None,
                                                                "note": None, "marked_by": None, "marked_at": None})\
                        .eq("id", opts[k]).execute()
                st.rerun()


# ── NORMAL ORDER REPORT (admin / manager) ─────────────────────────────────────
def show_order_sheet_report(kp="osr"):
    st.subheader("🛒 Normal Orders — sheet vs ordered")
    c1, c2 = st.columns(2)
    with c1: day = st.date_input("Sheet date", value=today_ist(), key=f"{kp}_day")
    with c2: area = st.selectbox("Area", ["All Areas"] + load_areas(), key=f"{kp}_area")
    d = day.strftime("%Y-%m-%d")
    try:
        all_lines = load_sheet_lines(area, d)
        sheets = supabase.table("order_sheets").select("*").eq("sheet_date", d).execute().data or []
    except Exception as e:
        st.error(f"Could not load — has normal_order_setup.sql been run in Supabase? ({e})")
        return
    by_id = {l["id"]: l for l in all_lines}
    ls = [l for l in all_lines if l.get("status") != "Superseded"]
    if not ls:
        st.info("No order sheet uploaded for this date / area.")
        return
    S = lambda l: l.get("status")
    ordered = [l for l in ls if S(l) == "Ordered"]
    notord = [l for l in ls if S(l) == "Not Ordered"]
    pend = [l for l in ls if S(l) == "Pending"]
    rep = [l for l in ls if l.get("repeat_of")]
    notbest = [l for l in ordered if l.get("best_margin") is not None and (l.get("dist_rank") or 99) != 1]
    m = st.columns(6)
    with m[0]: st.metric("📋 To order", len(ls))
    with m[1]: st.metric("✅ Ordered", len(ordered), f"{round(100 * len(ordered) / len(ls))}%", delta_color="off")
    with m[2]: st.metric("❌ Not ordered", len(notord))
    with m[3]: st.metric("⏳ Not marked", len(pend))
    with m[4]: st.metric("🔁 Came again", len(rep), help="Medicine appeared again in a later round after it was ordered")
    with m[5]: st.metric("⚠️ Not best distributor", len(notbest))

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**❌ Not ordered — reasons**")
        rs = {}
        for l in notord:
            rs[l.get("not_ordered_reason") or "No reason"] = rs.get(l.get("not_ordered_reason") or "No reason", 0) + 1
        st.markdown("\n".join(f"- {r}: **{rs[r]}**" for r in NOT_ORDERED_REASONS + [k for k in rs if k not in NOT_ORDERED_REASONS] if rs.get(r))
                    or "_None_")
    with c2:
        st.markdown("**By Med Type**")
        mts = sorted(set(l.get("med_type") or "—" for l in ls), key=_mt_sort)
        mdf = pd.DataFrame([{"Med Type": t,
                             "To order": sum(1 for l in ls if (l.get("med_type") or "—") == t),
                             "Ordered": sum(1 for l in ordered if (l.get("med_type") or "—") == t),
                             "Not ordered": sum(1 for l in notord if (l.get("med_type") or "—") == t),
                             "Not marked": sum(1 for l in pend if (l.get("med_type") or "—") == t)} for t in mts])
        mdf["% Ordered"] = (100 * mdf["Ordered"] / mdf["To order"]).round(0).astype(int).astype(str) + "%"
        st.dataframe(mdf, hide_index=True, width='stretch')

    st.markdown("**👤 By person**")
    people = sorted(set(l.get("marked_by") for l in ls if l.get("marked_by")))
    if people:
        pr = []
        for p in people:
            o = [l for l in ordered if l.get("marked_by") == p]
            lost = [(l["best_margin"] - (l.get("dist_margin") or 0)) for l in o
                    if l.get("best_margin") is not None and l.get("dist_margin") is not None and (l.get("dist_rank") or 99) != 1]
            pr.append({"Person": p, "SKUs ordered": len(o), "Strips": _qty_txt(sum(float(l.get("ordered_qty") or 0) for l in o)),
                       "Distributors": len(set(l.get("distributor") for l in o)),
                       "Not ordered marked": sum(1 for l in notord if l.get("marked_by") == p),
                       "Not best dist": len(lost), "Avg margin lost": f"{round(sum(lost) / len(lost), 2)}%" if lost else ""})
        st.dataframe(pd.DataFrame(pr), hide_index=True, width='stretch')
    else:
        st.caption("Nothing marked yet.")

    st.markdown("**📤 Uploads (rounds)**")
    sh = [s for s in sheets if area == "All Areas" or s.get("area") == area]
    if sh:
        st.dataframe(pd.DataFrame([{
            "Area": s.get("area"), "Round": s.get("round"),
            "Uploaded": (to_ist(s.get("uploaded_at")) or now_ist()).strftime("%I:%M %p"), "By": s.get("uploaded_by"),
            "Medicines": s.get("lines"),
            "Ordered": sum(1 for l in ordered if l.get("sheet_id") == s["id"]),
            "Not ordered": sum(1 for l in notord if l.get("sheet_id") == s["id"]),
            "Moved to next round": sum(1 for l in all_lines if l.get("sheet_id") == s["id"] and S(l) == "Superseded"),
            "Not marked": sum(1 for l in pend if l.get("sheet_id") == s["id"])}
            for s in sorted(sh, key=lambda s: (s.get("area"), s.get("round")))]), hide_index=True, width='stretch')

    if notbest:
        st.markdown("**⚠️ Not ordered from Best Dist 1**")
        nb = [{"Medicine": l.get("item_name"), "Area": l.get("area"), "Ordered from": f"{l.get('distributor')} " + (f"(#{l['dist_rank']})" if l.get("dist_rank") else "(not in sheet)"),
               "Margin": f"{l.get('dist_margin')}%" if l.get("dist_margin") is not None else "",
               "Best was": _best_txt(l),
               "Lost": f"-{round(l['best_margin'] - l['dist_margin'], 2)}%" if l.get("dist_margin") is not None else "",
               "Why": l.get("off_top_reason") or ("(within top 3)" if (l.get("dist_rank") or 99) <= 3 else ""),
               "Note": l.get("note") or "", "By": l.get("marked_by")}
              for l in sorted(notbest, key=lambda l: -((l.get("best_margin") or 0) - (l.get("dist_margin") or 0)))]
        st.dataframe(pd.DataFrame(nb), hide_index=True, width='stretch')

    st.markdown("**📋 Every medicine**")
    search = st.text_input("🔍 Search medicine / distributor / person", key=f"{kp}_q").strip().lower()
    stat_f = st.multiselect("Status", ["Ordered", "Not Ordered", "Pending"], key=f"{kp}_st", placeholder="All")
    icon = {"Ordered": "✅ Ordered", "Not Ordered": "❌ Not ordered", "Pending": "⏳ Not marked"}
    rows = []
    for l in sorted(ls, key=lambda l: (l.get("area"), _mt_sort(l.get("med_type")), l.get("item_name", ""))):
        if stat_f and S(l) not in stat_f:
            continue
        oq, q = float(l.get("order_qty") or 0), l.get("ordered_qty")
        qflag = ""
        if q is not None and oq and (float(q) < 0.5 * oq or float(q) > 2 * oq):
            qflag = " ⚠️"
        r = {"Area": l.get("area"), "Rnd": l.get("round"), "Medicine": l.get("item_name"), "Pack": l.get("pack_size"),
             "Type": l.get("item_type"), "Med Type": l.get("med_type"), "Stock": _qty_txt(l.get("closing_strip")),
             "Order": _qty_txt(oq), "Status": icon.get(S(l), S(l)),
             "Ordered Qty": (_qty_txt(q) + qflag) if q is not None else "",
             "Distributor": l.get("distributor") or "", "Rank": f"#{l['dist_rank']}" if l.get("dist_rank") else "",
             "Margin": f"{l.get('dist_margin')}%" if l.get("dist_margin") is not None else "",
             "Best #1": _best_txt(l),
             "Reason": l.get("not_ordered_reason") or l.get("off_top_reason") or "", "Note": l.get("note") or "",
             "🔁": _repeat_txt(l, by_id), "By": l.get("marked_by") or "",
             "At": to_ist(l.get("marked_at")).strftime("%I:%M %p") if to_ist(l.get("marked_at")) else ""}
        if search and search not in " ".join(str(v) for v in r.values()).lower():
            continue
        rows.append(r)
    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, width='stretch')
    st.caption("⚠️ next to Ordered Qty = less than half or more than double the sheet's Order qty.")
    if len(df):
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df.to_excel(w, index=False, sheet_name="Medicines")
            mdf.to_excel(w, index=False, sheet_name="By Med Type")
        st.download_button("⬇️ Download Excel", buf.getvalue(), f"normal-orders-{d}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"{kp}_dl")


# ── MY DAY (admin's own planner, focus timer, interruption log) ───────────────
MD_SLOTS = ["Any time"] + [datetime(2000, 1, 1, h, m).strftime("%I:%M %p") for h in range(6, 24) for m in (0, 30)]
MD_KINDS = ["📞 Call", "💬 WhatsApp", "🚶 Walk-in", "📧 Other"]
MD_CATS = ["🎯 Deep work", "👥 Team", "📞 Calls / follow-up", "🧾 Admin / accounts", "🏪 Store visit", "🙋 Personal"]
MD_DEFAULT_WINDOWS = ["11:30 AM", "03:00 PM", "06:00 PM"]

def _md_slot_key(s):
    try:
        return datetime.strptime(s, "%I:%M %p").time()
    except Exception:
        return datetime.max.time()

def _md_secs(t, now=None):
    s = int(t.get("actual_secs") or 0)
    if t.get("status") == "Running" and to_ist(t.get("run_started_at")):
        s += max(0, int(((now or now_ist()) - to_ist(t.get("run_started_at"))).total_seconds()))
    return s

def _md_load(person, day):
    tasks = supabase.table("my_day_tasks").select("*").eq("person", person).eq("day", day).execute().data or []
    ints = supabase.table("my_day_interruptions").select("*").eq("person", person).eq("day", day).execute().data or []
    notes = supabase.table("my_day_notes").select("*").eq("person", person).eq("day", day).execute().data or []
    tasks.sort(key=lambda t: (_md_slot_key(t.get("slot") or ""), int(t.get("id") or 0)))
    ints.sort(key=lambda i: str(i.get("at") or ""))
    return tasks, ints, notes

def _md_settings(person):
    try:
        r = supabase.table("my_day_settings").select("*").eq("person", person).execute().data or []
        if r:
            return (r[0].get("call_windows") or MD_DEFAULT_WINDOWS), int(r[0].get("window_mins") or 20)
    except Exception:
        pass
    return MD_DEFAULT_WINDOWS, 20

def _md_window_status(windows, mins, now=None):
    now = now or now_ist()
    starts = []
    for w in windows:
        try:
            starts.append(IST.localize(datetime.combine(now.date(), datetime.strptime(w, "%I:%M %p").time())))
        except Exception:
            pass
    from datetime import timedelta
    for s in sorted(starts):
        if s <= now < s + timedelta(minutes=mins):
            return "now", s + timedelta(minutes=mins)
    nxt = [s for s in sorted(starts) if s > now]
    return ("next", nxt[0]) if nxt else ("none", None)

def _md_pause(t, status="Paused"):
    upd = {"status": status, "actual_secs": _md_secs(t), "run_started_at": None}
    if status == "Done":
        upd["ended_at"] = now_iso()
    supabase.table("my_day_tasks").update(upd).eq("id", t["id"]).execute()

def _md_start(t, tasks):
    for x in tasks:
        if x.get("status") == "Running" and x["id"] != t["id"]:
            _md_pause(x)
    upd = {"status": "Running", "run_started_at": now_iso()}
    if not t.get("started_at"):
        upd["started_at"] = now_iso()
    supabase.table("my_day_tasks").update(upd).eq("id", t["id"]).execute()

def _md_close_int(i):
    t = to_ist(i.get("at"))
    mins = max(1, round((now_ist() - t).total_seconds() / 60)) if t else None
    supabase.table("my_day_interruptions").update({"ended_at": now_iso(), "mins": mins}).eq("id", i["id"]).execute()

def _md_move_unfinished(person, from_day, to_day):
    old = supabase.table("my_day_tasks").select("*").eq("person", person).eq("day", from_day).execute().data or []
    n = 0
    for t in old:
        if t.get("status") in ("Planned", "Paused", "Running"):
            left = max(5, int(t.get("planned_mins") or 30) - _md_secs(t) // 60)
            supabase.table("my_day_tasks").insert({
                "person": person, "day": to_day, "title": t.get("title"), "category": t.get("category"),
                "slot": t.get("slot") or "Any time", "planned_mins": left, "top3": bool(t.get("top3")),
                "status": "Planned", "actual_secs": 0, "carried_from": t["id"]}).execute()
            if t.get("status") == "Running":
                _md_pause(t)
            supabase.table("my_day_tasks").update({"status": "Moved"}).eq("id", t["id"]).execute()
            n += 1
    return n

def _md_team_names():
    return sorted(u.get("name") for u in (load_users() or {}).values() if u.get("name"))

def show_my_day(kp="md"):
    person = st.session_state.name
    st.subheader("🎯 My Day")
    try:
        windows, wmins = _md_settings(person)
        tasks, ints, notes = _md_load(person, date_str())
    except Exception as e:
        st.error(f"Could not load My Day — has my_day_setup.sql been run in Supabase? ({e})")
        return
    now = now_ist()
    running = next((t for t in tasks if t.get("status") == "Running"), None)
    open_int = next((i for i in ints if not i.get("ended_at")), None)
    live = [t for t in tasks if t.get("status") != "Moved"]
    focus = sum(_md_secs(t, now) for t in live)
    stars = [t for t in live if t.get("top3")]
    wst, wtime = _md_window_status(windows, wmins, now)

    m = st.columns(5)
    with m[0]: st.metric("✅ Done", f"{sum(1 for t in live if t.get('status') == 'Done')} / {len(live)}")
    with m[1]: st.metric("⭐ Top 3 done", f"{sum(1 for t in stars if t.get('status') == 'Done')} / {len(stars)}")
    with m[2]: st.metric("⏱️ Focus time", fmt_secs(focus))
    with m[3]: st.metric("📞 Interruptions", len(ints), f"{sum(int(i.get('mins') or 0) for i in ints)} min", delta_color="off")
    with m[4]:
        if wst == "now":
            st.metric("📞 Call window", "NOW", f"until {wtime.strftime('%I:%M %p')}", delta_color="off")
        elif wst == "next":
            st.metric("📵 Focus — next call window", wtime.strftime("%I:%M %p"))
        else:
            st.metric("📞 Call windows", "Done for today")

    view = st.radio("View", ["▶️ Today", "📝 Plan", "📊 Review", "📈 Weekly", "⚙️ Call windows"], horizontal=True,
                    key=f"{kp}_view", label_visibility="collapsed")
    if view == "▶️ Today":
        _md_today(kp, person, tasks, ints, notes, running, open_int, now)
    elif view == "📝 Plan":
        _md_plan(kp, person, tasks)
    elif view == "📊 Review":
        _md_review(kp, person)
    elif view == "📈 Weekly":
        _md_weekly(kp, person)
    else:
        _md_windows(kp, person, windows, wmins)

def _md_int_form(kp, running):
    with st.form(f"{kp}_int_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1: kind = st.radio("Type", MD_KINDS, key=f"{kp}_int_kind")
        with c2:
            who = st.selectbox("Who", ["—"] + _md_team_names() + ["Customer", "Distributor", "Family", "Other"], key=f"{kp}_int_who")
            who_other = st.text_input("…or name", key=f"{kp}_int_who2")
        with c3:
            why = st.text_input("Why? (one or two words — e.g. bill status, payment, stock)", key=f"{kp}_int_why")
            urgent = st.checkbox("Really needed me now", key=f"{kp}_int_urgent",
                                 help="Untick if it could have waited for a call window or been answered by the app")
        if st.form_submit_button("⏸️ Log & pause" if running else "📝 Log", type="primary"):
            if running:
                _md_pause(running)
            supabase.table("my_day_interruptions").insert({
                "person": st.session_state.name, "day": date_str(), "at": now_iso(),
                "kind": kind, "who": who_other.strip() or (who if who != "—" else ""), "why": why.strip(),
                "urgent": urgent, "task_id": running["id"] if running else None}).execute()
            st.session_state[f"{kp}_int_open"] = False
            st.rerun()

def _md_today(kp, person, tasks, ints, notes, running, open_int, now):
    # current state banner
    if open_int:
        back = next((t for t in tasks if t["id"] == open_int.get("task_id")), None)
        st.warning(f"📞 **On interruption since {to_ist(open_int['at']).strftime('%I:%M %p')}** "
                   f"({fmt_age(age_mins(open_int['at'], now))}) — {open_int.get('kind','')} {open_int.get('who','')}"
                   + (f" · {open_int.get('why')}" if open_int.get("why") else ""))
        c1, c2 = st.columns(2)
        with c1:
            if back and back.get("status") != "Done" and st.button(f"▶️ Back to: {back.get('title')}", key=f"{kp}_back",
                                                                  type="primary", width='stretch'):
                _md_close_int(open_int)
                _md_start(back, tasks)
                st.rerun()
        with c2:
            if st.button("✔️ Interruption finished", key=f"{kp}_int_done", width='stretch'):
                _md_close_int(open_int)
                st.rerun()
    elif running:
        secs = _md_secs(running, now)
        plan = int(running.get("planned_mins") or 0) * 60
        over = plan and secs > plan
        st.success(f"🎯 **FOCUS: {running.get('title')}** — {fmt_secs(secs)}"
                   + (f" of {running.get('planned_mins')} min planned" if plan else "")
                   + (" · ⚠️ over plan" if over else ""))
        if plan:
            st.progress(min(1.0, secs / plan))
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("✅ Done", key=f"{kp}_done", type="primary", width='stretch'):
                _md_pause(running, "Done")
                st.session_state["mission_done"] = secs
                st.rerun()
        with c2:
            if st.button("⏸️ Pause", key=f"{kp}_pause", width='stretch'):
                _md_pause(running)
                st.rerun()
        with c3:
            if st.button("📞 Interrupted!", key=f"{kp}_int_btn", width='stretch'):
                st.session_state[f"{kp}_int_open"] = True
    else:
        st.info("Nothing running. Pick a task below and press ▶️ — start with a ⭐ one.")

    if not open_int and (st.session_state.get(f"{kp}_int_open") or not running):
        with st.expander("📞 Log an interruption", expanded=bool(st.session_state.get(f"{kp}_int_open"))):
            _md_int_form(kp, running)

    # task list
    live = [t for t in tasks if t.get("status") != "Moved"]
    if not live:
        st.info("No plan for today yet — open 📝 Plan and add your tasks (top 3 first).")
    else:
        st.markdown("**📋 Today's plan**")
        icon = {"Planned": "⚪", "Running": "🟢", "Paused": "⏸️", "Done": "✅"}
        for t in live:
            secs = _md_secs(t, now)
            c1, c2, c3 = st.columns([6, 2, 1])
            with c1:
                st.markdown(f"{icon.get(t.get('status'), '⚪')} {'⭐ ' if t.get('top3') else ''}**{t.get('title')}** "
                            f"· {t.get('slot') or 'Any time'} · {t.get('category') or ''}")
            with c2:
                st.markdown(f"{fmt_secs(secs) if secs else '—'} / {t.get('planned_mins')} min")
            with c3:
                if t.get("status") in ("Planned", "Paused") and st.button("▶️", key=f"{kp}_start_{t['id']}",
                                                                         help="Start (pauses whatever is running)"):
                    if open_int:
                        _md_close_int(open_int)
                    _md_start(t, tasks)
                    st.rerun()

    # parking lot
    st.markdown("**🅿️ Parking lot** — a thought pops up? Write it here and go back to your task.")
    with st.form(f"{kp}_note_form", clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        with c1: txt = st.text_input("Note", key=f"{kp}_note", label_visibility="collapsed", placeholder="e.g. check Sehgal payment")
        with c2: add = st.form_submit_button("➕ Park it")
        if add and txt.strip():
            supabase.table("my_day_notes").insert({"person": person, "day": date_str(), "text": txt.strip(), "done": False}).execute()
            st.rerun()
    for n in sorted(notes, key=lambda n: (bool(n.get("done")), n["id"])):
        c1, c2 = st.columns([6, 1])
        with c1: st.markdown(("~~" + n["text"] + "~~") if n.get("done") else f"• {n['text']}")
        with c2:
            if not n.get("done") and st.button("✔️", key=f"{kp}_nd_{n['id']}", help="Done"):
                supabase.table("my_day_notes").update({"done": True}).eq("id", n["id"]).execute()
                st.rerun()

def _md_plan(kp, person, tasks):
    from datetime import timedelta
    st.caption("Plan in 5 minutes: pick your ⭐ top 3 (the tasks that make today a good day), give each a time slot and an estimate.")
    live = [t for t in tasks if t.get("status") != "Moved"]
    y = (today_ist() - timedelta(days=1)).strftime("%Y-%m-%d")
    c1, c2 = st.columns([3, 1])
    with c2:
        if st.button("↪️ Bring yesterday's unfinished", key=f"{kp}_carry", width='stretch'):
            n = _md_move_unfinished(person, y, date_str())
            st.session_state[f"{kp}_msg"] = f"↪️ {n} unfinished task(s) brought from yesterday" if n else "Nothing unfinished yesterday 👍"
            st.rerun()
    msg = st.session_state.pop(f"{kp}_msg", None)
    if msg:
        st.success(msg)
    with st.form(f"{kp}_add", clear_on_submit=True):
        c1, c2, c3, c4, c5 = st.columns([4, 2, 2, 1, 1])
        with c1: title = st.text_input("Task *", placeholder="e.g. Review Normal Orders report")
        with c2: cat = st.selectbox("Type", MD_CATS)
        with c3: slot = st.selectbox("Time slot", MD_SLOTS)
        with c4: mins = st.number_input("Mins", min_value=5, max_value=480, value=30, step=5)
        with c5:
            st.write("")
            top = st.checkbox("⭐ Top 3")
        if st.form_submit_button("➕ Add", type="primary"):
            if not title.strip():
                st.error("Write the task.")
            else:
                supabase.table("my_day_tasks").insert({
                    "person": person, "day": date_str(), "title": title.strip(), "category": cat, "slot": slot,
                    "planned_mins": int(mins), "top3": top, "status": "Planned", "actual_secs": 0}).execute()
                st.rerun()
    if not live:
        return
    n_star = sum(1 for t in live if t.get("top3"))
    total = sum(int(t.get("planned_mins") or 0) for t in live)
    st.markdown(f"**{len(live)} tasks · {total // 60}h {total % 60}m planned · ⭐ {n_star}**"
                + (" — ⚠️ more than 3 stars: a top 3 only works if it's 3" if n_star > 3 else ""))
    if total > 6 * 60:
        st.warning("⚠️ More than 6 hours planned. Calls and team work will take time too — plan less, finish more.")
    df = pd.DataFrame([{"id": t["id"], "⭐": bool(t.get("top3")), "Task": t.get("title"), "Type": t.get("category") or MD_CATS[0],
                        "Slot": t.get("slot") or "Any time", "Mins": int(t.get("planned_mins") or 0),
                        "Status": t.get("status"), "🗑️": False} for t in live])
    ver = st.session_state.get(f"{kp}_pver", 0)
    ed = st.data_editor(df, key=f"{kp}_ped_{ver}", hide_index=True, width='stretch', disabled=["Status"],
                        column_config={"id": None, "⭐": st.column_config.CheckboxColumn("⭐"),
                                       "Type": st.column_config.SelectboxColumn("Type", options=MD_CATS),
                                       "Slot": st.column_config.SelectboxColumn("Slot", options=MD_SLOTS),
                                       "Mins": st.column_config.NumberColumn("Mins", min_value=5, max_value=480, step=5),
                                       "🗑️": st.column_config.CheckboxColumn("🗑️ Delete")})
    old = {r["id"]: r for r in df.to_dict("records")}
    ch = [r for r in ed.to_dict("records") if any(r[k] != old[r["id"]][k] for k in ("⭐", "Task", "Type", "Slot", "Mins", "🗑️"))]
    if st.button(f"💾 Save plan changes ({len(ch)})", key=f"{kp}_psave", disabled=not ch):
        for r in ch:
            if r["🗑️"]:
                supabase.table("my_day_tasks").delete().eq("id", r["id"]).execute()
            else:
                supabase.table("my_day_tasks").update({"top3": bool(r["⭐"]), "title": r["Task"], "category": r["Type"],
                                                       "slot": r["Slot"], "planned_mins": int(r["Mins"])}).eq("id", r["id"]).execute()
        st.session_state[f"{kp}_pver"] = ver + 1
        st.rerun()

def _md_count(items, key):
    out = {}
    for i in items:
        k = (i.get(key) or "").strip() or "—"
        out[k] = out.get(k, 0) + 1
    return sorted(out.items(), key=lambda kv: -kv[1])

def _md_review(kp, person):
    from datetime import timedelta
    day = st.date_input("Day", value=today_ist(), key=f"{kp}_rday")
    d = day.strftime("%Y-%m-%d")
    tasks, ints, _ = _md_load(person, d)
    live = [t for t in tasks if t.get("status") != "Moved"]
    if not live and not ints:
        st.info("Nothing recorded for this day.")
        return
    planned = sum(int(t.get("planned_mins") or 0) for t in live) * 60
    actual = sum(_md_secs(t) for t in live)
    done_actual = sum(_md_secs(t) for t in live if t.get("status") == "Done")
    done_plan = sum(int(t.get("planned_mins") or 0) for t in live if t.get("status") == "Done") * 60
    stars = [t for t in live if t.get("top3")]
    int_min = sum(int(i.get("mins") or 0) for i in ints)
    avoid = sum(1 for i in ints if i.get("urgent") is False)
    m = st.columns(5)
    with m[0]: st.metric("✅ Tasks done", f"{sum(1 for t in live if t.get('status') == 'Done')} / {len(live)}")
    with m[1]: st.metric("⭐ Top 3 done", f"{sum(1 for t in stars if t.get('status') == 'Done')} / {len(stars)}")
    with m[2]: st.metric("⏱️ Focus time", fmt_secs(actual), f"planned {fmt_secs(planned)}", delta_color="off")
    with m[3]: st.metric("📞 Interruptions", len(ints), f"{int_min} min lost", delta_color="off")
    with m[4]: st.metric("🙅 Could have waited", avoid, help="Interruptions you marked as not really needing you then")
    if done_plan:
        ratio = done_actual / done_plan
        st.caption(f"Finished tasks took **{round(ratio * 100)}%** of the time you estimated"
                   + (" — you're under-estimating; add a buffer." if ratio > 1.3 else " — good estimates 👍" if ratio >= 0.8 else " — you over-estimate; you can plan more."))
    if live:
        rows = []
        for t in live:
            a = _md_secs(t)
            p = int(t.get("planned_mins") or 0)
            rows.append({"⭐": "⭐" if t.get("top3") else "", "Task": t.get("title"), "Type": t.get("category"),
                         "Slot": t.get("slot"),
                         "Started": to_ist(t.get("started_at")).strftime("%I:%M %p") if to_ist(t.get("started_at")) else "",
                         "Planned": f"{p} min", "Actual": fmt_secs(a) if a else "—",
                         "Diff": (f"+{round(a / 60 - p)} min" if a / 60 > p else f"{round(a / 60 - p)} min") if a else "",
                         "Interruptions": sum(1 for i in ints if i.get("task_id") == t["id"]),
                         "Status": t.get("status")})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch')
    if ints:
        st.markdown("**📞 Interruptions**")
        tmap = {t["id"]: t.get("title") for t in tasks}
        st.dataframe(pd.DataFrame([{"Time": to_ist(i.get("at")).strftime("%I:%M %p") if to_ist(i.get("at")) else "",
                                    "Type": i.get("kind"), "Who": i.get("who"), "Why": i.get("why"),
                                    "Mins": i.get("mins") or "", "Needed me?": "✅" if i.get("urgent") else "🙅 could wait",
                                    "During": tmap.get(i.get("task_id"), "")} for i in ints]),
                     hide_index=True, width='stretch')
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Who interrupted most**")
            st.markdown("\n".join(f"- {k}: **{v}**" for k, v in _md_count(ints, "who")[:8]))
        with c2:
            st.markdown("**Why**")
            st.markdown("\n".join(f"- {k}: **{v}**" for k, v in _md_count(ints, "why")[:8]))
    unfinished = [t for t in live if t.get("status") in ("Planned", "Paused", "Running")]
    if d == date_str() and unfinished:
        if st.button(f"➡️ Move {len(unfinished)} unfinished task(s) to tomorrow", key=f"{kp}_tomorrow"):
            n = _md_move_unfinished(person, d, (today_ist() + timedelta(days=1)).strftime("%Y-%m-%d"))
            st.success(f"➡️ {n} task(s) moved to tomorrow")

def _md_weekly(kp, person):
    from datetime import timedelta
    start = (today_ist() - timedelta(days=13)).strftime("%Y-%m-%d")
    tasks = fetch_all("my_day_tasks", lambda q: q.eq("person", person).gte("day", start))
    ints = fetch_all("my_day_interruptions", lambda q: q.eq("person", person).gte("day", start))
    if not tasks and not ints:
        st.info("No data yet — use My Day for a few days and the trend appears here.")
        return
    def day_stats(d):
        ts = [t for t in tasks if t.get("day") == d and t.get("status") != "Moved"]
        its = [i for i in ints if i.get("day") == d]
        st_ = [t for t in ts if t.get("top3")]
        return {"Day": datetime.strptime(d, "%Y-%m-%d").strftime("%a %d %b"),
                "Planned": len(ts), "Done": sum(1 for t in ts if t.get("status") == "Done"),
                "⭐ Top 3 done": f"{sum(1 for t in st_ if t.get('status') == 'Done')}/{len(st_)}" if st_ else "",
                "Focus hrs": round(sum(_md_secs(t) for t in ts) / 3600, 1),
                "Interruptions": len(its), "Mins lost": sum(int(i.get("mins") or 0) for i in its),
                "Could have waited": sum(1 for i in its if i.get("urgent") is False)}
    days = [(today_ist() - timedelta(days=k)).strftime("%Y-%m-%d") for k in range(13, -1, -1)]
    rows = [day_stats(d) for d in days]
    this, last = rows[7:], rows[:7]
    tot = lambda rs, k: sum(r[k] for r in rs)
    m = st.columns(4)
    with m[0]: st.metric("⏱️ Focus hrs (7 days)", round(tot(this, "Focus hrs"), 1),
                         round(tot(this, "Focus hrs") - tot(last, "Focus hrs"), 1))
    with m[1]: st.metric("✅ Tasks done (7 days)", tot(this, "Done"), tot(this, "Done") - tot(last, "Done"))
    with m[2]: st.metric("📞 Interruptions (7 days)", tot(this, "Interruptions"),
                         tot(this, "Interruptions") - tot(last, "Interruptions"), delta_color="inverse")
    with m[3]: st.metric("⏳ Mins lost (7 days)", tot(this, "Mins lost"), tot(this, "Mins lost") - tot(last, "Mins lost"),
                         delta_color="inverse")
    st.caption("Change is vs the 7 days before. Green = better.")
    st.dataframe(pd.DataFrame([r for r in this if r["Planned"] or r["Interruptions"]] or this),
                 hide_index=True, width='stretch')
    week_ints = [i for i in ints if i.get("day") >= days[7]]
    if week_ints:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Who interrupted most this week**")
            st.markdown("\n".join(f"- {k}: **{v}**" for k, v in _md_count(week_ints, "who")[:10]))
        with c2:
            st.markdown("**Top reasons this week**")
            st.markdown("\n".join(f"- {k}: **{v}**" for k, v in _md_count(week_ints, "why")[:10]))
        st.caption("💡 The same reason again and again? Fix it once — a rule, a WhatsApp group, or an app screen — instead of answering it daily.")

def _md_windows(kp, person, windows, wmins):
    st.caption("Fixed times when you return calls and reply on WhatsApp. Between them your phone is on Do Not Disturb "
               "(starred contacts only; team calls twice for a real emergency).")
    with st.form(f"{kp}_win"):
        sel = st.multiselect("Call windows", MD_SLOTS[1:], default=[w for w in windows if w in MD_SLOTS], key=f"{kp}_wsel")
        mins = st.number_input("Minutes per window", min_value=5, max_value=90, value=wmins, step=5, key=f"{kp}_wmins")
        if st.form_submit_button("💾 Save", type="primary"):
            sel = sorted(sel, key=_md_slot_key)
            supabase.table("my_day_settings").upsert({"person": person, "call_windows": sel, "window_mins": int(mins)},
                                                     on_conflict="person").execute()
            st.success("✅ Saved")
            st.rerun()



STOCK_MENU = [
    ("✅ Processing", [("✔️ Bill Cross Check", "crosscheck"), ("📤 Bill Upload", "upload")]),
    ("📥 Incoming Stock", [("📒 Register Entry", "register"), ("📦 Receive Porter", "receive"),
                          ("🧾 Bills Register", "bills"), ("✏️ Edit Entry", "edit")]),
    ("🔧 Other Work", [("↩️ Purchase Return", "return"), ("🧹 Rack Cleaning", "rack"),
                      ("📊 Inventory Check", "inventory"), ("✏️ Other", "other")]),
]

ARR_STAGE = {
    "Pending": "🕐 Ordered — at distributor",
    "Porter Booked": "🚚 On the way", "Picked Up": "🚚 On the way", "Picked": "🚚 On the way",
    "Handed Over": "🚚 On the way", "Delivered": "🚚 On the way",
    "Reached Warehouse": "📦 Arrived — check bill",
    "Bill Cross Checked": "✔️ Checked — upload bill",
}

def show_incoming_arrangements(area, full=False):
    """Stock team: which arrangement orders are coming, from which distributor (no pickup timeline)"""
    from datetime import timedelta
    since = (today_ist() - timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        arrs = supabase.table("arrangements").select("*").gte("order_placed_date", since).execute().data or []
    except Exception as e:
        st.error(f"Could not load arrangements ({e})")
        return
    if area and area != "All Areas":
        arrs = [a for a in arrs if a.get("area") == area]
    DONE = ("Bill Uploaded", "Stock Placed", "Completed")
    open_ = [a for a in arrs if a.get("status") not in DONE]
    done_today = [a for a in arrs if a.get("status") in DONE and a.get("order_placed_date") == date_str()]
    st.markdown(f"#### 📦 Incoming arrangement orders — {area}")
    if not open_:
        st.success("No arrangement orders pending." + (f" ✅ {len(done_today)} done today." if done_today else ""))
        return
    # customer delivery deadline of the medicines in each arrangement
    now = now_ist()
    meds_by_arr = {}
    try:
        nos = [a.get("arrangement_no") for a in open_ if a.get("arrangement_no")]
        links = []
        if nos:
            links = supabase.table("arrangement_lines").select("arrangement_no,line_id,item_name,order_no")\
                .in_("arrangement_no", nos).execute().data or []
        ids = list({l["line_id"] for l in links if l.get("line_id")})
        cl = {}
        for ch in _chunks(ids, 200):
            for c in supabase.table("customer_order_lines").select("id,scheduled_date,delivery_time,customer_name")\
                    .in_("id", ch).execute().data or []:
                cl[c["id"]] = c
        for l in links:
            c = cl.get(l.get("line_id")) or {}
            meds_by_arr.setdefault(l["arrangement_no"], []).append({**l, **{k: c.get(k) for k in ("scheduled_date", "delivery_time", "customer_name")}})
    except Exception:
        pass

    def due_txt(c):
        di = due_info(c, now)
        if di:
            return di[1], f"{di[0]} {c.get('delivery_time')} ({di[2]})"
        if c.get("scheduled_date"):
            return 10**8, f"📅 {_sched_label(c.get('scheduled_date'))}"
        return 10**9, ""

    order = list(ARR_STAGE.values())
    rows, med_rows = [], []
    for a in open_:
        stage = ARR_STAGE.get(a.get("status"), a.get("status") or "")
        u = a.get("urgency") or "Normal"
        meds = meds_by_arr.get(a.get("arrangement_no"), [])
        dues = sorted(due_txt(m) for m in meds)
        first = dues[0] if dues else (10**9, "")
        for m in meds:
            mins, txt = due_txt(m)
            med_rows.append({"ARR #": a.get("arrangement_no", ""), "Medicine": m.get("item_name", ""),
                             "Customer": m.get("customer_name") or "", "Order #": m.get("order_no") or "",
                             "Deliver by": txt, "Status": stage, "_m": mins})
        rows.append({"": "🔴" if u == "Very Urgent" else "🟡" if u == "Urgent" else "🟢",
                     "ARR #": a.get("arrangement_no", ""), "Distributor": a.get("distributor", ""),
                     "Medicines": a.get("no_medicines", ""), "Status": stage,
                     "Customer deliver by": first[1] + (f" +{len(meds) - 1} more" if len(meds) > 1 and first[1] else ""),
                     "Ordered": (("Yday " if a.get("order_placed_date") != date_str() else "") + str(a.get("order_placed_time") or "")),
                     **({"Area": a.get("area", "")} if area in (None, "", "All Areas") else {}),
                     "_k": (order.index(stage) if stage in order else 99), "_m": first[0]})
    # arrived first (what to process now), then the most urgent customer deadline
    rows.sort(key=lambda r: (-(r["_k"] >= order.index("📦 Arrived — check bill")), r["_m"], -r["_k"], r["ARR #"]))
    st.dataframe(pd.DataFrame(rows).drop(columns=["_k", "_m"]), hide_index=True, width='stretch')
    if med_rows:
        with st.expander(f"💊 Medicine-wise customer delivery times ({len(med_rows)})", expanded=full):
            med_rows.sort(key=lambda r: (r["_m"], r["ARR #"]))
            st.dataframe(pd.DataFrame(med_rows).drop(columns=["_m"]), hide_index=True, width='stretch')
            st.caption("🔴 due within 1 hr or overdue · 🟡 within 3 hrs · 🟢 later. Process 🔴 first.")
    arrived = sum(1 for a in open_ if a.get("status") in ("Reached Warehouse", "Bill Cross Checked"))
    st.caption(f"{len(open_)} open · {arrived} at warehouse to process · ✅ {len(done_today)} done today")

def stock_main_menu():
    """Big buttons on the main screen — works on phones where the sidebar is hidden"""
    st.markdown("### 📋 Select Task")
    for title, items in STOCK_MENU:
        st.markdown(f"**{title}**")
        for i in range(0, len(items), 2):
            cols = st.columns(2)
            for col, (label, key) in zip(cols, items[i:i + 2]):
                with col:
                    if st.button(label, key=f"sm_{key}", width='stretch',
                                 type="primary" if title == "✅ Processing" else "secondary"):
                        st.session_state.stock_active_form = key
                        st.rerun()
    st.divider()

def show_my_performance():
    with st.expander("📊 My Performance Today", expanded=False):
        try:
            perf_resp = supabase.table("daily_tasks").select("*")\
                .eq("person", st.session_state.name)\
                .eq("date", date_str()).execute()
            # finished tasks only (unfinished timers are not counted)
            perf_data = [r for r in (perf_resp.data or []) if r.get("status") != "In Progress"]

            if not perf_data:
                st.info("No tasks completed today yet!")
            else:
                perf_df = pd.DataFrame(perf_data)

                # Summary metrics
                total_tasks    = len(perf_df)
                total_duration = sum([int(float(r.get("duration_mins",0) or 0)) for r in perf_data])
                completed      = len(perf_data)

                c1,c2,c3 = st.columns(3)
                with c1: st.metric("✅ Tasks Completed", completed)
                with c2: st.metric("⏱️ Total Time", fmt_secs(sum(task_secs(r) for r in perf_data)))
                with c3: st.metric("📋 Total Tasks", total_tasks)

                st.divider()

                # Time per task breakdown
                st.markdown("**⏱️ Time Spent Per Task:**")
                task_summary = {}
                for r in perf_data:
                    task = r.get("task_type","")
                    dur  = int(float(r.get("duration_mins",0) or 0))
                    if task not in task_summary:
                        task_summary[task] = {"count": 0, "duration": 0}
                    task_summary[task]["count"]    += 1
                    task_summary[task]["duration"] += dur

                for task, data in task_summary.items():
                    count = data["count"]
                    dur   = data["duration"]
                    avg   = round(dur/count, 1) if count > 0 else 0
                    c1,c2,c3,c4 = st.columns([3,1,1,1])
                    with c1: st.markdown(f"**{task}**")
                    with c2: st.markdown(f"x{count}")
                    with c3: st.markdown(f"⏱️ {dur} mins")
                    with c4: st.markdown(f"Avg: {avg} mins")

                st.divider()

                # Bar chart of time per task
                if task_summary:
                    chart_data = pd.DataFrame([
                        {"Task": k, "Minutes": v["duration"]}
                        for k,v in task_summary.items()
                    ]).set_index("Task")
                    st.bar_chart(chart_data)
        except Exception as e:
            st.error(f"Error: {e}")

# ── WORK AREA LOCK + REFRESH-SAFE SCREENS (mobile) ────────────────────────────
FORM_KEYS = {"Stock": "stock_active_form", "Purchase": "purchase_active_form",
             "Call": "call_active_form", "Delivery": "delivery_active_form"}

def get_area_lock(person):
    """Area chosen by / set for this person today (kept until they log out and log in again)"""
    try:
        rows = supabase.table("work_area_log").select("*").eq("person", person).eq("date", date_str())\
            .order("chosen_at", desc=True).limit(1).execute().data or []
        return rows[0] if rows else None
    except Exception:
        return None

def set_area_lock(person, area, by):
    try:
        supabase.table("work_area_log").insert({"person": person, "area": area, "date": date_str(),
                                                "chosen_at": now_iso(), "set_by": by}).execute()
    except Exception:
        pass

def show_area_status(kp="area"):
    """📍 area line for Stock team (main screen, works on mobile)"""
    area = st.session_state.get("work_area") or ""
    lock = st.session_state.get("area_lock")
    by = (lock or {}).get("set_by")
    st.markdown(f"📍 **{area}**" + (f" · set by {by}" if by and by != st.session_state.name else ""))
    st.caption("To change area: 🚪 Logout and log in again (or ask Admin / Dharmendra / Sachin).")

def sync_form_with_link(team):
    """Keep the open screen in the page link so a refresh / phone reload comes back to it"""
    fk = FORM_KEYS.get(team)
    if not fk:
        return
    try:
        if not st.session_state.get("_form_restored"):
            st.session_state["_form_restored"] = True
            f = st.query_params.get("f")
            if f and not st.session_state.get(fk):
                st.session_state[fk] = f
        cur = st.session_state.get(fk)
        if cur and st.query_params.get("f") != cur:
            st.query_params["f"] = cur
        elif not cur and "f" in st.query_params:
            del st.query_params["f"]
    except Exception:
        pass

def restore_timer(key, task_name=None):
    """After a refresh: pick up the 'In Progress' record saved when Start was pressed"""
    name = task_name or key.replace("_", " ").title()
    try:
        rows = supabase.table("daily_tasks").select("id,start_time,time").eq("person", st.session_state.name)\
            .eq("date", date_str()).eq("status", "In Progress").eq("task_type", name).execute().data or []
    except Exception:
        return False
    if not rows:
        return False
    rows.sort(key=lambda r: int(r.get("id") or 0))
    keep = rows[-1]
    for r in rows[:-1]:                     # stray duplicates from earlier refreshes
        try:
            supabase.table("daily_tasks").delete().eq("id", r["id"]).eq("status", "In Progress").execute()
        except Exception:
            pass
    t = parse_task_time(keep.get("start_time") or keep.get("time"))
    if not t:
        return False
    start = IST.localize(datetime.combine(today_ist(), t.time()))
    if start > now_ist():
        return False
    st.session_state[f"{key}_start"] = start
    st.session_state[f"{key}_task_id"] = keep["id"]
    return True

def show_staff_areas(kp="sa"):
    """Admin / manager: who is in which area today; change a wrong pick"""
    from datetime import timedelta
    with st.expander("📍 Staff areas today (Stock team) — change a wrong area here", expanded=False):
        try:
            rows = supabase.table("work_area_log").select("*").eq("date", date_str()).order("chosen_at").execute().data or []
        except Exception:
            st.caption("Run work_area_setup.sql in Supabase to turn on area locking.")
            return
        latest = {}
        for r in rows:
            latest[r["person"]] = r
        stock = [u["name"] for u in (load_users() or {}).values() if u.get("team") == "Stock"]
        people = sorted(set(stock) | set(latest))
        if not people:
            st.caption("No Stock team members.")
            return
        opts = load_areas() + ["All Areas"]
        for p in people:
            r = latest.get(p)
            c1, c2, c3, c4 = st.columns([2, 3, 2, 1])
            with c1:
                st.markdown(f"**{p}**")
            with c2:
                if r:
                    t = to_ist(r.get("chosen_at"))
                    st.markdown(f"📍 {r.get('area')} · since {t.strftime('%I:%M %p') if t else ''}"
                                + (f" · by {r.get('set_by')}" if r.get("set_by") != p else ""))
                else:
                    st.markdown("— not chosen today")
            with c3:
                new = st.selectbox("Area", opts, key=f"{kp}_sel_{p}", label_visibility="collapsed",
                                   index=opts.index(r["area"]) if r and r.get("area") in opts else 0)
            with c4:
                if st.button("Set", key=f"{kp}_set_{p}"):
                    set_area_lock(p, new, st.session_state.name)
                    st.rerun()
        n_changes = {p: sum(1 for r in rows if r["person"] == p) for p in latest}
        many = [f"{p} ({n})" for p, n in n_changes.items() if n > 2]
        if many:
            st.caption("🔁 Area changed several times today: " + ", ".join(many))

# ── ADMIN DASHBOARD ───────────────────────────────────────────────────────────
def show_admin_page():
    st.title("👑 RapidSurge Warehouse — Admin")
    st.caption(f"Welcome **{st.session_state.name}** | {today_ist().strftime('%A, %d %B %Y')} | {time_str()}")
    st.divider()

    tab0, tab1, tab12, tab2, tab3, tab4, tab5, tab6, tab7, tab13, tab8, tab9, tab10, tab11 = st.tabs([
        "🎯 My Day",
        "📊 Dashboard",
        "👥 All Staff Work",
        "🔄 Pipeline",
        "📈 Performance",
        "📝 Submit Entry",
        "👥 Settings",
        "📥 Reports",
        "📦 Customer Orders",
        "🛒 Normal Orders",
        "🧾 Bills Register",
        "🕐 Attendance",
        "📌 Assign Tasks",
        "📅 Shift Planner"
    ])

    with tab0:
        show_my_day("md")

    with tab11:
        show_shift_planner("adm_shift")

    with tab13:
        show_order_sheet_report("adm_osr")

    with tab12:
        show_all_staff_work("adm_asw")

    with tab10:
        show_assign_tasks_admin("adm_asg")

    with tab9:
        show_attendance_admin("adm_att")

    with tab7:
        show_customer_order_tracker("adm", show_phone=True)

    with tab8:
        show_bills_register("adm_bills")

    with tab1:
        try:
            tasks_resp = supabase.table("daily_tasks").select("*").eq("date", date_str()).execute()
            df = pd.DataFrame(tasks_resp.data) if tasks_resp.data else pd.DataFrame()
        except:
            df = pd.DataFrame()

        try:
            arr_resp = supabase.table("arrangements").select("*").eq("order_placed_date", date_str()).execute()
            arr_today = arr_resp.data if arr_resp.data else []
        except:
            arr_today = []

        # ── ALERTS & BOTTLENECKS ──────────────────────────────────────────────
        from datetime import datetime as dt
        alerts = []

        for arr in arr_today:
            status = arr.get("status","")
            order_time = arr.get("order_placed_time","")
            if status not in ["Completed","Bill Uploaded","Stock Placed"] and order_time:
                try:
                    order_dt  = dt.strptime(order_time, "%I:%M %p")
                    now_dt    = dt.strptime(time_str(), "%I:%M %p")
                    diff_mins = int((now_dt - order_dt).total_seconds() / 60)
                    if diff_mins > 120:
                        hours = diff_mins // 60
                        mins  = diff_mins % 60
                        alerts.append(f"⚠️ **#{arr.get('arrangement_no')}** — {arr.get('distributor','')} stuck at **{status}** for **{hours}h {mins}m**!")
                except:
                    pass

        pending_self = [a for a in arr_today if a.get("status")=="Pending" and a.get("pickup_type")=="Self Pick"]
        if len(pending_self) > 3:
            alerts.append(f"⚠️ **{len(pending_self)} arrangements** pending Self Pick!")

        reached = [a for a in arr_today if a.get("status")=="Reached Warehouse"]
        if len(reached) > 2:
            alerts.append(f"⚠️ **{len(reached)} arrangements** at warehouse — not cross checked!")

        try:
            all_users = supabase.table("app_users").select("*").eq("active",True).neq("role","admin").execute()
            if all_users.data and not df.empty:
                active_persons = df["person"].unique().tolist() if "person" in df.columns else []
                for u in all_users.data:
                    if u["name"] not in active_persons:
                        alerts.append(f"⚠️ **{u['name']}** ({u['team']}) — No activity today!")
        except:
            pass

        # Show as expander
        with st.expander(f"🚨 Alerts & Bottlenecks ({len(alerts)} alerts)", expanded=len(alerts)>0):
            if alerts:
                for alert in alerts:
                    st.warning(alert)
            else:
                st.success("✅ All good! No alerts.")

        st.divider()

        # ── REAL TIME TEAM STATUS ─────────────────────────────────────────────
        try:
            all_users_resp = supabase.table("app_users").select("*").eq("active",True).neq("role","admin").execute()
            all_users_data = all_users_resp.data if all_users_resp.data else []

            latest_tasks = {}
            if not df.empty:
                for _, row in df.iterrows():
                    person = row.get("person","")
                    if person not in latest_tasks:
                        latest_tasks[person] = row
                    else:
                        try:
                            existing = dt.strptime(str(latest_tasks[person].get("time","12:00 AM")), "%I:%M %p")
                            new_t    = dt.strptime(str(row.get("time","12:00 AM")), "%I:%M %p")
                            if new_t > existing:
                                latest_tasks[person] = row
                        except:
                            pass

            # Team filter
            selected_team = st.selectbox("👥 View Team Status",
                ["All Teams","Purchase","Stock","Call","Delivery"],
                key="team_status_filter")

            teams_to_show = ["Purchase","Stock","Call","Delivery"] if selected_team == "All Teams" else [selected_team]

            with st.expander("👥 Real Time Team Status", expanded=True):
                for team in teams_to_show:
                    team_users = [u for u in all_users_data if u.get("team") == team]
                    if team_users:
                        st.markdown(f"**{team} Team:**")
                        for u in team_users:
                            name = u["name"]
                            c1,c2,c3 = st.columns([2,3,2])
                            with c1: st.markdown(f"👤 **{name}**")
                            if name in latest_tasks:
                                task = latest_tasks[name]
                                if task.get("status") == "In Progress":
                                    with c2: st.markdown(f"🔄 **{task.get('task_type','')}**")
                                else:
                                    with c2: st.markdown(f"✅ **{task.get('task_type','')}**")
                                with c3: st.markdown(f"🕐 {task.get('time','')}")
                            else:
                                with c2: st.markdown("⏳ No activity yet")
                                with c3: st.markdown("")
                        st.divider()
        except Exception as e:
            st.error(f"Error: {e}")

        st.divider()

        # ── ARRANGEMENT SUMMARY ───────────────────────────────────────────────
        st.subheader("📋 Today's Arrangement Summary")
        a1,a2,a3,a4,a5 = st.columns(5)
        with a1: st.metric("Total", len(arr_today))
        with a2: st.metric("🔴 Pending", len([a for a in arr_today if a.get("status")=="Pending"]))
        with a3: st.metric("🚚 In Transit", len([a for a in arr_today if "Transit" in str(a.get("status",""))]))
        with a4: st.metric("🏭 At Warehouse", len([a for a in arr_today if a.get("status")=="Reached Warehouse"]))
        with a5: st.metric("✅ Completed", len([a for a in arr_today if a.get("status")=="Completed"]))

        st.divider()

        # ── PIPELINE HEALTH ───────────────────────────────────────────────────
        st.subheader("📈 Arrangement Pipeline Health")
        try:
            pipeline_times = []
            for arr in arr_today:
                try:
                    o = dt.strptime(arr.get("order_placed_time",""), "%I:%M %p")
                    u = dt.strptime(arr.get("bill_upload_time",""), "%I:%M %p")
                    diff = int((u-o).total_seconds()/60)
                    if diff > 0:
                        pipeline_times.append(diff)
                except:
                    pass
            if pipeline_times:
                avg_t = int(sum(pipeline_times)/len(pipeline_times))
                min_t = min(pipeline_times)
                max_t = max(pipeline_times)
                c1,c2,c3 = st.columns(3)
                with c1: st.metric("⏱️ Avg Order→Bill Upload", f"{avg_t} mins")
                with c2: st.metric("⚡ Fastest", f"{min_t} mins")
                with c3:
                    icon = "🔴" if max_t > 180 else "🟡" if max_t > 120 else "🟢"
                    st.metric(f"{icon} Slowest", f"{max_t} mins")
            else:
                st.info("No completed pipeline data yet today!")
        except Exception as e:
            st.error(f"Error: {e}")

        st.divider()

        # Team tasks
        st.subheader("👥 Team Tasks Today")
        if not df.empty:
            cols = st.columns(4)
            for i,t in enumerate(["Purchase","Stock","Call","Delivery"]):
                with cols[i]: st.metric(t, len(df[df["team"]==t]), "tasks")
            st.divider()
            c1,c2 = st.columns(2)
            with c1: st.bar_chart(df["team"].value_counts())
            with c2: st.bar_chart(df["person"].value_counts())
        else:
            st.info("No tasks today yet!")

        st.divider()

        # All arrangements
        st.subheader("📋 All Arrangements Today")
        try:
            arr = supabase.table("arrangements").select("*")\
                .eq("order_placed_date", date_str()).execute()
            if arr.data:
                arr_df = pd.DataFrame(arr.data)
                display_cols = ["arrangement_no","distributor","area","order_placed_time","order_by","urgency","pickup_type","status"]
                existing_cols = [c for c in display_cols if c in arr_df.columns]
                st.dataframe(arr_df[existing_cols], width='stretch')
            else:
                st.info("No arrangements today.")
        except Exception as e:
            st.error(f"Error: {e}")

    with tab2:
        st.subheader("🔄 Pipeline View")

        pipe_type = st.radio("Select Pipeline",
            ["📦 Arrangement Orders", "🧾 Normal Orders"],
            horizontal=True, key="pipe_type_tab")

        if pipe_type == "🧾 Normal Orders":
            st.subheader("🧾 Normal Order Pipeline")

            c1,c2,c3,c4 = st.columns(4)
            with c1:
                no_date = st.date_input("Date", value=today_ist(), key="no_date")
            with c2:
                try:
                    areas_resp = supabase.table("areas").select("name").eq("active",True).execute()
                    no_area_list = ["All Areas"] + [a["name"] for a in (areas_resp.data or [])]
                except:
                    no_area_list = ["All Areas"]
                no_area = st.selectbox("Area", no_area_list, key="no_area")
            with c3:
                no_dist = st.text_input("Search Distributor", placeholder="Type to search...", key="no_dist")
            with c4:
                no_bill = st.text_input("Search Bill No", placeholder="Type bill no...", key="no_bill")

            no_date_str = no_date.strftime("%Y-%m-%d")

            try:
                reg_resp = supabase.table("daily_tasks").select("*")\
                    .eq("task_type", "Register Entry")\
                    .eq("date", no_date_str).execute()
                register_entries = reg_resp.data or []

                cross_resp = supabase.table("daily_tasks").select("*")\
                    .eq("task_type", "Bill Cross Check")\
                    .eq("date", no_date_str).execute()
                cross_checks = {t.get("details",{}).get("bill_no",""):t for t in (cross_resp.data or []) if not t.get("details",{}).get("arrangement_no","")}

                upload_resp = supabase.table("daily_tasks").select("*")\
                    .eq("task_type", "Bill Upload")\
                    .eq("date", no_date_str).execute()
                uploads = {t.get("details",{}).get("bill_no",""):t for t in (upload_resp.data or []) if not t.get("details",{}).get("arrangement_no","")}

                place_resp = supabase.table("daily_tasks").select("*")\
                    .eq("task_type", "Stock Placement")\
                    .eq("date", no_date_str).execute()
                placements = {t.get("details",{}).get("bill_no",""):t for t in (place_resp.data or []) if not t.get("details",{}).get("arrangement_no","")}

                pcheck_resp = supabase.table("daily_tasks").select("*")\
                    .eq("task_type", "Placement Cross Check")\
                    .eq("date", no_date_str).execute()
                place_checks = {t.get("details",{}).get("bill_no",""):t for t in (pcheck_resp.data or [])}

            except Exception as e:
                st.error(f"Error: {e}")
                register_entries = []
                cross_checks = {}
                uploads = {}
                placements = {}
                place_checks = {}

            if not register_entries:
                st.info("No normal orders found for selected date!")
            else:
                if no_dist:
                    register_entries = [r for r in register_entries if no_dist.lower() in r.get("details",{}).get("distributor","").lower()]
                if no_bill:
                    register_entries = [r for r in register_entries if no_bill.lower() in r.get("details",{}).get("bill_no","").lower()]

                pipeline_rows = []
                for r in register_entries:
                    d       = r.get("details",{})
                    bill_no = d.get("bill_no","")
                    dist    = d.get("distributor","")
                    items   = d.get("no_items","")
                    amount  = d.get("bill_amount","")
                    delby   = d.get("delivery_by","")

                    cross  = cross_checks.get(bill_no)
                    upload = uploads.get(bill_no)
                    place  = placements.get(bill_no)
                    pcheck = place_checks.get(bill_no)

                    if pcheck:
                        status = "✅ Completed"
                    elif place:
                        status = "🔍 Cross Check Pending"
                    elif upload:
                        status = "📍 Placement Pending"
                    elif cross:
                        status = "📤 Upload Pending"
                    else:
                        status = "✔️ Cross Check Pending"

                    pipeline_rows.append({
                        "Bill No": bill_no,
                        "Distributor": dist,
                        "Date": r.get("date",""),
                        "SKUs": items,
                        "Amount(₹)": f"₹{float(amount or 0):,.0f}",
                        "Arrived": r.get("time",""),
                        "Received By": r.get("person",""),
                        "Delivered By": delby,
                        "Check Time": f"{cross.get('duration_mins','-')} mins" if cross else "⏳",
                        "Checked By": cross.get("person","") if cross else "⏳",
                        "Upload Time": f"{upload.get('duration_mins','-')} mins" if upload else "⏳",
                        "Uploaded By": upload.get("person","") if upload else "⏳",
                        "Place Time": f"{place.get('duration_mins','-')} mins" if place else "⏳",
                        "Placed By": place.get("person","") if place else "⏳",
                        "Cross Check": "✅ " + pcheck.get("person","") if pcheck else "⏳",
                        "Status": status
                    })

                if pipeline_rows:
                    pipeline_df = pd.DataFrame(pipeline_rows)
                    st.markdown(f"**{len(pipeline_df)} bills found**")

                    status_filter = st.selectbox("Filter by Status", [
                        "All","✔️ Cross Check Pending","📤 Upload Pending",
                        "📍 Placement Pending","🔍 Cross Check Pending","✅ Completed"
                    ], key="no_status")

                    if status_filter != "All":
                        pipeline_df = pipeline_df[pipeline_df["Status"]==status_filter]

                    st.dataframe(pipeline_df, width='stretch')

                    # Detailed expander view
                    st.markdown("**📋 Detailed View:**")
                    for r in pipeline_rows:
                        with st.expander(f"Bill: {r['Bill No']} | {r['Distributor']} | {r['Status']}"):
                            c1,c2 = st.columns(2)
                            with c1:
                                st.markdown("**📒 Register Entry:**")
                                st.markdown(f"- Arrived: **{r['Arrived']}**")
                                st.markdown(f"- Received By: **{r['Received By']}**")
                                st.markdown(f"- Delivered By: **{r['Delivered By']}**")
                                st.markdown(f"- SKUs: **{r['SKUs']}**")
                                st.markdown(f"- Amount: **{r['Amount(₹)']}**")
                                st.divider()
                                st.markdown("**✔️ Bill Cross Check:**")
                                st.markdown(f"- Checked By: **{r['Checked By']}**")
                                st.markdown(f"- Time Taken: **{r['Check Time']}**")
                            with c2:
                                st.markdown("**📤 Bill Upload:**")
                                st.markdown(f"- Uploaded By: **{r['Uploaded By']}**")
                                st.markdown(f"- Time Taken: **{r['Upload Time']}**")
                                st.divider()
                                st.markdown("**📍 Stock Placement:**")
                                st.markdown(f"- Placed By: **{r['Placed By']}**")
                                st.markdown(f"- Time Taken: **{r['Place Time']}**")
                                st.divider()
                                st.markdown("**🔍 Final Cross Check:**")
                                st.markdown(f"- Result: **{r['Cross Check']}**")

                            # Show invoice image if available
                            reg_entry = next((t for t in register_entries 
                                if t.get("details",{}).get("bill_no","") == r["Bill No"]), None)
                            if reg_entry:
                                img_name = reg_entry.get("details",{}).get("invoice_image","")
                                if img_name:
                                    st.divider()
                                    st.markdown("**📸 Invoice Image:**")
                                    try:
                                        img_data = supabase.storage.from_("Images").download(img_name)
                                        from PIL import Image
                                        import io as io_mod
                                        pil_img = Image.open(io_mod.BytesIO(img_data))
                                        st.image(pil_img, width='stretch')
                                        st.download_button(
                                            "🔍 Download Full Size",
                                            img_data,
                                            file_name=f"invoice_{r['Bill No']}.jpg",
                                            mime="image/jpeg",
                                            key=f"dl_inv_{r['Bill No']}"
                                        )
                                    except:
                                        st.warning("Image not available")

                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine="openpyxl") as w:
                        pipeline_df.to_excel(w, index=False)
                    st.download_button("⬇️ Download Excel", buf.getvalue(),
                        f"normal_orders_{no_date_str}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="no_excel")
                else:
                    st.info("No bills match selected filters!")

        else:
            st.subheader("🔄 Arrangement Pipeline View")
        c1,c2,c3 = st.columns(3)
        with c1:
            pipeline_date = st.date_input("Date", value=today_ist(), key="pipeline_date_tab")
        with c2:
            try:
                areas_resp = supabase.table("areas").select("name").eq("active", True).execute()
                area_list = ["All Areas"] + [a["name"] for a in areas_resp.data]
            except:
                area_list = ["All Areas"]
            pipeline_area = st.selectbox("Area", area_list, key="pipeline_area_tab")
        with c3:
            pipeline_status = st.selectbox("Status", [
                "All","Pending","Picked Up - In Transit","Porter Booked",
                "Given to Porter - In Transit","Reached Warehouse",
                "Bill Cross Checked","Bill Uploaded","Stock Placed","Completed"
            ], key="pipeline_status_tab")

        try:
            pipeline_resp = supabase.table("arrangements").select("*")\
                .eq("order_placed_date", pipeline_date.strftime("%Y-%m-%d")).execute()
            pipeline_arrs = pipeline_resp.data if pipeline_resp.data else []
        except Exception as e:
            st.error(f"Error: {e}")
            pipeline_arrs = []

        if pipeline_area != "All Areas":
            pipeline_arrs = [a for a in pipeline_arrs if a.get("area","") == pipeline_area]
        if pipeline_status != "All":
            pipeline_arrs = [a for a in pipeline_arrs if a.get("status","") == pipeline_status]

        st.markdown(f"**{len(pipeline_arrs)} arrangements found**")

        for arr in pipeline_arrs:
            status  = arr.get("status","")
            urgency = arr.get("urgency","Normal")
            urgency_color = "🔴" if urgency == "Very Urgent" else "🟡" if urgency == "Urgent" else "🟢"

            steps = [
                ("Order Placed",      arr.get("order_placed_time",""), arr.get("order_by",""),                    True),
                ("Picked Up",         arr.get("pickup_time",""),       arr.get("pickup_by",""),                   arr.get("pickup_time","") != ""),
                ("Reached Warehouse", "",                              "",                                        status in ["Reached Warehouse","Bill Cross Checked","Bill Uploaded","Stock Placed","Completed"]),
                ("Bill Cross Checked",arr.get("cross_check_time",""), arr.get("cross_checked_by",""),            status in ["Bill Cross Checked","Bill Uploaded","Stock Placed","Completed"]),
                ("Bill Uploaded",     arr.get("bill_upload_time",""), arr.get("bill_uploaded_by",""),            status in ["Bill Uploaded","Stock Placed","Completed"]),
                ("Stock Placed",      arr.get("placement_time",""),   arr.get("placed_by",""),                   status in ["Stock Placed","Completed"]),
                ("Completed",         "",                              "",                                        status == "Completed"),
            ]

            with st.expander(f"{urgency_color} **#{arr.get('arrangement_no','')}** | {arr.get('distributor','')} | {arr.get('area','')} | **{status}**"):
                for step_name, step_time, step_by, done in steps:
                    if done:
                        time_val = f"— {step_time}" if step_time else ""
                        by_val   = f"— {step_by}" if step_by else ""
                        st.markdown(f"✅ **{step_name}** {time_val} {by_val}")
                    else:
                        st.markdown(f"⏳ {step_name}")

    with tab3:
        st.subheader("📈 Performance & CEO Dashboard")

        perf_tab1, perf_tab2 = st.tabs(["👤 Team Performance", "💼 CEO Dashboard"])

        with perf_tab1:
            st.subheader("👤 Individual Performance")

            c1,c2 = st.columns(2)
            with c1:
                perf_date = st.date_input("Date", value=today_ist(), key="perf_date_ind")
            with c2:
                try:
                    users_resp = supabase.table("app_users").select("*")\
                        .eq("active",True).neq("role","admin").execute()
                    person_list = [u["name"] for u in (users_resp.data or [])]
                    teams_dict  = {u["name"]: u["team"] for u in (users_resp.data or [])}
                except:
                    person_list = []
                    teams_dict  = {}
                sel_person = st.selectbox("Select Person", person_list, key="perf_person")

            perf_date_str = perf_date.strftime("%Y-%m-%d")
            from datetime import timedelta
            yesterday_str = (perf_date - timedelta(days=1)).strftime("%Y-%m-%d")

            if sel_person:
                team = teams_dict.get(sel_person, "")

                # Complete day: attendance + every task (any team) + breaks + idle gaps
                st.markdown(f"#### 📋 Full Day — {sel_person}")
                show_person_day(sel_person, perf_date)
                st.divider()
                st.markdown(f"#### 📊 {team} task metrics")

                # Load today tasks
                try:
                    tasks_resp = supabase.table("daily_tasks").select("*")\
                        .eq("person", sel_person)\
                        .eq("date", perf_date_str).execute()
                    tasks = tasks_resp.data or []

                    # Load yesterday tasks
                    yest_resp = supabase.table("daily_tasks").select("*")\
                        .eq("person", sel_person)\
                        .eq("date", yesterday_str).execute()
                    yest_tasks = yest_resp.data or []
                except:
                    tasks = []
                    yest_tasks = []

                if not tasks:
                    st.info(f"No tasks found for {sel_person} on {perf_date_str}!")
                else:
                    # ── PURCHASE TEAM METRICS ─────────────────────────────
                    if team == "Purchase":
                        task_config = {
                            "Purchase Order":       ("no_sku",     "SKUs"),
                            "Arrangement Order":    ("no_medicines","Medicines"),
                            "Purchase Return":      ("no_items",   "Items"),
                            "PharmaRack Search":    ("no_searched","Searched"),
                            "Bounce Medicine Study":("no_bounced", "Bounced"),
                        }

                    # ── STOCK TEAM METRICS ────────────────────────────────
                    elif team == "Stock":
                        task_config = {
                            "Register Entry":       ("no_items",   "Items"),
                            "Bill Cross Check":     ("no_items",   "Items"),
                            "Bill Upload":          ("no_items",   "Items"),
                            "Bill Upload (Arrangement)": ("no_items","Items"),
                            "Stock Placement":      ("no_medicines","Medicines"),
                            "Rack Cleaning":        ("no_racks",   "Racks"),
                            "Inventory Check":      ("no_items",   "Items"),
                        }

                    # ── CALL TEAM METRICS ─────────────────────────────────
                    elif team == "Call":
                        task_config = {
                            "Call Log":         ("calls_made",  "Calls"),
                            "Medicine Search":  ("no_searched", "Searched"),
                        }
                    else:
                        task_config = {}

                    # Build performance table
                    perf_rows = []
                    total_time  = 0
                    total_count = 0
                    total_skus  = 0

                    for task_type, (sku_field, sku_label) in task_config.items():
                        task_list = [t for t in tasks if t.get("task_type") == task_type]
                        if not task_list:
                            continue

                        count    = len(task_list)
                        duration = sum([int(float(t.get("duration_mins",0) or 0)) for t in task_list])
                        skus     = sum([int(float((t.get("details") or {}).get(sku_field,0) or 0)) for t in task_list])
                        avg_sku  = round(duration/skus, 2) if skus > 0 else 0

                        # Yesterday comparison
                        yest_list     = [t for t in yest_tasks if t.get("task_type") == task_type]
                        yest_duration = sum([int(float(t.get("duration_mins",0) or 0)) for t in yest_list])
                        yest_skus     = sum([int(float((t.get("details") or {}).get(sku_field,0) or 0)) for t in yest_list])
                        yest_avg      = round(yest_duration/yest_skus, 2) if yest_skus > 0 else None

                        # Trend
                        if avg_sku != "-" and yest_avg:
                            trend = "✅ Better" if float(avg_sku) < float(yest_avg) else "⚠️ Slower"
                        else:
                            trend = "-"

                        total_time  += duration
                        total_count += count
                        total_skus  += skus

                        perf_rows.append({
                            "Task": task_type,
                            f"Count": count,
                            "Total Time (mins)": duration,
                            f"{sku_label}": skus,
                            "Avg/SKU (mins)": avg_sku,
                            "Yesterday Avg": yest_avg or "",
                            "Trend": trend
                        })

                    if perf_rows:
                        # Summary metrics
                        overall_avg = round(total_time/total_skus, 2) if total_skus > 0 else 0
                        c1,c2,c3,c4 = st.columns(4)
                        with c1: st.metric(f"👤 {sel_person}", team)
                        with c2: st.metric("⏱️ Total Time", f"{total_time} mins")
                        with c3: st.metric("📋 Total Tasks", total_count)
                        with c4: st.metric("📦 Total SKUs", total_skus)

                        st.divider()

                        # Performance table
                        perf_df = pd.DataFrame(perf_rows)
                        st.dataframe(perf_df, width='stretch')

                        # Total row
                        st.markdown(f"**📊 Overall Avg/SKU: {overall_avg} mins**")

                        # Bar chart - time per task
                        st.divider()
                        st.markdown("**⏱️ Time Distribution:**")
                        chart_df = pd.DataFrame([
                            {"Task": r["Task"], "Minutes": r["Total Time (mins)"]}
                            for r in perf_rows
                        ]).set_index("Task")
                        st.bar_chart(chart_df)

                        # Trend analysis
                        st.divider()
                        st.markdown("**📈 Trend vs Yesterday:**")
                        for r in perf_rows:
                            if r["Trend"] != "-":
                                st.markdown(f"**{r['Task']}**: Today {r['Avg/SKU (mins)']} mins/SKU | Yesterday {r['Yesterday Avg']} mins/SKU | {r['Trend']}")
                    else:
                        st.caption(f"No {team} team tasks for {sel_person} on this day — see the Full Day table above for everything else.")

        with perf_tab2:
            st.subheader("📈 CEO Dashboard")

        # Date and filters
        c1,c2,c3 = st.columns(3)
        with c1:
            dash_date = st.date_input("Date", value=today_ist(), key="dash_date")
        with c2:
            try:
                areas_resp = supabase.table("areas").select("name").eq("active",True).execute()
                area_list = ["All Areas"] + [a["name"] for a in (areas_resp.data or [])]
            except:
                area_list = ["All Areas"]
            dash_area = st.selectbox("Area", area_list, key="dash_area")
        with c3:
            try:
                users_resp = supabase.table("app_users").select("name").eq("team","Stock").eq("active",True).execute()
                person_list = ["All Persons"] + [u["name"] for u in (users_resp.data or [])]
            except:
                person_list = ["All Persons"]
            dash_person = st.selectbox("Person", person_list, key="dash_person")

        dash_date_str = dash_date.strftime("%Y-%m-%d")

        try:
            # Load all tasks for selected date
            tasks_resp = supabase.table("daily_tasks").select("*").eq("date", dash_date_str).execute()
            all_tasks = tasks_resp.data or []

            # Load arrangements
            arr_resp = supabase.table("arrangements").select("*").eq("order_placed_date", dash_date_str).execute()
            arrangements = arr_resp.data or []

        except Exception as e:
            st.error(f"Error: {e}")
            all_tasks = []
            arrangements = []

        # Filter tasks
        reg_tasks   = [t for t in all_tasks if t.get("task_type") == "Register Entry"]
        cross_tasks = [t for t in all_tasks if t.get("task_type") == "Bill Cross Check"]
        upload_tasks= [t for t in all_tasks if t.get("task_type") in ["Bill Upload","Bill Upload (Arrangement)"]]
        place_tasks = [t for t in all_tasks if t.get("task_type") == "Stock Placement"]

        # Apply area filter
        if dash_area != "All Areas":
            arrangements = [a for a in arrangements if a.get("area","") == dash_area]

        # Apply person filter
        if dash_person != "All Persons":
            reg_tasks    = [t for t in reg_tasks    if t.get("person") == dash_person]
            cross_tasks  = [t for t in cross_tasks  if t.get("person") == dash_person]
            upload_tasks = [t for t in upload_tasks if t.get("person") == dash_person]
            place_tasks  = [t for t in place_tasks  if t.get("person") == dash_person]

        # ── SECTION 1 — TODAY'S RECEIPTS ─────────────────────────────────────
        st.markdown("### 📥 Today's Receipts")

        total_bills   = len(reg_tasks)
        total_skus    = sum([int(float((t.get("details") or {}).get("no_items",0) or 0)) for t in reg_tasks])
        total_amount  = sum([float((t.get("details") or {}).get("bill_amount",0) or 0) for t in reg_tasks])

        # Time calculations
        cross_dur  = sum([int(float(t.get("duration_mins",0) or 0)) for t in cross_tasks])
        upload_dur = sum([int(float(t.get("duration_mins",0) or 0)) for t in upload_tasks])
        place_dur  = sum([int(float(t.get("duration_mins",0) or 0)) for t in place_tasks])

        avg_cross  = round(cross_dur/len(cross_tasks), 1)  if cross_tasks  else 0
        avg_upload = round(upload_dur/len(upload_tasks), 1) if upload_tasks else 0
        avg_place  = round(place_dur/len(place_tasks), 1)  if place_tasks  else 0

        c1,c2,c3 = st.columns(3)
        with c1:
            st.metric("📋 Bills Received", total_bills)
            st.metric("📦 Total SKUs", total_skus)
            st.metric("💰 Total Amount", f"₹{total_amount:,.0f}")
        with c2:
            st.metric("⏱️ Total Check Time", f"{cross_dur} mins")
            st.metric("⏱️ Total Upload Time", f"{upload_dur} mins")
            st.metric("⏱️ Total Place Time", f"{place_dur} mins")
        with c3:
            st.metric("📊 Avg Check/Bill", f"{avg_cross} mins")
            st.metric("📊 Avg Upload/Bill", f"{avg_upload} mins")
            st.metric("📊 Avg Place/Bill", f"{avg_place} mins")

        st.divider()

        # ── SECTION 2 — PENDING WORK ──────────────────────────────────────────
        st.markdown("### ⏳ Pending Work")

        # Count pending at each stage
        reached_wh    = [a for a in arrangements if a.get("status") == "Reached Warehouse"]
        cross_checked = [a for a in arrangements if a.get("status") == "Bill Cross Checked"]
        bill_uploaded = [a for a in arrangements if a.get("status") == "Bill Uploaded"]
        stock_placed  = [a for a in arrangements if a.get("status") == "Stock Placed" and a.get("cross_check_status") == "Pending"]

        # Normal orders pending
        normal_cross_pending  = [t for t in all_tasks if t.get("task_type") == "Register Entry" and not any(c.get("details",{}).get("bill_no","") == t.get("details",{}).get("bill_no","") for c in cross_tasks)]
        normal_upload_pending = [t for t in cross_tasks if not t.get("details",{}).get("arrangement_no","") and not t.get("details",{}).get("bill_uploaded")]
        normal_place_pending  = [t for t in upload_tasks if not t.get("details",{}).get("arrangement_no","") and not t.get("details",{}).get("placement_done")]

        p1,p2,p3,p4 = st.columns(4)
        with p1:
            total_cross_pending = len(reached_wh) + len(normal_cross_pending)
            st.metric("✔️ Cross Check Pending", total_cross_pending)
        with p2:
            total_upload_pending = len(cross_checked) + len(normal_upload_pending)
            st.metric("📤 Upload Pending", total_upload_pending)
        with p3:
            total_place_pending = len(bill_uploaded) + len(normal_place_pending)
            st.metric("📍 Placement Pending", total_place_pending)
        with p4:
            st.metric("🔍 Final Check Pending", len(stock_placed))

        st.divider()

        # ── SECTION 3 — PERSON WISE PERFORMANCE ──────────────────────────────
        st.markdown("### 👤 Person Wise Performance")

        # Get all stock team members
        try:
            stock_users = supabase.table("app_users").select("name").eq("team","Stock").eq("active",True).execute()
            stock_names = [u["name"] for u in (stock_users.data or [])]
        except:
            stock_names = list(set([t.get("person","") for t in cross_tasks + upload_tasks + place_tasks]))

        person_rows = []
        for person in stock_names:
            if dash_person != "All Persons" and person != dash_person:
                continue

            p_cross  = [t for t in cross_tasks  if t.get("person") == person]
            p_upload = [t for t in upload_tasks if t.get("person") == person]
            p_place  = [t for t in place_tasks  if t.get("person") == person]

            p_cross_dur  = sum([int(float(t.get("duration_mins",0) or 0)) for t in p_cross])
            p_upload_dur = sum([int(float(t.get("duration_mins",0) or 0)) for t in p_upload])
            p_place_dur  = sum([int(float(t.get("duration_mins",0) or 0)) for t in p_place])

            person_rows.append({
                "Person": person,
                "Bills Checked": len(p_cross),
                "Total Check(mins)": p_cross_dur,
                "Avg Check/Bill": round(p_cross_dur/len(p_cross),1) if p_cross else 0,
                "Bills Uploaded": len(p_upload),
                "Total Upload(mins)": p_upload_dur,
                "Avg Upload/Bill": round(p_upload_dur/len(p_upload),1) if p_upload else 0,
                "Bills Placed": len(p_place),
                "Total Place(mins)": p_place_dur,
                "Avg Place/Bill": round(p_place_dur/len(p_place),1) if p_place else 0,
            })

        if person_rows:
            person_df = pd.DataFrame(person_rows)
            st.dataframe(person_df, width='stretch')

            # Team summary
            st.markdown("**📊 Team Summary:**")
            s1,s2,s3 = st.columns(3)
            with s1:
                st.metric("Total Bills Checked", sum([r["Bills Checked"] for r in person_rows]))
                st.metric("Team Avg Check/Bill", f"{round(sum([p_cross_dur for p_cross_dur in [r['Total Check(mins)'] for r in person_rows] if p_cross_dur > 0]) / max(sum([r['Bills Checked'] for r in person_rows]),1), 1)} mins")
            with s2:
                st.metric("Total Bills Uploaded", sum([r["Bills Uploaded"] for r in person_rows]))
                st.metric("Team Avg Upload/Bill", f"{round(sum([r['Total Upload(mins)'] for r in person_rows]) / max(sum([r['Bills Uploaded'] for r in person_rows]),1), 1)} mins")
            with s3:
                st.metric("Total Bills Placed", sum([r["Bills Placed"] for r in person_rows]))
                st.metric("Team Avg Place/Bill", f"{round(sum([r['Total Place(mins)'] for r in person_rows]) / max(sum([r['Bills Placed'] for r in person_rows]),1), 1)} mins")
        else:
            st.info("No stock team data for selected filters!")

        st.divider()

        # ── SECTION 4 — AREA WISE SUMMARY ────────────────────────────────────
        st.markdown("### 📍 Area Wise Summary")
        try:
            area_data = {}
            for arr in arrangements:
                area = arr.get("area","Unknown")
                if area not in area_data:
                    area_data[area] = {"bills": 0, "skus": 0, "amount": 0, "pending": 0}
                area_data[area]["bills"] += 1
                area_data[area]["skus"]  += int(float(arr.get("no_medicines",0) or 0))
                if arr.get("status") not in ["Completed","Stock Placed"]:
                    area_data[area]["pending"] += 1

            if area_data:
                area_rows = [{"Area": k, "Bills": v["bills"], "SKUs": v["skus"], "Pending": v["pending"]} for k,v in area_data.items()]
                st.dataframe(pd.DataFrame(area_rows), width='stretch')
            else:
                st.info("No area data available!")
        except Exception as e:
            st.error(f"Error: {e}")

        st.divider()

        st.subheader("📈 CEO Dashboard")

        # Date selector
        ceo_date = st.date_input("Select Date", value=today_ist(), key="ceo_date")
        ceo_date_str = ceo_date.strftime("%Y-%m-%d")

        try:
            # Load all data
            tasks_resp = supabase.table("daily_tasks").select("*").eq("date", ceo_date_str).execute()
            tasks = tasks_resp.data or []
            arr_resp = supabase.table("arrangements").select("*").eq("order_placed_date", ceo_date_str).execute()
            arrangements = arr_resp.data or []
        except Exception as e:
            st.error(f"Error: {e}")
            tasks = []
            arrangements = []

        # ── FINANCIAL OVERVIEW ────────────────────────────────────────────────
        st.markdown("### 💰 Financial Overview")
        reg_entries = [t for t in tasks if t.get("task_type") == "Register Entry"]
        
        total_amount = sum([float((t.get("details") or {}).get("bill_amount",0) or 0) for t in reg_entries])
        arr_amount   = sum([float((t.get("details") or {}).get("bill_amount",0) or 0) for t in reg_entries if (t.get("details") or {}).get("order_type") == "Arrangement"])
        normal_amount = sum([float((t.get("details") or {}).get("bill_amount",0) or 0) for t in reg_entries if (t.get("details") or {}).get("order_type") == "Normal Order"])
        porter_payments = supabase.table("porter_bookings").select("*").eq("date", ceo_date_str).eq("status","Payment Done").execute()
        porter_cost = sum([float(p.get("porter_cost",0) or 0) for p in (porter_payments.data or [])])

        c1,c2,c3,c4 = st.columns(4)
        with c1: st.metric("💰 Total Purchase", f"₹{total_amount:,.0f}")
        with c2: st.metric("📋 Arrangement", f"₹{arr_amount:,.0f}")
        with c3: st.metric("🛒 Normal Orders", f"₹{normal_amount:,.0f}")
        with c4: st.metric("🚛 Porter Cost", f"₹{porter_cost:,.0f}")

        st.divider()

        # ── WEEK ON WEEK TRENDS ───────────────────────────────────────────────
        st.markdown("### 📈 Week on Week Trends")
        try:
            from datetime import timedelta
            
            # This week vs last week
            this_week_start = (ceo_date - timedelta(days=ceo_date.weekday())).strftime("%Y-%m-%d")
            last_week_start = (ceo_date - timedelta(days=ceo_date.weekday()+7)).strftime("%Y-%m-%d")
            last_week_end   = (ceo_date - timedelta(days=ceo_date.weekday()+1)).strftime("%Y-%m-%d")

            this_week_tasks = supabase.table("daily_tasks").select("*")                .gte("date", this_week_start)                .lte("date", ceo_date_str).execute()
            last_week_tasks = supabase.table("daily_tasks").select("*")                .gte("date", last_week_start)                .lte("date", last_week_end).execute()

            this_week_arr = supabase.table("arrangements").select("*")                .gte("order_placed_date", this_week_start)                .lte("order_placed_date", ceo_date_str).execute()
            last_week_arr = supabase.table("arrangements").select("*")                .gte("order_placed_date", last_week_start)                .lte("order_placed_date", last_week_end).execute()

            this_week_count = len(this_week_tasks.data or [])
            last_week_count = len(last_week_tasks.data or [])
            this_arr_count  = len(this_week_arr.data or [])
            last_arr_count  = len(last_week_arr.data or [])

            task_delta = this_week_count - last_week_count
            arr_delta  = this_arr_count - last_arr_count

            c1,c2,c3,c4 = st.columns(4)
            with c1: st.metric("📋 This Week Tasks", this_week_count, f"{'+' if task_delta>=0 else ''}{task_delta} vs last week")
            with c2: st.metric("📦 This Week Arrangements", this_arr_count, f"{'+' if arr_delta>=0 else ''}{arr_delta} vs last week")
            with c3:
                this_week_amount = sum([float((t.get("details") or {}).get("bill_amount",0) or 0) for t in (this_week_tasks.data or []) if t.get("task_type")=="Register Entry"])
                last_week_amount = sum([float((t.get("details") or {}).get("bill_amount",0) or 0) for t in (last_week_tasks.data or []) if t.get("task_type")=="Register Entry"])
                amount_delta = this_week_amount - last_week_amount
                st.metric("💰 This Week Purchase", f"₹{this_week_amount:,.0f}", f"{'+'if amount_delta>=0 else ''}₹{amount_delta:,.0f}")
            with c4:
                # Avg processing time this week
                pipeline_times = []
                for arr in (this_week_arr.data or []):
                    try:
                        from datetime import datetime as dt
                        o = dt.strptime(arr.get("order_placed_time",""), "%I:%M %p")
                        u = dt.strptime(arr.get("bill_upload_time",""), "%I:%M %p")
                        diff = int((u-o).total_seconds()/60)
                        if diff > 0:
                            pipeline_times.append(diff)
                    except:
                        pass
                avg_pipeline = round(sum(pipeline_times)/len(pipeline_times),0) if pipeline_times else 0
                st.metric("⏱️ Avg Pipeline Time", f"{int(avg_pipeline)} mins")

        except Exception as e:
            st.error(f"Trends error: {e}")

        st.divider()

        # ── DISTRIBUTOR PERFORMANCE ───────────────────────────────────────────
        st.markdown("### 🏪 Distributor Performance")
        try:
            # Count orders and issues per distributor
            dist_data = {}
            for t in tasks:
                if t.get("task_type") in ["Register Entry","Bill Upload","Bill Cross Check"]:
                    d = t.get("details",{}) or {}
                    dist = d.get("distributor","")
                    if not dist:
                        continue
                    if dist not in dist_data:
                        dist_data[dist] = {
                            "orders": 0, "amount": 0,
                            "near_expiry": 0, "damaged": 0,
                            "contra": 0, "wrong_batch": 0,
                            "shortage": 0
                        }
                    if t.get("task_type") == "Register Entry":
                        dist_data[dist]["orders"] += 1
                        dist_data[dist]["amount"] += float(d.get("bill_amount",0) or 0)
                    if t.get("task_type") == "Bill Cross Check":
                        dist_data[dist]["near_expiry"] += int(float(d.get("near_expiry",0) or 0))
                        dist_data[dist]["damaged"]     += int(float(d.get("damaged",0) or 0))
                        dist_data[dist]["contra"]      += int(float(d.get("contra",0) or 0))
                        dist_data[dist]["wrong_batch"] += int(float(d.get("wrong_batch",0) or 0))
                        dist_data[dist]["shortage"]    += int(float(d.get("shortage",0) or 0))

            if dist_data:
                dist_rows = []
                for dist, data in dist_data.items():
                    total_issues = data["near_expiry"] + data["damaged"] + data["contra"] + data["wrong_batch"] + data["shortage"]
                    status = "🔴 Issues" if total_issues > 0 else "✅ Good"
                    dist_rows.append({
                        "Distributor": dist,
                        "Orders": data["orders"],
                        "Amount(₹)": f"₹{data['amount']:,.0f}",
                        "Near Expiry": data["near_expiry"],
                        "Damaged": data["damaged"],
                        "Contra": data["contra"],
                        "Wrong Batch": data["wrong_batch"],
                        "Shortage": data["shortage"],
                        "Total Issues": total_issues,
                        "Status": status
                    })
                dist_df = pd.DataFrame(dist_rows).sort_values("Total Issues", ascending=False)
                st.dataframe(dist_df, width='stretch')
            else:
                st.info("No distributor data for selected date!")
        except Exception as e:
            st.error(f"Distributor error: {e}")

        st.divider()

        # ── TEAM PRODUCTIVITY ─────────────────────────────────────────────────
        st.markdown("### 👥 Team Productivity")
        if tasks:
            tasks_df = pd.DataFrame(tasks)
            person_summary = tasks_df.groupby(["person","team"]).agg(
                Tasks=("task_type","count")
            ).reset_index()
            person_summary["Total_mins"] = person_summary.apply(
                lambda row: sum([int(float(t.get("duration_mins",0) or 0)) 
                    for t in tasks if t.get("person")==row["person"]]), axis=1)
            person_summary = person_summary.sort_values("Tasks", ascending=False)
            st.dataframe(person_summary, width='stretch')
            st.bar_chart(tasks_df.groupby("person").size())
        else:
            st.info("No team data for selected date!")

        st.divider()

        st.subheader("📈 Performance Dashboard")
        perf_date = st.date_input("Date", value=today_ist(), key="perf_date_tab")
        perf_date_str = perf_date.strftime("%Y-%m-%d")
        try:
            tasks_resp = supabase.table("daily_tasks").select("*").eq("date", perf_date_str).execute()
            tasks = tasks_resp.data if tasks_resp.data else []
        except:
            tasks = []

        if not tasks:
            st.info("No data for selected date!")
        else:
            tasks_df = pd.DataFrame(tasks)
            st.markdown("### 👥 Team Performance")
            person_summary = tasks_df.groupby(["person","team","task_type"]).size().reset_index(name="count")
            st.dataframe(person_summary, width='stretch')
            st.bar_chart(tasks_df.groupby("person").size())

    with tab4:
        st.subheader("📝 Submit Entry")
        tabs_entry = st.tabs(["🛒 Purchase","📋 Arrangement","🧾 Bill Upload",
                              "📞 Call","🚚 Delivery","🚛 Book Porter",
                              "🚛 Handover","📦 Receive","💰 Payment","✏️ Other"])
        with tabs_entry[0]: form_purchase_order()
        with tabs_entry[1]: form_arrangement()
        with tabs_entry[2]: form_bill_upload()
        with tabs_entry[3]: form_call_log()
        with tabs_entry[4]: form_delivery()
        with tabs_entry[5]: form_book_porter()
        with tabs_entry[6]: form_porter_handover()
        with tabs_entry[7]: form_porter_receive()
        with tabs_entry[8]: form_porter_payment()
        with tabs_entry[9]: form_other_task()

    with tab5:
        st.subheader("👥 User Management")
        tab_u1, tab_u2 = st.tabs(["➕ Add User","👥 Manage Users"])
        with tab_u1:
            with st.form("add_user_form", clear_on_submit=True):
                c1,c2 = st.columns(2)
                with c1:
                    new_username = st.text_input("Username *")
                    new_name     = st.text_input("Full Name *")
                    new_password = st.text_input("Password *")
                with c2:
                    new_team = st.selectbox("Team", ["Purchase","Stock","Call","Delivery","Admin"], key="nu_team")
                    new_role = st.selectbox("Role", ["user","manager","admin"], key="nu_role",
                                            help="manager = own work + Team View (no settings/passwords)")
                    new_phone = st.text_input("Mobile (for WhatsApp reminders)", placeholder="98XXXXXXXX")
                if st.form_submit_button("Add User ✅", type="primary", width='stretch'):
                    if not new_username or not new_name or not new_password:
                        st.error("Fill all fields!")
                    else:
                        try:
                            check = supabase.table("app_users").select("id").eq("username", new_username).execute()
                            if check.data:
                                st.error(f"❌ Username already exists!")
                            else:
                                supabase.table("app_users").insert({
                                    "username": new_username, "password": new_password,
                                    "name": new_name, "team": new_team,
                                    "role": new_role, "active": True,
                                    **({"phone": new_phone.strip()} if new_phone.strip() else {})
                                }).execute()
                                load_users.clear()
                                st.success(f"✅ {new_name} added!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        with tab_u2:
            try:
                users_resp = supabase.table("app_users").select("*").order("team").execute()
                with st.expander("📱 Mobile numbers & roles", expanded=False):
                    act_users = [u for u in (users_resp.data or []) if u.get("active") and u.get("role") != "admin"]
                    if act_users and "phone" not in act_users[0]:
                        st.warning("Run the new line in attendance_setup.sql in Supabase first (adds the phone column).")
                    elif act_users:
                        ph_df = pd.DataFrame([{"id": u["id"], "Name": u["name"], "Team": u.get("team",""),
                                               "Mobile": u.get("phone") or "", "Role": u.get("role") or "user"} for u in act_users])
                        ph_ed = st.data_editor(ph_df, key="phone_editor", hide_index=True, width='stretch',
                                               disabled=["Name","Team"],
                                               column_config={"id": None,
                                                              "Role": st.column_config.SelectboxColumn("Role", options=["user","manager"], required=True,
                                                                        help="manager = own work + 👥 Team View")})
                        if st.button("💾 Save", key="save_phones", type="primary"):
                            old = {u["id"]: (u.get("phone") or "", u.get("role") or "user") for u in act_users}
                            done, failed = [], []
                            for _, r in ph_ed.iterrows():
                                uid = int(r["id"])
                                new = (str(r["Mobile"] or "").strip(), str(r["Role"] or "user"))
                                if new == old.get(uid, ("", "user")):
                                    continue
                                try:
                                    supabase.table("app_users").update({"phone": new[0], "role": new[1]}).eq("id", uid).execute()
                                    chk = supabase.table("app_users").select("role,phone").eq("id", uid).execute().data or []
                                    if chk and (chk[0].get("role") or "user") == new[1]:
                                        done.append(r["Name"])
                                    else:
                                        failed.append(f"{r['Name']}: database did not accept the change")
                                except Exception as e:
                                    failed.append(f"{r['Name']}: {e}")
                            load_users.clear()
                            if done:
                                st.success(f"✅ Saved: {', '.join(done)} — a new role applies after that person logs out and in again")
                            for f in failed:
                                st.error(f"❌ {f} — run fix_roles.sql in Supabase (see Claude's note), then try again")
                            if not done and not failed:
                                st.info("Nothing changed — edit a cell first, then Save.")
                if users_resp.data:
                    for u in users_resp.data:
                        c1,c2,c3,c4,c5 = st.columns([2,2,2,1,1])
                        with c1: st.markdown(f"👤 **{u['name']}**")
                        with c2: st.markdown(f"🔑 `{u['username']}`")
                        with c3: st.markdown(f"🔒 `{u['password']}`")
                        with c4: st.markdown("✅" if u.get("active") else "❌")
                        with c5:
                            if u.get("active"):
                                if st.button("Deactivate", key=f"deact_{u['id']}"):
                                    supabase.table("app_users").update({"active": False}).eq("id", u["id"]).execute()
                                    st.rerun()
                            else:
                                if st.button("Activate", key=f"act_{u['id']}"):
                                    supabase.table("app_users").update({"active": True}).eq("id", u["id"]).execute()
                                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

        st.divider()
        st.subheader("🏭 Warehouses, Areas & Distributors")
        tab_w, tab_a, tab_d = st.tabs(["🏭 Warehouses","📍 Areas","🚚 Distributors"])
        with tab_d:
            show_distributors_admin("adm_dist")
        with tab_w:
            c1,c2 = st.columns(2)
            with c1:
                with st.form("add_warehouse", clear_on_submit=True):
                    wh_name = st.text_input("Warehouse Name *")
                    wh_loc  = st.text_input("Location")
                    if st.form_submit_button("Add ✅"):
                        if wh_name:
                            try:
                                supabase.table("warehouses").insert({"name": wh_name, "location": wh_loc}).execute()
                                st.success(f"✅ {wh_name} added!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
            with c2:
                try:
                    wh_resp = supabase.table("warehouses").select("*").eq("active", True).execute()
                    if wh_resp.data:
                        for wh in wh_resp.data:
                            c1,c2 = st.columns([3,1])
                            with c1: st.markdown(f"🏭 **{wh['name']}**")
                            with c2:
                                if st.button("Remove", key=f"rm_wh_{wh['id']}"):
                                    supabase.table("warehouses").update({"active": False}).eq("id", wh["id"]).execute()
                                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        with tab_a:
            c1,c2 = st.columns(2)
            with c1:
                with st.form("add_area", clear_on_submit=True):
                    area_name = st.text_input("Area Name *")
                    if st.form_submit_button("Add ✅"):
                        if area_name:
                            try:
                                supabase.table("areas").insert({"name": area_name}).execute()
                                load_areas.clear()
                                st.success(f"✅ {area_name} added!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
            with c2:
                try:
                    area_resp = supabase.table("areas").select("*").eq("active", True).execute()
                    if area_resp.data:
                        for area in area_resp.data:
                            c1,c2 = st.columns([3,1])
                            with c1: st.markdown(f"📍 **{area['name']}**")
                            with c2:
                                if st.button("Remove", key=f"rm_area_{area['id']}"):
                                    supabase.table("areas").update({"active": False}).eq("id", area["id"]).execute()
                                    load_areas.clear()
                                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    with tab6:
        st.subheader("📥 Download Reports")
        c1,c2,c3 = st.columns(3)
        with c1: sel_team   = st.selectbox("Team", ["All","Purchase","Stock","Call","Delivery"], key="r_team")
        with c2: date_f     = st.selectbox("Period", ["Today","Yesterday","Last 7 Days","Last 30 Days","All Time"], key="r_date")
        with c3: sel_person = st.text_input("Person Name", placeholder="Leave blank for all", key="r_person")

        try:
            from datetime import timedelta
            _today = today_ist()
            _from = {"Today": _today, "Yesterday": _today - timedelta(days=1),
                     "Last 7 Days": _today - timedelta(days=7), "Last 30 Days": _today - timedelta(days=30)}.get(date_f)
            _to = _today - timedelta(days=1) if date_f == "Yesterday" else _today
            def _rep_filter(q):
                if _from:
                    q = q.gte("date", _from.strftime("%Y-%m-%d")).lte("date", _to.strftime("%Y-%m-%d"))
                if sel_team != "All":
                    q = q.eq("team", sel_team)
                return q
            all_rows  = fetch_all("daily_tasks", _rep_filter)   # all rows, not just the first 1000
            filtered  = pd.DataFrame(all_rows) if all_rows else pd.DataFrame()
            if not filtered.empty:
                filtered["date"] = pd.to_datetime(filtered["date"])
                if sel_team != "All": filtered = filtered[filtered["team"]==sel_team]
                if sel_person: filtered = filtered[filtered["person"].str.contains(sel_person, case=False)]
                if date_f == "Today": filtered = filtered[filtered["date"]==pd.to_datetime(date_str())]
                elif date_f == "Yesterday": filtered = filtered[filtered["date"]==pd.to_datetime(date_str())-pd.Timedelta(days=1)]
                elif date_f == "Last 7 Days": filtered = filtered[filtered["date"]>=pd.Timestamp.now()-pd.Timedelta(days=7)]
                elif date_f == "Last 30 Days": filtered = filtered[filtered["date"]>=pd.Timestamp.now()-pd.Timedelta(days=30)]
                st.markdown(f"**{len(filtered)} tasks found**")
                st.dataframe(filtered.sort_values("date", ascending=False), width='stretch')
                c1,c2 = st.columns(2)
                with c1:
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine="openpyxl") as w:
                        filtered.to_excel(w, index=False)
                    st.download_button("⬇️ Excel", buf.getvalue(),
                        f"rapidsurge_{date_str()}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl_excel_tab")
                with c2:
                    st.download_button("⬇️ CSV", filtered.to_csv(index=False).encode(),
                        f"rapidsurge_{date_str()}.csv", "text/csv", key="dl_csv_tab")
        except Exception as e:
            st.error(f"Error: {e}")




def show_forms_section():
    st.subheader("📝 Submit Entry")
    tabs = st.tabs(["🛒 Purchase","📋 Arrangement","🧾 Bill Upload","📞 Call","🚚 Delivery","🚛 Book Porter","🚛 Handover","📦 Receive","💰 Payment","✏️ Other"])
    with tabs[0]: form_purchase_order()
    with tabs[1]: form_arrangement()
    with tabs[2]: form_bill_upload()
    with tabs[3]: form_call_log()
    with tabs[4]: form_delivery()
    with tabs[5]: form_book_porter()
    with tabs[6]: form_porter_handover()
    with tabs[7]: form_porter_receive()
    with tabs[8]: form_porter_payment()
    with tabs[9]: form_other_task()

def main():
    if not st.session_state.logged_in:
        show_login()
    else:
        show_sidebar()
        if st.session_state.role == "admin":
            show_admin_page()
        else:
            show_user_page()

if __name__ == "__main__":
    main()
