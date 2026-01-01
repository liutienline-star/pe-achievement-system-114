import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="114學年度連線測試", layout="centered")
st.title("🔗 Google Sheets 連線測試系統")

# 建立連線物件
conn = st.connection("gsheets", type=GSheetsConnection)

st.divider()

# --- 測試 1：讀取資料 ---
st.subheader("第一步：讀取測試")
if st.button("嘗試讀取 Scores 工作表"):
    try:
        df = conn.read(worksheet="Scores", ttl="0s")
        st.success("✅ 讀取成功！")
        st.dataframe(df.head()) # 顯示前幾行資料
    except Exception as e:
        st.error(f"❌ 讀取失敗：{e}")
        st.info("請檢查：1. 工作表名稱是否真的叫 Scores？ 2. 是否已給 Service Account 編輯權限？")

# --- 測試 2：寫入資料 ---
st.subheader("第二步：寫入測試")
with st.form("test_form"):
    test_name = st.text_input("測試姓名", value="連線測試員")
    test_score = st.number_input("測試分數", value=100)
    submit = st.form_submit_button("點我測試寫入一筆資料")

if submit:
    try:
        # 1. 先讀取舊資料
        df_old = conn.read(worksheet="Scores", ttl="0s")
        
        # 2. 建立新的一列
        new_data = pd.DataFrame([{
            "班級": "測試班",
            "姓名": test_name,
            "成績": test_score,
            "紀錄時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])
        
        # 3. 合併並更新
        df_updated = pd.concat([df_old, new_data], ignore_index=True)
        conn.update(worksheet="Scores", data=df_updated)
        
        st.success(f"🎉 寫入成功！請打開您的 Google Sheet 查看是否有『{test_name}』。")
    except Exception as e:
        st.error(f"❌ 寫入失敗：{e}")

# --- 測試 3：檢查其他分頁 ---
st.subheader("第三步：檢查常模分頁")
if st.button("讀取 Norms 常模數據"):
    try:
        df_norms = conn.read(worksheet="Norms", ttl="0s")
        st.write("目前常模設定：")
        st.table(df_norms)
    except:
        st.warning("尚未偵測到 Norms 工作表，或內容為空。")
