import os
os.environ["OTEL_SDK_DISABLED"] = "true"

import streamlit as st
import uuid
from supabase import create_client, Client
from streamlit_cookies_manager import EncryptedCookieManager
from my_project.crew import MyProjectCrew

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="SkyWishes Portal", 
    page_icon="🏮", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 终极 UI 修复 (CSS) ---
st.markdown("""
    <style>
    /* 护眼底色 */
    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
        color: #e6edf3;
    }
    
    /* 修复 1：侧边栏 Logo 与 Header 颜色 */
    [data-testid="stSidebarNav"]::before {
        content: "🏮 SkyWishes";
        color: #f0f6fc;
        font-size: 1.5rem;
        font-weight: bold;
        padding: 20px;
        display: block;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #f0f6fc !important;
    }
    
    /* 修复 2：Kanban 编辑框文字颜色 (高对比度) */
    .stTextArea textarea {
        background-color: #010409 !important;
        color: #ffffff !important; /* 确保文字绝对可见 */
        border: 1px solid #30363d !important;
        font-size: 0.9rem !important;
        padding: 10px !important;
    }
    
    /* 强制标签与文字颜色 */
    label, p, .stCaption {
        color: #c9d1d9 !important;
    }

    /* 按钮美化 */
    .stButton > button {
        background-color: rgba(35, 134, 54, 0.3) !important;
        color: #aff5b4 !important;
        border: 1px solid rgba(46, 160, 67, 0.5) !important;
        border-radius: 8px;
    }
    .stButton > button:hover {
        background-color: rgba(35, 134, 54, 0.5) !important;
        border-color: #3fb950 !important;
    }
    
    .step-header {
        color: #d29922;
        font-weight: bold;
        font-size: 0.8rem;
        margin-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 基础初始化 ---
cookies = EncryptedCookieManager(password="SkyWishes_Secure_2026")
if not cookies.ready(): st.stop()

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

if "guest_id" not in cookies or not cookies["guest_id"]:
    cookies["guest_id"] = str(uuid.uuid4())
    cookies.save()
current_guest_id = cookies.get("guest_id")

# --- 4. 语言文案 ---
LANGS = {
    "English": {
        "title": "🏮 SkyWishes Portal",
        "subtitle": "Manifest your 2026 aspirations into the stellar void.",
        "wish_label": "What is your heart's desire for the new year?",
        "launch_btn": "Launch Sky Lantern",
        "save_btn": "Save Plan Changes",
        "history_title": "✨ Celestial Memories",
        "step_hint": "Action Roadmap (Editable)",
        "loading": "Architecting your path...",
        "auth_welcome": "🌟 Welcome to our celestial community!",
        "auth_benefit": "Create an account to preserve and sync your dreams."
    },
    "中文": {
        "title": "🏮 SkyWishes | 孔明灯广场",
        "subtitle": "点亮 2026 的期许，让愿望在星空下有迹可循。",
        "wish_label": "许下你的 2026 新年愿望...",
        "launch_btn": "放飞孔明灯",
        "save_btn": "保存修改后的计划",
        "history_title": "✨ 往昔星火 (历史记录)",
        "step_hint": "行动看板 (可点击下方文字直接修改)",
        "loading": "愿望架构师正在绘制蓝图...",
        "auth_welcome": "🌟 欢迎加入星空社区！",
        "auth_benefit": "注册账号后，愿望将多端同步并永久保存。"
    }
}

top_col1, top_col2 = st.columns([8, 2])
with top_col2:
    sel_lang = st.selectbox("Lang", ["English", "中文"], label_visibility="collapsed")
T = LANGS[sel_lang]

with top_col1:
    st.title(T["title"])
    st.markdown(f"*{T['subtitle']}*")

# --- 5. 侧边栏 ---
with st.sidebar:
    st.header("✨ Account")
    u_id = st.session_state.get("u_id")
    if not u_id:
        st.write(T["auth_welcome"])
        st.caption(T["auth_benefit"])
        auth_mode = st.radio("Mode", ["Guest", "Login", "Sign Up"], label_visibility="collapsed")
        if auth_mode != "Guest":
            email = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            if auth_mode == "Login" and st.button("Sign In"):
                res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                if res.user:
                    st.session_state["u_id"] = res.user.id
                    supabase.table("wish_history").update({"user_id": res.user.id}).eq("guest_id", current_guest_id).execute()
                    st.rerun()
            if auth_mode == "Sign Up" and st.button("Create Account"):
                supabase.auth.sign_up({"email": email, "password": pw})
                st.success("Check your email!")
    else:
        st.success("Connected to Stars")
        if st.button("Sign Out"):
            st.session_state.clear()
            st.rerun()

# --- 6. 核心逻辑 ---
user_wish = st.text_input(T["wish_label"], placeholder="e.g. Find a new job in 3 months")

if st.button(T["launch_btn"]):
    if user_wish:
        with st.spinner(T["loading"]):
            try:
                result = MyProjectCrew().crew().kickoff(inputs={'wish': user_wish})
                data = result.pydantic 
                db_entry = {
                    "guest_id": current_guest_id,
                    "user_id": st.session_state.get("u_id"),
                    "wish_text": user_wish,
                    "plan_json": data.dict(),
                    "lang": sel_lang
                }
                res = supabase.table("wish_history").insert(db_entry).execute()
                # 获取新插入记录的 ID 用于后续保存修改
                if res.data:
                    st.session_state["current_wish_db_id"] = res.data[0]['id']
                
                st.session_state["last_plan"] = data.dict()
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Process failed: {e}")

# --- 7. 可编辑看板 ---
if "last_plan" in st.session_state:
    plan = st.session_state["last_plan"]
    st.divider()
    st.subheader(f"✨ {plan.get('lantern_name', T['lantern'])}")
    st.write(plan.get('response', ''))
    
    st.markdown(f"#### 📋 {T['step_hint']}")
    steps = plan.get('steps', [])
    edited_steps = []
    
    if steps:
        cols = st.columns(len(steps))
        for i, s in enumerate(steps):
            with cols[i]:
                st.markdown(f'<div class="step-header">STEP {i+1}</div>', unsafe_allow_html=True)
                new_s = st.text_area(f"edit_{i}", value=s, height=200, label_visibility="collapsed")
                edited_steps.append(new_s)
        
        # 修复 4：添加保存按钮
        if st.button(T["save_btn"], use_container_width=True):
            if "current_wish_db_id" in st.session_state:
                plan['steps'] = edited_steps
                supabase.table("wish_history").update({"plan_json": plan}).eq("id", st.session_state["current_wish_db_id"]).execute()
                st.session_state["last_plan"] = plan
                st.toast("Roadmap saved to celestial archive! ✨")

# --- 8. 历史回顾 ---
st.divider()
st.subheader(T["history_title"])
if current_guest_id and current_guest_id != "None":
    try:
        q = supabase.table("wish_history").select("*")
        if u_id: q = q.eq("user_id", u_id)
        else: q = q.eq("guest_id", current_guest_id)
        history = q.order("created_at", desc=True).execute()

        for item in history.data:
            with st.expander(f"🏮 {item['wish_text']} ({item['created_at'][:10]})"):
                p = item['plan_json']
                st.write(p.get('response', ''))
                h_steps = p.get('steps', [])
                if h_steps:
                    h_cols = st.columns(len(h_steps))
                    for idx, hs in enumerate(h_steps):
                        h_cols[idx].info(f"**Step {idx+1}**\n\n{hs}")
    except Exception:
        pass