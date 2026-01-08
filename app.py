import os
# 禁用遥测信号报错
os.environ["OTEL_SDK_DISABLED"] = "true"

import streamlit as st
import uuid
from supabase import create_client, Client
from streamlit_cookies_manager import EncryptedCookieManager
from my_project.crew import MyProjectCrew

# --- 1. 页面配置：初始展开侧边栏 ---
st.set_page_config(
    page_title="SkyWishes Portal", 
    page_icon="🏮", 
    layout="wide",
    initial_sidebar_state="expanded"  # 侧边栏初始展开
)

# --- 2. 护眼视觉主题 (CSS 注入) ---
st.markdown("""
    <style>
    /* 1. 护眼午夜背景：深沉且不刺眼 */
    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
        color: #e6edf3;
    }
    
    /* 2. 侧边栏增强：深色玻璃拟态，高对比度文字 */
    [data-testid="stSidebar"] {
        background-color: #010409 !important;
        border-right: 1px solid #30363d;
    }
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label {
        color: #f0f6fc !important;
        font-weight: 500;
    }

    /* 3. 解决标签太淡问题：强制输入框标题清晰 */
    label, .stMarkdown p, .stCaption {
        color: #c9d1d9 !important;
        font-weight: 500 !important;
    }

    /* 4. 按钮优化：拒绝空白格，常驻背景色 */
    .stButton > button {
        background-color: rgba(35, 134, 54, 0.2) !important; /* 墨绿色柔和背景 */
        color: #aff5b4 !important;
        border: 1px solid rgba(46, 160, 67, 0.5) !important;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.2s ease;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: rgba(35, 134, 54, 0.4) !important;
        border-color: #3fb950 !important;
        box-shadow: 0 0 12px rgba(63, 185, 80, 0.3);
    }

    /* 5. Kanban 卡片与编辑区域 */
    div[data-testid="stVerticalBlock"] > div.stTextArea {
        background: #161b22;
        border-radius: 12px;
        border: 1px solid #30363d;
        padding: 8px;
    }
    textarea {
        color: #e6edf3 !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
    }
    
    .step-header {
        color: #d29922; /* 沉稳的金色 */
        font-weight: bold;
        font-size: 0.85rem;
        margin-bottom: 8px;
        letter-spacing: 0.5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 基础服务初始化 ---
cookies = EncryptedCookieManager(password="SkyWishes_Secure_2026")
if not cookies.ready(): 
    st.stop()

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

if "guest_id" not in cookies or not cookies["guest_id"]:
    cookies["guest_id"] = str(uuid.uuid4())
    cookies.save()
current_guest_id = cookies.get("guest_id")

# --- 4. 语言文案配置 ---
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
        "auth_header": "✨ Account",
        "auth_welcome": "🌟 Welcome to our celestial community!",
        "auth_benefit": "Your past wishes will be safely synced across all devices upon signing up.",
        "register_btn": "Create My Account",
        "login_btn": "Sign In",
        "confirm_email": "Check your inbox to confirm!",
        "logout_btn": "Sign Out"
    },
    "中文": {
        "title": "🏮 SkyWishes | 孔明灯广场",
        "subtitle": "点亮 2026 的期许，让愿望在星空下有迹可循。",
        "wish_label": "许下你的 2026 新年愿望...",
        "launch_btn": "放飞孔明灯",
        "history_title": "✨ 往昔星火 (历史记录)",
        "step_hint": "行动看板 (点击文本可微调内容)",
        "loading": "愿望架构师正在绘制蓝图...",
        "lantern": "孔明灯",
        "auth_header": "✨ 账户中心",
        "auth_welcome": "🌟 欢迎加入星空社区！",
        "auth_benefit": "注册后，你之前的愿望将被永久保存并在多端同步。",
        "register_btn": "立即注册",
        "login_btn": "登录账号",
        "confirm_email": "请查收邮件激活账号！",
        "logout_btn": "退出登录"
    }
}

# --- 5. 顶部导航与语言切换 ---
top_col1, top_col2 = st.columns([8, 2])
with top_col2:
    sel_lang = st.selectbox("Lang", ["English", "中文"], label_visibility="collapsed")

T = LANGS[sel_lang]

with top_col1:
    st.title(T["title"])
    st.markdown(f"*{T['subtitle']}*")

# --- 6. 侧边栏：账户管理 ---
with st.sidebar:
    st.header(T["auth_header"])
    u_id = st.session_state.get("u_id")
    
    if not u_id:
        st.write(T["auth_welcome"])
        st.caption(T['auth_benefit'])
        
        auth_mode = st.radio("Mode", ["Guest", "Login", "Sign Up"], label_visibility="collapsed")
        
        if auth_mode != "Guest":
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password")
            
            if auth_mode == "Login" and st.button(T["login_btn"]):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res.user:
                        st.session_state["u_id"] = res.user.id
                        st.session_state["user_email"] = res.user.email
                        # 将访客历史合并至账号
                        supabase.table("wish_history").update({"user_id": res.user.id}).eq("guest_id", current_guest_id).execute()
                        st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")
            
            if auth_mode == "Sign Up" and st.button(T["register_btn"]):
                try:
                    supabase.auth.sign_up({"email": email, "password": password})
                    st.success(T["confirm_email"])
                except Exception as e:
                    st.error(f"Failed: {e}")
    else:
        st.write(f"Active User: **{st.session_state.get('user_email')}**")
        if st.button(T["logout_btn"]):
            st.session_state.clear()
            st.rerun()

# --- 7. 愿望发射区域 ---
st.write("") 
user_wish = st.text_input(T["wish_label"], placeholder="e.g. Master CrewAI development and stay healthy")

if st.button(T["launch_btn"]):
    if user_wish:
        with st.spinner(T["loading"]):
            try:
                # 运行 CrewAI 代理任务
                result = MyProjectCrew().crew().kickoff(inputs={'wish': user_wish})
                data = result.pydantic 

                # 存入数据库
                db_entry = {
                    "guest_id": current_guest_id,
                    "user_id": st.session_state.get("u_id"),
                    "wish_text": user_wish,
                    "plan_json": data.dict(),
                    "lang": sel_lang
                }
                supabase.table("wish_history").insert(db_entry).execute()
                
                # 更新状态并刷新页面
                st.session_state["last_plan"] = data.dict()
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Process Interrupted: {e}")

# --- 8. 可编辑 Kanban 行动看板 ---
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
                st.markdown(f'<div class="step-header">STEP {i+1}</div>', unsafe_allow_html=True)
                # 使用 text_area 让用户可以编辑步骤内容
                st.text_area(
                    label=f"edit_{i}",
                    value=s,
                    height=180,
                    key=f"kanban_{i}",
                    label_visibility="collapsed"
                )

# --- 9. 历史记录查询 ---
st.divider()
st.subheader(T["history_title"])

if current_guest_id and current_guest_id != "None":
    try:
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
                        h_cols[idx].info(f"**Step {idx+1}**\n\n{hs}")
    except Exception as e:
        st.caption("Waiting for your stellar aspirations...")