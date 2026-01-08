import os
# 彻底禁用遥测信号报错，确保多线程环境下运行稳定
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
    initial_sidebar_state="expanded" # 侧边栏初始展开
)

# --- 2. 视觉一致性优化 (CSS 注入) ---
st.markdown("""
    <style>
    /* 全局深色底色 */
    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
        color: #e6edf3;
    }
    
    /* 1. 侧边栏视觉修复：解决颜色太淡看不清的问题 */
    [data-testid="stSidebar"] {
        background-color: #010409 !important; /* 极深背景 */
        border-right: 1px solid #30363d;
    }
    
    /* 强制侧边栏标题、标签、单选按钮、普通文本为纯白，不透明度设为 1 */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] div[role="radiogroup"] label p {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 500 !important;
    }

    /* 侧边栏收缩按钮 "<<" 的颜色改为白色 */
    button[data-testid="stSidebarCollapseButton"] svg {
        fill: #ffffff !important;
        color: #ffffff !important;
    }

    /* 2. 愿望栏上方提示文字颜色 (高对比度白色) */
    .stTextInput label, .stSelectbox label, .stTextArea label {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
    }
    
    /* 3. Kanban 编辑框：深色背景 + 纯白文字 */
    .stTextArea textarea {
        background-color: #0d1117 !important;
        color: #ffffff !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        font-size: 0.95rem !important;
    }
    
    /* 4. 按钮美化：绿色常驻背景，解决鼠标移开看不清的问题 */
    .stButton > button {
        background-color: rgba(35, 134, 54, 0.4) !important;
        color: #ffffff !important;
        border: 1px solid rgba(46, 160, 67, 0.6) !important;
        border-radius: 8px;
        transition: all 0.2s ease;
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

# --- 3. 初始化服务与 UUID 非空检查逻辑 ---
cookies = EncryptedCookieManager(password="SkyWishes_Secure_2026")
if not cookies.ready(): st.stop()

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# 管理 Guest ID 并防止 "None" 字符串污染
if "guest_id" not in cookies or not cookies["guest_id"] or cookies["guest_id"] == "None":
    cookies["guest_id"] = str(uuid.uuid4())
    cookies.save()

# 获取并再次检查 current_guest_id，确保传给 Supabase 的是有效 UUID
raw_guest_id = cookies.get("guest_id")
current_guest_id = raw_guest_id if (raw_guest_id and raw_guest_id != "None") else None

# --- 4. 语言文案配置 (已补全 lantern 键) ---
LANGS = {
    "English": {
        "title": "🏮 SkyWishes Portal",
        "subtitle": "Manifest your 2026 aspirations into the stellar void.",
        "wish_label": "What is your heart's desire for the new year?",
        "launch_btn": "Launch Sky Lantern",
        "save_btn": "Save Roadmap Changes",
        "history_title": "✨ Celestial Memories",
        "step_hint": "Action Roadmap (Directly edit below)",
        "loading": "Architecting your path...",
        "auth_welcome": "🌟 Welcome back to the stars!",
        "auth_benefit": "Accounts sync your wishes across devices.",
        "forgot_pw": "Forgot Password?",
        "reset_sent": "Check your email for reset link!",
        "user_exists": "This email is already registered. Please login.",
        "lantern": "Sky Lantern" # 补全此键
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
        "lantern": "孔明灯" # 补全此键
    }
}

top_col1, top_col2 = st.columns([8, 2])
with top_col2:
    sel_lang = st.selectbox("Lang", ["English", "中文"], label_visibility="collapsed")
T = LANGS[sel_lang]

with top_col1:
    st.title(T["title"])
    st.markdown(f"*{T['subtitle']}*")

# --- 5. 侧边栏：账户管理与注册检测 ---
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
            
            # 智能检测邮箱是否已注册
            if auth_mode == "Sign Up" and st.button("Create Account"):
                try:
                    res = supabase.auth.sign_up({"email": email, "password": pw})
                    # 如果 identities 列表为空，说明该邮箱已被占用
                    if res.user and res.user.identities is not None and len(res.user.identities) == 0:
                        st.warning(T["user_exists"])
                    elif res.user:
                        st.success("Verification email sent!")
                except Exception as e:
                    st.error(f"Registration Error: {e}")

            if auth_mode == "Login":
                if st.button("Sign In"):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                        if res.user:
                            st.session_state["u_id"] = res.user.id
                            st.session_state["user_email"] = res.user.email
                            # 自动合并访客数据（仅当 UUID 有效时）
                            if current_guest_id:
                                supabase.table("wish_history").update({"user_id": res.user.id}).eq("guest_id", current_guest_id).execute()
                            st.rerun()
                    except Exception: st.error("Login failed. Check your email or password.")
                
                if st.button(T["forgot_pw"]):
                    if email:
                        supabase.auth.reset_password_for_email(email)
                        st.info(T["reset_sent"])
                    else: st.warning("Please enter your email address first.")
    else:
        st.success(f"Online: {st.session_state.get('user_email', 'Celestial Member')}")
        if st.button("Sign Out"):
            st.session_state.clear()
            st.rerun()

# --- 6. 愿望交互逻辑 ---
user_wish = st.text_input(T["wish_label"], placeholder="e.g. Master AI development and stay healthy in 2026")

if st.button(T["launch_btn"]):
    if user_wish:
        with st.spinner(T["loading"]):
            try:
                # 调用 CrewAI 架构师
                result = MyProjectCrew().crew().kickoff(inputs={'wish': user_wish})
                data = result.pydantic 
                
                db_entry = {
                    "guest_id": current_guest_id,
                    "user_id": st.session_state.get("u_id"),
                    "wish_text": user_wish,
                    "plan_json": data.dict(),
                    "lang": sel_lang
                }
                # 只有在 current_guest_id 存在时才插入
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
    
    # 安全获取 lantern_name，防 KeyError
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
                new_s = st.text_area(f"edit_box_{i}", value=s, height=220, label_visibility="collapsed")
                edited_steps.append(new_s)
        
        # 保存对计划的自定义修改
        if st.button(T["save_btn"], use_container_width=True):
            if "current_wish_db_id" in st.session_state:
                plan['steps'] = edited_steps
                supabase.table("wish_history").update({"plan_json": plan}).eq("id", st.session_state["current_wish_db_id"]).execute()
                st.session_state["last_plan"] = plan
                st.toast("Roadmap saved to your archive! 🌟")

# --- 8. 历史回顾 (UUID 非空保护) ---
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
else:
    st.info("Start by making your first wish to see your history!")