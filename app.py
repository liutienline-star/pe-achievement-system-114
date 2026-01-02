import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import re

# 頁面設定
st.set_page_config(page_title="114學年度體育成績管理系統", layout="wide")

# --- 0. 登入權限管理 ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]: return True
    st.title("🔒 體育成績管理系統 - 登入")
    col1, _ = st.columns([1, 2])
    with col1:
        u = st.text_input("👤 管理員帳號", value="")
        p = st.text_input("🔑 密碼", type="password")
        if st.button("🚀 確認登入"):
            if u == "tienline" and p == "641101":
                st.session_state["password_correct"] = True
                st.rerun()
            else: st.error("🚫 帳號或密碼錯誤")
    return False

if not check_password(): st.stop()

# --- 1. 體適能常模數據 ---
NORMS = {
    "仰臥捲腹": {"男": {13: {"金": 46, "銀": 40, "銅": 26, "中": 16}, 14: {"金": 48, "銀": 40, "銅": 28, "中": 18}, 15: {"金": 50, "銀": 42, "銅": 30, "中": 20}, 16: {"金": 50, "銀": 42, "銅": 30, "中": 21}}, "女": {13: {"金": 40, "銀": 32, "銅": 21, "中": 12}, 14: {"金": 40, "銀": 32, "銅": 21, "中": 12}, 15: {"金": 40, "銀": 32, "銅": 21, "中": 13}, 16: {"金": 41, "銀": 33, "銅": 24, "中": 14}}},
    "坐姿體前彎": {"男": {13: {"金": 33, "銀": 30, "銅": 24, "中": 18}, 14: {"金": 34, "銀": 31, "銅": 25, "中": 18}, 15: {"金": 35, "銀": 32, "銅": 25, "中": 18}, 16: {"金": 36, "銀": 33, "銅": 26, "中": 18}}, "女": {13: {"金": 39, "銀": 35, "銅": 30, "中": 24}, 14: {"金": 40, "銀": 37, "銅": 30, "中": 23}, 15: {"金": 42, "銀": 38, "銅": 31, "中": 25}, 16: {"金": 42, "銀": 39, "銅": 32, "中": 24}}},
    "立定跳遠": {"男": {13: {"金": 200, "銀": 190, "銅": 170, "中": 148}, 14: {"金": 213, "銀": 203, "銅": 185, "中": 165}, 15: {"金": 221, "銀": 213, "銅": 195, "中": 175}, 16: {"金": 230, "銀": 220, "銅": 200, "中": 180}}, "女": {13: {"金": 164, "銀": 155, "銅": 138, "中": 120}, 14: {"金": 165, "銀": 155, "銅": 138, "中": 122}, 15: {"金": 168, "銀": 158, "銅": 140, "中": 125}, 16: {"金": 172, "銀": 163, "銅": 145, "中": 127}}},
    "心肺耐力跑": {"男": {13: {"金": 474, "銀": 500, "銅": 590, "中": 676}, 14: {"金": 448, "銀": 477, "銅": 554, "中": 659}, 15: {"金": 438, "銀": 466, "銅": 533, "中": 619}, 16: {"金": 429, "銀": 452, "銅": 507, "中": 578}}, "女": {13: {"金": 243, "銀": 256, "銅": 283, "中": 316}, 14: {"金": 250, "銀": 263, "銅": 289, "中": 323}, 15: {"金": 246, "銀": 259, "銅": 287, "中": 320}, 16: {"金": 243, "銀": 254, "銅": 278, "中": 311}}}
}

# --- 2. 輔助函式 ---
def clean_numeric_string(val):
    if pd.isna(val) or val == 'nan': return ""
    s = str(val).strip()
    return str(int(float(s))) if re.match(r'^\d+\.0$', s) else s

def parse_time_to_seconds(time_str):
    try:
        if ":" in str(time_str):
            main, _ = str(time_str).split('.')
            m, s = main.split(':')
            return int(m) * 60 + int(s)
        return float(time_str)
    except: return 0

def judge_medal(item, gender, age, value):
    if item not in NORMS: return "尚未判定"
    try:
        age_key = min(max(int(float(age)), 13), 16)
        thr = NORMS[item][gender][age_key]
        val = parse_time_to_seconds(value) if item == "心肺耐力跑" else float(value)
        if item == "心肺耐力跑":
            for k, m in [("金質獎", "金"), ("銀質獎", "銀"), ("銅質獎", "銅"), ("中等", "中")]:
                if val <= thr[m]: return k
        else:
            for k, m in [("金質獎", "金"), ("銀質獎", "銀"), ("銅質獎", "銅"), ("中等", "中")]:
                if val >= thr[m]: return k
    except: pass
    return "待加強"

