import os
os.environ["OTEL_SDK_DISABLED"] = "true"

import streamlit as st
import uuid
import time
import random
from supabase import create_client, Client
from streamlit_cookies_manager import EncryptedCookieManager
# 确保导入路径与您的文件夹结构一致
from my_project.crew import MyProjectCrew

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="SkyWishes Portal", 
    page_icon="🏮", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- 2. 动态生成星空 ---
def get_star_field_html():
    stars = ""
    for _ in range(100):
        top = random.randint(0, 100)
        left = random.randint(0, 100)
        size = random.uniform(1, 3)
        delay = random.uniform(0, 5)
        stars += f'<div class="star" style="top:{top}%; left:{left}%; width:{size}px; height:{size}px; animation-delay: {delay}s;"></div>'
    return f'<div class="star-layer">{stars}</div>'

# --- 3. 注入视觉样式 (CSS) ---
# 强制侧边栏所有文字为白色，确保可见
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #0d1117, #161b22, #0d1117, #1a1a2e);
        background-size: 400% 400%;
        animation: aurora-bg 15s ease infinite;
        color: #e6edf3;
    }}
    @keyframes aurora-bg {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}
    /* 强制侧边栏文本为白色 */
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {{
        color: #ffffff !important;
        opacity: 1 !important;
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
    .star-layer {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; pointer-events: none; }}
    .star {{ position: absolute; background: white; border-radius: 50%; animation: twinkle 3s infinite ease-in-out; }}
    @keyframes twinkle {{ 0%, 100% {{ opacity: 0.3; transform: scale(1); }} 50% {{ opacity: 1; transform: scale(1.3); }} }}
    .ritual-container {{ position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; height: 100%; z-index: 9999; pointer-events: none; }}
    .loading-lantern {{ position: absolute; left: 50%; bottom: -100px; width: 45px; height: 60px; background: #ff4d4d; border: 3px solid #330000; box-shadow: 0 0 25px #ff9933; animation: rise-ritual 8s linear infinite; }}
    @keyframes rise-ritual {{ 0% {{ bottom: -10%; opacity: 1; }} 100% {{ bottom: 110%; opacity: 0; }} }}
    </style>
    {get_star_field_html()}
    """, unsafe_allow_html=True)

# --- 4. 初始化服务 ---
cookies = EncryptedCookieManager(password="SkyWishes_Secure_2026")
if not cookies.ready(): st.stop()

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

if "guest_id" not in cookies or not cookies["guest_id"] or cookies["guest_id"] == "None":
    cookies["guest_id"] = str(uuid.uuid4())
    cookies.save()

current_guest_id = cookies.get("guest_id")

# --- 5. 文案配置 ---
LANGS = {
    "English": {
        "wish_label": "🌟What's on your wish list?",
        "launch_btn": "Release My Sky Lantern",
        "forgot_pw": "Forgot Password?",
        "reset_sent": "Check your email for the link!",
        "reset_error": "Please enter your email first.",
        "quota_error": "🌟 You've reached today's wish limit. ✨",
        "loading": "Celestial winds are carrying your wish upwards..."
    },
    "中文": {
        "wish_label": "许下你的 2026 新年愿望...",
        "launch_btn": "放飞孔明灯",
        "forgot_pw": "忘记密码？",
        "reset_sent": "重置链接已发送至邮箱！",
        "reset_error": "请先输入邮箱地址。",
        "quota_error": "🌟 今天的愿望额度已达上限。✨",
        "loading": "星空之风正带着你的愿望冉冉升起..."
    }
}
sel_lang = st.sidebar.selectbox("Language", ["English", "中文"])
T = LANGS[sel_lang]

# --- 6. 侧边栏：账户与重置功能 ---
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
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                        if res.user:
                            st.session_state["u_id"] = res.user.id
                            st.rerun()
                    except: st.error("Login failed.")
                
                # 密码重置功能 - 位于登录按钮下方
                if st.button(T["forgot_pw"]):
                    if email:
                        try:
                            supabase.auth.reset_password_for_email(email)
                            st.success(T["reset_sent"])
                        except Exception as e: st.error(f"Error: {e}")
                    else: st.warning(T["reset_error"])
            else:
                if st.button("Create Account"):
                    try: supabase.auth.sign_up({"email": email, "password": pw}); st.success("Check email!")
                    except Exception as e: st.error(f"Error: {e}")
    else:
        if st.button("Sign Out"): st.session_state.clear(); st.rerun()

# --- 7. 核心交互：模型轮询 ---
st.title("🏮 SkyWishes Portal")
user_wish = st.text_input(T["wish_label"])

# 整合截图中所有可用模型，Lite 优先
MODELS_TO_TRY = [
    "gemini-2.5-flash-lite", 
    "gemini-3-flash", 
    "gemini-2.5-flash", 
    "gemma-3-27b", "gemma-3-12b", "gemma-3-4b", "gemma-3-2b", "gemma-3-1b",
    "gemini-2.0-flash", "gemini-2.5-pro"
]

if st.button(T["launch_btn"], use_container_width=True):
    if user_wish:
        ritual = st.empty()
        ritual.markdown('<div class="ritual-container"><div class="loading-lantern"></div></div>', unsafe_allow_html=True)
        with st.spinner(T["loading"]):
            success = False
            for model_name in MODELS_TO_TRY:
                try:
                    # 修复 ImportError：不再在 crew.py 内部循环导入
                    result = MyProjectCrew(model_name=model_name).crew().kickoff(inputs={'wish': user_wish})
                    st.session_state["last_plan"] = result.pydantic.dict()
                    st.balloons()
                    success = True
                    break
                except Exception as e:
                    print(f"DEBUG: {model_name} failed: {e}")
                    continue
            if not success: st.error(T["quota_error"])
            else: st.rerun()

# --- 8. 显示结果 ---
if "last_plan" in st.session_state:
    plan = st.session_state["last_plan"]
    st.subheader(f"✨ {plan.get('lantern_name', 'Wish Plan')}")
    st.write(plan.get('response', ''))
    for i, step in enumerate(plan.get('steps', [])):
        st.info(f"**Step {i+1}**: {step}")