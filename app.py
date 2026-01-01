import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import re

# 頁面設定
st.set_page_config(page_title="114學年度體育成績管理系統", layout="wide")

# --- 0. 登入權限管理 (確保資訊安全) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True

    st.title("🔒 體育成績管理系統 - 登入")
    col1, _ = st.columns([1, 2])
    with col1:
        user_input = st.text_input("👤 管理員帳號", value="")
        password_input = st.text_input("🔑 密碼", type="password")
        if st.button("🚀 確認登入"):
            if user_input == "tienline" and password_input == "641101":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("🚫 帳號或密碼錯誤，請重試")
    return False

if not check_password():
    st.stop()

# --- 1. 體適能常模數據 ---
NORMS = {
    "仰臥捲腹": {
        "男": {13: {"金": 46, "銀": 40, "銅": 26, "中": 16}, 14: {"金": 48, "銀": 40, "銅": 28, "中": 18}, 15: {"金": 50, "銀": 42, "銅": 30, "中": 20}, 16: {"金": 50, "銀": 42, "銅": 30, "中": 21}},
        "女": {13: {"金": 40, "銀": 32, "銅": 21, "中": 12}, 14: {"金": 40, "銀": 32, "銅": 21, "中": 12}, 15: {"金": 40, "銀": 32, "銅": 21, "中": 13}, 16: {"金": 41, "銀": 33, "銅": 24, "中": 14}}
    },
    "坐姿體前彎": {
        "男": {13: {"金": 33, "銀": 30, "銅": 24, "中": 18}, 14: {"金": 34, "銀": 31, "銅": 25, "中": 18}, 15: {"金": 35, "銀": 32, "銅": 25, "中": 18}, 16: {"金": 36, "銀": 33, "銅": 26, "中": 18}},
        "女": {13: {"金": 39, "銀": 35, "銅": 30, "中": 24}, 14: {"金": 40, "銀": 37, "銅": 30, "中": 23}, 15: {"金": 42, "銀": 38, "銅": 31, "中": 25}, 16: {"金": 42, "銀": 39, "銅": 32, "中": 24}}
    },
    "立定跳遠": {
        "男": {13: {"金": 200, "銀": 190, "銅": 170, "中": 148}, 14: {"金": 213, "銀": 203, "銅": 185, "中": 165}, 15: {"金": 221, "銀": 213, "銅": 195, "中": 175}, 16: {"金": 230, "銀": 220, "銅": 200, "中": 180}},
        "女": {13: {"金": 164, "銀": 155, "銅": 138, "中": 120}, 14: {"金": 165, "銀": 155, "銅": 138, "中": 122}, 15: {"金": 168, "銀": 158, "銅": 140, "中": 125}, 16: {"金": 172, "銀": 163, "銅": 145, "中": 127}}
    },
    "心肺耐力跑": {
        "男": {13: {"金": 474, "銀": 500, "銅": 590, "中": 676}, 14: {"金": 448, "銀": 477, "銅": 554, "中": 659}, 15: {"金": 438, "銀": 466, "銅": 533, "中": 619}, 16: {"金": 429, "銀": 452, "銅": 507, "中": 578}},
        "女": {13: {"金": 243, "銀": 256, "銅": 283, "中": 316}, 14: {"金": 250, "銀": 263, "銅": 289, "中": 323}, 15: {"金": 246, "銀": 259, "銅": 287, "中": 320}, 16: {"金": 243, "銀": 254, "銅": 278, "中": 311}}
    }
}

# --- 2. 智慧格式化函式 ---
def clean_numeric_string(val):
    """將整數 .0 去除 (如座號 1.0 -> 1)，但保留如 13.5 或 0.00"""
    s = str(val)
    if re.match(r'^\d+\.0$', s):
        return str(int(float(s)))
    return s

def judge_medal(item, gender, age, value):
    if item not in NORMS: return "尚未判定"
    try:
        age_key = min(max(int(age), 13), 16)
        thresholds = NORMS[item][gender][age_key]
        if item == "心肺耐力跑":
            if value <= thresholds["金"]: return "金質獎"
            if value <= thresholds["銀"]: return "銀質獎"
            if value <= thresholds["銅"]: return "銅質獎"
            if value <= thresholds["中"]: return "中等"
        else:
            if value >= thresholds["金"]: return "金質獎"
            if value >= thresholds["銀"]: return "銀質獎"
            if value >= thresholds["銅"]: return "銅質獎"
            if value >= thresholds["中"]: return "中等"
    except: pass
    return "待加強"

