import json
import os

import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000/api/v1"


@st.cache_data
def load_taiwan_districts():
    """Load district data from local JSON file."""
    file_path = os.path.join(os.path.dirname(__file__), "..", "data", "taiwan_districts.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback minimal data for testing
        return {"台北市": ["信義區", "大安區", "中山區"], "新北市": ["板橋區", "三重區", "新莊區", "泰山區"]}


def init_session():
    if "stage" not in st.session_state:
        st.session_state.stage = "INIT"
    if "has_competitor" not in st.session_state:
        st.session_state.has_competitor = False
    if "competitor_knockout" not in st.session_state:
        st.session_state.competitor_knockout = False
    if "recommended_q1_score" not in st.session_state:
        st.session_state.recommended_q1_score = 5
    if "cvs_mcd_in_200m" not in st.session_state:
        st.session_state.cvs_mcd_in_200m = []


def render_init():
    st.title("LaundroVision AI")
    st.header("Step 1: 站點定位")
    districts = load_taiwan_districts()
    city = st.selectbox("縣市", list(districts.keys()))
    district = st.selectbox("鄉鎮市區", districts[city])
    address = st.text_input("地址/街道").strip()
    st.write(f"您選擇的地址是：{city}{district}{address}")
    if st.button("搜尋周邊"):
        full_address = f"{city}{district}{address}"
        with st.spinner("Geocoding and scanning for competitors..."):
            try:
                res = requests.post(f"{API_BASE_URL}/locations/enrich", json={"address": full_address})
                res.raise_for_status()
                data = res.json()

                st.session_state.has_competitor = data["has_competitor_in_1000m"]
                st.session_state.recommended_q1_score = data["recommended_q1_score"]
                st.session_state.cvs_mcd_in_200m = data["cvs_mcd_in_200m"]

                if st.session_state.has_competitor:
                    st.session_state.stage = "COMPETITOR_EVAL"
                else:
                    st.session_state.stage = "TARGET_EVAL"
                st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"API Request Failed: {e}")


def render_competitor_eval():
    st.header("Step 2: 競爭對手評估模式")
    q2 = st.radio("Q2. 住宅型態", [1, 2, 3, 4, 5], horizontal=True)
    q3 = st.radio("Q3. 視覺攔截力", [1, 2, 3, 4, 5], horizontal=True)
    q4 = st.radio("Q4. 招牌設立", [1, 2, 3, 4, 5], horizontal=True)
    q5 = st.radio("Q5. 機車停靠", [1, 2, 3, 4, 5], horizontal=True)
    q7 = st.radio("Q7. 機器運轉", [1, 2, 3, 4, 5], horizontal=True)
    q8 = st.radio("Q8. 整潔度", [1, 2, 3, 4, 5], horizontal=True)
    if st.button("驗證對手強度"):
        payload = {
            "q2_residential": q2,
            "q3_visibility": q3,
            "q4_signage": q4,
            "q5_motorcycle": q5,
            "q7_machine_status": q7,
            "q8_cleanliness": q8,
        }
        res = requests.post(f"{API_BASE_URL}/assessments/evaluate-competitor", json=payload).json()
        if res["knock_out"]:
            st.error(res["message"])
            st.session_state.competitor_knockout = True
        else:
            st.session_state.stage = "TARGET_EVAL"
            st.rerun()


def render_target_eval():
    st.header("Step 3: 候選店址評估")
    cvs_list = st.session_state.get("cvs_mcd_in_200m", [])
    st.info(f"API 探測周邊 POI: {cvs_list}")

    default_q1_index = st.session_state.get("recommended_q1_score", 5) - 1

    q1 = st.radio("Q1. CVS / 麥當勞", [1, 2, 3, 4, 5], index=default_q1_index, horizontal=True)

    q2 = st.radio("Q2. 住宅型態", [1, 2, 3, 4, 5], horizontal=True)
    q3 = st.radio("Q3. 視覺攔截力", [1, 2, 3, 4, 5], horizontal=True)
    q4 = st.radio("Q4. 招牌設立", [1, 2, 3, 4, 5], horizontal=True)
    q5 = st.radio("Q5. 機車停靠", [1, 2, 3, 4, 5], horizontal=True)
    q7 = 5 if st.session_state.has_competitor else None
    q8 = 5 if st.session_state.has_competitor else None
    notes = st.text_area("綜合文字評述 (顧問筆記)")
    st.write("評述內容：", notes)
    if st.button("產生分析報告"):
        payload = {
            "has_competitor": st.session_state.has_competitor,
            "q1_cvs": q1,
            "q2_residential": q2,
            "q3_visibility": q3,
            "q4_signage": q4,
            "q5_motorcycle": q5,
            "q7_machine_status": q7,
            "q8_cleanliness": q8,
        }
        res = requests.post(f"{API_BASE_URL}/assessments/calculate-score", json=payload).json()
        st.session_state.total_score = res["total_score"]
        st.session_state.stage = "REPORT"
        st.rerun()


def render_report():
    st.header("Step 4: AI 決策報告")
    score = st.session_state.get("total_score", 0)
    if score >= 4.0:
        st.success(f"🟢 綠燈！總分：{score}")
        with st.expander("展開財務試算面板", expanded=True):
            st.write("預估回本月數：24 個月")
    elif score >= 3.0:
        st.warning(f"🟡 黃燈！總分：{score}")
    else:
        st.error(f"🔴 紅燈！總分：{score}")
    if st.button("重新評估"):
        st.session_state.stage = "INIT"
        st.rerun()


def main():
    init_session()
    if st.session_state.stage == "INIT":
        render_init()
    elif st.session_state.stage == "COMPETITOR_EVAL":
        render_competitor_eval()
    elif st.session_state.stage == "TARGET_EVAL":
        render_target_eval()
    elif st.session_state.stage == "REPORT":
        render_report()


if __name__ == "__main__":
    main()
