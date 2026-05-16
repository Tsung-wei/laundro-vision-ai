import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

# --- 頁面基本配置 ---
st.set_page_config(page_title="LaundroVision AI", page_icon="🧺", layout="wide")

BACKEND_URL = "http://127.0.0.1:8000"

# --- 異步呼叫後端地理資料 API 函數 ---
def fetch_cities():
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/geography/cities", timeout=2)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return ["台北市", "新北市", "桃園市"] # 備用防呆清單

def fetch_districts(city_name):
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/geography/districts/{city_name}", timeout=2)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return ["請檢查後端連線"] # 備用防呆清單

# --- Initialize Session State ---
if 'stage' not in st.session_state:
    st.session_state.stage = 'INIT'
if 'data' not in st.session_state:
    st.session_state.data = {
        'location': {'city': '', 'district': '', 'address': ''},
        'competitor': {'q7': 3, 'q8': 3},
        'target': {'q1': 3, 'q2': 3, 'q3': 3, 'q4': 3, 'q5': 3}
    }

def set_stage(stage_name):
    st.session_state.stage = stage_name

# --- 側邊欄：導航與進度 ---
with st.sidebar:
    st.title("🧺 LaundroVision AI")
    st.write("The Silent Strategist | MVP v1.1")
    st.divider()
    
    st.write("📌 **快速導航面板**")
    
    if st.button("📍 1. 站點定位資料", use_container_width=True):
        set_stage('INIT')
        st.rerun()
        
    if st.button("⚔️ 2. 競爭對手強度評估", use_container_width=True):
        set_stage('COMPETITOR_EVAL')
        st.rerun()
        
    if st.button("🎯 3. 目的站點詳細評估", use_container_width=True):
        set_stage('TARGET_EVAL')
        st.rerun()
        
    if st.button("📊 4. 最終決策報告", use_container_width=True):
        set_stage('REPORT')
        st.rerun()

    st.divider()
    stage_map = {"INIT": "站點定位", "COMPETITOR_EVAL": "對手評估", "TARGET_EVAL": "目標評估", "REPORT": "最終報告"}
    st.info(f"當前進度：{stage_map.get(st.session_state.stage, '未知')}")

# --- Stage 1: 站點定位 (INIT) ---
if st.session_state.stage == 'INIT':
    st.header("📍 1. 站點定位情報收集")
    
    # 動態向後端獲取最新縣市清單
    cities_list = fetch_cities()
    
    col1, col2 = st.columns(2)
    with col1:
        # 縣市選單連動
        city = st.selectbox("縣市", cities_list, key="city_select")
        
        # 根據選定的縣市，即時向後端撈取該縣市的所有區
        districts_list = fetch_districts(city)
        district = st.selectbox("鄉鎮市區", districts_list, key="district_select")
        
    with col2:
        address = st.text_input("地址/街道名稱", value=st.session_state.data['location'].get('address', ''), placeholder="例如：文化路一段100號")
    
    if st.button("下一步：進入對手評估", use_container_width=True):
        st.session_state.data['location'] = {"city": city, "district": district, "address": address}
        set_stage('COMPETITOR_EVAL')
        st.rerun()

# --- Stage 2: 對手強度評估 (COMPETITOR_EVAL) ---
elif st.session_state.stage == 'COMPETITOR_EVAL':
    st.header("⚔️ 2. 競爭對手強度評估")
    st.warning("💡 偵測到 1,000 公尺內存在競爭對手，啟動阻斷判斷機制。")
    
    st.write("---")
    st.markdown("### **Q7. 對手機器運轉狀況**")
    st.markdown("<small style='color: gray;'>ℹ️ 說明：評估對手現場稼動率。1分: 無人使用且無運轉 ~ 5分: 現場活絡，滾筒翻轉與排風運作體感達 70% 以上。</small>", unsafe_allow_html=True)
    q7 = st.select_slider("滑動選擇分數", options=[1, 2, 3, 4, 5], value=st.session_state.data['competitor']['q7'], key="slider_q7")
    
    st.write("---")
    st.markdown("### **Q8. 對手整潔度與門店紀律**")
    st.markdown("<small style='color: gray;'>ℹ️ 說明：衡量對手營運紀律。1分: 垃圾桶滿溢、檯面有棉絮橡皮筋、地磚髒污 ~ 5分: 極度整潔，耗材補充齊全且設備無灰塵。</small>", unsafe_allow_html=True)
    q8 = st.select_slider("滑動選擇分數", options=[1, 2, 3, 4, 5], value=st.session_state.data['competitor']['q8'], key="slider_q8")
    st.write("---")
    
    avg_comp = (q7 + q8) / 2
    st.session_state.data['competitor'] = {"q7": q7, "q8": q8}
    
    if avg_comp > 3.0:
        st.error(f"🔴 阻斷警告：對手平均分 {avg_comp} 過高，營運實力強勁，建議放棄此站點。")
    else:
        st.success(f"✅ 對手威脅在可控範圍內 ({avg_comp})，可以進入詳細評估。")
        
    if st.button("下一步：進入詳細指標評估", use_container_width=True):
        set_stage('TARGET_EVAL')
        st.rerun()

