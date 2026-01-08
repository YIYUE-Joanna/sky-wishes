import os
# 彻底禁用遥测报错
os.environ["OTEL_SDK_DISABLED"] = "true"

import streamlit as st
import uuid
from supabase import create_client, Client
from streamlit_cookies_manager import EncryptedCookieManager
from my_project.crew import MyProjectCrew

# --- 1. 页面基本配置 ---
st.set_page_config(
    page_title="SkyWishes Portal", 
    page_icon="🏮", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 终极 UI 视觉增强 (CSS) ---
st.markdown("""
    <style>
    /* 1. 护眼底色：深邃但有质感 */
    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
        color: #e6edf3;
    }
    
    /* 2. 侧边栏重塑：解决颜色太淡问题 */
    [data-testid="stSidebar"] {
        background-color: #010409 !important; /* 极深背景 */
        border-right: 1px solid #30363d;
    }
    /* 侧边栏所有标题、文本、标签强制高亮 */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] .stMarkdown {
        color: #f0f6fc !important;
        opacity: 1 !important;
    }
    
    /* 3. Kanban 编辑框修复：深色背景 + 白色文字 */
    .stTextArea textarea {
        background-color: #0d1117 !important;
        color: #ffffff !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
    }
    
    /* 4. 按钮一致性：不再是空白格 */
    .stButton > button {
        background-color: rgba(35, 134, 54, 0.3) !important;
        color: #aff5b4 !important;
        border: 1px solid rgba(46, 160, 67, 0.5) !important;
        border-radius: 8px;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: rgba(35, 134, 54, 0.5) !important;
        border-color: #3fb950 !important;
        box-shadow: 0 0 10px rgba(63, 185, 80, 0.2);
    }
    
    /* 5. 提示框样式优化 */
    .stAlert {
        background-color: rgba(22, 27, 34, 0.8) !important;
        border: 1px solid #30363d !important;
        color: #e6edf3 !important;
    }

    .step-header {
        color: #d29922;
        font-weight: bold;
        font-size: 0.9rem;
        margin-bottom: 8px;
        text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 初始化服务 ---
cookies = EncryptedCookieManager(password="SkyWishes_Secure_2026")
if not cookies.ready(): st.stop()

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

if "guest_id" not in cookies or not cookies["guest_id"]:
    cookies["guest_id"] = str(uuid.uuid4())
    cookies.save()
current_guest_id = cookies.get("guest_id")

# --- 4. 多语言 Human-Tone 配置 ---
LANGS = {
    "English": {
        "title": "🏮 SkyWishes Portal",
        "subtitle": "Manifest your 2026 aspirations into the stellar void.",
        "wish_label": "What is your heart's desire for the new year?",
        "launch_btn": "Launch Sky Lantern",
        "save_btn": "Save Changes",
        "history_title": "✨ Celestial Memories",
        "step_hint": "Action Roadmap (Directly edit below)",
        "loading": "Architecting your path...",
        "auth_welcome": "🌟 Welcome to the community!",
        "auth_benefit": "Accounts sync your wishes across all devices.",
        "forgot_pw": "Forgot Password?",
        "reset_sent": "Password reset link sent to your email!",
        "user_exists": "This email is already registered. Please login instead."
    },
    "中文": {
        "title": "🏮 SkyWishes | 孔明灯广场",
        "subtitle": "点亮 2026 的期许，让愿望在星空下有迹可循。",
        "wish_label": "许下你的 2026 新年愿望...",
        "launch_btn": "放飞孔明灯",
        "save_btn": "保存计划修改",
        "history_title": "✨ 往昔星火 (历史记录)",
        "step_hint": "行动看板 (点击文本框可直接微调)",
        "loading": "愿望架构师正在绘制蓝图...",
        "auth_welcome": "🌟 欢迎加入星空社区！",
        "auth_benefit": "注册账号后，愿望将多端同步并永久保存。",
        "forgot_pw": "忘记密码？",
        "reset_sent": "密码重置链接已发送至您的邮箱！",
        "user_exists": "该邮箱已注册，请直接尝试登录。"
    }
}

top_col1, top_col2 = st.columns([8, 2])
with top_col2:
    sel_lang = st.selectbox("Lang", ["English", "中文"], label_visibility="collapsed")
T = LANGS[sel_lang]

with top_col1:
    st.title(T["title"])
    st.markdown(f"*{T['subtitle']}*")

# --- 5. 侧边栏：增强的账户与找回功能 ---
with st.sidebar:
    st.header("✨ Account")
    u_id = st.session_state.get("u_id")
    
    if not u_id:
        st.write(T["auth_welcome"])
        st.caption(T["auth_benefit"])
        auth_mode = st.radio("Mode", ["Guest", "Login", "Sign Up"], label_visibility="collapsed")
        
        if auth_mode != "Guest":
            email = st.text_input("Email", placeholder="your@email.com")
            pw = st.text_input("Password", type="password")
            
            # 功能 1：注册逻辑与冲突检测
            if auth_mode == "Sign Up" and st.button("Create Account"):
                try:
                    res = supabase.auth.sign_up({"email": email, "password": pw})
                    if res.user:
                        st.success("Verification email sent!")
                except Exception as e:
                    if "already registered" in str(e).lower():
                        st.warning(T["user_exists"])
                    else:
                        st.error(f"Error: {e}")

            # 功能 2：登录逻辑
            if auth_mode == "Login":
                if st.button("Sign In"):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                        if res.user:
                            st.session_state["u_id"] = res.user.id
                            supabase.table("wish_history").update({"user_id": res.user.id}).eq("guest_id", current_guest_id).execute()
                            st.rerun()
                    except Exception as e:
                        st.error("Login failed. Check your credentials.")
                
                # 功能 3：找回密码 UI
                st.divider()
                if st.button(T["forgot_pw"]):
                    if email:
                        supabase.auth.reset_password_for_email(email)
                        st.info(T["reset_sent"])
                    else:
                        st.warning("Please enter your email first.")
    else:
        st.success(f"Online: {st.session_state.get('user_email', 'Celestial Member')}")
        if st.button("Sign Out"):
            st.session_state.clear()
            st.rerun()

# --- 6. 核心交互流程 ---
user_wish = st.text_input(T["wish_label"], placeholder="e.g. Master AI and launch my first app")

if st.button(T["launch_btn"]):
    if user_wish:
        with st.spinner(T["loading"]):
            try:
                # 运行后台 CrewAI 逻辑
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
                if res.data:
                    st.session_state["current_wish_db_id"] = res.data[0]['id']
                
                st.session_state["last_plan"] = data.dict()
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to light lantern: {e}")

# --- 7. 可编辑看板与保存功能 ---
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
                new_s = st.text_area(f"kanban_edit_{i}", value=s, height=220, label_visibility="collapsed")
                edited_steps.append(new_s)
        
        # 允许保存用户对建议的修改
        if st.button(T["save_btn"], use_container_width=True):
            if "current_wish_db_id" in st.session_state:
                plan['steps'] = edited_steps
                supabase.table("wish_history").update({"plan_json": plan}).eq("id", st.session_state["current_wish_db_id"]).execute()
                st.session_state["last_plan"] = plan
                st.toast("Changes saved to the stars! 🌟")

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