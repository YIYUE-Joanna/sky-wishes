import os
# 禁用遥测警告
os.environ["OTEL_SDK_DISABLED"] = "true"

import streamlit as st
import uuid
import time
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

# --- 2. 视觉一致性与动画 (CSS 注入) ---
# 包含：流星背景、闪烁繁星、以及放飞灯笼/烟花的动画逻辑
st.markdown("""
    <style>
    /* 全局背景 */
    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
        color: #e6edf3;
        overflow: hidden;
    }

    /* --- 星空背景层 --- */
    .star-bg {
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        z-index: -1;
        background: transparent;
    }
    
    .shooting-star {
        position: absolute;
        left: 50%; top: 50%;
        height: 2px;
        background: linear-gradient(-45deg, #5f91ff, rgba(0, 0, 255, 0));
        filter: drop-shadow(0 0 6px #699bff);
        animation: tail 3000ms ease-in-out infinite, shooting 3000ms ease-in-out infinite;
    }
    @keyframes tail { 0% { width: 0; } 30% { width: 100px; } 100% { width: 0; } }
    @keyframes shooting { 0% { transform: translateX(0) translateY(0) rotate(45deg); } 100% { transform: translateX(-500px) translateY(500px) rotate(45deg); } }
    
    .shooting-star:nth-child(1) { top: 10%; right: 10%; animation-delay: 0s; }
    .shooting-star:nth-child(2) { top: 30%; right: 20%; animation-delay: 5s; }
    .shooting-star:nth-child(3) { top: 5%; right: 40%; animation-delay: 8s; }

    /* --- 像素灯笼上升动画 --- */
    @keyframes lantern-up {
        0% { bottom: -100px; opacity: 1; transform: scale(1); }
        80% { opacity: 1; transform: scale(1.2); }
        100% { bottom: 80%; opacity: 0; transform: scale(0.5); }
    }
    
    .pixel-lantern {
        position: fixed;
        left: 50%;
        width: 40px;
        height: 50px;
        background: #ff4d4d;
        border: 4px solid #330000;
        box-shadow: 0 0 20px #ff9933;
        z-index: 9999;
        animation: lantern-up 3s forwards ease-in;
    }
    .pixel-lantern::after {
        content: "";
        position: absolute;
        bottom: -15px; left: 10px;
        width: 12px; height: 15px;
        background: #ffcc00;
    }

    /* --- 烟花粒子效果 --- */
    @keyframes firework {
        0% { transform: scale(0.1); opacity: 1; }
        100% { transform: scale(2); opacity: 0; }
    }
    .firework-particle {
        position: fixed;
        top: 20%; left: 50%;
        width: 100px; height: 100px;
        border: 2px dotted #ffcc00;
        border-radius: 50%;
        animation: firework 1s 2.8s forwards;
        z-index: 9998;
    }

    /* --- 原有 UI 修复 --- */
    [data-testid="stSidebar"] {
        background-color: #010409 !important;
        border-right: 1px solid #30363d;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] .stMarkdown {
        color: #ffffff !important;
    }
    button[data-testid="stSidebarCollapseButton"] svg { fill: #ffffff !important; }
    .stTextInput label, .stSelectbox label, .stTextArea label { color: #ffffff !important; }
    .stTextArea textarea { background-color: #0d1117 !important; color: #ffffff !important; border: 1px solid #30363d !important; }
    
    .stButton > button {
        background-color: rgba(35, 134, 54, 0.4) !important;
        color: #ffffff !important;
        border: 1px solid rgba(46, 160, 67, 0.6) !important;
        border-radius: 8px;
    }
    .stButton > button:hover { background-color: rgba(35, 134, 54, 0.6) !important; border-color: #3fb950 !important; }
    </style>
    
    <div class="star-bg">
        <div class="shooting-star"></div>
        <div class="shooting-star"></div>
        <div class="shooting-star"></div>
    </div>
    """, unsafe_allow_html=True)