# --- 3. 一般術科常模 (區間判定) ---
def judge_subject_score(item, gender, value):
    try:
        v = float(value)
        if "排球發球" in item:
            norms = {"男": [(13,100),(12,97),(11,93),(10,89),(9,85),(8,81),(7,77),(6,73),(5,69),(4,66),(3,63),(2,60),(1,55),(0,50)],
                     "女": [(11,100),(10,97),(9,92),(8,87),(7,82),(6,77),(5,72),(4,69),(3,66),(2,63),(1,60),(0,50)]}
            for thr, s in norms[gender]:
                if v >= thr: return f"{s}分"
        elif "籃球罰球" in item:
            norms = {"男": [(13,100),(12,97),(11,94),(10,91),(9,88),(8,84),(7,80),(6,76),(5,72),(4,68),(3,64),(2,60),(1,55),(0,53)],
                     "女": [(13,100),(12,98),(11,96),(10,93),(9,90),(8,87),(7,84),(6,81),(5,78),(4,75),(3,72),(2,68),(1,60),(0,55)]}
            for thr, s in norms[gender]:
                if v >= thr: return f"{s}分"
        elif "立定跳遠" in item:
            norms = {"男": [(230,100),(225,98),(220,97),(217,96),(214,94),(210,92),(205,90),(200,88),(195,86),(190,84),(185,82),(180,80),(174,78),(165,76),(160,74),(155,72),(150,70),(147,68),(143,66),(139,64),(135,62),(130,60),(125,58),(124,56),(0,50)],
                     "女": [(200,100),(197,98),(194,97),(191,96),(188,94),(185,92),(182,90),(179,88),(175,86),(170,84),(165,82),(160,80),(155,78),(150,76),(145,74),(140,72),(135,70),(130,68),(125,66),(120,64),(115,62),(110,60),(105,58),(104,56),(0,50)]}
            for thr, s in norms[gender]:
                if v >= thr: return f"{s}分"
        elif "運球上籃" in item:
            norms = {"男": [(7.0,100),(7.5,99),(8.0,98),(8.5,97),(9.0,96),(9.5,95),(10.0,94),(10.5,93),(11.0,92),(11.5,91),(12.0,90),(12.5,89),(13.0,87),(13.2,85),(13.4,83),(13.6,82),(13.8,81),(14.0,79),(14.2,77),(14.4,75),(14.6,73),(14.8,71),(15.0,70),(15.6,69),(16.6,68),(17.6,67),(18.6,65),(19.6,63),(20.6,61),(21.6,59),(22.6,57),(23.6,55),(24.6,53),(99,50)],
                     "女": [(9.5,100),(10.0,98),(10.5,97),(11.0,96),(11.5,95),(12.0,94),(12.5,93),(13.0,92),(13.2,91),(13.4,90),(13.6,89),(13.8,88),(14.0,87),(14.2,86),(14.4,85),(14.6,84),(14.8,83),(15.0,82),(15.2,81),(15.4,80),(15.6,79),(15.8,78),(16.0,77),(16.6,75),(17.6,73),(18.6,71),(19.6,69),(20.6,67),(21.6,65),(22.6,63),(23.6,60),(24.6,57),(25.6,55),(99,53)]}
            for thr, s in norms[gender]:
                if v <= thr: return f"{s}分"
    except: pass
    return "尚未判定"

# --- 4. 資料連線 ---
conn = st.connection("gsheets", type=GSheetsConnection)
scores_df = conn.read(worksheet="Scores", ttl="0s").astype(str).map(clean_numeric_string)
student_list = conn.read(worksheet="Student_List", ttl="0s").astype(str).map(clean_numeric_string)

# --- 5. 側邊欄 ---
if not student_list.empty:
    cl_list = student_list['班級'].unique()
    sel_class = st.sidebar.selectbox("🏫 選擇班級", cl_list)
    stu_df = student_list[student_list['班級'] == sel_class]
    no_list = stu_df['座號'].sort_values(key=lambda x: pd.to_numeric(x, errors='coerce')).unique()
    sel_no = st.sidebar.selectbox("🔢 選擇學生座號", no_list)
    stu = stu_df[stu_df['座號'] == sel_no].iloc[0]
    sel_name = stu['姓名'] # 用於報表查詢
    st.sidebar.info(f"📌 {sel_name} | 性別：{stu['性別']} | {stu['年齡']}歲")
