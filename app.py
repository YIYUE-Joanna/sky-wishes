import streamlit as st
import uuid
from supabase import create_client, Client
from streamlit_cookies_manager import EncryptedCookieManager
from my_project.crew import MyProjectCrew
import os

# --- 1. 初始化加密 Cookie 管理器 (用于记住浏览器) ---
cookies = EncryptedCookieManager(password="your_secret_password_here")
if not cookies.ready():
    st.stop()

# --- 2. 初始化 Supabase ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"] # 这里是 anon key
supabase: Client = create_client(url, key)

# --- 3. 获取或生成 Guest ID ---
if "guest_id" not in cookies:
    cookies["guest_id"] = str(uuid.uuid4())
    cookies.save()
current_guest_id = cookies["guest_id"]

# --- 4. 侧边栏：登录与注册 ---
with st.sidebar:
    st.title("🏮 SkyWishes Portal")
    mode = st.radio("Mode / 模式", ["Guest / 访客", "Login / 登录", "Sign Up / 注册"])
    
    user_id = None
    if mode != "Guest / 访客":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if mode == "Sign Up / 注册" and st.button("Create Account"):
            res = supabase.auth.sign_up({"email": email, "password": password})
            st.success("Check your email for confirmation!")
            
        if mode == "Login / 登录" and st.button("Sign In"):
            auth_res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if auth_res.user:
                user_id = auth_res.user.id
                st.session_state["user_id"] = user_id
                # 关键：合并访客历史到正式账户
                supabase.table("wish_history").update({"user_id": user_id}).eq("guest_id", current_guest_id).execute()
                st.success("Login success & History merged!")

# --- 5. 主页面逻辑 ---
st.title("🏮 天灯广场 2026")
user_wish = st.text_input("许下你的新年愿望...")

if st.button("点亮天灯"):
    with st.spinner("架构师正在规划..."):
        inputs = {'wish': user_wish}
        result = MyProjectCrew().crew().kickoff(inputs=inputs)
        data = result.pydantic # 拿到 CrewAI 的结构化 JSON

        # 准备存入数据库的数据
        db_data = {
            "guest_id": current_guest_id,
            "user_id": st.session_state.get("user_id"),
            "wish_text": user_wish,
            "plan_json": data.dict()
        }
        supabase.table("wish_history").insert(db_data).execute()
        st.session_state["current_plan"] = data.dict()

# --- 6. 展示专属记忆 (Kanban 视图) ---
st.subheader("我的专属记忆 / My History")
# 同时查询该 guest_id 或 该 user_id 的愿望
query = supabase.table("wish_history").select("*")
if st.session_state.get("user_id"):
    query = query.eq("user_id", st.session_state["user_id"])
else:
    query = query.eq("guest_id", current_guest_id)

history = query.order("created_at", desc=True).execute()

for item in history.data:
    with st.expander(f"🏮 {item['wish_text']} ({item['created_at'][:10]})"):
        st.json(item['plan_json'])