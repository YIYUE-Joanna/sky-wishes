import streamlit as st
import uuid
import os
from supabase import create_client, Client
from streamlit_cookies_manager import EncryptedCookieManager
from my_project.crew import MyProjectCrew

# --- 1. 视觉主题与 CSS 注入 ---
st.set_page_config(page_title="SkyWishes Portal", page_icon="🏮", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        color: #ffffff;
    }
    .kanban-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    .step-label {
        color: #FFD700;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 0.8rem;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 基础初始化 ---
cookies = EncryptedCookieManager(password="SkyWishes_Secure_2026")
if not cookies.ready(): st.stop()

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

if "guest_id" not in cookies:
    cookies["guest_id"] = str(uuid.uuid4())
    cookies.save()
current_guest_id = cookies["guest_id"]

# --- 3. 语言配置 ---
LANGS = {
    "English": {
        "title": "🏮 SkyWishes Portal",
        "subtitle": "Manifest your 2026 aspirations into the stellar void.",
        "wish_label": "What is your heart's desire for the new year?",
        "launch_btn": "Launch Sky Lantern",
        "history_title": "✨ Celestial Memories",
        "step_hint": "Action Roadmap (Click to refine)",
        "loading": "Architecting your path...",
        "lantern": "Sky Lantern"
    },
    "中文": {
        "title": "🏮 SkyWishes | 孔明灯广场",
        "subtitle": "点亮 2026 的期许，让每一个愿望在星空下有迹可循。",
        "wish_label": "许下你的 2026 新年愿望...",
        "launch_btn": "点亮并放飞孔明灯",
        "history_title": "✨ 往昔星火 (历史记忆)",
        "step_hint": "行动看板 (点击内容可直接微调)",
        "loading": "愿望架构师正在规划路径...",
        "lantern": "孔明灯"
    }
}

sel_lang = st.sidebar.selectbox("Language / 语言", ["English", "中文"])
T = LANGS[sel_lang]

st.title(T["title"])
st.markdown(f"*{T['subtitle']}*")

# --- 4. 愿望发射中心 ---
user_wish = st.text_input(T["wish_label"], placeholder="e.g. Mastering AI development in 2026")

if st.button(T["launch_btn"], use_container_width=True):
    if user_wish:
        with st.spinner(T["loading"]):
            result = MyProjectCrew().crew().kickoff(inputs={'wish': user_wish})
            data = result.pydantic 

            db_entry = {
                "guest_id": current_guest_id,
                "user_id": st.session_state.get("u_id"),
                "wish_text": user_wish,
                "plan_json": data.dict(),
                "lang": sel_lang
            }
            supabase.table("wish_history").insert(db_entry).execute()
            
            st.session_state["last_plan"] = data.dict()
            st.balloons() # 烟花升空感
            st.rerun()

# --- 5. Kanban 看板展示 ---
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
                st.text_area("Edit", s, key=f"edit_{i}", label_visibility="collapsed")

# --- 6. 历史记忆 ---
st.divider()
st.subheader(T["history_title"])
q = supabase.table("wish_history").select("*").eq("guest_id", current_guest_id).order("created_at", desc=True).execute()

for item in q.data:
    with st.expander(f"🏮 {item['wish_text']} ({item['created_at'][:10]})"):
        p = item['plan_json']
        st.write(p.get('response', ''))
        h_cols = st.columns(len(p.get('steps', [])))
        for idx, s in enumerate(p.get('steps', [])):
            h_cols[idx].info(f"**Step {idx+1}**\n{s}")