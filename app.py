import os
# 禁用遥测警告，优化运行环境
os.environ["OTEL_SDK_DISABLED"] = "true"

import streamlit as st
import uuid
from supabase import create_client, Client
from streamlit_cookies_manager import EncryptedCookieManager
from my_project.crew import MyProjectCrew

# --- 1. 页面基本配置与初始状态 ---
st.set_page_config(
    page_title="SkyWishes Portal", 
    page_icon="🏮", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- 2. 视觉一致性优化 (CSS 注入) ---
st.markdown("""
    <style>
    /* 全局背景与基础文字 */
    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
        color: #e6edf3;
    }
    
    /* 侧边栏视觉增强 */
    [data-testid="stSidebar"] {
        background-color: #010409 !important;
        border-right: 1px solid #30363d;
    }
    /* 强制侧边栏内所有元素为高对比度纯白 */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] div[role="radiogroup"] label p {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 500 !important;
    }

    /* 修复：将侧边栏收缩箭头 "<<" 彻底改为白色 */
    button[data-testid="stSidebarCollapseButton"] svg {
        fill: #ffffff !important;
        color: #ffffff !important;
    }

    /* 修复：愿望输入框上方的提示文字颜色 */
    .stTextInput label, .stSelectbox label, .stTextArea label {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
    }
    
    /* Kanban 编辑框视觉优化 */
    .stTextArea textarea {
        background-color: #0d1117 !important;
        color: #ffffff !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }
    
    /* 按钮视觉补强：常驻背景色，解决“看不见”的问题 */
    .stButton > button {
        background-color: rgba(35, 134, 54, 0.4) !important;
        color: #ffffff !important;
        border: 1px solid rgba(46, 160, 67, 0.6) !important;
        border-radius: 8px;
    }
    .stButton > button:hover {
        background-color: rgba(35, 134, 54, 0.6) !important;
        border-color: #3fb950 !important;
        box-shadow: 0 0 10px rgba(63, 185, 80, 0.3);
    }

    .step-header {
        color: #d29922;
        font-weight: bold;
        font-size: 0.9rem;
        margin-bottom: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 初始化服务与 UUID 逻辑 ---
cookies = EncryptedCookieManager(password="SkyWishes_Secure_2026")
if not cookies.ready(): st.stop()

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# 严防 "None" 字符串污染
if "guest_id" not in cookies or not cookies["guest_id"] or cookies["guest_id"] == "None":
    cookies["guest_id"] = str(uuid.uuid4())
    cookies.save()

raw_guest_id = cookies.get("guest_id")
current_guest_id = raw_guest_id if (raw_guest_id and raw_guest_id != "None") else None

# --- 4. 严格语言隔离配置 (Native Human Tone) ---
LANGS = {
    "English": {
        "title": "🏮 SkyWishes Portal",
        "subtitle": "Manifest your 2026 aspirations into the stellar void.",
        "wish_label": "What is your heart's desire for the new year?",
        "launch_btn": "Launch Sky Lantern",
        "save_btn": "Save Roadmap Changes",
        "history_title": "✨ Celestial Memories",
        "step_hint": "Action Roadmap (Feel free to refine your path below)",
        "loading": "Architecting your path...",
        "auth_welcome": "🌟 Welcome back to the stars!",
        "auth_benefit": "Your account preserves your dreams across all devices.",
        "forgot_pw": "Forgot Password?",
        "reset_sent": "Check your email for the reset link!",
        "user_exists": "This email is already registered. Please sign in instead.",
        "lantern": "Sky Lantern",
        "auth_mode_label": "Choose Your Path"
    },
    "中文": {
        "title": "🏮 SkyWishes | 孔明灯广场",
        "subtitle": "点亮 2026 的期许，让愿望在星空下有迹可循。",
        "wish_label": "许下你的 2026 新年愿望...",
        "launch_btn": "放飞孔明灯",
        "save_btn": "保存计划修改内容",
        "history_title": "✨ 往昔星火 (历史记录)",
        "step_hint": "行动看板 (可点击文本框直接微调)",
        "loading": "愿望架构师正在绘制蓝图...",
        "auth_welcome": "🌟 欢迎重回星空！",
        "auth_benefit": "登录后，愿望将多端同步并永久保存。",
        "forgot_pw": "忘记密码？",
        "reset_sent": "重置链接已发送至邮箱！",
        "user_exists": "该邮箱已注册，请尝试直接登录。",
        "lantern": "孔明灯",
        "auth_mode_label": "选择身份"
    }
}

# 顶部语言切换
top_col1, top_col2 = st.columns([8, 2])
with top_col2:
    sel_lang = st.selectbox("Language Switcher", ["English", "中文"], label_visibility="collapsed")
T = LANGS[sel_lang]

with top_col1:
    st.title(T["title"])
    st.markdown(f"*{T['subtitle']}*")

# --- 5. 侧边栏：账户系统逻辑 ---
with st.sidebar:
    st.header("✨ Account")
    u_id = st.session_state.get("u_id")
    
    if not u_id:
        st.write(T["auth_welcome"])
        st.caption(T["auth_benefit"])
        # 移除单选框中的中文字符混合
        modes = ["Guest", "Login", "Sign Up"] if sel_lang == "English" else ["访客模式", "登录", "注册"]
        auth_mode = st.radio(T["auth_mode_label"], modes, label_visibility="collapsed")
        
        # 判断模式索引
        is_guest = auth_mode in ["Guest", "访客模式"]
        is_login = auth_mode in ["Login", "登录"]
        is_signup = auth_mode in ["Sign Up", "注册"]

        if not is_guest:
            email = st.text_input("Email", placeholder="your@email.com")
            pw = st.text_input("Password", type="password")
            
            if is_signup and st.button(T["launch_btn"] if sel_lang == "English" else "提交注册"):
                try:
                    res = supabase.auth.sign_up({"email": email, "password": pw})
                    if res.user and res.user.identities is not None and len(res.user.identities) == 0:
                        st.warning(T["user_exists"])
                    elif res.user:
                        st.success("Verification email sent!")
                except Exception as e:
                    st.error(f"Error: {e}")

            if is_login:
                if st.button("Sign In" if sel_lang == "English" else "立即登录"):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                        if res.user:
                            st.session_state["u_id"] = res.user.id
                            st.session_state["user_email"] = res.user.email
                            if current_guest_id:
                                supabase.table("wish_history").update({"user_id": res.user.id}).eq("guest_id", current_guest_id).execute()
                            st.rerun()
                    except Exception: st.error("Authentication failed.")
                
                if st.button(T["forgot_pw"]):
                    if email:
                        supabase.auth.reset_password_for_email(email)
                        st.info(T["reset_sent"])
                    else: st.warning("Enter email first.")
    else:
        st.success(f"Online: {st.session_state.get('user_email', 'Member')}")
        if st.button("Sign Out" if sel_lang == "English" else "退出登录"):
            st.session_state.clear()
            st.rerun()

# --- 6. 愿望交互逻辑 ---
user_wish = st.text_input(T["wish_label"], placeholder="e.g. Master AI development and find inner peace")

if st.button(T["launch_btn"]):
    if user_wish:
        with st.spinner(T["loading"]):
            try:
                # 核心改进：传递语言参数给 AI 代理，防止双语混杂
                result = MyProjectCrew().crew().kickoff(inputs={
                    'wish': user_wish,
                    'language': sel_lang 
                })
                data = result.pydantic 
                
                db_entry = {
                    "guest_id": current_guest_id,
                    "user_id": st.session_state.get("u_id"),
                    "wish_text": user_wish,
                    "plan_json": data.dict(),
                    "lang": sel_lang
                }
                if current_guest_id:
                    res = supabase.table("wish_history").insert(db_entry).execute()
                    if res.data:
                        st.session_state["current_wish_db_id"] = res.data[0]['id']
                
                st.session_state["last_plan"] = data.dict()
                st.balloons() 
                st.rerun()
            except Exception as e:
                st.error(f"Launch failed: {e}")

# --- 7. 可编辑的 Kanban 展示 ---
if "last_plan" in st.session_state:
    plan = st.session_state["last_plan"]
    st.divider()
    l_name = plan.get('lantern_name', T['lantern'])
    st.subheader(f"✨ {l_name}")
    st.write(plan.get('response', ''))
    
    st.markdown(f"#### 📋 {T['step_hint']}")
    steps = plan.get('steps', [])
    edited_steps = []
    
    if steps:
        cols = st.columns(len(steps))
        for i, s in enumerate(steps):
            with cols[i]:
                st.markdown(f'<div class="step-header">STEP {i+1}</div>', unsafe_allow_html=True)
                new_s = st.text_area(f"edit_{i}", value=s, height=220, label_visibility="collapsed")
                edited_steps.append(new_s)
        
        if st.button(T["save_btn"], use_container_width=True):
            if "current_wish_db_id" in st.session_state:
                plan['steps'] = edited_steps
                supabase.table("wish_history").update({"plan_json": plan}).eq("id", st.session_state["current_wish_db_id"]).execute()
                st.session_state["last_plan"] = plan
                st.toast("Modifications saved! 🌟")

# --- 8. 历史回顾 ---
st.divider()
st.subheader(T["history_title"])
if current_guest_id:
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