
import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
import io
import pytz
from supabase import create_client

st.set_page_config(
    page_title="RapidSurge Warehouse",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

def load_warehouses():
    try:
        resp = supabase.table("warehouses").select("*").eq("active", True).execute()
        return [w["name"] for w in resp.data] if resp.data else ["Warehouse 1","Warehouse 2","Warehouse 3"]
    except:
        return ["Warehouse 1","Warehouse 2","Warehouse 3"]

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
                "role": u["role"]
            }
        return users
    except:
        return {}

USERS = load_users()

DISTRIBUTORS = [
    "Acorns Health Solutions Private Limited","Admire Enterprises",
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
    "Vtc Tradewings Pvt Ltd","Xcelent Pharmaceuticals Private Limited",
]

IMG_FOLDER = "images"
os.makedirs(IMG_FOLDER, exist_ok=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
for k,v in [("logged_in",False),("username",""),("name",""),("team",""),("role","")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── IMAGE UPLOAD ──────────────────────────────────────────────────────────────
def upload_image(file, prefix="img"):
    if file is None:
        return ""
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
        st.markdown("### Warehouse Management System")
        st.markdown("---")
        username = st.text_input("👤 Username", placeholder="Enter username")
        password = st.text_input("🔒 Password", type="password", placeholder="Enter password")
        if st.button("🚀 Login", use_container_width=True, type="primary"):
            if username in USERS and USERS[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.name = USERS[username]["name"]
                st.session_state.team = USERS[username]["team"]
                st.session_state.role = USERS[username]["role"]
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
        quotes = [
            "💪 Great things never come from comfort zones!",
            "🎯 Success is the sum of small efforts repeated daily!",
            "🔥 Push yourself because no one else will do it for you!",
            "⭐ Hard work beats talent when talent doesn't work hard!",
            "🚀 The only way to do great work is to love what you do!",
            "💡 Every expert was once a beginner. Keep going!",
            "🏆 Champions keep playing until they get it right!",
        ]
        st.info(quotes[today_ist().weekday()])
        st.divider()

        # Personal stats
        try:
            from datetime import timedelta
            yesterday = (today_ist() - timedelta(days=1)).strftime("%Y-%m-%d")
            yest_resp = supabase.table("daily_tasks").select("id")\
                .eq("person", st.session_state.name)\
                .eq("date", yesterday).execute()
            yest_count = len(yest_resp.data) if yest_resp.data else 0
            today_resp = supabase.table("daily_tasks").select("id")\
                .eq("person", st.session_state.name)\
                .eq("date", date_str()).execute()
            today_count = len(today_resp.data) if today_resp.data else 0
            st.markdown("**📊 Your Performance:**")
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
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            for k in ["logged_in","username","name","team","role"]:
                st.session_state[k] = False if k=="logged_in" else ""
            st.rerun()

# ── TIMER BUTTON ──────────────────────────────────────────────────────────────
def timer_button(key, task_name=None):
    sk = f"{key}_start"
    if sk not in st.session_state:
        st.session_state[sk] = None

    if st.session_state[sk] is None:
        st.info("👆 Click START when you begin this task")
        if st.button("▶️ Start", key=f"btn_{key}", type="primary"):
            st.session_state[sk] = now_ist()
            st.rerun()
        return None
    else:
        elapsed = int((now_ist() - st.session_state[sk]).total_seconds() / 60)
        st.success(f"⏱️ Started at {st.session_state[sk].strftime('%I:%M %p')} — {elapsed} mins elapsed")
        return st.session_state[sk]

def end_timer(key, start_time):
    end = now_ist()
    duration = int((end - start_time).total_seconds() / 60)
    st.session_state[f"{key}_start"] = None
    # Update In Progress record to Completed
    task_id = st.session_state.get(f"{key}_task_id")
    if task_id:
        try:
            supabase.table("daily_tasks").update({
                "end_time": end.strftime("%I:%M %p"),
                "duration_mins": str(duration),
                "status": "Completed"
            }).eq("id", task_id).execute()
        except:
            pass
        st.session_state[f"{key}_task_id"] = None
    return end.strftime("%I:%M %p"), duration

# ── PURCHASE TEAM FORMS ───────────────────────────────────────────────────────
def form_purchase_order():
    st.subheader("🛒 Purchase Order")
    start = timer_button("purchase_order")
    if start is None: return
    with st.form("purchase_order_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            distributor = st.selectbox("Distributor *", DISTRIBUTORS, key="po_dist")
            order_type  = st.selectbox("Order Type", ["Regular","Arrangement"], key="po_type")
            no_sku      = st.number_input("No of SKUs", min_value=0, step=1)
        with c2:
            mode        = st.selectbox("Mode", ["Through Call","Pharma Rack","Excel Send"], key="po_mode")
            urgency     = st.selectbox("Urgency", ["Normal","Urgent","Very Urgent"], key="po_urgency")
        remarks = st.text_input("Remarks")
        if st.form_submit_button("Submit ✅", type="primary", use_container_width=True):
            end_time, duration = end_timer("purchase_order", start)
            try:
                supabase.table("daily_tasks").insert({
                    "date": date_str(), "time": time_str(),
                    "person": st.session_state.name, "team": "Purchase",
                    "task_type": "Purchase Order",
                    "details": {"distributor": distributor, "order_type": order_type,
                               "no_sku": str(no_sku), "mode": mode, "urgency": urgency,
                               "remarks": remarks},
                    "start_time": start.strftime("%I:%M %p"),
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
        if st.form_submit_button("Submit ✅", type="primary", use_container_width=True):
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
                        "start_time": start.strftime("%I:%M %p"),
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
        if st.form_submit_button("Submit ✅", type="primary", use_container_width=True):
            end_time, duration = end_timer("pharmarack", start)
            try:
                supabase.table("daily_tasks").insert({
                    "date": date_str(), "time": time_str(),
                    "person": st.session_state.name, "team": "Purchase",
                    "task_type": "PharmaRack Search",
                    "details": {"no_searched": str(no_searched), "no_found": str(no_found),
                               "no_not_found": str(no_not_found), "no_ordered": str(no_ordered),
                               "remarks": remarks},
                    "start_time": start.strftime("%I:%M %p"),
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
            upload_opt = st.radio("Image Option", ["Upload","Camera"], horizontal=True, key="bounce_radio", label_visibility="collapsed")
        if upload_opt == "Upload":
            img = st.file_uploader("Select Image", type=["jpg","jpeg","png"], key="bounce_upload")
        else:
            img = st.camera_input("Take Photo", key="bounce_cam")
        remarks = st.text_input("Remarks")
        if st.form_submit_button("Submit ✅", type="primary", use_container_width=True):
            end_time, duration = end_timer("bounce", start)
            img_name = upload_image(img, "bounce") if img else ""
            try:
                supabase.table("daily_tasks").insert({
                    "date": date_str(), "time": time_str(),
                    "person": st.session_state.name, "team": "Purchase",
                    "task_type": "Bounce Medicine Study",
                    "details": {"no_bounced": str(no_bounced), "no_useful": str(no_useful),
                               "image": img_name, "remarks": remarks},
                    "start_time": start.strftime("%I:%M %p"),
                    "end_time": end_time, "duration_mins": str(duration)
                }).execute()
                st.success("✅ Bounce Medicine Study submitted!")
                st.balloons()
            except Exception as e:
                st.error(f"Error: {e}")

# ── ARRANGEMENT FORM ──────────────────────────────────────────────────────────
def form_arrangement():
    st.subheader("📋 New Arrangement Order")

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

    with st.form("arrangement_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            arr_no        = st.text_input("Arrangement No", value=auto_arr_no, disabled=True)
            distributor   = st.selectbox("Distributor *", DISTRIBUTORS, key="arr_dist")
            area          = st.selectbox("Customer Area *", AREAS, key="arr_area")
            bill_order_id = st.text_input("Bill Number / Order ID")
        with c2:
            urgency       = st.selectbox("Urgency", ["Normal","Urgent","Very Urgent"], key="arr_urgency")
            pickup_type   = st.selectbox("Pickup Type", ["Self Pick","Porter","Distributor Delivers"], key="arr_pickup")
            no_medicines  = st.number_input("No of Medicines to Pick", min_value=0, step=1)
            order_time    = st.text_input("Order Time", value=time_str())

        medicines = st.text_area("Medicines (one per line) *", placeholder="Medicine 1 - Qty\nMedicine 2 - Qty")
        st.markdown("📸 **Image of Order**")
        upload_opt = st.radio("Image Option", ["Upload","Camera"], horizontal=True, key="arr_radio", label_visibility="collapsed")
        if upload_opt == "Upload":
            img = st.file_uploader("Select Image", type=["jpg","jpeg","png"], key="arr_upload")
        else:
            img = st.camera_input("Take Photo", key="arr_cam")
        remarks = st.text_input("Remarks")

        if st.form_submit_button("Submit ✅", type="primary", use_container_width=True):
            if not arr_no or not medicines:
                st.error("Fill Arrangement No and Medicines!")
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
                        img_name = upload_image(img, "arr") if img else ""
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
                        for med in medicines.strip().split("\n"):
                            if med.strip():
                                parts = med.split("-")
                                med_name = parts[0].strip()
                                qty = parts[1].strip() if len(parts) > 1 else "1"
                                supabase.table("arrangement_medicines").insert({
                                    "arrangement_id": arr_id,
                                    "medicine_name": med_name,
                                    "quantity": qty
                                }).execute()
                        st.success(f"✅ Arrangement #{arr_no} placed successfully!")
                        st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")

# ── STOCK TEAM FORMS ──────────────────────────────────────────────────────────
def form_bill_upload():
    st.subheader("🧾 Bill Upload")
    with st.form("bill_upload_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            distributor  = st.selectbox("Distributor *", DISTRIBUTORS, key="bu_dist")
            bill_no      = st.text_input("Bill Number *")
            bill_date    = st.date_input("Bill Date")
        with c2:
            delivery_by  = st.selectbox("Delivery By", ["Porter","Naresh","Sandeep","Distributor"], key="bu_del")
            order_type   = st.selectbox("Order Type", ["Regular","Arrangement"], key="bu_type")
        st.markdown("📸 **Bill Image**")
        upload_opt = st.radio("Image Option", ["Upload","Camera"], horizontal=True, key="bu_radio", label_visibility="collapsed")
        if upload_opt == "Upload":
            img = st.file_uploader("Select Image", type=["jpg","jpeg","png","pdf"], key="bu_upload")
        else:
            img = st.camera_input("Take Photo", key="bu_cam")
        remarks = st.text_input("Remarks")
        if st.form_submit_button("Submit ✅", type="primary", use_container_width=True):
            if not bill_no:
                st.error("Fill Bill Number!")
            else:
                img_name = upload_image(img, "bill") if img else ""
                try:
                    supabase.table("daily_tasks").insert({
                        "date": date_str(), "time": time_str(),
                        "person": st.session_state.name, "team": "Stock",
                        "task_type": "Bill Upload",
                        "details": {"distributor": distributor, "bill_no": bill_no,
                                   "bill_date": str(bill_date), "delivery_by": delivery_by,
                                   "order_type": order_type, "image": img_name,
                                   "remarks": remarks, "check_status": "Unchecked"},
                        "start_time": time_str(), "end_time": time_str()
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
        if st.form_submit_button("Submit ✅", type="primary", use_container_width=True):
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
                        "start_time": start.strftime("%I:%M %p"),
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
        if st.form_submit_button("Submit ✅", type="primary", use_container_width=True):
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
                        "start_time": start.strftime("%I:%M %p"),
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

        if st.form_submit_button("Submit ✅", type="primary", use_container_width=True):
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
                    "start_time": start.strftime("%I:%M %p"),
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
        if st.form_submit_button("Submit ✅", type="primary", use_container_width=True):
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
                    "start_time": start.strftime("%I:%M %p"),
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
        st.info(f"📋 Area: **{preview_arr.get('area','N/A')}** | Bill/Order ID: **{preview_arr.get('bill_order_id','N/A')}** | Medicines to Pick: **{preview_arr.get('no_medicines','N/A')}**")
        order_img = preview_arr.get("order_image","")
        if order_img and order_img.strip():
            st.markdown("**📄 Invoice Image from Purchase Team:**")
            try:
                img_data = supabase.storage.from_("Images").download(order_img.strip())
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(img_data))
                st.image(img, caption=f"Invoice - {preview_arr.get('arrangement_no','')}", width=400)
            except Exception as img_err:
                st.warning(f"⚠️ Image error: {img_err}")
        else:
            st.warning("⚠️ No invoice image uploaded by Purchase Team for this arrangement")

    with st.form("pickup_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            distributor   = st.selectbox("Distributor *", DISTRIBUTORS, key="pu_dist")
            arr_select    = st.selectbox("Arrangement No", ["—"] + list(arr_options.keys()), key="pu_arr")
            delivery_by   = st.selectbox("Delivery By", ["Self Pick","Distributor"], key="pu_delby")
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
        st.markdown("**📸 Image of Medicine Received**")
        upload_opt = st.radio("Image Option", ["Upload","Camera"], horizontal=True, key="pu_radio", label_visibility="collapsed")
        if upload_opt == "Upload":
            medicine_img = st.file_uploader("Select Image", type=["jpg","jpeg","png"], key="pu_upload")
        else:
            medicine_img = st.camera_input("Take Photo", key="pu_cam")

        remarks = st.text_input("Remarks")

        if st.form_submit_button("Submit ✅", type="primary", use_container_width=True):
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
            if st.form_submit_button("▶️ Start Trip", type="primary", use_container_width=True):
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
        if st.button("✅ Complete This Activity", type="primary", use_container_width=True):
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
        if st.form_submit_button("Submit ✅", type="primary", use_container_width=True):
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
                        "start_time": start.strftime("%I:%M %p"),
                        "end_time": end_time, "duration_mins": str(duration)
                    }).execute()
                    st.success("✅ Task submitted!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")

# ── STOCK PLACEMENT & CROSS CHECK FORMS ──────────────────────────────────────

def form_stock_placement():
    st.subheader("📍 Stock Placement")

    # Load Bill Uploaded arrangements
    try:
        from datetime import timedelta
        two_days_ago = (today_ist() - timedelta(days=2)).strftime("%Y-%m-%d")
        arr_resp = supabase.table("arrangements").select("*")\
            .eq("status", "Bill Uploaded")\
            .gte("order_placed_date", two_days_ago)\
            .execute()
        arrangements = arr_resp.data if arr_resp.data else []
    except Exception as e:
        st.error(f"Error: {e}")
        arrangements = []

    # Load Normal Orders with bill uploaded
    try:
        from datetime import timedelta
        two_days_ago = (today_ist() - timedelta(days=2)).strftime("%Y-%m-%d")
        normal_resp = supabase.table("daily_tasks").select("*")\
            .eq("task_type", "Bill Upload")\
            .gte("date", two_days_ago)\
            .execute()
        normal_orders = []
        for t in (normal_resp.data or []):
            d = t.get("details",{})
            if not d.get("arrangement_no","") and not d.get("placement_done"):
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
            st.warning("No medicines found for this arrangement — they may not have been entered during order placement!")
            total_items = st.number_input("Total Items Placed", min_value=0, step=1)

        st.divider()
        st.markdown("**📸 Photo of Placement Area**")
        upload_opt = st.radio("", ["Upload","Camera"], horizontal=True,
            key="sp_radio", label_visibility="collapsed")
        if upload_opt == "Upload":
            placement_img = st.file_uploader("Select Image",
                type=["jpg","jpeg","png"], key="sp_upload")
        else:
            placement_img = st.camera_input("Take Photo", key="sp_cam")

        remarks = st.text_input("Remarks")

        if st.form_submit_button("Submit Placement ✅", type="primary", use_container_width=True):
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
                        "distributor": selected_data.get("distributor","") if item_type=="arrangement" else selected_data.get("details",{}).get("distributor",""),
                        "no_medicines": str(len(medicines)),
                        "placement_image": img_name,
                        "remarks": remarks
                    },
                    "start_time": start.strftime("%I:%M %p"),
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

        if st.form_submit_button("Submit Cross Check ✅", type="primary", use_container_width=True):
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

def form_register_entry():
    st.subheader("📒 Register Entry")
    st.caption("Quick entry when stock arrives — no need to make distributor/porter wait!")

    with st.form("register_entry_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            order_type  = st.selectbox("Order Type *", ["Normal Order","Arrangement"], key="re_type")
            distributor = st.selectbox("Distributor *", DISTRIBUTORS, key="re_dist")
            bill_no     = st.text_input("Bill Number *")
        with c2:
            no_items    = st.number_input("No of Items Received *", min_value=0, step=1)
            delivery_by = st.selectbox("Delivered By", ["Distributor","Porter","Naresh","Sandeep","Other"], key="re_delby")

        # Show arrangement dropdown if arrangement selected
        arr_no = ""
        if order_type == "Arrangement":
            try:
                from datetime import timedelta
                two_days_ago = (today_ist() - timedelta(days=2)).strftime("%Y-%m-%d")
                resp = supabase.table("arrangements").select("*")\
                    .eq("status", "Reached Warehouse")\
                    .gte("order_placed_date", two_days_ago)\
                    .execute()
                arr_list = resp.data if resp.data else []
                if arr_list:
                    arr_options = ["—"] + [f"#{a.get('arrangement_no')} — {a.get('distributor','')}" for a in arr_list]
                    arr_select = st.selectbox("Arrangement No", arr_options, key="re_arr")
                    if arr_select != "—":
                        arr_no = arr_select.split("—")[0].replace("#","").strip()
                else:
                    st.info("No arrangements found!")
            except Exception as e:
                st.error(f"Error: {e}")

        bill_amount = st.number_input("Bill Amount (₹)", min_value=0.0, step=100.0, key="re_amount")
        remarks = st.text_input("Remarks", placeholder="Any notes about delivery condition...")

        if st.form_submit_button("Submit Entry ✅", type="primary", use_container_width=True):
            if not bill_no or no_items == 0:
                st.error("Fill Bill Number and No of Items!")
            else:
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

    # Load arrangements that reached warehouse
    try:
        from datetime import timedelta
        two_days_ago = (today_ist() - timedelta(days=2)).strftime("%Y-%m-%d")
        resp = supabase.table("arrangements").select("*")\
            .eq("status", "Reached Warehouse")\
            .gte("order_placed_date", two_days_ago)\
            .execute()
        arrangements = resp.data if resp.data else []
    except Exception as e:
        st.error(f"Error: {e}")
        arrangements = []

    # Load normal orders from register entry
    try:
        normal_resp = supabase.table("daily_tasks").select("*")\
            .eq("task_type", "Register Entry")\
            .eq("date", date_str())\
            .execute()
        normal_orders = normal_resp.data if normal_resp.data else []
        # Filter out already cross checked
        normal_orders = [n for n in normal_orders 
                        if not n.get("details",{}).get("cross_checked")]
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

    start = timer_button("bill_crosscheck")
    if start is None:
        return

    with st.form("bill_crosscheck_form", clear_on_submit=True):
        selected_label = st.selectbox("Select Item *", list(arr_options.keys()), key="bc_arr")
        selected_item  = arr_options[selected_label]
        item_type      = selected_item["type"]
        selected_data  = selected_item["data"]

        if item_type == "arrangement":
            st.info(f"📋 Distributor: **{selected_data.get('distributor','')}** | Area: **{selected_data.get('area','')}** | Arrangement: **{selected_data.get('arrangement_no','')}**")
            bill_no = st.text_input("Bill Number", value=selected_data.get("bill_order_id",""))
        else:
            d = selected_data.get("details",{})
            st.info(f"📋 Distributor: **{d.get('distributor','')}** | Bill: **{d.get('bill_no','')}** | Items: **{d.get('no_items','')}** | Amount: ₹**{d.get('bill_amount','')}**")
            bill_no = st.text_input("Bill Number", value=d.get("bill_no",""))

        c1,c2,c3 = st.columns(3)
        with c1:
            no_items     = st.number_input("No of Items Checked", min_value=0, step=1)
            near_expiry  = st.number_input("Near Expiry Items", min_value=0, step=1)
            damaged      = st.number_input("Damaged Items", min_value=0, step=1)
        with c2:
            contra       = st.number_input("Contra Items (Wrong Medicine)", min_value=0, step=1)
            wrong_batch  = st.number_input("Wrong Batch", min_value=0, step=1)
            wrong_disc   = st.number_input("Wrong Discount", min_value=0, step=1)
        with c3:
            wrong_calc   = st.number_input("Wrong Calculation", min_value=0, step=1)
            shortage     = st.number_input("Shortage Items", min_value=0, step=1)

        st.markdown("---")
        st.markdown("📹 **Video Evidence**")
        st.markdown("[📁 Open RapidSurge Stock Videos Folder](https://drive.google.com/drive/folders/1DbkuKSFeftMVpVFqVwcRRDssc49X9YJQ)")
        st.caption("Record video → Upload to folder → Copy link → Paste below")
        video_link = st.text_input("Paste Video Link", placeholder="https://drive.google.com/file/d/...")
        remarks = st.text_input("Remarks")

        if st.form_submit_button("Submit Cross Check ✅", type="primary", use_container_width=True):
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
                        "distributor": dist,
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
                        "remarks": remarks
                    },
                    "start_time": start.strftime("%I:%M %p"),
                    "end_time": end_time,
                    "duration_mins": str(duration)
                }).execute()

                st.success(f"✅ Bill Cross Check done! Avg time per item: {avg_time} mins")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

def form_bill_upload_arrangement():
    st.subheader("📤 Bill Upload")

    # Load cross checked arrangements
    try:
        from datetime import timedelta
        two_days_ago = (today_ist() - timedelta(days=2)).strftime("%Y-%m-%d")
        arr_resp = supabase.table("arrangements").select("*")\
            .eq("status", "Bill Cross Checked")\
            .gte("order_placed_date", two_days_ago)\
            .execute()
        arrangements = arr_resp.data if arr_resp.data else []
    except Exception as e:
        st.error(f"Error: {e}")
        arrangements = []

    # Load cross checked normal orders (last 2 days)
    try:
        from datetime import timedelta
        two_days_ago = (today_ist() - timedelta(days=2)).strftime("%Y-%m-%d")
        normal_resp = supabase.table("daily_tasks").select("*")\
            .eq("task_type", "Bill Cross Check")\
            .gte("date", two_days_ago)\
            .execute()
        cross_checked_normal = []
        for t in (normal_resp.data or []):
            d = t.get("details",{})
            # Show only normal orders (no arrangement_no) not yet uploaded
            if not d.get("arrangement_no","") and not d.get("bill_uploaded"):
                cross_checked_normal.append(t)
    except Exception as e:
        st.error(f"Error loading normal orders: {e}")
        cross_checked_normal = []

    if not arrangements and not cross_checked_normal:
        st.info("No items pending bill upload!")
        return

    # Show pending counts
    st.markdown(f"**Pending:** {len(arrangements)} Arrangements + {len(cross_checked_normal)} Normal Orders")

    # Build combined options
    all_options = {}
    for a in arrangements:
        all_options[f"ARR: #{a.get('arrangement_no')} — {a.get('distributor','')} — {a.get('area','')}"] = {"type": "arrangement", "data": a}
    for n in cross_checked_normal:
        d = n.get("details",{})
        all_options[f"NORMAL: {d.get('distributor','')} — Bill: {d.get('bill_no','')} — Items: {d.get('no_items','')}"] = {"type": "normal", "data": n}

    with st.form("bill_upload_arr_form", clear_on_submit=True):
        selected_label = st.selectbox("Select Item *", list(all_options.keys()), key="ba_arr")
        selected_item  = all_options[selected_label]
        item_type      = selected_item["type"]
        selected_data  = selected_item["data"]

        # Auto fill details
        if item_type == "arrangement":
            auto_bill_no  = selected_data.get("bill_order_id","")
            auto_dist     = selected_data.get("distributor","")
            auto_area     = selected_data.get("area","")
            auto_items    = 0
            auto_amount   = 0.0
            st.info(f"📋 Distributor: **{auto_dist}** | Area: **{auto_area}**")
        else:
            d = selected_data.get("details",{})
            auto_bill_no  = d.get("bill_no","")
            auto_dist     = d.get("distributor","")
            auto_area     = ""
            auto_items    = int(d.get("no_items",0) or 0)
            auto_amount   = float(d.get("bill_amount",0) or 0)
            st.info(f"📋 Distributor: **{auto_dist}** | Bill: **{auto_bill_no}** | Items: **{auto_items}** | Amount: ₹**{auto_amount}**")

        c1,c2 = st.columns(2)
        with c1:
            bill_no   = st.text_input("Bill Number *", value=auto_bill_no)
            bill_date = st.date_input("Bill Date")
            bill_amt  = st.number_input("Bill Amount (₹)", min_value=0.0, step=100.0, value=auto_amount)
        with c2:
            no_items   = st.number_input("No of Items", min_value=0, step=1, value=auto_items)
            order_type = st.selectbox("Order Type", ["Arrangement","Normal Order"], key="ba_type")

        st.markdown("📸 **Bill Image**")
        upload_opt = st.radio("", ["Upload","Camera"], horizontal=True,
            key="ba_radio", label_visibility="collapsed")
        if upload_opt == "Upload":
            bill_img = st.file_uploader("Select Bill Image",
                type=["jpg","jpeg","png","pdf"], key="ba_upload")
        else:
            bill_img = st.camera_input("Take Photo", key="ba_cam")

        remarks = st.text_input("Remarks")

        if st.form_submit_button("Upload Bill ✅", type="primary", use_container_width=True):
            if not bill_no:
                st.error("Enter Bill Number!")
            else:
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

                    # Save to daily tasks
                    supabase.table("daily_tasks").insert({
                        "date": date_str(), "time": time_str(),
                        "person": st.session_state.name, "team": st.session_state.team,
                        "task_type": "Bill Upload",
                        "details": {
                            "arrangement_no": arr_no,
                            "distributor": dist,
                            "bill_no": bill_no,
                            "bill_date": str(bill_date),
                            "bill_amount": str(bill_amt),
                            "no_items": str(no_items),
                            "order_type": order_type,
                            "bill_image": img_name,
                            "remarks": remarks
                        },
                        "start_time": time_str(),
                        "end_time": time_str(),
                    }).execute()

                    st.success("✅ Bill uploaded successfully!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# ── PICKUP IMAGES VIEWER ─────────────────────────────────────────────────────

def show_pickup_images():
    st.subheader("📸 Pickup Images from Naresh/Sandeep")

    try:
        from datetime import timedelta
        two_days_ago = (today_ist() - timedelta(days=2)).strftime("%Y-%m-%d")

        # Load pickup tasks with images
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

    # Filter by date, distributor and arrangement number
    c1,c2,c3 = st.columns(3)
    with c1:
        filter_date = st.date_input("Filter by Date", value=today_ist(), key="pi_date")
    with c2:
        filter_dist = st.text_input("Search Distributor", placeholder="Type to search...", key="pi_dist")
    with c3:
        filter_arr = st.text_input("Arrangement No", placeholder="e.g. ARR-20260718-001", key="pi_arr")

    filter_date_str = filter_date.strftime("%Y-%m-%d")
    filtered = [p for p in pickups if p.get("date","") == filter_date_str]
    if filter_dist:
        filtered = [p for p in filtered if filter_dist.lower() in p.get("details",{}).get("distributor","").lower()]
    if filter_arr:
        filtered = [p for p in filtered if filter_arr.lower() in p.get("details",{}).get("arrangement_no","").lower()]

    st.markdown(f"**{len(filtered)} pickup entries found**")

    for p in filtered:
        d = p.get("details",{})
        dist      = d.get("distributor","")
        arr_no    = d.get("arrangement_no","")
        img_name  = d.get("medicine_image","")
        pickup_by = p.get("person","")
        pickup_time = p.get("start_time","")
        no_sku    = d.get("no_sku_received","")

        with st.expander(f"📦 {dist} | Arr: {arr_no} | By: {pickup_by} | Time: {pickup_time}"):
            c1,c2 = st.columns([2,1])
            with c1:
                if img_name:
                    try:
                        img_data = supabase.storage.from_("Images").download(img_name)
                        from PIL import Image
                        import io as io_module
                        img = Image.open(io_module.BytesIO(img_data))
                        st.image(img, caption=f"Pickup by {pickup_by}", use_container_width=True)
                    except Exception as e:
                        st.warning(f"Image not available: {e}")
                else:
                    st.warning("⚠️ No image uploaded for this pickup!")
            with c2:
                st.markdown(f"**Distributor:** {dist}")
                st.markdown(f"**Arrangement:** {arr_no}")
                st.markdown(f"**Picked by:** {pickup_by}")
                st.markdown(f"**Time:** {pickup_time}")
                st.markdown(f"**SKUs Received:** {no_sku}")
                if img_name:
                    try:
                        img_data = supabase.storage.from_("Images").download(img_name)
                        st.download_button(
                            "⬇️ Download Image",
                            img_data,
                            file_name=f"pickup_{arr_no}_{pickup_by}.jpg",
                            mime="image/jpeg",
                            key=f"dl_pickup_{p['id']}"
                        )
                    except:
                        pass

# ── PORTER FORMS ─────────────────────────────────────────────────────────────

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
            porter_no    = st.text_input("Porter Number *", placeholder="e.g. 9876543210")
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

        if st.form_submit_button("Book Porter ✅", type="primary", use_container_width=True):
            if not porter_no or not pickup_point or not delivery_point:
                st.error("Fill Porter No, Pickup and Delivery Point!")
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

    # Load porter booked arrangements
    try:
        resp = supabase.table("porter_bookings").select("*")\
            .eq("status", "Booked").execute()
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
        upload_opt = st.radio("Image Option", ["Upload","Camera"], horizontal=True, key="ph_radio", label_visibility="collapsed")
        if upload_opt == "Upload":
            handover_img = st.file_uploader("Select Image", type=["jpg","jpeg","png"], key="ph_upload")
        else:
            handover_img = st.camera_input("Take Photo", key="ph_cam")

        remarks = st.text_input("Remarks")

        if st.form_submit_button("Submit Handover ✅", type="primary", use_container_width=True):
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

    try:
        from datetime import timedelta
        two_days_ago = (today_ist() - timedelta(days=2)).strftime("%Y-%m-%d")

        # All arrangements not yet received
        all_resp = supabase.table("arrangements").select("*")\
            .not_.in_("status", ["Reached Warehouse","Bill Cross Checked",
                                  "Bill Uploaded","Stock Placed","Completed",
                                  "Placement Issue Found"])\
            .gte("order_placed_date", two_days_ago)\
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
            selected_area = st.selectbox("Filter by Area/Warehouse", 
                ["All Areas"] + all_areas, key="incoming_area_filter")
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
            upload_opt = st.radio("", ["Upload","Camera"], horizontal=True,
                key="dr_radio", label_visibility="collapsed")
            if upload_opt == "Upload":
                recv_img = st.file_uploader("Select Image", type=["jpg","jpeg","png"], key="dr_upload")
            else:
                recv_img = st.camera_input("Take Photo", key="dr_cam")

            remarks = st.text_input("Remarks", key="dr_remarks")

            if st.form_submit_button("Confirm Receipt ✅", type="primary", use_container_width=True):
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
            up_opt = st.radio("", ["Upload","Camera"], horizontal=True,
                key=f"pr_radio_{arr_no}", label_visibility="collapsed")
            if up_opt == "Upload":
                img = st.file_uploader(f"Image for #{arr_no}",
                    type=["jpg","jpeg","png"], key=f"pr_upload_{arr_no}")
            else:
                img = st.camera_input(f"Photo for #{arr_no}", key=f"pr_cam_{arr_no}")
            arr_images[arr_no] = img

        remarks = st.text_input("Remarks")

        if st.form_submit_button("Confirm Receipt ✅", type="primary", use_container_width=True):
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
        upload_opt = st.radio("Image Option", ["Upload","Camera"], horizontal=True, key="pp_radio", label_visibility="collapsed")
        if upload_opt == "Upload":
            bill_img = st.file_uploader("Select Image", type=["jpg","jpeg","png"], key="pp_upload")
        else:
            bill_img = st.camera_input("Take Photo", key="pp_cam")

        remarks = st.text_input("Remarks")

        if st.form_submit_button("Submit Payment ✅", type="primary", use_container_width=True):
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
    st.title(f"💊 RapidSurge — {team} Team")
    st.caption(f"👤 {st.session_state.name} | 📅 {today_ist().strftime('%A, %d %B %Y')}")
    st.divider()

    # Check for incomplete In Progress tasks from previous session
    try:
        inprog = supabase.table("daily_tasks").select("*")\
            .eq("person", st.session_state.name)\
            .eq("status", "In Progress")\
            .execute()
        if inprog.data:
            st.warning(f"⚠️ You have {len(inprog.data)} incomplete task(s) from previous session!")
            for t in inprog.data:
                c1,c2,c3 = st.columns([3,1,1])
                with c1:
                    st.markdown(f"**{t.get('task_type','')}** started at {t.get('start_time','')} on {t.get('date','')}")
                with c2:
                    if st.button("✅ Complete", key=f"comp_{t['id']}"):
                        supabase.table("daily_tasks").update({
                            "status": "Completed",
                            "end_time": time_str(),
                            "duration_mins": "0"
                        }).eq("id", t["id"]).execute()
                        st.rerun()
                with c3:
                    if st.button("🗑️ Discard", key=f"disc_{t['id']}"):
                        supabase.table("daily_tasks").delete()\
                            .eq("id", t["id"]).execute()
                        st.rerun()
            st.divider()
    except:
        pass

    if team == "Purchase":
        tabs = st.tabs(["🛒 Purchase Order","↩️ Purchase Return","💊 PharmaRack","📋 Bounce Medicine","📦 Arrangement","🚛 Book Porter","💰 Porter Payment","📸 Pickup Images","📒 Register Entry","✔️ Bill Cross Check","📍 Stock Placement","✏️ Other"])
        with tabs[0]: form_purchase_order()
        with tabs[1]: form_purchase_return()
        with tabs[2]: form_pharmarack()
        with tabs[3]: form_bounce_medicine()
        with tabs[4]: form_arrangement()
        with tabs[5]: form_book_porter()
        with tabs[6]: form_porter_payment()
        with tabs[7]: show_pickup_images()
        with tabs[8]: form_register_entry()
        with tabs[9]: form_bill_crosscheck()
        with tabs[10]: form_stock_placement()
        with tabs[11]: form_other_task()

    elif team == "Stock":
        tabs = st.tabs(["📒 Register Entry","🧾 Bill Upload","✔️ Bill Cross Check","📤 Bill Upload (Arr)","📍 Stock Placement","🔍 Placement Check","🧹 Rack Cleaning","📊 Inventory","🚛 Book Porter","📦 Receive Porter","🛒 Purchase Order","📦 Arrangement","✏️ Other"])
        with tabs[0]: form_register_entry()
        with tabs[1]: form_bill_upload()
        with tabs[2]: form_bill_crosscheck()
        with tabs[3]: form_bill_upload_arrangement()
        with tabs[4]: form_stock_placement()
        with tabs[5]: form_placement_crosscheck()
        with tabs[6]: form_rack_cleaning()
        with tabs[7]: form_inventory_check()
        with tabs[8]: form_book_porter()
        with tabs[9]: form_porter_receive()
        with tabs[10]: form_purchase_order()
        with tabs[11]: form_arrangement()
        with tabs[12]: form_other_task()

    elif team == "Call":
        tabs = st.tabs(["📞 Call Log","🔍 Medicine Search","🚛 Book Porter","✏️ Other"])
        with tabs[0]: form_call_log()
        with tabs[1]: form_medicine_search()
        with tabs[2]: form_book_porter()
        with tabs[3]: form_other_task()

    elif team == "Delivery":
        tabs = st.tabs(["📋 Pending Pickups","🚛 Porter Handover","🚚 Delivery Trip","✏️ Other"])
        with tabs[0]: form_pickup()
        with tabs[1]: form_porter_handover()
        with tabs[2]: form_delivery()
        with tabs[3]: form_other_task()

    st.divider()

    # ── ARRANGEMENT PIPELINE (visible to all) ────────────────────────────────
    with st.expander("🔄 View Today's Arrangement Pipeline", expanded=False):
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
            "other_task": "Other Task",
        }
    elif team == "Stock":
        timer_keys = {
            "bill_crosscheck": "Bill Cross Check",
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
    for key, task_name in timer_keys.items():
        start_time = st.session_state.get(f"{key}_start")
        if start_time:
            elapsed = int((now_ist() - start_time).total_seconds() / 60)
            in_progress.append({
                "Time": start_time.strftime("%I:%M %p"),
                "Task": task_name,
                "Details": "🔄 In Progress...",
                "Start": start_time.strftime("%I:%M %p"),
                "End": "In Progress",
                "Duration": f"{elapsed} mins",
                "Count": "-",
                "Avg/Item": "-",
            })

    if in_progress:
        st.warning(f"⏳ {len(in_progress)} task(s) in progress:")
        st.dataframe(pd.DataFrame(in_progress), use_container_width=True)
    try:
        resp = supabase.table("daily_tasks").select("*")\
            .eq("person", st.session_state.name)\
            .eq("date", date_str()).execute()

        # Also load In Progress tasks from yesterday (not completed)
        inprogress_resp = supabase.table("daily_tasks").select("*")\
            .eq("person", st.session_state.name)\
            .eq("status", "In Progress")\
            .execute()
        inprogress_data = [t for t in (inprogress_resp.data or []) 
                          if t.get("date") != date_str()]

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
        
        # Combine all
        all_data = (resp.data or []) + arr_tasks + inprogress_data
        if resp.data or arr_tasks:
            df = pd.DataFrame(all_data)
            display_rows = []
            total_sku = 0
            total_duration = 0

            for _, row in df.iterrows():
                details = row.get("details", {}) or {}
                try:
                    duration = int(float(row.get("duration_mins",0) or 0))
                except:
                    duration = 0

                # Get SKU based on task type
                if row.get("task_type") == "Purchase Order":
                    try:
                        sku = int(float(details.get("no_sku",0) or 0))
                    except:
                        sku = 0
                    extra = f"SKUs: {sku}"
                elif row.get("task_type") == "Bill Cross Check":
                    sku = int(float(details.get("no_items",0) or 0))
                    extra = f"Items: {sku}"
                elif row.get("task_type") == "Stock Placement":
                    sku = int(float(details.get("no_medicines",0) or 0))
                    extra = f"Medicines: {sku}"
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
                    sku = int(float(details.get("no_items",0) or 0))
                    extra = f"Items: {sku} | Bill: {details.get('bill_no','')}"
                else:
                    sku = 0
                    extra = details.get("distributor","") or details.get("task_name","")

                avg = round(duration/sku, 1) if sku > 0 and duration > 0 else "-"
                total_sku += sku
                total_duration += duration

                # Customize column names per task type
                if row.get("task_type") == "Call Log":
                    count_label = "Calls Made"
                    avg_label   = "Avg mins/Call"
                elif row.get("task_type") == "Purchase Order":
                    count_label = "SKUs Ordered"
                    avg_label   = "Avg mins/SKU"
                elif row.get("task_type") in ["Bill Cross Check","Register Entry"]:
                    count_label = "Items"
                    avg_label   = "Avg mins/Item"
                elif row.get("task_type") == "Stock Placement":
                    count_label = "Medicines"
                    avg_label   = "Avg mins/Med"
                else:
                    count_label = "Count"
                    avg_label   = "Avg/Item"

                display_rows.append({
                    "Time": row.get("time",""),
                    "Task": row.get("task_type",""),
                    "Details": extra,
                    "Start": row.get("start_time",""),
                    "End": row.get("end_time",""),
                    "Duration": f"{duration} mins",
                    count_label: sku if sku > 0 else "-",
                    avg_label: f"{avg} mins" if avg != "-" else "-",
                })

            st.dataframe(pd.DataFrame(display_rows), use_container_width=True)

            # Smart Summary based on team
            overall_avg = round(total_duration/total_sku, 1) if total_sku > 0 else 0
            team = st.session_state.team

            c1,c2,c3,c4 = st.columns(4)
            with c1: st.metric("Total Tasks", len(display_rows))
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
                arrangements  = [row for _, row in df.iterrows() if row.get("task_type") == "Arrangement"]
                pharmarack    = [row for _, row in df.iterrows() if row.get("task_type") == "PharmaRack Search"]
                returns       = [row for _, row in df.iterrows() if row.get("task_type") == "Purchase Return"]

                # SKU metrics
                total_skus = sum([int((row.get("details") or {}).get("no_sku",0) or 0) for row in normal_orders])
                avg_sku_per_min = round(total_skus/total_duration, 2) if total_duration > 0 and total_skus > 0 else 0

                # Avg time per order type
                normal_duration = sum([int(row.get("duration_mins",0) or 0) for row in normal_orders])
                arr_duration    = sum([int(row.get("duration_mins",0) or 0) for row in arrangements])
                avg_normal_time = round(normal_duration/len(normal_orders), 1) if normal_orders else 0
                avg_arr_time    = round(arr_duration/len(arrangements), 1) if arrangements else 0

                with c2: st.metric("Total SKUs", total_skus)
                with c4: st.metric("Avg SKU/min", avg_sku_per_min)

                st.divider()
                r1,r2,r3,r4 = st.columns(4)
                with r1: st.metric("🛒 Normal Orders", len(normal_orders))
                with r2: st.metric("⏱️ Avg Time/Normal", f"{avg_normal_time} mins")
                with r3: st.metric("📋 Arrangements", len(arrangements))
                with r4: st.metric("⏱️ Avg Time/Arr", f"{avg_arr_time} mins")

                st.divider()
                r5,r6 = st.columns(2)
                with r5: st.metric("💊 PharmaRack", len(pharmarack))
                with r6: st.metric("↩️ Returns", len(returns))
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

# ── ADMIN DASHBOARD ───────────────────────────────────────────────────────────
def show_admin_page():
    st.title("👑 RapidSurge Warehouse — Admin")
    st.caption(f"Welcome **{st.session_state.name}** | {today_ist().strftime('%A, %d %B %Y')} | {time_str()}")
    st.divider()

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard",
        "🔄 Pipeline",
        "📈 Performance",
        "📝 Submit Entry",
        "👥 Settings",
        "📥 Reports"
    ])

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

        st.subheader("📋 Today Arrangement Summary")
        a1,a2,a3,a4,a5 = st.columns(5)
        with a1: st.metric("Total", len(arr_today))
        with a2: st.metric("🔴 Pending", len([a for a in arr_today if a.get("status")=="Pending"]))
        with a3: st.metric("🚚 In Transit", len([a for a in arr_today if "Transit" in str(a.get("status",""))]))
        with a4: st.metric("🏭 At Warehouse", len([a for a in arr_today if a.get("status")=="Reached Warehouse"]))
        with a5: st.metric("✅ Completed", len([a for a in arr_today if a.get("status")=="Completed"]))

        st.divider()

        if not df.empty:
            st.subheader("👥 Team Tasks Today")
            teams = ["Purchase","Stock","Call","Delivery"]
            cols  = st.columns(4)
            for i,t in enumerate(teams):
                with cols[i]:
                    count = len(df[df["team"]==t])
                    st.metric(t, count, "tasks")
            st.divider()
            c1,c2 = st.columns(2)
            with c1:
                st.bar_chart(df["team"].value_counts())
            with c2:
                st.bar_chart(df["person"].value_counts())
        else:
            st.info("No tasks today yet!")

        st.divider()

        st.subheader("🔴 Live Delivery Tracking")
        try:
            live = supabase.table("daily_tasks").select("*")\
                .eq("team","Delivery").eq("status","In Progress").execute()
            if live.data:
                for e in live.data:
                    d = e.get("details",{})
                    c1,c2,c3,c4 = st.columns([2,2,2,1])
                    with c1: st.markdown(f"👤 **{e.get('person','')}**")
                    with c2: st.markdown(f"📍 **{d.get('location_a','')}**")
                    with c3: st.markdown(f"🚦 **{d.get('trip_type','')}**")
                    with c4: st.markdown(f"🕐 **{e.get('start_time','')}**")
            else:
                st.info("No delivery in progress.")
        except Exception as e:
            st.error(f"Error: {e}")

        st.divider()

        st.subheader("📋 All Arrangements Today")
        try:
            arr = supabase.table("arrangements").select("*")\
                .eq("order_placed_date", date_str()).execute()
            if arr.data:
                arr_df = pd.DataFrame(arr.data)
                display_cols = ["arrangement_no","distributor","area","order_placed_time","order_by","urgency","pickup_type","status"]
                existing_cols = [c for c in display_cols if c in arr_df.columns]
                st.dataframe(arr_df[existing_cols], use_container_width=True)
            else:
                st.info("No arrangements today.")
        except Exception as e:
            st.error(f"Error: {e}")

    with tab2:
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
            st.dataframe(person_summary, use_container_width=True)
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
                    new_role = st.selectbox("Role", ["user","admin"], key="nu_role")
                if st.form_submit_button("Add User ✅", type="primary", use_container_width=True):
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
                                    "role": new_role, "active": True
                                }).execute()
                                load_users.clear()
                                st.success(f"✅ {new_name} added!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        with tab_u2:
            try:
                users_resp = supabase.table("app_users").select("*").order("team").execute()
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
        st.subheader("🏭 Warehouses & Areas")
        tab_w, tab_a = st.tabs(["🏭 Warehouses","📍 Areas"])
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
            all_tasks = supabase.table("daily_tasks").select("*").execute()
            filtered  = pd.DataFrame(all_tasks.data) if all_tasks.data else pd.DataFrame()
            if not filtered.empty:
                filtered["date"] = pd.to_datetime(filtered["date"])
                if sel_team != "All": filtered = filtered[filtered["team"]==sel_team]
                if sel_person: filtered = filtered[filtered["person"].str.contains(sel_person, case=False)]
                if date_f == "Today": filtered = filtered[filtered["date"]==pd.to_datetime(date_str())]
                elif date_f == "Yesterday": filtered = filtered[filtered["date"]==pd.to_datetime(date_str())-pd.Timedelta(days=1)]
                elif date_f == "Last 7 Days": filtered = filtered[filtered["date"]>=pd.Timestamp.now()-pd.Timedelta(days=7)]
                elif date_f == "Last 30 Days": filtered = filtered[filtered["date"]>=pd.Timestamp.now()-pd.Timedelta(days=30)]
                st.markdown(f"**{len(filtered)} tasks found**")
                st.dataframe(filtered.sort_values("date", ascending=False), use_container_width=True)
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