else: st.stop()

# --- 6. 主介面 ---
st.title(f"🏆 114學年度體育成績管理系統")
mode = st.radio("🎯 功能切換", ["一般術科測驗", "114年體適能", "📊 數據報表查詢"], horizontal=True)

if mode == "一般術科測驗":
    col1, col2 = st.columns(2)
    with col1:
        test_cat = st.selectbox("🗂️ 類別", ["球類", "田徑", "體操", "其他"])
        test_item = st.selectbox("📝 項目", ["排球發球(15球)", "籃球罰球(15球)", "立定跳遠", "運球上籃", "垂直跳高", "其他"])
        if test_item == "其他": test_item = st.text_input("✍️ 名稱")
    with col2:
        fmt = st.selectbox("📏 格式", ["分數/個數 (純數字)", "秒數 (00.00)"])
        auto_j = st.checkbox("🤖 自動換算分數", value=True)
        manual_m = st.selectbox("🏅 等第", ["優", "甲", "乙", "丙", "丁", "尚未判定"])
    
    if "秒數" in fmt:
        c1, c2 = st.columns(2)
        final_score = f"{c1.number_input('秒', 0, 99, 13)}.{c2.number_input('毫秒', 0, 99, 0):02d}"
    else: final_score = clean_numeric_string(st.text_input("📊 輸入數值", "0"))
    final_medal = judge_subject_score(test_item, stu['性別'], final_score) if auto_j else manual_m
    note = st.text_input("💬 備註", "")
    
    # 歷史紀錄顯示 (保留)
    st.write("🕒 **該項目近期測驗紀錄：**")
    recent = scores_df[(scores_df['姓名'] == sel_name) & (scores_df['項目'] == test_item)]
    if not recent.empty:
        st.dataframe(recent[['紀錄時間', '成績', '等第/獎牌']].tail(3), use_container_width=True)
    else: st.info("尚無紀錄")

elif mode == "114年體適能":
    test_cat = "體適能"
    status = st.selectbox("🩺 學生狀態", ["一般生", "身障/重大傷病 (比照銅牌)", "身體羸弱 (比照待加強)"])
    fit_item = st.selectbox("🏃 檢測項目", list(NORMS.keys()))
    test_item = fit_item
    if status == "一般生":
        if fit_item == "心肺耐力跑":
            c1, c2 = st.columns(2)
            final_score, fmt = f"{c1.number_input('分', 0, 20, 8):02d}:{c2.number_input('秒', 0, 59, 0):02d}.0", "秒數 (00:00.0)"
            final_medal = judge_medal("心肺耐力跑", stu['性別'], stu['年齡'], final_score)
        else:
            val = st.number_input("🔢 數據", 0.0, 500.0, 0.0)
            final_score, fmt = clean_numeric_string(val), "次數/公分"
            final_medal = judge_medal(fit_item, stu['性別'], stu['年齡'], val)
        note = ""
    else:
        final_score, fmt = "N/A", "特殊判定"
        final_medal, note = ("銅牌" if "身障" in status else "待加強"), status

