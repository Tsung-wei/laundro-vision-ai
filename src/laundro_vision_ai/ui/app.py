import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 頁面基本配置 ---
st.set_page_config(page_title="LaundroVision AI", page_icon="🧺", layout="wide")

# --- 初始化 Session State (狀態機核心) ---
if 'stage' not in st.session_state:
    st.session_state.stage = 'INIT'
if 'data' not in st.session_state:
    st.session_state.data = {
        'location': {},
        'competitor': {'q7': 3, 'q8': 3},
        'target': {'q1': 3, 'q2': 3, 'q3': 3, 'q4': 3, 'q5': 3}
    }

def set_stage(stage_name):
    st.session_state.stage = stage_name

# --- 側邊欄：導航與進度 ---
with st.sidebar:
    st.title("🧺 LaundroVision")
    st.caption("The Silent Strategist | MVP v1.1")
    st.divider()
    
    stages = ["站點定位", "對手評估", "目標評估", "最終報告"]
    stage_map = {"INIT": 0, "COMPETITOR_EVAL": 1, "TARGET_EVAL": 2, "REPORT": 3}
    current_idx = stage_map.get(st.session_state.stage, 0)
    
    st.progress((current_idx + 1) / len(stages))
    for i, s in enumerate(stages):
        if i < current_idx: st.write(f"✅ {s}")
        elif i == current_idx: st.write(f"🔵 **{s}**")
        else: st.write(f"⚪ {s}")

# --- Stage 1: 站點定位 (INIT) ---
if st.session_state.stage == 'INIT':
    st.header("📍 1. 站點定位")
    col1, col2 = st.columns(2)
    with col1:
        city = st.selectbox("縣市", ["台北市", "新北市", "桃園市"])
        district = st.selectbox("鄉鎮市區", ["中正區", "板橋區", "大園區"])
    with col2:
        address = st.text_input("地址/街道名稱", placeholder="例如：文化路一段100號")
    
    if st.button("下一步：獲取地理情報", use_container_width=True):
        # 此處未來將串接 POST /api/v1/locations/enrich
        st.session_state.data['location'] = {"city": city, "district": district, "address": address}
        set_stage('COMPETITOR_EVAL')
        st.rerun()

# --- Stage 2: 對手強度評估 (COMPETITOR_EVAL) ---
elif st.session_state.stage == 'COMPETITOR_EVAL':
    st.header("⚔️ 2. 競爭對手強度評估")
    st.info("💡 偵測到 1,000 公尺內存在競爭對手，啟動阻斷判斷機制。")
    
    q7 = st.select_slider("Q7. 對手機器運轉狀況", options=[1, 2, 3, 4, 5], value=3, help="1:無運作 ~ 5:70%以上")
    q8 = st.select_slider("Q8. 對手整潔度", options=[1, 2, 3, 4, 5], value=3, help="1:髒亂 ~ 5:極度整潔")
    
    if st.button("驗證阻斷條件", use_container_width=True):
        avg_comp = (q7 + q8) / 2
        st.session_state.data['competitor'] = {"q7": q7, "q8": q8}
        # 阻斷邏輯：平均分 > 3.0
        if avg_comp > 3.0:
            st.error(f"🔴 阻斷警告：對手平均分 {avg_comp} 過高，建議放棄此站點。")
            if st.button("重新選址"):
                st.session_state.clear()
                st.rerun()
        else:
            st.success(f"✅ 對手威脅在可控範圍內 ({avg_comp})，進入詳細評估。")
            set_stage('TARGET_EVAL')
            st.rerun()

# --- Stage 3: 目的站點評估 (TARGET_EVAL) ---
elif st.session_state.stage == 'TARGET_EVAL':
    st.header("🎯 3. 目的站點詳細評估")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**客群分析**")
        q1 = st.radio("Q1. 便利商店/麥當勞密度", [1, 2, 3, 4, 5], index=2, horizontal=True)
        q2 = st.radio("Q2. 商圈住宅型態", [1, 2, 3, 4, 5], index=2, horizontal=True)
    with col2:
        st.write("**店面硬體**")
        q3 = st.radio("Q3. 視覺攔截力/面寬", [1, 2, 3, 4, 5], index=2, horizontal=True)
        q4 = st.radio("Q4. 招牌可見度", [1, 2, 3, 4, 5], index=2, horizontal=True)
        q5 = st.radio("Q5. 機車停靠方便性", [1, 2, 3, 4, 5], index=2, horizontal=True)
    
    if st.button("產生決策報告", use_container_width=True):
        st.session_state.data['target'] = {"q1":q1, "q2":q2, "q3":q3, "q4":q4, "q5":q5}
        set_stage('REPORT')
        st.rerun()

# --- Stage 4: 最終報告與決策 (REPORT) ---
elif st.session_state.stage == 'REPORT':
    st.header("📊 4. 決策分析報告")
    d = st.session_state.data
    # 動態權重公式實作 (有競爭對手模式)
    score = (d['target']['q1']*0.30 + d['target']['q2']*0.15 + 
             d['target']['q3']*0.10 + d['target']['q4']*0.10 + d['target']['q5']*0.10 + 
             d['competitor']['q7']*0.15 + d['competitor']['q8']*0.10)

    col_score, col_radar = st.columns([1, 2])
    with col_score:
        st.metric("站點綜合分數", f"{score:.2f}")
        # 燈號決策
        if score > 4.0: st.success("🟢 綠燈：優質店址")
        elif score >= 3.0: st.warning("🟡 黃燈：需審慎考慮")
        else: st.error("🔴 紅燈：高風險")
            
    with col_radar:
        # 雷達圖繪製
        categories = ['客群', '硬體', '競爭力']
        values = [(d['target']['q1'] + d['target']['q2']) / 2, 
                  (d['target']['q3'] + d['target']['q4'] + d['target']['q5']) / 3, 
                  (d['competitor']['q7'] + d['competitor']['q8']) / 2]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    if score > 4.0:
        st.divider()
        with st.expander("💰 財務評估面板"):
            c1, c2, c3 = st.columns(3)
            capex = c1.number_input("CAPEX (萬元)", value=250)
            rent = c2.number_input("月租金 (萬元)", value=5)
            rev = c3.number_input("預估月營收 (萬元)", value=15)
            # 簡易回收期計算
            profit = rev - 4 - rent # 假設 OPEX 為 4
            if profit > 0: st.info(f"預估回收期：{capex / profit:.1f} 個月")

    if st.button("重新評估新站點"):
        st.session_state.clear()
        st.rerun()


# --- 深度 UI 樣式優化 ---
st.markdown("""
    <style>
    /* 全域背景與字體 */
    .stApp {
        background-color: #F0F2F6;
    }
    
    /* 側邊欄美化 */
    [data-testid="stSidebar"] {
        background-image: linear-gradient(#2E3440, #4C566A);
        color: white;
    }
    [data-testid="stSidebar"] .stMarkdown p {
        color: #D8DEE9;
    }

    /* 卡片式容器設計 */
    div.stButton > button {
        border-radius: 8px;
        padding: 0.6rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* 主要按鈕顏色 (深藍色) */
    div.stButton > button:first-child {
        background-color: #1E3A8A;
        border: none;
        color: white;
    }
    
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        background-color: #2563EB;
    }

    /* 單選按鈕 (Radio) 水平排列美化 */
    div[data-row='true'] {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #E5E7EB;
        margin-bottom: 10px;
    }

    /* 評分數字強化顯示 */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1F2937;
    }

    /* 訊息方塊美化 */
    .stAlert {
        border-radius: 12px;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* 隱藏預設的 Streamlit 選單與頁尾 (增加專業感) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)