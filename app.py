import os
# 彻底禁用遥测信号报错
os.environ["OTEL_SDK_DISABLED"] = "true"

import streamlit as st
import uuid
import time
import random
from datetime import datetime, timezone
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

# --- 2. 动态生成星空 HTML 逻辑 ---
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
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #0d1117, #161b22, #0d1117, #1a1a2e);
        background-size: 400% 400%;
        animation: aurora-bg 15s ease infinite;
        color: #e6edf3;
        overflow-x: hidden;
    }}
    @keyframes aurora-bg {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}

    /* 侧边栏样式 - 确保所有文字和标签为纯白 */
    [data-testid="stSidebar"] {{
        background-color: #010409 !important;
        border-right: 1px solid #30363d;
    }}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] div[role="radiogroup"] label p {{
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 500 !important;
    }}
    button[data-testid="stSidebarCollapseButton"] svg {{ fill: #ffffff !important; }}

    .stButton > button {{
        background-color: rgba(35, 134, 54, 0.4) !important;
        color: #ffffff !important;
        border: 2px solid rgba(210, 153, 34, 0.6) !important;
        border-radius: 8px;
        animation: breathing-gold 2.5s infinite ease-in-out;
    }}
    @keyframes breathing-gold {{
        0% {{ box-shadow: 0 0 5px rgba(210, 153, 34, 0.2); }}
        50% {{ box-shadow: 0 0 20px rgba(210, 153, 34, 0.7); border-color: rgba(212, 175, 55, 1); }}
        100% {{ box-shadow: 0 0 5px rgba(210, 153, 34, 0.2); }}
    }}

    .star-layer {{
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        z-index: 0;
        pointer-events: none;
    }}
    .star {{
        position: absolute;
        background: white;
        border-radius: 50%;
        animation: twinkle 3s infinite ease-in-out;
    }}
    @keyframes twinkle {{
        0%, 100% {{ opacity: 0.3; transform: scale(1); }}
        50% {{ opacity: 1; transform: scale(1.3); }}
    }}

    .ritual-container {{
        position: fixed;
        bottom: 0; left: 50%;
        transform: translateX(-50%);
        width: 100%; height: 100%;
        z-index: 9999;
        pointer-events: none;
    }}
    .loading-lantern {{
        position: absolute;
        left: 50%; bottom: -100px;
        width: 45px; height: 60px;
        background: #ff4d4d;
        border: 3px solid #330000;
        box-shadow: 0 0 25px #ff9933;
        animation: rise-ritual 8s linear infinite;
    }}
    @keyframes rise-ritual {{
        0% {{ bottom: -10%; opacity: 1; }}
        100% {{ bottom: 110%; opacity: 0; }}
    }}
    .firework-burst {{
        position: absolute;
        width: 4px; height: 4px;
        border-radius: 50%;
        animation: explode 2.5s infinite ease-out;
    }}
    @keyframes explode {{
        0% {{ transform: scale(1); opacity: 1; box-shadow: 0 0 0 white; }}
        100% {{ transform: scale(35); opacity: 0; box-shadow: 0 0 20px 5px orange, 15px -15px 20px red, -15px 15px 20px yellow; }}
    }}

    .stTextInput label, .stTextArea label, .stSelectbox label {{ color: #ffffff !important; }}
    </style>
    {get_star_field_html()}
    """, unsafe_allow_html=True)

# --- 4. 初始化服务与 UUID ---
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

# --- 5. 语言文案配置 ---
LANGS = {
    "English": {
        "title": "🏮 SkyWishes Portal",
        "subtitle": "Bring your 2026 dreams to life among the stars.",
        "wish_label": "🌟What's on your wish list?",
        "launch_btn": "Release My Sky Lantern",
        "save_btn": "Save Roadmap Changes",
        "history_title": "✨ Celestial Memories",
        "step_hint": "Action Roadmap (Feel free to refine below)",
        "loading": "Celestial winds are carrying your wish upwards...",
        "auth_welcome": "🌟 Welcome back to the stars!",
        "auth_benefit": "Accounts sync your wishes across devices.",
        "forgot_pw": "Forgot Password?",
        "reset_sent": "Check your email for the link!",
        "reset_error": "Please enter your email first.",
        "user_exists": "This email is already registered. Please login.",
        "lantern": "Sky Lantern",
        "auth_mode_label": "Choose Your Path",
        "quota_error": "You've reached today's wish limit. Come back tomorrow to light another wish ✨",
        "quota_status": "Daily Sparks: {count} / 5 used"
    },
    "中文": {
        "title": "🏮 SkyWishes | 孔明灯广场",
        "subtitle": "点亮 2026 的期许，让愿望在星空下有迹可循。",
        "wish_label": "许下你的 2026 新年愿望...",
        "launch_btn": "放飞孔明灯",
        "save_btn": "保存计划修改内容",
        "history_title": "✨ 往昔星火 (历史记录)",
        "step_hint": "行动看板 (可点击文本框直接微调)",
        "loading": "星空之风正带着你的愿望冉冉升起...",
        "auth_welcome": "🌟 欢迎重回星空！",
        "auth_benefit": "登录后，愿望将多端同步并永久保存。",
        "forgot_pw": "忘记密码？",
        "reset_sent": "重置链接已发送至邮箱！",
        "reset_error": "请先输入邮箱地址。",
        "user_exists": "该邮箱已注册，请尝试直接登录。",
        "lantern": "孔明灯",
        "auth_mode_label": "选择身份",
        "quota_error": "今天的愿望额度已满。请明天再来点亮愿望！ ✨",
        "quota_status": "今日已点亮: {count} / 5"
    }
}

top_col1, top_col2 = st.columns([8, 2])
with top_col2:
    sel_lang = st.selectbox("Lang", ["English", "中文"], label_visibility="collapsed")
T = LANGS[sel_lang]

with top_col1:
    st.title(T["title"])
    st.markdown(f"*{T['subtitle']}*")

# --- 6. 侧边栏：账户管理 ---
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

# --- 7. 额度检查逻辑 (修改：返回具体数值) ---
def get_daily_usage(user_id, guest_id):
    """查询今日已使用的次数"""
    try:
        today_start = datetime.now(timezone.utc).strftime('%Y-%m-%dT00:00:00')
        query = supabase.table("wish_history").select("id", count="exact")
        if user_id:
            query = query.eq("user_id", user_id)
        else:
            query = query.eq("guest_id", guest_id)
        
        res = query.gte("created_at", today_start).execute()
        return res.count if res.count is not None else 0
    except Exception:
        return 0

# --- 8. 核心愿望交互 ---
user_wish = st.text_input(T["wish_label"], placeholder="e.g. I hope to make deeper connections with friends and family in 2026")

# 获取并显示实时额度
usage_count = get_daily_usage(st.session_state.get("u_id"), current_guest_id)
st.caption(T["quota_status"].format(count=usage_count))

if st.button(T["launch_btn"], use_container_width=True):
    if user_wish:
        # 1. 额度预检
        if usage_count >= 5:
            st.error(T["quota_error"])
        else:
            MODELS_TO_TRY = [
                "gemini-2.5-flash-lite", 
                "gemini-2.5-flash", 
                "gemini-3-flash", 
                "gemini-2.5-flash-tts",
                "gemma-3-27b",
                "gemma-3-12b",
                "gemma-3-2b",
                "gemma-3-1b"
            ]
            
            ritual_placeholder = st.empty()
            ritual_placeholder.markdown("""
                <div class="ritual-container">
                    <div class="loading-lantern"></div>
                    <div class="firework-burst" style="top:20%; left:48%; animation-delay: 1s;"></div>
                    <div class="firework-burst" style="top:40%; left:52%; animation-delay: 3.5s;"></div>
                </div>
            """, unsafe_allow_html=True)

            success = False
            with st.spinner(T["loading"]):
                for model_name in MODELS_TO_TRY:
                    try:
                        result = MyProjectCrew(model_name=model_name).crew().kickoff(inputs={'wish': user_wish, 'language': sel_lang})
                        data = result.pydantic 
                        
                        db_entry = {
                            "guest_id": current_guest_id,
                            "user_id": st.session_state.get("u_id"),
                            "wish_text": user_wish,
                            "plan_json": data.dict(),
                            "lang": sel_lang
                        }
                        if current_guest_id or st.session_state.get("u_id"):
                            res = supabase.table("wish_history").insert(db_entry).execute()
                            if res.data:
                                st.session_state["current_wish_db_id"] = res.data[0]['id']
                        
                        st.session_state["last_plan"] = data.dict()
                        success = True
                        break 
                    except Exception as e:
                        err_str = str(e)
                        if any(x in err_str for x in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
                            continue 
                        else:
                            ritual_placeholder.empty()
                            st.error(f"Launch failed on {model_name}: {e}")
                            break

                if success:
                    st.balloons()
                    st.rerun()
                elif not success:
                    ritual_placeholder.empty()
                    st.error(T["quota_error"])

# --- 9. Kanban 展示与保存 ---
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
                st.markdown(f'<div class="step-header" style="color:#d29922; font-weight:bold;">STEP {i+1}</div>', unsafe_allow_html=True)
                new_s = st.text_area(f"edit_{i}", value=s, height=220, label_visibility="collapsed", key=f"kanban_step_{i}")
                edited_steps.append(new_s)
        
        if st.button(T["save_btn"], use_container_width=True):
            if "current_wish_db_id" in st.session_state:
                plan['steps'] = edited_steps
                supabase.table("wish_history").update({"plan_json": plan}).eq("id", st.session_state["current_wish_db_id"]).execute()
                st.session_state["last_plan"] = plan
                st.toast("Modifications saved! 🌟")

# --- 10. 历史回顾 ---
st.divider()
st.subheader(T["history_title"])
if current_guest_id or u_id:
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