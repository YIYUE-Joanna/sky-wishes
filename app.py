import os
# 禁用遥测警告
os.environ["OTEL_SDK_DISABLED"] = "true"

import streamlit as st
import uuid
from supabase import create_client, Client
from streamlit_cookies_manager import EncryptedCookieManager
from my_project.crew import MyProjectCrew

# --- 1. 页面配置与视觉优化 (CSS) ---
st.set_page_config(page_title="SkyWishes Portal", page_icon="🏮", layout="wide")

st.markdown("""
    <style>
    /* 星空背景 */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        color: #ffffff;
    }
    
    /* 修复问题 2：让输入框标签文字变清晰 (白色) */
    .stTextInput label, .stSelectbox label {
        color: white !important;
        font-weight: 500;
        opacity: 1 !important;
    }

    /* 修复问题 3：美化按钮，解决空白格与悬停可见问题 */
    .stButton > button {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 8px;
        padding: 10px 24px;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.2) !important;
        border-color: #FFD700 !important;
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.2);
    }

    /* Kanban 卡片样式 */
    .kanban-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .step-label {
        color: #FFD700;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 基础初始化 (Cookies & Supabase) ---
cookies = EncryptedCookieManager(password="SkyWishes_Secure_2026")
if not cookies.ready(): 
    st.stop()

# 从 Secrets 获取配置
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# 管理 Guest ID
if "guest_id" not in cookies or cookies["guest_id"] is None:
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
        "step_hint": "Action Roadmap (Click to refine)",
        "loading": "Architecting your path...",
        "lantern": "Sky Lantern",
        "db_error": "Access denied. Check RLS policies."
    },
    "中文": {
        "title": "🏮 SkyWishes | 孔明灯广场",
        "subtitle": "点亮 2026 的期许，让每一个愿望在星空下有迹可循。",
        "wish_label": "许下你的 2026 新年愿望...",
        "launch_btn": "点亮并放飞孔明灯",
        "history_title": "✨ 往昔星火 (历史记忆)",
        "step_hint": "行动看板 (点击内容可直接微调)",
        "loading": "愿望架构师正在规划路径...",
        "lantern": "孔明灯",
        "db_error": "数据库访问受限，请检查 RLS 策略。"
    }
}

# --- 4. 修复问题 4：右上角语言切换 ---
top_col1, top_col2 = st.columns([8, 2])
with top_col2:
    # 语言选择器移至顶部右侧
    sel_lang = st.selectbox("Language / 语言", ["English", "中文"], label_visibility="collapsed")

T = LANGS[sel_lang]

with top_col1:
    st.title(T["title"])
    st.markdown(f"*{T['subtitle']}*")

# --- 5. 侧边栏：账户系统 ---
with st.sidebar:
    st.header("Account")
    u_id = st.session_state.get("u_id")
    if not u_id:
        mode = st.radio("Mode", ["Guest", "Login", "Sign Up"])
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        if mode == "Login" and st.button("Sign In"):
            res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
            if res.user:
                st.session_state["u_id"] = res.user.id
                st.rerun()
    else:
        st.success("Online")
        if st.button("Log out"):
            st.session_state.clear()
            st.rerun()

# --- 6. 愿望交互区 ---
st.write("") 
user_wish = st.text_input(T["wish_label"], placeholder="e.g. Mastering AI development and staying healthy")

if st.button(T["launch_btn"]):
    if user_wish:
        with st.spinner(T["loading"]):
            try:
                # 调用 CrewAI
                result = MyProjectCrew().crew().kickoff(inputs={'wish': user_wish})
                data = result.pydantic 

                # 准备数据
                db_entry = {
                    "guest_id": current_guest_id,
                    "user_id": st.session_state.get("u_id"),
                    "wish_text": user_wish,
                    "plan_json": data.dict(),
                    "lang": sel_lang
                }
                # 写入
                supabase.table("wish_history").insert(db_entry).execute()
                
                st.session_state["last_plan"] = data.dict()
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# --- 7. Kanban 展示 ---
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
                st.markdown(f'<div class="kanban-card"><div class="step-label">Step {i+1}</div>{s}</div>', unsafe_allow_html=True)

# --- 8. 历史回顾 (修复 UUID "None" 报错) ---
st.divider()
st.subheader(T["history_title"])

# 修复核心逻辑：只有在 current_guest_id 不是字符串 "None" 且有效时才查询
if current_guest_id and current_guest_id != "None":
    try:
        q = supabase.table("wish_history").select("*").eq("guest_id", current_guest_id).order("created_at", desc=True).execute()
        for item in q.data:
            with st.expander(f"🏮 {item['wish_text']} ({item['created_at'][:10]})"):
                p = item['plan_json']
                st.write(p.get('response', ''))
                h_steps = p.get('steps', [])
                if h_steps:
                    h_cols = st.columns(len(h_steps))
                    for idx, s in enumerate(h_steps):
                        h_cols[idx].info(f"**Step {idx+1}**\n{s}")
    except Exception as e:
        st.warning(f"Could not load history: {e}")
else:
    st.info("Start by making your first wish to see your history!")