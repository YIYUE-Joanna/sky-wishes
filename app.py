import os
os.environ["OTEL_SDK_DISABLED"] = "true"

import streamlit as st
import uuid
import time
import random
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

# --- 2. 注入视觉样式 (CSS) ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #0d1117, #161b22, #0d1117, #1a1a2e);
        background-size: 400% 400%;
        animation: aurora-bg 15s ease infinite;
        color: #e6edf3;
    }}
    /* 强制标签为白色 */
    .stTextInput label, .stTextArea label, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {{
        color: #ffffff !important;
    }}
    /* 核心修复：确保输入框文字为深色可见 */
    input {{
        color: #31333F !important;
        -webkit-text-fill-color: #31333F !important;
    }}
    [data-testid="stSidebar"] {{
        background-color: #010409 !important;
        border-right: 1px solid #30363d;
    }}
    .stButton > button {{
        background-color: rgba(35, 134, 54, 0.4) !important;
        color: #ffffff !important;
        border: 2px solid rgba(210, 153, 34, 0.6) !important;
        border-radius: 8px;
    }}
    </style>
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

current_guest_id = cookies.get("guest_id")

# --- 4. 语言文案 ---
LANGS = {
    "English": {
        "title": "SkyWishes Portal",
        "subtitle": "Bring your 2026 dreams to life among the stars.",
        "wish_label": "🌟 What's on your wish list?",
        "placeholder": "e.g. I hope to make deeper connections with friends and family.",
        "launch_btn": "Release My Sky Lantern",
        "forgot_pw": "Forgot Password?",
        "reset_sent": "Check your email for the link!",
        "reset_error": "Please enter your email first.",
        "quota_error": "🌟 Today's limit reached. ✨"
    },
    "中文": {
        "title": "SkyWishes | 孔明灯广场",
        "subtitle": "点亮 2026 的期许，让愿望在星空下有迹可循。",
        "wish_label": "🌟 许下你的 2026 新年愿望...",
        "placeholder": "例如：我希望能与朋友和家人建立更深层次的联系。",
        "launch_btn": "放飞孔明灯",
        "forgot_pw": "忘记密码？",
        "reset_sent": "重置链接已发送至邮箱！",
        "reset_error": "请先输入邮箱地址。",
        "quota_error": "🌟 今天的愿望额度已达上限。✨"
    }
}

col_title, col_lang = st.columns([7, 1.5])
with col_lang:
    sel_lang = st.selectbox("Lang", ["English", "中文"], label_visibility="collapsed")
T = LANGS[sel_lang]

with col_title:
    st.markdown(f"# 🏮 {T['title']}")

# --- 5. 侧边栏与登录修复 ---
with st.sidebar:
    st.header("✨ Account")
    u_id = st.session_state.get("u_id")
    if not u_id:
        auth_mode = st.radio("Path", ["Login", "Sign Up", "Guest"])
        if auth_mode != "Guest":
            email = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            
            if auth_mode == "Login":
                if st.button("Sign In"):
                    login_success = False
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                        if res.user:
                            st.session_state["u_id"] = res.user.id
                            st.session_state["user_email"] = res.user.email
                            if current_guest_id:
                                supabase.table("wish_history").update({"user_id": res.user.id}).eq("guest_id", current_guest_id).execute()
                            login_success = True
                    except Exception as e:
                        st.error(f"Login failed: {e}")
                    
                    # 关键修复：将 st.rerun() 移出 try 块，防止信号被拦截
                    if login_success:
                        st.rerun()

                if st.button(T["forgot_pw"]):
                    if email:
                        try:
                            supabase.auth.reset_password_for_email(email)
                            st.success(T["reset_sent"])
                        except Exception as e: st.error(f"Error: {e}")
                    else: st.warning(T["reset_error"])
    else:
        st.success(f"Online: {st.session_state.get('user_email')}")
        if st.button("Sign Out"): st.session_state.clear(); st.rerun()

# --- 6. 核心交互 ---
user_wish = st.text_input(T["wish_label"], placeholder=T["placeholder"])

MODELS_TO_TRY = [
    "gemini-2.5-flash-lite", "gemini-3-flash", "gemini-2.5-flash", "gemma-3-27b", "gemini-2.5-pro"
]

if st.button(T["launch_btn"], use_container_width=True):
    if user_wish:
        with st.spinner("Processing..."):
            success = False
            for model_name in MODELS_TO_TRY:
                try:
                    result = MyProjectCrew(model_name=model_name).crew().kickoff(inputs={'wish': user_wish})
                    st.session_state["last_plan"] = result.pydantic.dict()
                    st.balloons()
                    success = True
                    break
                except Exception: continue
            if not success: st.error(T["quota_error"])
            else: st.rerun()

if "last_plan" in st.session_state:
    plan = st.session_state["last_plan"]
    st.subheader(f"✨ {plan.get('lantern_name')}")
    st.write(plan.get('response'))