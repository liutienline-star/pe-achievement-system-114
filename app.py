import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. 初始化與連接 ---
st.set_page_config(page_title="體育成績管理系統 - 萬用版", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. 萬用判定引擎 (核心邏輯) ---
def universal_judge(category, item, gender, age, value, norms_df):
    """
    從 Norms_Settings 搜尋符合的門檻，並回傳判定結果。
    """
    if norms_df is None or norms_df.empty:
        return "常模未載入"
        
    try:
        # 基礎篩選：類別、項目、性別
        mask = (norms_df['測驗類別'] == category) & \
               (norms_df['項目名稱'] == item) & \
               (norms_df['性別'] == gender)
        
        filtered_norms = norms_df[mask].copy()
        
        if filtered_norms.empty:
            return "查無常模"

        # 年齡篩選 (若常模填 0 代表不分年齡)
        age_val = int(age) if age else 0
        age_mask = (filtered_norms['年齡'] == age_val) | (filtered_norms['年齡'] == 0)
        filtered_norms = filtered_norms[age_mask]

        if filtered_norms.empty:
            return "查無此年齡標準"

        # 數值轉換 (確保為浮點數以利比較)
        v = float(value)

        # 根據比較方式排序並尋找符合的第一個門檻
        # 取得該項目的比較方式 (假設同一項目比較方式一致)
        comp_method = filtered_norms['比較方式'].iloc[0]

        if comp_method == ">=":
            # 越多越好：門檻由高到低排，找到第一個 v >= 門檻 的結果
            target_rules = filtered_norms.sort_values(by='門檻值', ascending=False)
            for _, rule in target_rules.iterrows():
                if v >= float(rule['門檻值']):
                    return rule['判定結果']
        elif comp_method == "<=":
            # 越快越好：門檻由低到高排，找到第一個 v <= 門檻 的結果
            target_rules = filtered_norms.sort_values(by='門檻值', ascending=True)
            for _, rule in target_rules.iterrows():
                if v <= float(rule['門檻值']):
                    return rule['判定結果']
                    
    except Exception as e:
        return f"計算錯誤"
        
    return "尚未達標"

# --- 3. 介面分頁設計 ---
tab1, tab2, tab3 = st.tabs(["📊 成績登錄與判定", "📈 數據統計", "⚙️ 常模管理中心"])

# --- Tab 3: 常模管理中心 (您最核心的需求) ---
with tab3:
    st.subheader("📝 自定義測驗常模設定")
    st.info("您可以在此直接編輯所有術科與體適能的標準。修改後請點擊下方儲存。")
    
    # 讀取 Norms_Settings 分頁
    try:
        norms_df = conn.read(worksheet="Norms_Settings", ttl="0s")
        
        # 讓使用者直接在網頁上像 Excel 一樣編輯
        edited_norms = st.data_editor(
            norms_df, 
            num_rows="dynamic", # 允許自行增加新項目列
            use_container_width=True,
            key="norms_editor"
        )
        
        if st.button("💾 儲存並套用新常模"):
            conn.update(worksheet="Norms_Settings", data=edited_norms)
            st.success("常模設定已更新！系統現在將採用最新的標準。")
            st.rerun()
    except Exception as e:
        st.error(f"讀取常模分頁失敗，請確認試算表中有名稱為 'Norms_Settings' 的分頁。")

# --- Tab 1: 成績登錄與判定 ---
with tab1:
    st.subheader("逐步成績判定")
    
    # 載入學生資料與常模資料
    students_df = conn.read(worksheet="Scores")
    current_norms = conn.read(worksheet="Norms_Settings")
    
    # 範例：單筆判定介面
    with st.expander("快速判定工具"):
        col1, col2, col3 = st.columns(3)
        with col1:
            cat = st.selectbox("類別", ["一般術科", "體適能"])
            gender = st.selectbox("性別", ["男", "女"])
        with col2:
            # 動態連動：只顯示該類別有的項目
            available_items = current_norms[current_norms['測驗類別'] == cat]['項目名稱'].unique()
            item = st.selectbox("測驗項目", available_items)
            age = st.number_input("年齡", value=14)
        with col3:
            score_val = st.text_input("輸入原始數值 (如次數或秒數)")
            
        if st.button("即時判定"):
            result = universal_judge(cat, item, gender, age, score_val, current_norms)
            st.metric(label="判定結果", value=result)

    # 全校自動化重算邏輯 (按鈕觸發)
    if st.button("🔄 依據新常模重新判定全校成績"):
        # 這裡實作迴圈讀取 Scores 表，調用 universal_judge，再存回 Google Sheets
        st.write("正在根據您的新定義重新計算中...")
        # (此處加入批次更新邏輯)
