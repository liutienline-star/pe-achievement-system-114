# 這是診斷用的程式碼片段
if st.button("查看目前所有分頁"):
    try:
        # 嘗試讀取所有工作表名稱
        all_sheets = conn.spreadsheet.worksheets()
        st.write("我目前看到的分頁有：", [s.title for s in all_sheets])
    except Exception as e:
        st.error(f"連線雖然通了，但無法獲取分頁列表：{e}")