# --- 數據報表查詢 (完整還原自您的原始碼) ---
elif mode == "📊 數據報表查詢":
    tab1, tab2, tab3 = st.tabs(["👤 個人成績單", "👥 班級總覽", "⚙️ 系統維護工具"])
    
    with tab1:
        st.subheader(f"🔍 {sel_name} 的個人測驗紀錄")
        personal_data = scores_df[scores_df['姓名'] == sel_name].copy()
        if not personal_data.empty:
            c1, c2 = st.columns(2)
            with c1:
                p_cat = st.selectbox("🗂️ 篩選測驗類別", ["顯示全部"] + list(personal_data['測驗類別'].unique()), key="p_cat")
            with c2:
                p_items = personal_data['項目'].unique() if p_cat == "顯示全部" else personal_data[personal_data['測驗類別'] == p_cat]['項目'].unique()
                p_item = st.selectbox("🎯 篩選檢測項目", ["顯示全部"] + list(p_items), key="p_item")
            
            df_to_show = personal_data.copy()
            if p_cat != "顯示全部": df_to_show = df_to_show[df_to_show['測驗類別'] == p_cat]
            if p_item != "顯示全部": df_to_show = df_to_show[df_to_show['項目'] == p_item]
            
            cols = ['座號', '測驗類別', '項目', '成績', '等第/獎牌', '紀錄時間', '備註']
            st.dataframe(df_to_show[[c for c in cols if c in df_to_show.columns]], use_container_width=True)
        else:
            st.info(f"💡 目前尚未有 {sel_name} 的測驗紀錄。")

    with tab2:
        st.subheader(f"📂 {sel_class} 班級成績彙整")
        class_data = scores_df[scores_df['班級'] == sel_class].copy()
        if not class_data.empty:
            c1, c2 = st.columns(2)
            with c1:
                cl_cat = st.selectbox("🗂️ 篩選測驗類別", ["顯示全部"] + list(class_data['測驗類別'].unique()), key="cl_cat")
            with c2:
                cl_items = class_data['項目'].unique() if cl_cat == "顯示全部" else class_data[class_data['測驗類別'] == cl_cat]['項目'].unique()
                cl_item = st.selectbox("🎯 篩選檢測項目", ["顯示全部"] + list(cl_items), key="cl_item")
            
            df_cl_show = class_data.copy()
            if cl_cat != "顯示全部": df_cl_show = df_cl_show[df_cl_show['測驗類別'] == cl_cat]
            if cl_item != "顯示全部": df_cl_show = df_cl_show[df_cl_show['項目'] == cl_item]
            
            if '座號' in df_cl_show.columns:
                df_cl_show['座號'] = pd.to_numeric(df_cl_show['座號'], errors='coerce')
                df_cl_show = df_cl_show.sort_values(by=['座號', '項目'])
            st.dataframe(df_cl_show, use_container_width=True)
            csv = df_cl_show.to_csv(index=False).encode('utf-8-sig')
            st.download_button(f"📥 下載此報表 (CSV)", csv, f"{sel_class}_filtered_report.csv", "text/csv")
        else:
            st.info(f"💡 目前該班級尚未有任何紀錄。")
    
    with tab3:
        st.subheader("🛠️ 全校體適能成績重新判定")
        st.warning("⚠️ 此功能會將 Scores 分頁中所有的「體適能」成績依照常模重新計算一次「等第/獎牌」。")
        if st.button("🚀 開始全自動重新判定"):
            with st.spinner("正在比對名單並計算中..."):
                stu_info = student_list.set_index('姓名')[['性別', '年齡']].to_dict('index')
                updated_count = 0
                for idx, row in scores_df.iterrows():
                    if row['測驗類別'] == "體適能" and row['姓名'] in stu_info:
                        s_info = stu_info[row['姓名']]
                        new_medal = judge_medal(row['項目'], s_info['性別'], s_info['年齡'], row['成績'])
                        scores_df.at[idx, '等第/獎牌'] = new_medal
                        updated_count += 1
                final_df = scores_df.map(clean_numeric_string)
                conn.update(worksheet="Scores", data=final_df)
                st.success(f"🎊 重新判定完成！共更新 {updated_count} 筆體適能成績。")
                st.rerun()

# --- 7. 複測自動偵測與儲存 (完整還原自您的原始碼) ---
if mode in ["一般術科測驗", "114年體適能"]:
    st.divider()
    existing_mask = (scores_df['姓名'] == sel_name) & (scores_df['項目'] == test_item)
    has_old = existing_mask.any()
    if has_old:
        old_row = scores_df[existing_mask].iloc[-1]
        st.warning(f"🕒 偵測到歷史紀錄：成績 {old_row['成績']} ({old_row['等第/獎牌']})")
    
    if st.button("💾 點擊確認：存入試算表"):
        new_data = {
            "紀錄時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "班級": clean_numeric_string(sel_class),
            "座號": clean_numeric_string(stu['座號']),
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
        else:
            new_row = pd.DataFrame([new_data])
            updated_df = pd.concat([scores_df, new_row], ignore_index=True)
        
        updated_df = updated_df.map(clean_numeric_string)
        conn.update(worksheet="Scores", data=updated_df)
        st.balloons()
        st.success("✅ 成績紀錄已成功同步至雲端！")
        st.rerun()

if st.sidebar.button("🚪 登出系統"):
    st.session_state["password_correct"] = False
    st.rerun()
