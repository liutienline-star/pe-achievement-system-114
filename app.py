import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="114學年度體育成績系統", layout="wide")

# --- 1. 連線與資料讀取 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    scores_df = conn.read(worksheet="Scores", ttl="0s")
    norms_df = conn.read(worksheet="Norms", ttl="0s")
    student_list = conn.read(worksheet="Student_List", ttl="0s")
    return scores_df, norms_df, student_list

scores_df, norms_df, student_list = load_data()

# --- 2. 側邊欄：基本資訊選擇 ---
st.sidebar.header("📋 學生基本資訊")

if not student_list.empty:
    all_classes = student_list['班級'].unique()
    sel_class = st.sidebar.selectbox("選擇班級", all_classes)
    
    class_students = student_list[student_list['班級'] == sel_class]
    sel_student = st.sidebar.selectbox("選擇學生", class_students['姓名'])
    
    # 自動抓取性別與年齡
    student_info = class_students[class_students['姓名'] == sel_student].iloc[0]
    st.sidebar.write(f"性別：{student_info['性別']} | 年齡：{student_info['年齡']}歲")
else:
    st.sidebar.warning("請先在 Student_List 工作表建立學生名單")
    st.stop()

# --- 3. 主頁面：成績輸入 ---
st.title(f"🏆 114學年度成績登錄 - {sel_student}")

tab1, tab2 = st.tabs(["🎯 術科專項", "💪 體適能測驗"])

with tab1:
    st.subheader("術科成績登錄")
    col1, col2 = st.columns(2)
    
    with col1:
        category = st.selectbox("測驗類別", ["球類", "田徑", "體操", "其他"], key="cat")
        item = st.text_input("測驗項目 (例如: 100公尺, 三分球)", value="100公尺")
    
    with col2:
        format_type = st.radio("成績顯示格式", ["秒數 (00:00.00)", "次數", "成功率 (%)"])
        
        if format_type == "秒數 (00:00.00)":
            m = st.number_input("分", min_value=0, max_value=59, step=1)
            s = st.number_input("秒", min_value=0, max_value=59, step=1)
            ms = st.number_input("毫秒", min_value=0, max_value=99, step=1)
            final_score = f"{m:02d}:{s:02d}.{ms:02d}"
        elif format_type == "次數":
            final_score = st.number_input("輸入次數", min_value=0, step=1)
        else:
            final_score = st.slider("成功率", 0, 100, 50)

with tab2:
    st.subheader("114學年度體適能新制")
    st.caption("系統將根據性別、年齡自動判定獎牌等級 (金/銀/銅/合格)")
    
    fit_item = st.selectbox("體適能項目", ["仰臥捲撐", "坐姿體前彎", "立定跳遠", "PACER(漸進式折返跑)"])
    fit_val = st.number_input(f"請輸入 {fit_item} 原始數值", min_value=0.0, step=0.1)
    
    # 簡易獎牌判定邏輯 (示範用，完整邏輯需對照 Norms 表)
    medal = "尚未判定"
    if st.button("計算體適能等級"):
        # 這裡未來會加入讀取 Norms 的邏輯
        st.info("等級判定功能已啟動，將對照 Norms 表進行計算...")
        medal = "合格" # 範例

# --- 4. 儲存功能 ---
st.divider()
if st.button("📤 儲存成績到 Google Sheets"):
    new_record = pd.DataFrame([{
        "班級": sel_class,
        "座號": student_info['座號'],
        "姓名": sel_student,
        "性別": student_info['性別'],
        "年齡": student_info['年齡'],
        "測驗類別": category if 'category' in locals() else "體適能",
        "項目": item if 'item' in locals() else fit_item,
        "成績": final_score if 'final_score' in locals() else fit_val,
        "顯示格式": format_type if 'format_type' in locals() else "體適能數值",
        "獎牌": medal,
        "紀錄時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    
    try:
        updated_df = pd.concat([scores_df, new_record], ignore_index=True)
        conn.update(worksheet="Scores", data=updated_df)
        st.success(f"✅ {sel_student} 的成績已成功上傳！")
        st.balloons()
    except Exception as e:
        st.error(f"儲存失敗：{e}")

# --- 5. 歷史紀錄查詢 ---
st.divider()
st.subheader("📊 本次連線已登錄紀錄")
st.dataframe(updated_df if 'updated_df' in locals() else scores_df)
