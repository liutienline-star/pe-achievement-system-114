import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 頁面基本設定
st.set_page_config(page_title="114學年度連線診斷", layout="centered")
st.title("🔍 系統連線深度診斷")

# 建立連線
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    st.success("1. 建立連線物件：成功 ✅")
except Exception as e:
    st.error(f"1. 建立連線物件：失敗 ❌\n錯誤訊息：{e}")

st.divider()

# 診斷按鈕
if st.button("開始全面診斷"):
    # 測試 A：讀取分頁清單
    st.subheader("A. 測試分頁存取")
    try:
        # 嘗試直接透過底層 API 獲取所有工作表
        all_sheets = conn.client.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"]).worksheets()
        sheet_names = [s.title for s in all_sheets]
        st.write(f"目前偵測到的分頁：{sheet_names}")
        if "Scores" in sheet_names:
            st.success("找到 Scores 分頁！✅")
        else:
            st.warning("找不到 Scores 分頁，請確認名稱是否正確。")
    except Exception as e:
        st.error(f"無法存取試算表，這通常是權限問題 (401)。\n錯誤訊息：{e}")
        st.info("💡 請檢查：您的試算表是否已分享給『知道連結的人即可編輯』？")

    # 測試 B：讀取內容
    st.subheader("B. 測試資料讀取")
    try:
        df = conn.read(worksheet="Scores", ttl="0s")
        st.write("讀取到的標題列：", df.columns.tolist())
        st.dataframe(df)
        st.success("資料讀取成功！✅")
    except Exception as e:
        st.error(f"讀取資料失敗：{e}")

st.divider()
st.info("若診斷顯示 401 錯誤，請確認您的 Streamlit Secrets 內網址是否正確。")