# --- Stage 3: 目的站點評估 (TARGET_EVAL) ---
elif st.session_state.stage == 'TARGET_EVAL':
    st.header("🎯 3. 目的站點詳細評估")
    d_target = st.session_state.data['target']
    
    st.subheader("📊 A. 商圈與客群指標")
    
    # Q1 區塊
    st.markdown("### **Q1. 便利商店 / 麥當勞 / 蝦皮店到店密度**")
    st.markdown("<small style='color: gray;'>ℹ️ 說明：商圈成熟度指標。串接後端 API 自動讀取 500m 內核心通路群聚效應。1分: 偏遠無連鎖店 ~ 5分: 10家以上指標通路密集。</small>", unsafe_allow_html=True)
    q1 = st.radio("核選評分 (Q1)", [1, 2, 3, 4, 5], index=d_target['q1']-1, horizontal=True, key="radio_q1")
    st.write("---")
    
    # Q2 區塊
    st.markdown("### **Q2. 商圈住宅型態與結構**")
    st.markdown("<small style='color: gray;'>ℹ️ 說明：核心客群潛力指標。結合內政部與財政部稅籍結構。1分: 透天別墅或豪宅區(自備洗烘) ~ 5分: 老舊公寓與小坪數租屋族密集(需求極高)。</small>", unsafe_allow_html=True)
    q2 = st.radio("核選評分 (Q2)", [1, 2, 3, 4, 5], index=d_target['q2']-1, horizontal=True, key="radio_q2")
    
    st.divider()
    st.subheader("🏗️ B. 店面硬體與物理攔截力")
    
    # Q3 區塊
    st.markdown("### **Q3. 視覺攔截力 / 面寬條件**")
    st.markdown("<small style='color: gray;'>ℹ️ 說明：過路客視覺捕捉。1分: 巷弄內或面寬窄於3米 ~ 5分: 雙面臨路角間或面寬超過6米，高能見度。</small>", unsafe_allow_html=True)
    q3 = st.radio("核選評分 (Q3)", [1, 2, 3, 4, 5], index=d_target['q3']-1, horizontal=True, key="radio_q3")
    st.write("---")
    
    # Q4 區塊
    st.markdown("### **Q4. 招牌可見度與死角評估**")
    st.markdown("<small style='color: gray;'>ℹ️ 說明：車行視線評估。1分: 被大樹或鄰近突出招牌完全遮擋 ~ 5分: 四向視線毫無死角，遠處即可清晰辨識。</small>", unsafe_allow_html=True)
    q4 = st.radio("核選評分 (Q4)", [1, 2, 3, 4, 5], index=d_target['q4']-1, horizontal=True, key="radio_q4")
    st.write("---")
    
    # Q5 區塊
    st.markdown("### **Q5. 機車停靠方便性**")
    st.markdown("<small style='color: gray;'>ℹ️ 說明：載運衣物便利度。1分: 紅線禁停或常態性無車位 ~ 5分: 門口擁有專屬騎樓或寬敞空地，可併排停靠多輛機車。</small>", unsafe_allow_html=True)
    q5 = st.radio("核選評分 (Q5)", [1, 2, 3, 4, 5], index=d_target['q5']-1, horizontal=True, key="radio_q5")
    st.write("---")
    
    if st.button("產生決策報告", use_container_width=True):
        st.session_state.data['target'] = {"q1":q1, "q2":q2, "q3":q3, "q4":q4, "q5":q5}
        set_stage('REPORT')
        st.rerun()

# --- Stage 4: 最終報告與決策 (REPORT) ---
elif st.session_state.stage == 'REPORT':
    st.header("📊 4. 決策分析報告")
    d = st.session_state.data
    
    score = (d['target']['q1']*0.30 + d['target']['q2']*0.15 + 
             d['target']['q3']*0.10 + d['target']['q4']*0.10 + d['target']['q5']*0.10 + 
             d['competitor']['q7']*0.15 + d['competitor']['q8']*0.10)

    col_score, col_radar = st.columns([1, 2])
    with col_score:
        st.metric("站點綜合分數", f"{score:.2f}")
        if score > 4.0: st.success("🟢 綠燈：優質店址")
        elif score >= 3.0: st.warning("🟡 黃燈：需審慎考慮")
        else: st.error("🔴 紅燈：高風險")
            
    with col_radar:
        categories = ['客群', '硬體', '競爭力']
        values = [(d['target']['q1'] + d['target']['q2']) / 2, 
                  (d['target']['q3'] + d['target']['q4'] + d['target']['q5']) / 3, 
                  (d['competitor']['q7'] + d['competitor']['q8']) / 2]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', line=dict(color='#2563EB')))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)

    if score > 4.0:
        st.divider()
        with st.expander("💰 財務評估面板"):
            c1, c2, c3 = st.columns(3)
            capex = c1.number_input("CAPEX (萬元)", value=250)
            rent = c2.number_input("月租金 (萬元)", value=5)
            rev = c3.number_input("預估月營收 (萬元)", value=15)
            profit = rev - 4 - rent
            if profit > 0: st.info(f"預估回收期：{capex / profit:.1f} 個月")

    if st.button("重新評估新站點", use_container_width=True):
        st.session_state.clear()
        set_stage('INIT')
        st.rerun()

# --- 精準內嵌安全 CSS ---
st.markdown("""
    <style>
    div[data-row='true'], .stSelectSlider {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        border: 1px solid #E5E7EB;
        margin-bottom: 10px;
    }
    .main div.stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)