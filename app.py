import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="114學年度體育成績管理系統", layout="wide")

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
    },
    "PACER": {
        "男": {13: {"金": 76, "銀": 65, "銅": 47, "中": 32}, 14: {"金": 80, "銀": 69, "銅": 51, "中": 34}, 15: {"金": 89, "銀": 74, "銅": 54, "中": 38}, 16: {"金": 89, "銀": 77, "銅": 54, "中": 40}},
        "女": {13: {"金": 53, "銀": 44, "銅": 30, "中": 23}, 14: {"金": 53, "銀": 44, "銅": 31, "中": 23}, 15: {"金": 54, "銀": 45, "銅": 32, "中": 24}, 16: {"金": 54, "銀": 47, "銅": 33, "中": 25}}
    }
}

# 輔助函式：時間轉秒數 (00:25.00 -> 25.0)
def time_to_seconds(t_str):
    try:
        parts = t_str.split(':')
        m = int(parts[0])
        s = float(parts[1])
        return m * 60 + s
    except: return 9999.0

def judge_medal(item, gender, age, value):
    target_age = min(max(age, 13), 16)
    thresholds = NORMS[item][gender][target_age]
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
    return "待加強"

# --- 2. 資料連線 ---
conn = st.connection("gsheets", type=GSheetsConnection)
scores_df = conn.read(worksheet="Scores", ttl="0s")
student_list = conn.read(worksheet="Student_List", ttl="0s")

# --- 3. 側邊欄 ---
st.sidebar.header("📂 學生資訊選取")
if not student_list.empty:
    sel_class = st.sidebar.selectbox("🏫 班級", student_list['班級'].unique())
    students = student_list[student_list['班級'] == sel_class]
    sel_name = st.sidebar.selectbox("👤 姓名", students['姓名'])
    stu = students[students['姓名'] == sel_name].iloc[0]
    st.sidebar.info(f"📌 性別：{stu['性別']} | 年齡：{stu['年齡']}歲")
else: st.stop()

# --- 4. 主介面 ---
st.title(f"🏆 114學年度體育成績管理系統")
mode = st.radio("🎯 測驗模式切換", ["一般術科測驗", "114年體適能"], horizontal=True)

if mode == "一般術科測驗":
    col1, col2 = st.columns(2)
    with col1:
        test_cat = st.selectbox("🗂️ 類別", ["田徑", "球類", "體操", "其他"])
        test_item = st.text_input("📝 項目名稱", "100公尺")
    with col2:
        fmt = st.selectbox("📏 顯示格式", ["秒數 (00:00.00)", "分數/次數 (純數字)"])
        final_medal = st.selectbox("🏅 等第評定", ["優", "甲", "乙", "丙", "丁", "尚未判定"])
    
    if "秒數" in fmt:
        c1, c2, c3 = st.columns(3)
        mm, ss, ms = c1.number_input("分",0,59,0), c2.number_input("秒",0,59,25), c3.number_input("毫秒",0,99,0)
        final_score = f"{mm:02d}:{ss:02d}.{ms:02d}"
    else:
        final_score = st.text_input("📊 輸入數值", "85")
    note = st.text_input("💬 備註", "")

else: # 體適能
    test_cat = "體適能"
    status = st.selectbox("🩺 學生狀態", ["一般生", "身障/重大傷病 (比照銅牌)", "身體羸弱 (比照待加強)"])
    if status == "一般生":
        fit_item = st.selectbox("🏃 檢測項目", list(NORMS.keys()))
        test_item = fit_item
        if fit_item == "心肺耐力跑":
            fmt = "秒數 (00:00.00)"
            c1, c2 = st.columns(2)
            m, s = c1.number_input("分",0,20,8), c2.number_input("秒",0,59,0)
            final_score = f"{m:02d}:{s:02d}.00"
            final_medal = judge_medal("心肺耐力跑", stu['性別'], stu['年齡'], m*60+s)
        else:
            fmt = "次數/公分 (純數字)"
            val = st.number_input("🔢 數據", 0.0, 500.0, 0.0)
            final_score, final_medal = str(val), judge_medal(fit_item, stu['性別'], stu['年齡'], val)
        note = ""
    else:
        test_item, fmt, final_score = "體適能免測", "特殊判定", "N/A"
        final_medal, note = ("銅牌" if "身障" in status else "待加強"), status

# --- 5. 複測比對與儲存邏輯 ---
st.divider()
# 檢查是否有歷史紀錄
existing_mask = (scores_df['姓名'] == sel_name) & (scores_df['項目'] == test_item)
has_old = existing_mask.any()

if has_old:
    old_row = scores_df[existing_mask].iloc[-1]
    st.warning(f"🕒 偵測到歷史紀錄：成績 {old_row['成績']} ({old_row['等第/獎牌']})")
    
    # 判斷新成績是否更好
    is_better = False
    if "秒數" in fmt:
        is_better = time_to_seconds(final_score) < time_to_seconds(old_row['成績'])
    else:
        try: is_better = float(final_score) > float(old_row['成績'])
        except: is_better = True # 非數字則交由老師判斷
    
    if is_better: st.success("✨ 檢測結果：此為「最佳成績」，建議更新！")
    else: st.info("ℹ️ 檢測結果：此成績未超越歷史最佳成績。")

if st.button("💾 點擊確認：更新/存入試算表"):
    new_data = {
        "紀錄時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "班級": sel_class, "姓名": sel_name, "測驗類別": test_cat,
        "項目": test_item, "成績": final_score, "顯示格式": fmt,
        "等第/獎牌": final_medal, "備註": note
    }
    
    if has_old:
        # 修正/覆蓋舊紀錄
        scores_df.loc[existing_mask, list(new_data.keys())] = list(new_data.values())
        updated_df = scores_df
        msg = f"🆙 已成功「更新」{sel_name} 的最佳成績！"
    else:
        # 新增紀錄
        new_row = pd.DataFrame([new_data])
        updated_df = pd.concat([scores_df, new_row], ignore_index=True)
        msg = f"✅ 已成功「新增」{sel_name} 的成績紀錄！"
    
    conn.update(worksheet="Scores", data=updated_df)
    st.balloons()
    st.success(msg)