# --- 3. 資料讀取 ---
conn = st.connection("gsheets", type=GSheetsConnection)
# 修正處：讀取後統一對整個 DataFrame 執行 clean_numeric_string，避免 809.0 這種情況出現
scores_df = conn.read(worksheet="Scores", ttl="0s").astype(str).map(clean_numeric_string)
student_list = conn.read(worksheet="Student_List", ttl="0s").astype(str).map(clean_numeric_string)

# --- 4. 側邊欄 (新增座號選取) ---
st.sidebar.header("📂 學生資訊選取")
if not student_list.empty:
    class_list = student_list['班級'].unique()
    sel_class = st.sidebar.selectbox("🏫 選擇班級", class_list)
    
    class_students = student_list[student_list['班級'] == sel_class]
    
    # 座號清單
    no_list = class_students['座號'].sort_values(key=lambda x: x.astype(int)).unique()
    sel_no = st.sidebar.selectbox("🔢 選擇學生座號", no_list)
    
    students = class_students[class_students['座號'] == sel_no]
    sel_name = st.sidebar.selectbox("👤 選擇學生姓名", students['姓名'])
    
    stu = students[students['姓名'] == sel_name].iloc[0]
    st.sidebar.info(f"📌 性別：{stu['性別']} | 年齡：{stu['年齡']}歲")
else:
    st.error("❌ 找不到學生名單，請檢查試算表。")
    st.stop()

# --- 5. 主介面 ---
st.title(f"🏆 114學年度體育成績管理系統")
mode = st.radio("🎯 功能切換", ["一般術科測驗", "114年體適能", "📊 數據報表查詢"], horizontal=True)

if mode == "一般術科測驗":
    col1, col2 = st.columns(2)
    with col1:
        test_cat = st.selectbox("🗂️ 類別", ["田徑", "球類", "體操", "其他"])
        test_item = st.text_input("📝 項目名稱", "100公尺")
    with col2:
        fmt = st.selectbox("📏 顯示格式", ["秒數 (00.00)", "分數/次數 (純數字)"])
        final_medal = st.selectbox("🏅 等第評定", ["優", "甲", "乙", "丙", "丁", "尚未判定"])
    
    if "秒數" in fmt:
        c1, c2 = st.columns(2)
        ss = c1.number_input("秒 (如 13)", 0, 999, 13)
        ms = c2.number_input("毫秒/小數點後兩位 (如 05)", 0, 99, 0)
        final_score = f"{ss}.{ms:02d}"
    else:
        val_input = st.text_input("📊 輸入數值", "85")
        final_score = clean_numeric_string(val_input)
    note = st.text_input("💬 備註", "")

    st.markdown("---")
    st.markdown(f"##### 📋 {sel_name} - {test_cat} 類別已測驗項目檢閱")
    cat_history = scores_df[(scores_df['姓名'] == sel_name) & (scores_df['測驗類別'] == test_cat)]
    if not cat_history.empty:
        st.dataframe(cat_history[['項目', '成績', '等第/獎牌', '紀錄時間']], use_container_width=True)
    else:
        st.info(f"💡 目前尚無 {test_cat} 類別的歷史紀錄。")

elif mode == "114年體適能":
    test_cat = "體適能"
    status = st.selectbox("🩺 學生狀態", ["一般生", "身障/重大傷病 (比照銅牌)", "身體羸弱 (比照待加強)"])
    if status == "一般生":
        fit_item = st.selectbox("🏃 檢測項目", list(NORMS.keys()) + ["其他 (手動輸入)"])
        if fit_item == "其他 (手動輸入)":
            test_item = st.text_input("✍️ 請輸入自定義項目", "仰臥起坐")
            val = st.number_input("🔢 數據紀錄", 0.0, 500.0, 0.0)
            final_score = clean_numeric_string(val)
            final_medal = "尚未判定"
            fmt = "手動輸入"
        elif fit_item == "心肺耐力跑":
            test_item, fmt = fit_item, "秒數 (00:00.0)"
            c1, c2 = st.columns(2)
            m, s = c1.number_input("分", 0, 20, 8), c2.number_input("秒", 0, 59, 0)
            final_score = f"{m:02d}:{s:02d}.0"
            final_medal = judge_medal("心肺耐力跑", stu['性別'], stu['年齡'], m*60+s)
        else:
            test_item, fmt = fit_item, "次數/公分"
            val = st.number_input("🔢 數據", 0.0, 500.0, 0.0)
            final_score = clean_numeric_string(val)
            final_medal = judge_medal(fit_item, stu['性別'], stu['年齡'], float(val))
        note = ""
    else:
        test_item, fmt, final_score = "體適能免測", "特殊判定", "N/A"
        final_medal, note = ("銅牌" if "身障" in status else "待加強"), status

