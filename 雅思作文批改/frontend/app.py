import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os
import json

# Add project root to path so we can import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import database, crud
from backend.services.gemini_service import GeminiService
from backend.services.deepseek_service import DeepSeekService

# Page Config
st.set_page_config(
    page_title="IELTS Writing Coach",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize DB Tables
database.init_db()

# Apple Design System CSS
st.markdown("""
<style>
    /* ===== 全局样式 ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --apple-blue: #007AFF;
        --apple-blue-hover: #0056CC;
        --apple-gray-bg: #F5F5F7;
        --apple-white: #FFFFFF;
        --apple-text: #1D1D1F;
        --apple-text-secondary: #86868B;
        --apple-border: rgba(0,0,0,0.04);
        --apple-shadow: 0 4px 12px rgba(0,0,0,0.08);
        --apple-shadow-hover: 0 8px 24px rgba(0,0,0,0.12);
        --apple-radius: 16px;
        --apple-radius-sm: 12px;
    }

    .main, .stApp {
        background-color: var(--apple-gray-bg) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif !important;
    }

    /* ===== 标题样式 ===== */
    h1, h2, h3, h4, h5, h6 {
        color: var(--apple-text) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
    }

    h1 {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
    }

    /* ===== 侧边栏样式 ===== */
    [data-testid="stSidebar"] {
        background: rgba(255,255,255,0.72) !important;
        backdrop-filter: blur(20px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
        border-right: 1px solid var(--apple-border) !important;
    }

    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--apple-text) !important;
    }

    /* ===== 按钮样式 ===== */
    .stButton > button {
        background: var(--apple-blue) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--apple-radius-sm) !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(0,122,255,0.3) !important;
    }

    .stButton > button:hover {
        background: var(--apple-blue-hover) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0,122,255,0.4) !important;
    }

    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* 侧边栏历史按钮 */
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(0,0,0,0.04) !important;
        color: var(--apple-text) !important;
        box-shadow: none !important;
        text-align: left !important;
        justify-content: flex-start !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(0,0,0,0.08) !important;
        transform: none !important;
    }

    /* New Essay 按钮特殊样式 */
    [data-testid="stSidebar"] .stButton:first-of-type > button {
        background: var(--apple-blue) !important;
        color: white !important;
        box-shadow: 0 2px 8px rgba(0,122,255,0.3) !important;
    }

    /* ===== 输入框样式 ===== */
    .stTextArea textarea, .stTextInput input {
        background: var(--apple-white) !important;
        border: 1px solid rgba(0,0,0,0.1) !important;
        border-radius: var(--apple-radius-sm) !important;
        padding: 1rem !important;
        font-size: 1rem !important;
        transition: all 0.2s ease !important;
    }

    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: var(--apple-blue) !important;
        box-shadow: 0 0 0 3px rgba(0,122,255,0.15) !important;
        outline: none !important;
    }

    /* ===== 下拉框样式 ===== */
    .stSelectbox > div > div {
        background: var(--apple-white) !important;
        border: 1px solid rgba(0,0,0,0.1) !important;
        border-radius: var(--apple-radius-sm) !important;
    }

    /* ===== Metric 卡片样式 ===== */
    [data-testid="stMetric"] {
        background: var(--apple-white) !important;
        border-radius: var(--apple-radius) !important;
        padding: 1.5rem !important;
        box-shadow: var(--apple-shadow) !important;
        transition: all 0.3s ease !important;
        border: 1px solid var(--apple-border) !important;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-4px) !important;
        box-shadow: var(--apple-shadow-hover) !important;
    }

    [data-testid="stMetric"] label {
        color: var(--apple-text-secondary) !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }

    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--apple-blue) !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }

    /* ===== Tab 样式 ===== */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        gap: 0 !important;
        border-bottom: 1px solid rgba(0,0,0,0.1) !important;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--apple-text-secondary) !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        padding: 1rem 1.5rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: var(--apple-text) !important;
    }

    .stTabs [aria-selected="true"] {
        color: var(--apple-blue) !important;
        border-bottom: 2px solid var(--apple-blue) !important;
        background: transparent !important;
    }

    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1.5rem !important;
    }

    /* ===== 信息框样式 ===== */
    .stAlert {
        background: rgba(0,122,255,0.08) !important;
        border: none !important;
        border-radius: var(--apple-radius-sm) !important;
        border-left: 4px solid var(--apple-blue) !important;
    }

    /* ===== 分隔线 ===== */
    hr {
        border: none !important;
        height: 1px !important;
        background: rgba(0,0,0,0.08) !important;
        margin: 2rem 0 !important;
    }

    /* ===== Spinner ===== */
    .stSpinner > div {
        border-top-color: var(--apple-blue) !important;
    }

    /* ===== 成功/错误消息 ===== */
    .stSuccess {
        background: rgba(52,199,89,0.1) !important;
        border-left: 4px solid #34C759 !important;
        border-radius: var(--apple-radius-sm) !important;
    }

    .stError {
        background: rgba(255,59,48,0.1) !important;
        border-left: 4px solid #FF3B30 !important;
        border-radius: var(--apple-radius-sm) !important;
    }

    .stWarning {
        background: rgba(255,149,0,0.1) !important;
        border-left: 4px solid #FF9500 !important;
        border-radius: var(--apple-radius-sm) !important;
    }

    /* ===== 容器卡片效果 ===== */
    .element-container {
        transition: all 0.2s ease !important;
    }

    /* ===== 隐藏 Streamlit 品牌 ===== */
    #MainMenu, footer {
        visibility: hidden !important;
    }
    
    /* Ensure sidebar toggle button is visible */
    [data-testid="stSidebarCollapsedControl"] {
        visibility: visible !important;
    }

    /* ===== 滚动条样式 ===== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: transparent;
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(0,0,0,0.2);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

# Dependency Injection
st.session_state.gemini_service = GeminiService()
st.session_state.deepseek_service = DeepSeekService()

if "app_mode" not in st.session_state:
    st.session_state.app_mode = "IELTS"

if "app_mode_prev" not in st.session_state:
    st.session_state.app_mode_prev = st.session_state.app_mode

mode_index = 0 if st.session_state.app_mode == "IELTS" else 1
st.sidebar.selectbox("Mode", ["IELTS", "Kaoyan"], index=mode_index, key="app_mode")

if st.session_state.app_mode != st.session_state.app_mode_prev:
    st.session_state.page = "new" if st.session_state.app_mode == "IELTS" else "kaoyan_new"
    st.session_state.app_mode_prev = st.session_state.app_mode
    st.rerun()

# --- Sidebar: History ---
st.sidebar.title("📚 History")

if st.session_state.app_mode == "IELTS":
    conn = database.get_db_connection()
    try:
        history_essays = crud.get_active_essays(conn)
    finally:
        conn.close()

    if st.sidebar.button("➕ New Essay", use_container_width=True):
        st.session_state.page = "new"
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("Recent Essays")

    for essay in history_essays:
        try:
            dt = datetime.fromisoformat(essay["created_at"])
            date_str = dt.strftime("%Y-%m-%d")
        except Exception:
            date_str = str(essay.get("created_at", ""))[:10]

        topic = essay["topic"]
        topic_preview = (topic[:25] + "..") if len(topic) > 25 else topic

        if st.sidebar.button(f"{date_str} | {topic_preview}", key=f"hist_{essay['id']}"):
            st.session_state.page = "view"
            st.session_state.selected_essay_id = essay["id"]
            st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("📈 Trajectory Analysis", use_container_width=True):
        st.session_state.page = "analysis"
        st.rerun()
else:
    conn = database.get_db_connection()
    try:
        history_records = crud.get_active_kaoyan_records(conn)
    finally:
        conn.close()

    if st.sidebar.button("➕ New Kaoyan Essay", use_container_width=True):
        st.session_state.page = "kaoyan_new"
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("Recent Kaoyan")

    for record in history_records:
        try:
            dt = datetime.fromisoformat(record["created_at"])
            date_str = dt.strftime("%Y-%m-%d")
        except Exception:
            date_str = str(record.get("created_at", ""))[:10]

        topic = record["topic"]
        topic_preview = (topic[:25] + "..") if len(topic) > 25 else topic
        badge = "一" if "I" in str(record.get("exam_type", "")) else "二"
        part = "大" if str(record.get("paper_type", "")).endswith("large_essay") else "小"

        if st.sidebar.button(f"{date_str} | 英语{badge}{part} | {topic_preview}", key=f"ky_{record['id']}"):
            st.session_state.page = "kaoyan_view"
            st.session_state.selected_kaoyan_id = record["id"]
            st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("📈 Kaoyan Trajectory Analysis", use_container_width=True):
        st.session_state.page = "kaoyan_analysis"
        st.rerun()

# --- Main Content ---

if 'page' not in st.session_state:
    st.session_state.page = "new" if st.session_state.app_mode == "IELTS" else "kaoyan_new"

# 1. New Essay Page
if st.session_state.page == "new":
    st.title("✍️ IELTS Writing Coach")
    st.markdown("Submit your essay for AI-powered correction based on Simon's methodology.")

    col1, col2 = st.columns([2, 1])
    
    with col1:
        topic = st.text_area("Essay Topic", height=100, placeholder="Enter the essay question here...")
        content = st.text_area("Your Essay", height=400, placeholder="Paste your essay here...")
    
    with col2:
        st.markdown("### Settings")
        task_type = st.selectbox("Task Type", ["Task 2", "Task 1"])
        model_provider_ielts = st.selectbox("Model Provider", ["Gemini", "DeepSeek"], index=0)
        gemini_model_selection = "Flash"
        if model_provider_ielts == "Gemini":
            gemini_model_selection = st.selectbox("Gemini Model", ["Flash", "Pro"], index=0)
            if gemini_model_selection == "Pro":
                st.warning("⚠️ Pro模型需要付费API，免费用户请选择Flash")
            else:
                st.info("💡 Flash模型速度快且免费，适合日常使用")
        else:
            st.info("使用 DeepSeek 模型进行 IELTS 批改，需要正确配置 DEEPSEEK_API_KEY。")
        
        if st.button("🚀 Analyze Essay", use_container_width=True):
            if not topic or not content:
                st.error("Please provide both a topic and essay content.")
            else:
                provider_label = "Gemini" if model_provider_ielts == "Gemini" else "DeepSeek"
                with st.spinner(f"{provider_label} is analyzing your essay..."):
                    try:
                        if model_provider_ielts == "Gemini":
                            result = st.session_state.gemini_service.correct_essay(
                                topic=topic, 
                                content=content, 
                                task_type=task_type,
                                model_selection=gemini_model_selection
                            )
                        else:
                            result = st.session_state.deepseek_service.correct_ielts_essay(
                                topic=topic,
                                content=content,
                                task_type=task_type,
                            )
                        
                        if "error" in result:
                            st.error(f"Analysis Failed: {result['error']}")
                            if "API" in str(result['error']):
                                st.warning("Possible causes: Invalid API Key, Network issues (VPN required?), or Model access restricted.")
                        else:
                            conn = database.get_db_connection()
                            try:
                                new_id = crud.create_essay(
                                    conn=conn,
                                    topic=topic,
                                    user_content=content,
                                    task_type=task_type,
                                    ai_analysis=result
                                )
                            finally:
                                conn.close()
                                
                            st.session_state.page = "view"
                            st.session_state.selected_essay_id = new_id
                            st.rerun()
                    except Exception as e:
                        st.error(f"An unexpected error occurred: {str(e)}")

# 2. View Essay Page
elif st.session_state.page == "view":
    if 'selected_essay_id' in st.session_state:
        conn = database.get_db_connection()
        try:
            essay = crud.get_essay(conn, st.session_state.selected_essay_id)
        finally:
            conn.close()
            
        if essay and essay['status'] == 'active':
            st.title("📝 Correction Result")
            
            # Toolbar
            col_tool1, col_tool2 = st.columns([6, 1])
            with col_tool2:
                if st.button("🗑️ Delete", type="primary"):
                    conn = database.get_db_connection()
                    try:
                        crud.delete_essay(conn, essay['id'])
                    finally:
                        conn.close()
                        
                    st.success("Essay deleted.")
                    st.session_state.page = "new"
                    st.rerun()

            # Parse Analysis
            analysis = essay['ai_analysis']
            if isinstance(analysis, str):
                try:
                    analysis = json.loads(analysis)
                except:
                    analysis = {}

            # Score Cards
            scores = analysis.get("scores", {})
            st.markdown("### 📊 Band Scores")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Overall", scores.get("overall", "N/A"))
            c2.metric("TR", scores.get("TR", "N/A"))
            c3.metric("CC", scores.get("CC", "N/A"))
            c4.metric("LR", scores.get("LR", "N/A"))
            c5.metric("GRA", scores.get("GRA", "N/A"))
            
            # Tabs for details
            tab1, tab2, tab3, tab4 = st.tabs(["💡 Feedback", "📖 Sample Essay", "🔤 Vocabulary", "📄 Original Text"])
            
            with tab1:
                feedback = analysis.get("feedback", {})
                st.subheader("Strengths & Weaknesses")
                col_s, col_w = st.columns(2)
                with col_s:
                    st.markdown("**✅ Strengths**")
                    for s in feedback.get("strengths", []):
                        st.markdown(f"- {s}")
                with col_w:
                    st.markdown("**⚠️ Weaknesses**")
                    for w in feedback.get("weaknesses", []):
                        st.markdown(f"- {w}")
                
                st.markdown("---")
                st.subheader("🧠 Logic Check (Idea-Explain-Example)")
                st.info(feedback.get("logic_check", "No specific logic feedback provided."))
                
                st.markdown("---")
                st.subheader("🛠️ Improvements")
                for imp in analysis.get("improvements", []):
                    st.markdown(f"- {imp}")
                
                st.markdown("---")
                st.markdown("### Detailed Comments")
                st.markdown(feedback.get("detailed_comments", ""))

            with tab2:
                st.markdown("### Band 9 Sample Answer")
                st.markdown(analysis.get("band_9_sample", "No sample provided."))

            with tab3:
                vocab = analysis.get("vocabulary", {})
                st.markdown("### 💎 Lexical Resource")
                st.markdown("**Good Collocations Used:**")
                st.write(", ".join(vocab.get("good_collocations_used", [])))
                
                st.markdown("**Recommended Collocations:**")
                st.write(", ".join(vocab.get("recommended_collocations", [])))
                
                st.markdown("**Advanced Structures:**")
                for struct in vocab.get("advanced_structures", []):
                    st.markdown(f"- {struct}")

            with tab4:
                st.markdown("### Topic")
                st.info(essay['topic'])
                st.markdown("### Your Essay")
                st.text(essay['user_content'])
        else:
            st.error("Essay not found or deleted.")
            if st.button("Back to New"):
                st.session_state.page = "new"
                st.rerun()

# 3. Trajectory Analysis Page
elif st.session_state.page == "kaoyan_new":
    st.title("🎓 Kaoyan Writing Coach")
    st.markdown("Submit your essay for Kaoyan-style correction based on Pan Yun's nine-grid framework.")

    col1, col2 = st.columns([2, 1])

    with col1:
        topic = st.text_area("Essay Topic / Prompt", height=100, placeholder="输入考研作文题目/图表描述/写作要求...")
        content = st.text_area("Your Essay", height=400, placeholder="粘贴你的考研英语作文内容...")

    with col2:
        st.markdown("### Settings")
        exam_choice = st.radio("Exam Type", ["英语一", "英语二"], horizontal=True)
        paper_choice = st.radio("Essay Type", ["大作文", "小作文"], horizontal=True)
        model_provider = st.selectbox("Model Provider", ["DeepSeek", "Gemini"], index=0)

        gemini_model_selection = "Flash"
        if model_provider == "Gemini":
            gemini_model_selection = st.selectbox("Gemini Model", ["Flash", "Pro"], index=0)
            if gemini_model_selection == "Pro":
                st.warning("⚠️ Pro模型需要付费API，免费用户请选择Flash")
            else:
                st.info("💡 Flash模型速度快且免费，适合日常使用")

        if st.button("🚀 Analyze Kaoyan Essay", use_container_width=True):
            if not topic or not content:
                st.error("请填写题目和作文内容。")
            else:
                exam_type = "English I" if exam_choice == "英语一" else "English II"
                paper_type = "large_essay" if paper_choice == "大作文" else "small_essay"

                with st.spinner("AI is analyzing your essay (Kaoyan Mode)..."):
                    try:
                        if model_provider == "DeepSeek":
                            result = st.session_state.deepseek_service.correct_kaoyan_essay(
                                exam_type=exam_type,
                                paper_type=paper_type,
                                topic=topic,
                                content=content,
                            )
                        else:
                            result = st.session_state.gemini_service.correct_kaoyan_essay(
                                exam_type=exam_type,
                                paper_type=paper_type,
                                topic=topic,
                                content=content,
                                model_selection=gemini_model_selection,
                            )

                        if "error" in result:
                            st.error(f"Analysis Failed: {result['error']}")
                            err = str(result.get("error", ""))
                            if "Authentication" in err or "Authentication Fails" in err:
                                st.warning("可能是 API Key 无效或未配置。请检查 .env / Secrets 中的 DEEPSEEK_API_KEY 或 GOOGLE_API_KEY。")
                        else:
                            conn = database.get_db_connection()
                            try:
                                new_id = crud.create_kaoyan_record(
                                    conn=conn,
                                    exam_type=exam_type,
                                    paper_type=paper_type,
                                    topic=topic,
                                    user_content=content,
                                    ai_analysis=result,
                                )
                            finally:
                                conn.close()

                            st.session_state.page = "kaoyan_view"
                            st.session_state.selected_kaoyan_id = new_id
                            st.rerun()
                    except Exception as e:
                        st.error(f"An unexpected error occurred: {str(e)}")

elif st.session_state.page == "kaoyan_view":
    if "selected_kaoyan_id" in st.session_state:
        conn = database.get_db_connection()
        try:
            record = crud.get_kaoyan_record(conn, st.session_state.selected_kaoyan_id)
        finally:
            conn.close()

        if record and record.get("status") == "active":
            st.title("📝 Kaoyan Correction Result")

            col_tool1, col_tool2 = st.columns([6, 1])
            with col_tool2:
                if st.button("🗑️ Delete", type="primary"):
                    conn = database.get_db_connection()
                    try:
                        crud.delete_kaoyan_record(conn, record["id"])
                    finally:
                        conn.close()

                    st.success("Record deleted.")
                    st.session_state.page = "kaoyan_new"
                    st.rerun()

            analysis = record.get("ai_analysis")
            if isinstance(analysis, str):
                try:
                    analysis = json.loads(analysis)
                except Exception:
                    analysis = {}

            score = analysis.get("score", {}) if isinstance(analysis, dict) else {}
            exam_type = str(record.get("exam_type", ""))
            paper_type = str(record.get("paper_type", ""))

            if exam_type == "English I":
                max_score = 10 if paper_type == "small_essay" else 20
            elif exam_type == "English II":
                max_score = 10 if paper_type == "small_essay" else 15
            else:
                max_score = 20

            total_val = score.get("total_score")
            if total_val is None:
                total_val = score.get("total", record.get("total_score", "N/A"))

            band = score.get("band", "N/A")
            evaluation_summary = score.get("evaluation_summary", "")

            st.markdown("### 📊 Scores")
            c1, c2 = st.columns(2)
            c1.metric("Total", f"{total_val}/{max_score}" if total_val != "N/A" else "N/A")
            c2.metric("Band", band)
            if evaluation_summary:
                st.markdown(f"**Overall Comment:** {evaluation_summary}")

            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 综合评价", "🧯 语法与词汇错误", "📖 改进范文", "🔤 词汇与句型推荐", "📄 原文"])

            with tab1:
                st.subheader("Dimension Analysis")
                dimension = analysis.get("dimension_analysis", {})
                structure = analysis.get("structure_analysis", {})
                if dimension:
                    content_rel = dimension.get("content_relevance", "")
                    lang_acc = dimension.get("language_accuracy", "")
                    coh_fmt = dimension.get("coherence_format", "")

                    if content_rel:
                        st.markdown("#### 内容相关性（Content Relevance）")
                        st.markdown(content_rel)
                    if lang_acc:
                        st.markdown("---")
                        st.markdown("#### 语言准确性与多样性（Language Accuracy）")
                        st.markdown(lang_acc)
                    if coh_fmt:
                        st.markdown("---")
                        st.markdown("#### 连贯与格式（Coherence & Format）")
                        st.markdown(coh_fmt)
                elif structure:
                    opening = structure.get("opening_paragraph", "")
                    body = structure.get("body_paragraphs", "")
                    closing = structure.get("closing_paragraph", "")
                    alignment = structure.get("nine_grid_alignment", {})
                    suggestions = structure.get("suggestions", [])

                    st.markdown("#### 段落表现概览")
                    if opening:
                        st.markdown("**开头段（Opening Paragraph）**")
                        st.markdown(opening)
                    if body:
                        st.markdown("**主体段（Body Paragraphs）**")
                        st.markdown(body)
                    if closing:
                        st.markdown("**结尾段（Closing Paragraph）**")
                        st.markdown(closing)

                    if alignment:
                        st.markdown("---")
                        st.markdown("#### 九宫格契合度（Pan Yun Framework）")
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.markdown("**描述与引入**")
                            st.markdown(alignment.get("description_and_introduction", ""))
                        with col_b:
                            st.markdown("**分析与展开**")
                            st.markdown(alignment.get("analysis_and_expansion", ""))
                        with col_c:
                            st.markdown("**总结与建议**")
                            st.markdown(alignment.get("summary_and_suggestion", ""))

                    if suggestions:
                        st.markdown("---")
                        st.markdown("#### 结构与逻辑改进建议")
                        for idx, s in enumerate(suggestions, 1):
                            st.markdown(f"{idx}. {s}")
                else:
                    st.info("No analysis provided.")

            with tab2:
                st.subheader("Grammar and Vocabulary Errors")
                errors = analysis.get("grammar_and_vocab_errors") or analysis.get("grammar_errors", [])
                if errors:
                    try:
                        st.dataframe(pd.DataFrame(errors), use_container_width=True)
                    except Exception:
                        st.json(errors)
                else:
                    st.info("No grammar or vocabulary errors provided.")

            with tab3:
                st.subheader("Improved High-band Version")
                improved = analysis.get("improved_version") or analysis.get("sample_essay", "")
                if improved:
                    st.markdown(improved)
                else:
                    st.info("No improved version provided.")

            with tab4:
                st.subheader("Vocabulary and Sentence Suggestions")
                vocab = analysis.get("vocabulary", {})
                if vocab:
                    good = vocab.get("good_collocations_used", [])
                    rec = vocab.get("recommended_collocations", [])
                    adv = vocab.get("advanced_structures", [])

                    if good:
                        st.markdown("**Good Collocations Used**")
                        st.write(", ".join(good))
                    if rec:
                        st.markdown("**Recommended Higher-level Expressions**")
                        st.write(", ".join(rec))
                    if adv:
                        st.markdown("**Advanced Structures (Suggested or Used)**")
                        for s in adv:
                            st.markdown(f"- {s}")
                else:
                    st.info("No vocabulary suggestions provided.")

            with tab5:
                st.markdown("### Topic")
                st.info(record.get("topic", ""))
                st.markdown("### Your Essay")
                st.text(record.get("user_content", ""))
        else:
            st.error("Record not found or deleted.")
            if st.button("Back to New"):
                st.session_state.page = "kaoyan_new"
                st.rerun()

elif st.session_state.page == "analysis":
    st.title("📈 Growth Trajectory Analysis")
    
    conn = database.get_db_connection()
    try:
        history_data = crud.get_trajectory_data(conn)
    finally:
        conn.close()
    
    if len(history_data) < 2:
        st.warning("Not enough data for analysis. Please submit at least 2 essays.")
    else:
        st.markdown("### Settings")
        provider = st.selectbox("Model Provider", ["DeepSeek", "Gemini"], index=0, key="ielts_analysis_provider")
        gemini_hist_model = "Pro"
        if provider == "Gemini":
            gemini_hist_model = st.selectbox(
                "Gemini Model",
                ["Flash", "Pro"],
                index=1,
                key="ielts_analysis_gemini_model",
            )
        if st.button("🔄 Generate New Analysis Report"):
            if provider == "Gemini":
                with st.spinner("Gemini is analyzing your growth trends..."):
                    report = st.session_state.gemini_service.analyze_trajectory(
                        history_data,
                        model_selection=gemini_hist_model,
                    )
            else:
                with st.spinner("DeepSeek is analyzing your growth trends..."):
                    report = st.session_state.deepseek_service.analyze_trajectory(history_data)
            st.session_state.trajectory_report = report
        
        st.subheader("Score Trends")
        task1_data = [e for e in history_data if str(e.get("task_type", "")).strip() == "Task 1"]
        task2_data = [e for e in history_data if str(e.get("task_type", "")).strip() == "Task 2"]

        apple_colors = ['#007AFF', '#34C759', '#FF9500', '#AF52DE', '#FF3B30']

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### IELTS Task 1")
            if task1_data:
                df1 = pd.DataFrame(
                    [
                        {
                            "Submission": idx + 1,
                            "Topic": entry.get("topic", ""),
                            "Overall": entry.get("scores", {}).get("overall", 0),
                            "TR": entry.get("scores", {}).get("TR", 0),
                            "CC": entry.get("scores", {}).get("CC", 0),
                            "LR": entry.get("scores", {}).get("LR", 0),
                            "GRA": entry.get("scores", {}).get("GRA", 0),
                        }
                        for idx, entry in enumerate(task1_data)
                    ]
                )
                fig1 = px.line(
                    df1,
                    x="Submission",
                    y=["Overall", "TR", "CC", "LR", "GRA"],
                    markers=True,
                    title="Task 1 Score Progression",
                    color_discrete_sequence=apple_colors,
                )
                fig1.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(
                        family='-apple-system, BlinkMacSystemFont, Inter, sans-serif',
                        size=14,
                        color='#1D1D1F',
                    ),
                    title=dict(
                        font=dict(size=16, color='#1D1D1F'),
                        x=0,
                    ),
                    legend=dict(
                        bgcolor='rgba(255,255,255,0.8)',
                        bordercolor='rgba(0,0,0,0.1)',
                        borderwidth=1,
                        font=dict(size=10),
                    ),
                    xaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(0,0,0,0.06)',
                        linecolor='rgba(0,0,0,0.1)',
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(0,0,0,0.06)',
                        linecolor='rgba(0,0,0,0.1)',
                        range=[0, 9.5],
                    ),
                    hovermode='x unified',
                )
                fig1.update_traces(line=dict(width=3), marker=dict(size=8))
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No Task 1 essays found in history.")

        with col2:
            st.markdown("#### IELTS Task 2")
            if task2_data:
                df2 = pd.DataFrame(
                    [
                        {
                            "Submission": idx + 1,
                            "Topic": entry.get("topic", ""),
                            "Overall": entry.get("scores", {}).get("overall", 0),
                            "TR": entry.get("scores", {}).get("TR", 0),
                            "CC": entry.get("scores", {}).get("CC", 0),
                            "LR": entry.get("scores", {}).get("LR", 0),
                            "GRA": entry.get("scores", {}).get("GRA", 0),
                        }
                        for idx, entry in enumerate(task2_data)
                    ]
                )
                fig2 = px.line(
                    df2,
                    x="Submission",
                    y=["Overall", "TR", "CC", "LR", "GRA"],
                    markers=True,
                    title="Task 2 Score Progression",
                    color_discrete_sequence=apple_colors,
                )
                fig2.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(
                        family='-apple-system, BlinkMacSystemFont, Inter, sans-serif',
                        size=14,
                        color='#1D1D1F',
                    ),
                    title=dict(
                        font=dict(size=16, color='#1D1D1F'),
                        x=0,
                    ),
                    legend=dict(
                        bgcolor='rgba(255,255,255,0.8)',
                        bordercolor='rgba(0,0,0,0.1)',
                        borderwidth=1,
                        font=dict(size=10),
                    ),
                    xaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(0,0,0,0.06)',
                        linecolor='rgba(0,0,0,0.1)',
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(0,0,0,0.06)',
                        linecolor='rgba(0,0,0,0.1)',
                        range=[0, 9.5],
                    ),
                    hovermode='x unified',
                )
                fig2.update_traces(line=dict(width=3), marker=dict(size=8))
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No Task 2 essays found in history.")

        # Display Report
        if 'trajectory_report' in st.session_state:
            report = st.session_state.trajectory_report
            if "error" in report:
                st.error(report["error"])
            else:
                st.markdown("---")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("### 📉 Persistent Weaknesses")
                    for pw in report.get("persistent_weaknesses", []):
                        st.error(f"- {pw}")
                
                with c2:
                    st.markdown("### 🎯 Learning Plan")
                    plan = report.get("learning_plan", {})
                    st.markdown("**Focus Areas:**")
                    for area in plan.get("focus_areas", []):
                        st.markdown(f"- {area}")
                    st.markdown("**Suggested Exercises:**")
                    for ex in plan.get("suggested_exercises", []):
                        st.markdown(f"- {ex}")
                
                st.markdown("### 📊 Progress Analysis")
                st.info(report.get("progress_analysis", ""))
                
                st.markdown("### 📝 Summary")
                st.markdown(report.get("trend_summary", ""))

elif st.session_state.page == "kaoyan_analysis":
    st.title("📈 Kaoyan Growth Trajectory Analysis")

    conn = database.get_db_connection()
    try:
        history_data = crud.get_kaoyan_trajectory_data(conn)
    finally:
        conn.close()

    if len(history_data) < 2:
        st.warning("Not enough data for analysis. Please submit at least 2 Kaoyan essays.")
    else:
        st.markdown("### Settings")
        provider = st.selectbox("Model Provider", ["DeepSeek", "Gemini"], index=0, key="kaoyan_analysis_provider")
        gemini_hist_model_ky = "Pro"
        if provider == "Gemini":
            gemini_hist_model_ky = st.selectbox(
                "Gemini Model",
                ["Flash", "Pro"],
                index=1,
                key="kaoyan_analysis_gemini_model",
            )
        if st.button("🔄 Generate Kaoyan Analysis Report"):
            if provider == "Gemini":
                with st.spinner("Gemini is analyzing your Kaoyan score trends..."):
                    report = st.session_state.gemini_service.analyze_kaoyan_trajectory(
                        history_data,
                        model_selection=gemini_hist_model_ky,
                    )
            else:
                with st.spinner("DeepSeek is analyzing your Kaoyan score trends..."):
                    report = st.session_state.deepseek_service.analyze_kaoyan_trajectory(history_data)
            st.session_state.kaoyan_trajectory_report = report

        st.subheader("Score Trends")

        def _normalize_exam_type(value):
            v = str(value or "").lower()
            if "english ii" in v or "ii" in v or "2" in v or "二" in v:
                return "English II"
            if "english i" in v or "i" in v or "1" in v or "一" in v:
                return "English I"
            return "English I"

        def _normalize_paper_type(value):
            v = str(value or "").lower()
            if "small" in v or "小" in v:
                return "small_essay"
            if "large" in v or "大" in v:
                return "large_essay"
            return "large_essay"

        buckets = {
            ("English I", "large_essay"): [],
            ("English I", "small_essay"): [],
            ("English II", "large_essay"): [],
            ("English II", "small_essay"): [],
        }

        for item in history_data:
            exam = _normalize_exam_type(item.get("exam_type"))
            paper = _normalize_paper_type(item.get("paper_type"))
            buckets[(exam, paper)].append(item)

        apple_colors = ["#007AFF"]
        label_map = {
            ("English I", "large_essay"): "英语一大作文",
            ("English I", "small_essay"): "英语一小作文",
            ("English II", "large_essay"): "英语二大作文",
            ("English II", "small_essay"): "英语二小作文",
        }

        for key in [("English I", "large_essay"), ("English I", "small_essay"), ("English II", "large_essay"), ("English II", "small_essay")]:
            subset = buckets[key]
            label = label_map[key]
            st.markdown(f"#### {label}")
            if not subset:
                st.info(f"No records for {label} yet.")
                continue

            df_sub = pd.DataFrame(
                [
                    {
                        "Submission": idx + 1,
                        "Topic": item.get("topic", ""),
                        "Total Score": item.get("total_score", 0),
                    }
                    for idx, item in enumerate(subset)
                ]
            )

            fig_sub = px.line(
                df_sub,
                x="Submission",
                y=["Total Score"],
                markers=True,
                title=f"{label} Score Progression",
                color_discrete_sequence=apple_colors,
            )

            fig_sub.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(
                    family="-apple-system, BlinkMacSystemFont, Inter, sans-serif",
                    size=14,
                    color="#1D1D1F",
                ),
                title=dict(
                    font=dict(size=18, color="#1D1D1F"),
                    x=0,
                ),
                legend=dict(
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="rgba(0,0,0,0.1)",
                    borderwidth=1,
                    font=dict(size=10),
                ),
                xaxis=dict(
                    showgrid=True,
                    gridcolor="rgba(0,0,0,0.06)",
                    linecolor="rgba(0,0,0,0.1)",
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="rgba(0,0,0,0.06)",
                    linecolor="rgba(0,0,0,0.1)",
                ),
                hovermode="x unified",
            )

            fig_sub.update_traces(line=dict(width=3), marker=dict(size=8))

            st.plotly_chart(fig_sub, use_container_width=True)

        if "kaoyan_trajectory_report" in st.session_state:
            report = st.session_state.kaoyan_trajectory_report
            if "error" in report:
                st.error(report["error"])
            else:
                st.markdown("---")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("### 📉 Persistent Weaknesses")
                    for pw in report.get("persistent_weaknesses", []):
                        st.error(f"- {pw}")

                with c2:
                    st.markdown("### 🎯 Learning Plan")
                    plan = report.get("learning_plan", {})
                    st.markdown("**Focus Areas:**")
                    for area in plan.get("focus_areas", []):
                        st.markdown(f"- {area}")
                    st.markdown("**Suggested Exercises:**")
                    for ex in plan.get("suggested_exercises", []):
                        st.markdown(f"- {ex}")

                st.markdown("### 📊 Progress Analysis")
                st.info(report.get("progress_analysis", ""))

                st.markdown("### 📝 Summary")
                st.markdown(report.get("trend_summary", ""))
