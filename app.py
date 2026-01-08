import os
# 禁用遥测信号报错
os.environ["OTEL_SDK_DISABLED"] = "true"

import streamlit as st
import uuid
from supabase import create_client, Client
from streamlit_cookies_manager import EncryptedCookieManager
from my_project.crew import MyProjectCrew

# --- 1. 视觉主题与 CSS 注入 ---
st.set_page_config(page_title="SkyWishes Portal", page_icon="🏮", layout="wide")

st.markdown("""
    <style>
    /* 全局背景 */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        color: #ffffff;
    }
    
    /* 修复问题 2：输入框标签颜色 (白色) */
    label, .stMarkdown p {
        color: #f0f0f0 !important;
        font-weight: 500 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }

    /* 修复问题 3：按钮视觉效果 (解决空白格问题) */
    .stButton > button {
        background-color: rgba(255, 255, 255, 0.15) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        border-radius: 10px;
        padding: 12px 20px;
        font-weight: bold;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.25) !important;
        border-color: #FFD700 !important;
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.3);
    }

    /* 修复问题 1：Kanban 编辑卡片样式 */
    div[data-testid="stVerticalBlock"] > div.stTextArea {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 5px;
    }
    textarea {
        background-color: transparent !important;
        color: white !important;
        border: none !important;
        font-size: 1rem !important;
    }
    
    .step-header {
        color: #FFD700;
        font-weight: bold;
        font-size: 0.8rem;
        margin-bottom: 5px;
        text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 基础服务初始化 ---
cookies = EncryptedCookieManager(password="SkyWishes_Secure_2026")
if not cookies.ready(): 
    st.stop()

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# 管理访客 ID
if "guest_id" not in cookies or not cookies["guest_id"]:
    cookies["guest_id"] = str(uuid.uuid4())
    cookies.save()
current_guest_id = cookies.get("guest_id")

# --- 3. 语言与文本配置 ---
LANGS = {
    "English": {
        "title": "🏮 SkyWishes Portal",
        "subtitle": "Manifest your 2026 aspirations into the stellar void.",
        "wish_label": "What is your heart's desire for the new year?",
        "launch_btn": "Launch Sky Lantern",
        "history_title": "✨ Celestial Memories",
        "step_hint": "Action Roadmap (Editable)",
        "loading": "Architecting your path...",
        "lantern": "Sky Lantern",
        "auth_header": "User Portal",
        "login_success": "Welcome back!",
        "logout_btn": "Sign Out"
    },
    "中文": {
        "title": "🏮 SkyWishes | 孔明灯广场",
        "subtitle": "点亮 2026 的期许，让每一个愿望在星空下有迹可循。",
        "wish_label": "许下你的 2026 新年愿望...",
        "launch_btn": "点亮并放飞孔明灯",
        "history_title": "✨ 往昔星火 (历史记忆)",
        "step_hint": "行动看板 (点击文本可直接修改)",
        "loading": "愿望架构师正在规划路径...",
        "lantern": "孔明灯",
        "auth_header": "账户中心",
        "login_success": "欢迎回来！",
        "logout_btn": "退出登录"
    }
}

# --- 4. 修复问题 4：右上角语言切换 ---
top_col1, top_col2 = st.columns([8, 2])
with top_col2:
    sel_lang = st.selectbox("Lang", ["English", "中文"], label_visibility="collapsed")

T = LANGS[sel_lang]

with top_col1:
    st.title(T["title"])
    st.markdown(f"*{T['subtitle']}*")

# --- 5. 修复问题 2：侧边栏账户系统展示 ---
with st.sidebar:
    st.header(T["auth_header"])
    u_id = st.session_state.get("u_id")
    
    if not u_id:
        auth_mode = st.radio("Mode", ["Guest / 访客", "Login / 登录", "Sign Up / 注册"])
        
        if auth_mode != "Guest / 访客":
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            
            if auth_mode == "Login / 登录" and st.button("Sign In"):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res.user:
                        st.session_state["u_id"] = res.user.id
                        st.session_state["user_email"] = res.user.email
                        # 同步访客数据到该账号
                        supabase.table("wish_history").update({"user_id": res.user.id}).eq("guest_id", current_guest_id).execute()
                        st.success(T["login_success"])
                        st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")
            
            if auth_mode == "Sign Up / 注册" and st.button("Register"):
                try:
                    res = supabase.auth.sign_up({"email": email, "password": password})
                    st.info("Check your email for confirmation link!")
                except Exception as e:
                    st.error(f"Registration failed: {e}")
        else:
            st.info("Browsing as Guest. Log in to sync across devices.")
    else:
        st.write(f"Logged in as: **{st.session_state.get('user_email')}**")
        if st.button(T["logout_btn"]):
            st.session_state.clear()
            st.rerun()

# --- 6. 愿望交互逻辑 ---
st.write("") 
user_wish = st.text_input(T["wish_label"], placeholder="e.g. Mastering AI development and staying healthy")

if st.button(T["launch_btn"]):
    if user_wish:
        with st.spinner(T["loading"]):
            try:
                # 运行 CrewAI 代理
                result = MyProjectCrew().crew().kickoff(inputs={'wish': user_wish})
                data = result.pydantic 

                # 准备数据库条目
                db_entry = {
                    "guest_id": current_guest_id,
                    "user_id": st.session_state.get("u_id"),
                    "wish_text": user_wish,
                    "plan_json": data.dict(),
                    "lang": sel_lang
                }
                # 写入 Supabase
                supabase.table("wish_history").insert(db_entry).execute()
                
                # 触发动画
                st.session_state["last_plan"] = data.dict()
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Launch failed: {e}")

# --- 7. 修复问题 1：可编辑的 Kanban 看板展示 ---
if "last_plan" in st.session_state:
    plan = st.session_state["last_plan"]
    st.divider()
    st.subheader(f"✨ {plan.get('lantern_name', T['lantern'])}")
    st.write(plan.get('response', ''))
    
    st.markdown(f"#### 📋 {T['step_hint']}")
    steps = plan.get('steps', [])
    
    if steps:
        cols = st.columns(len(steps))
        for i, s in enumerate(steps):
            with cols[i]:
                st.markdown(f'<div class="step-header">Step {i+1}</div>', unsafe_allow_html=True)
                # 使用 text_area 允许用户直接更改内容
                edited_step = st.text_area(
                    label=f"step_edit_{i}",
                    value=s,
                    height=150,
                    key=f"kanban_step_{i}",
                    label_visibility="collapsed"
                )

# --- 8. 历史回顾 (仅显示用户自己的历史) ---
st.divider()
st.subheader(T["history_title"])

# 核心逻辑：根据登录状态决定查询条件
if current_guest_id:
    try:
        # 如果已登录，优先根据 user_id 查询；未登录则根据 guest_id 查询
        query = supabase.table("wish_history").select("*")
        if st.session_state.get("u_id"):
            query = query.eq("user_id", st.session_state["u_id"])
        else:
            query = query.eq("guest_id", current_guest_id)
            
        history = query.order("created_at", desc=True).execute()

        for item in history.data:
            with st.expander(f"🏮 {item['wish_text']} ({item['created_at'][:10]})"):
                p = item['plan_json']
                st.write(p.get('response', ''))
                h_steps = p.get('steps', [])
                if h_steps:
                    h_cols = st.columns(len(h_steps))
                    for idx, hs in enumerate(h_steps):
                        # 历史记录中的步骤使用 info 样式展示
                        h_cols[idx].info(f"**Step {idx+1}**\n\n{hs}")
    except Exception as e:
        st.caption(f"Waiting for your first wish... (Debug: {e})")