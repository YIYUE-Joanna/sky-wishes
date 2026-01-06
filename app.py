import streamlit as st
import uuid
import os
from supabase import create_client, Client
from streamlit_cookies_manager import EncryptedCookieManager
from my_project.crew import MyProjectCrew

# --- 1. 初始化设置 ---
st.set_page_config(page_title="Sky Wishes", page_icon="🏮", layout="wide")

# 初始化 Cookie 管理器 (用于记住浏览器访客)
cookies = EncryptedCookieManager(password="SkyWishes_Secure_2026")
if not cookies.ready():
    st.stop()

# 初始化 Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# 获取或生成 Guest ID
if "guest_id" not in cookies:
    cookies["guest_id"] = str(uuid.uuid4())
    cookies.save()
current_guest_id = cookies["guest_id"]

# --- 2. 语言与文本配置 (默认英文) ---
LANGS = {
    "English": {
        "title": "🏮 Sky Wishes",
        "lantern": "Sky Lanterns",
        "wish_label": "Make your wish for 2026...",
        "launch_btn": "Launch Sky Lantern",
        "history_title": "My Personal Memories",
        "login_msg": "Login to sync wishes across devices.",
        "merge_msg": "Guest history merged successfully!",
        "step_hint": "Action Kanban (Edit directly)",
        "loading": "Architecting your wish..."
    },
    "中文": {
        "title": "🏮 Sky Wishes (孔明灯)",
        "lantern": "孔明灯",
        "wish_label": "许下你的 2026 新年愿望...",
        "launch_btn": "点亮孔明灯",
        "history_title": "我的专属记忆",
        "login_msg": "登录后可跨设备同步您的所有愿望。",
        "merge_msg": "检测到访客记录，已自动合并！",
        "step_hint": "行动看板（点击内容可直接修改）",
        "loading": "架构师正在规划..."
    }
}

# --- 3. 顶部 UI：标题与右上角语言切换 ---
header_col1, header_col2 = st.columns([8, 2])
with header_col2:
    # 语言切换器
    sel_lang = st.selectbox("", ["English", "中文"], label_visibility="collapsed")

T = LANGS[sel_lang]

with header_col1:
    st.title(T["title"])

# --- 4. 侧边栏：用户系统 ---
with st.sidebar:
    st.header("Account / 账户")
    u_id = st.session_state.get("u_id")
    
    if not u_id:
        mode = st.radio("Mode", ["Guest", "Login", "Sign Up"])
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        
        if mode == "Sign Up" and st.button("Create"):
            supabase.auth.sign_up({"email": email, "password": pw})
            st.info("Check email to confirm!")
            
        if mode == "Login" and st.button("Sign In"):
            res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
            if res.user:
                st.session_state["u_id"] = res.user.id
                # 合并历史记录
                supabase.table("wish_history").update({"user_id": res.user.id}).eq("guest_id", current_guest_id).execute()
                st.success(T["merge_msg"])
                st.rerun()
    else:
        st.success(f"Logged in as: {email if 'email' in locals() else 'User'}")
        if st.button("Log out"):
            st.session_state.clear()
            st.rerun()

# --- 5. 主愿望发射区 ---
user_wish = st.text_input(T["wish_label"])

if st.button(T["launch_btn"]):
    if user_wish:
        with st.spinner(T["loading"]):
            # 调用 CrewAI
            inputs = {'wish': user_wish}
            result = MyProjectCrew().crew().kickoff(inputs=inputs)
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
            
            # 解决 UI 不显示的关键：存入 Session 并刷新
            st.session_state["last_plan"] = data.dict()
            st.rerun()

# --- 6. 核心 UI 展示：当前生成的计划 ---
if "last_plan" in st.session_state:
    plan = st.session_state["last_plan"]
    with st.container(border=True):
        st.subheader(f"✨ {plan.get('lantern_name', T['lantern'])}")
        st.write(plan.get('response', ''))
        
        st.divider()
        st.caption(T["step_hint"])
        cols = st.columns(3)
        for i, s in enumerate(plan.get('steps', [])):
            with cols[i % 3]:
                st.info(f"**Step {i+1}**\n\n{s}")

# --- 7. 历史记忆区 ---
st.divider()
st.subheader(T["history_title"])

q = supabase.table("wish_history").select("*")
if st.session_state.get("u_id"):
    q = q.eq("user_id", st.session_state["u_id"])
else:
    q = q.eq("guest_id", current_guest_id)

history = q.order("created_at", desc=True).execute()

for item in history.data:
    with st.expander(f"🏮 {item['wish_text']} ({item['created_at'][:10]})"):
        p = item['plan_json']
        st.write(p.get('response', ''))
        st.json(p.get('steps', []))