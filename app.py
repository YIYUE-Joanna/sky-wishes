import os
# 禁用遥测信号报错
os.environ["OTEL_SDK_DISABLED"] = "true"

import streamlit as st
import streamlit.components.v1 as components
import uuid
from supabase import create_client, Client
from streamlit_cookies_manager import EncryptedCookieManager
from my_project.crew import MyProjectCrew

# --- 1. 页面配置：修复问题 1 (侧边栏默认打开) ---
st.set_page_config(
    page_title="SkyWishes Portal", 
    page_icon="🏮", 
    layout="wide",
    initial_sidebar_state="expanded"  # 设置侧边栏一开始就是打开状态
)

# --- 2. 视觉一致性优化 (CSS 注入) ---
st.markdown("""
    <style>
    /* 全局背景 */
    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
        color: #e6edf3;
    }
    
    /* 侧边栏视觉增强 */
    [data-testid="stSidebar"] {
        background-color: #010409 !important;
        border-right: 1px solid #30363d;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] div[role="radiogroup"] label p {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 500 !important;
    }

    /* 侧边栏收缩箭头白色 */
    button[data-testid="stSidebarCollapseButton"] svg {
        fill: #ffffff !important;
        color: #ffffff !important;
    }

    /* 修复愿望栏上方文字颜色 */
    .stTextInput label, .stSelectbox label, .stTextArea label {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
    }
    
    /* Kanban 编辑框视觉 */
    .stTextArea textarea {
        background-color: #0d1117 !important;
        color: #ffffff !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }
    
    /* 按钮美化 */
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

    /* --- 孔明灯升空动画 --- */
    @keyframes riseUp {
        0% { bottom: -100px; opacity: 1; transform: translateX(0); }
        50% { transform: translateX(30px); }
        100% { bottom: 110vh; opacity: 0; transform: translateX(-20px); }
    }
    .pixel-lantern {
        position: fixed;
        left: 48%;
        font-size: 70px;
        z-index: 9999;
        pointer-events: none;
        animation: riseUp 5s ease-in-out infinite;
        image-rendering: pixelated;
    }
    </style>
    """, unsafe_allow_html=True)

# 修复问题 2：定义像素风烟花脚本
def trigger_pixel_fireworks():
    components.html("""
        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
        <script>
            var count = 200;
            var defaults = { origin: { y: 0.7 }, shapes: ['square'], scalar: 2.5, ticks: 150 };
            function fire(particleRatio, opts) {
              confetti({ ...defaults, ...opts, particleCount: Math.floor(count * particleRatio) });
            }
            fire(0.25, { spread: 26, startVelocity: 55 });
            fire(0.2, { spread: 60 });
            fire(0.35, { spread: 100, decay: 0.91, scalar: 1.5 });
            fire(0.1, { spread: 120, startVelocity: 25, decay: 0.92, scalar: 3 });
            fire(0.1, { spread: 120, startVelocity: 45 });
        </script>
    """, height=0)

# --- 3. 初始化服务 ---
cookies = EncryptedCookieManager(password="SkyWishes_Secure_2026")
if not cookies.ready(): st.stop()

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# 修复问题 3：UUID 非空逻辑
if "guest_id" not in cookies or not cookies["guest_id"] or cookies["guest_id"] == "None":
    cookies["guest_id"] = str(uuid.uuid4())
    cookies.save()

raw_guest_id = cookies.get("guest_id")
current_guest_id = raw_guest_id if (raw_guest_id and raw_guest_id != "None") else None

# --- 4. 语言配置 ---
LANGS = {
    "English": {
        "title": "🏮 SkyWishes Portal",
        "subtitle": "Manifest your 2026 aspirations into the stellar void.",
        "wish_label": "What is your heart's desire for the new year?",
        "launch_btn": "Launch Sky Lantern",
        "save_btn": "Save Roadmap Changes",
        "history_title": "✨ Celestial Memories",
        "step_hint": "Action Roadmap (Feel free to refine below)",
        "loading": "Architecting your path...",
        "lantern": "Sky Lantern"
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
        "lantern": "孔明灯"
    }
}

top_col1, top_col2 = st.columns([8, 2])
with top_col2:
    sel_lang = st.selectbox("Lang", ["English", "中文"], label_visibility="collapsed")
T = LANGS[sel_lang]

with top_col1:
    st.title(T["title"])
    st.markdown(f"*{T['subtitle']}*")

# --- 5. 愿望发射中心 ---
user_wish = st.text_input(T["wish_label"], placeholder="e.g. Master AI development in 2026")

if st.button(T["launch_btn"], use_container_width=True):
    if user_wish:
        # 显示升空灯笼
        lantern_placeholder = st.empty()
        lantern_placeholder.markdown('<div class="pixel-lantern">🏮</div>', unsafe_allow_html=True)
        
        with st.spinner(T["loading"]):
            try:
                # 调用 CrewAI
                result = MyProjectCrew().crew().kickoff(inputs={'wish': user_wish, 'language': sel_lang})
                data = result.pydantic 

                db_entry = {
                    "guest_id": current_guest_id,
                    "user_id": st.session_state.get("u_id"),
                    "wish_text": user_wish,
                    "plan_json": data.dict(),
                    "lang": sel_lang
                }
                
                # 写入数据库 (修复 500 报错的关键：检查 current_guest_id)
                if current_guest_id:
                    supabase.table("wish_history").insert(db_entry).execute()
                
                st.session_state["last_plan"] = data.dict()
                
                # 成功后移除灯笼并触发像素烟花
                lantern_placeholder.empty()
                trigger_pixel_fireworks() # 修复问题 2
                st.rerun()
            except Exception as e:
                lantern_placeholder.empty()
                st.error(f"Launch failed: {e}. Please check if Supabase project is active.")

# --- 6. Kanban 看板展示 ---
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
                st.markdown(f'<div class="step-header">STEP {i+1}</div>', unsafe_allow_html=True)
                st.text_area("Edit", s, key=f"edit_{i}", label_visibility="collapsed", height=200)

# --- 7. 历史记忆 (UUID 安全检查) ---
st.divider()
st.subheader(T["history_title"])
if current_guest_id:
    try:
        q = supabase.table("wish_history").select("*").eq("guest_id", current_guest_id).order("created_at", desc=True).execute()
        for item in q.data:
            with st.expander(f"🏮 {item['wish_text']} ({item['created_at'][:10]})"):
                p = item['plan_json']
                st.write(p.get('response', ''))
                h_cols = st.columns(len(p.get('steps', [])))
                for idx, s in enumerate(p.get('steps', [])):
                    h_cols[idx].info(f"**Step {idx+1}**\n{s}")
    except Exception as e:
        st.warning(f"Could not load history: {e}")