# --- 3. 初始化服务 ---
cookies = EncryptedCookieManager(password="SkyWishes_Secure_2026")
if not cookies.ready(): st.stop()

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

if "guest_id" not in cookies or not cookies["guest_id"] or cookies["guest_id"] == "None":
    cookies["guest_id"] = str(uuid.uuid4())
    cookies.save()

raw_guest_id = cookies.get("guest_id")
current_guest_id = raw_guest_id if (raw_guest_id and raw_guest_id != "None") else None

# --- 4. 语言配置 ---
LANGS = {
    "English": {
        "title": "🏮 SkyWishes Portal",
        "subtitle": "Bring your 2026 dreams to life among the stars.",
        "wish_label": "🌟What's on your wish list?",
        "launch_btn": "Release My Sky Lantern",
        "save_btn": "Save Roadmap Changes",
        "history_title": "✨ Celestial Memories",
        "step_hint": "Action Roadmap (Feel free to refine below)",
        "loading": "Watching your lantern carry your wish to the stars...",
        "auth_welcome": "🌟 Welcome back to the stars!",
        "auth_benefit": "Accounts sync your wishes across devices.",
        "forgot_pw": "Forgot Password?",
        "reset_sent": "Check your email for the link!",
        "reset_error": "Please enter your email first.",
        "user_exists": "This email is already registered. Please login.",
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
        "loading": "灯笼正带着你的愿望飞向星空...",
        "auth_welcome": "🌟 欢迎重回星空！",
        "auth_benefit": "登录后，愿望将多端同步并永久保存。",
        "forgot_pw": "忘记密码？",
        "reset_sent": "重置链接已发送至邮箱！",
        "reset_error": "请先输入邮箱地址。",
        "user_exists": "该邮箱已注册，请尝试直接登录。",
        "lantern": "孔明灯",
        "auth_mode_label": "选择身份"
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
        modes = ["Guest", "Login", "Sign Up"] if sel_lang == "English" else ["访客模式", "登录", "注册"]
        auth_mode = st.radio(T["auth_mode_label"], modes, label_visibility="collapsed")
        
        is_guest = auth_mode in ["Guest", "访客模式"]
        is_login = auth_mode in ["Login", "登录"]
        is_signup = auth_mode in ["Sign Up", "注册"]

        if not is_guest:
            email = st.text_input("Email", placeholder="your@email.com")
            pw = st.text_input("Password", type="password")
            
            if is_signup and st.button("Create Account" if sel_lang == "English" else "提交注册"):
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
                    except Exception: st.error("Login failed.")
                
                if st.button(T["forgot_pw"]):
                    if email:
                        try:
                            supabase.auth.reset_password_for_email(email)
                            st.info(T["reset_sent"])
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning(T["reset_error"])
    else:
        st.success(f"Online: {st.session_state.get('user_email', 'Member')}")
        if st.button("Sign Out" if sel_lang == "English" else "退出登录"):
            st.session_state.clear()
            st.rerun()

# --- 6. 愿望交互 (含放飞动画触发) ---
user_wish = st.text_input(T["wish_label"], placeholder="e.g. I want to take better care of my health.")

if st.button(T["launch_btn"], use_container_width=True):
    if user_wish:
        # 1. 注入动画 HTML
        animation_placeholder = st.empty()
        animation_placeholder.markdown("""
            <div class="pixel-lantern"></div>
            <div class="firework-particle"></div>
        """, unsafe_allow_html=True)
        
        # 2. 生成过程
        with st.spinner(T["loading"]):
            try:
                result = MyProjectCrew().crew().kickoff(inputs={'wish': user_wish, 'language': sel_lang})
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
                
                # 动画停留一小会儿让效果完整
                time.sleep(1) 
                st.balloons()
                st.rerun()
            except Exception as e:
                animation_placeholder.empty()
                st.error(f"Launch failed: {e}")

# --- 7. Kanban 展示与保存 ---
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
                new_s = st.text_area(f"edit_{i}", value=s, height=220, label_visibility="collapsed", key=f"kanban_step_{i}")
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