# --- 數據報表查詢 ---
elif mode == "📊 數據報表查詢":
    tab1, tab2 = st.tabs(["👤 個人成績單", "👥 班級總覽"])
    with tab1:
        st.subheader(f"🔍 {sel_name} 的個人測驗紀錄")
        personal_data = scores_df[scores_df['姓名'] == sel_name].copy()
        if not personal_data.empty:
            personal_data = personal_data.sort_values(by="測驗類別")
            st.dataframe(personal_data[['測驗類別', '項目', '成績', '等第/獎牌', '紀錄時間', '備註']], use_container_width=True)
            st.write("📈 獎牌/等第統計：")
            medal_counts = personal_data['等第/獎牌'].value_counts()
            st.bar_chart(medal_counts)
        else:
            st.info(f"💡 目前尚未有 {sel_name} 的測驗紀錄。")
    with tab2:
        st.subheader(f"📂 {sel_class} 班級成績彙整")
        class_data = scores_df[scores_df['班級'] == sel_class].copy()
        if not class_data.empty:
            all_items = class_data['項目'].unique()
            selected_report_item = st.selectbox("🎯 篩選單項檢視", ["顯示全部"] + list(all_items))
            if selected_report_item != "顯示全部":
                display_df = class_data[class_data['項目'] == selected_report_item]
            else:
                display_df = class_data
            st.dataframe(display_df.sort_values(by="項目"), use_container_width=True)
            csv = display_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(f"📥 下載 {sel_class} 成績表 (CSV)", csv, f"{sel_class}_report.csv", "text/csv")
        else:
            st.info(f"💡 目前該班級尚未有任何紀錄。")

# --- 6. 複測自動偵測與儲存 ---
if mode in ["一般術科測驗", "114年體適能"]:
    st.divider()
    existing_mask = (scores_df['姓名'] == sel_name) & (scores_df['項目'] == test_item)
    has_old = existing_mask.any()
    if has_old:
        old_row = scores_df[existing_mask].iloc[-1]
        st.warning(f"🕒 偵測到歷史紀錄：成績 {old_row['成績']} ({old_row['等第/獎牌']})")
        st.info("💡 若此為複測，點擊下方按鈕將自動『覆蓋並更新』為本次最佳成績。")
    if st.button("💾 點擊確認：存入試算表"):
        new_data = {
            "紀錄時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "班級": clean_numeric_string(sel_class), 
            "姓名": sel_name, 
            "測驗類別": test_cat,
            "項目": test_item, 
            "成績": final_score, 
            "顯示格式": fmt,
            "等第/獎牌": final_medal, 
            "備註": note
        }
        if has_old:
            for col, value in new_data.items():
                scores_df.loc[existing_mask, col] = str(value)
            updated_df = scores_df
            msg = f"🆙 已成功「更新」{sel_name} 的 {test_item} 最佳成績！"
        else:
            new_row = pd.DataFrame([new_data])
            updated_df = pd.concat([scores_df, new_row], ignore_index=True)
            msg = f"✅ 已成功「新增」{sel_name} 的成績紀錄！"
        
        # 修正處：存檔前再次確保 DataFrame 內的所有數值都沒有 .0
        updated_df = updated_df.map(clean_numeric_string)
        conn.update(worksheet="Scores", data=updated_df)
        st.balloons()
        st.success(msg)

# 登出按鈕
if st.sidebar.button("🚪 登出系統"):
    st.session_state["password_correct"] = False
    st.rerun()
