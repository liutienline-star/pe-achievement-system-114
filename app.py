import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import re

# 頁面設定 (保留原設定)
st.set_page_config(page_title="114學年度體育成績管理系統", layout="wide")

# --- 0. 登入權限管理 (保留原邏輯) ---
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

# --- 1. 資料連線 (新增 Norms_Settings 讀取) ---
conn = st.connection("gsheets", type=GSheetsConnection)

# 讀取三個分頁
scores_df = conn.read(worksheet="Scores", ttl="0s").astype(str)
student_list = conn.read(worksheet="Student_List", ttl="0s").astype(str)
# 萬用常模表
try:
    norms_settings_df = conn.read(worksheet="Norms_Settings", ttl="0s")
except:
    st.error("請在 Google Sheets 中建立名為 'Norms_Settings' 的分頁！")
    st.stop()

# --- 2. 輔助函式 (保留原函式) ---
def clean_numeric_string(val):
    if pd.isna(val) or val == 'nan' or val == "": return ""
    s = str(val).strip()
    return str(int(float(s))) if re.match(r'^\d+\.0$', s) else s

def parse_time_to_seconds(time_str):
    try:
        if ":" in str(time_str):
            main = str(time_str).split('.')[0]
            parts = main.split(':')
            if len(parts) == 2: return int(parts[0]) * 60 + int(parts[1])
            return int(parts[0])
        return float(time_str)
    except: return 0

# --- 3. 萬用判定引擎 (核心新功能) ---
def universal_judge(category, item, gender, age, value, norms_df):
    """
    取代原本硬編碼判定的核心引擎。
    """
    try:
        # 1. 篩選基本條件
        mask = (norms_df['測驗類別'] == category) & \
               (norms_df['項目名稱'] == item) & \
               (norms_df['性別'] == gender)
        item_norms = norms_df[mask].copy()
        
        if item_norms.empty: return "查無常模"

        # 2. 篩選年齡 (0 代表不分年齡)
        age_mask = (item_norms['年齡'].astype(int) == int(float(age))) | (item_norms['年齡'].astype(int) == 0)
        item_norms = item_norms[age_mask]

        # 3. 數值轉換
        v = parse_time_to_seconds(value) if ":" in str(value) else float(value)

        # 4. 判定比對 (依據比較方式排序)
        comp_method = item_norms['比較方式'].iloc[0]
        
        if comp_method == ">=":
            item_norms = item_norms.sort_values(by='門檻值', ascending=False)
            for _, rule in item_norms.iterrows():
                if v >= float(rule['門檻值']): return rule['判定結果']
        else: # <=
            item_norms = item_norms.sort_values(by='門檻值', ascending=True)
            for _, rule in item_norms.iterrows():
                if v <= float(rule['門檻值']): return rule['判定結果']
    except: pass
    return "尚未判定"

# --- 4. 舊函式轉接器 (維持原介面呼叫，內部改用新引擎) ---
def judge_medal(item, gender, age, value):
    return universal_judge("體適能", item, gender, age, value, norms_settings_df)

def judge_subject_score(item, gender, value):
    return universal_judge("一般術科", item, gender, 0, value, norms_settings_df)

# --- 5. 側邊欄 (保留原邏輯) ---
scores_df = scores_df.map(clean_numeric_string)
student_list = student_list.map(clean_numeric_string)

if not student_list.empty:
    cl_list = student_list['班級'].unique()
    sel_class = st.sidebar.selectbox("🏫 選擇班級", cl_list)
    stu_df = student_list[student_list['班級'] == sel_class]
    no_list = stu_df['座號'].sort_values(key=lambda x: pd.to_numeric(x, errors='coerce')).unique()
    sel_no = st.sidebar.selectbox("🔢 選擇學生座號", no_list)
    stu = stu_df[stu_df['座號'] == sel_no].iloc[0]
    sel_name = stu['姓名']
    st.sidebar.info(f"📌 {sel_name} | 性別：{stu['性別']} | {stu['年齡']}歲")
else: st.stop()

# --- 6. 主介面 (保留原版面) ---
st.title(f"🏆 114學年度體育成績管理系統")
mode = st.radio("🎯 功能切換", ["一般術科測驗", "114年體適能", "📊 數據報表查詢"], horizontal=True)

if mode == "一般術科測驗":
    col1, col2 = st.columns(2)
    with col1:
        test_cat = st.selectbox("🗂️ 類別", ["一般術科", "球類", "田徑", "體操", "其他"])
        # 改為讀取常模表中的術科項目
        subject_items = norms_settings_df[norms_settings_df['測驗類別'] != "體適能"]['項目名稱'].unique()
        test_item = st.selectbox("📝 項目", list(subject_items) + ["其他"])
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
    
    st.write("🕒 **該項目近期測驗紀錄：**")
    recent = scores_df[(scores_df['姓名'] == sel_name) & (scores_df['項目'] == test_item)]
    if not recent.empty:
        st.dataframe(recent[['紀錄時間', '成績', '等第/獎牌']].tail(3), use_container_width=True)
    else: st.info("尚無紀錄")

elif mode == "114年體適能":
    test_cat = "體適能"
    status = st.selectbox("🩺 學生狀態", ["一般生", "身障/重大傷病 (比照銅牌)", "身體羸弱 (比照待加強)"])
    # 讀取常模表中的體適能項目
    fitness_items = norms_settings_df[norms_settings_df['測驗類別'] == "體適能"]['項目名稱'].unique()
    fit_item = st.selectbox("🏃 檢測項目", list(fitness_items))
    test_item = fit_item
    if status == "一般生":
        if "跑" in fit_item or ":" in str(fit_item):
            c1, c2 = st.columns(2)
            final_score, fmt = f"{c1.number_input('分', 0, 20, 8):02d}:{c2.number_input('秒', 0, 59, 0):02d}.0", "秒數 (00:00.0)"
            final_medal = judge_medal(fit_item, stu['性別'], stu['年齡'], final_score)
        else:
            val = st.number_input("🔢 數據", 0.0, 500.0, 0.0)
            final_score, fmt = clean_numeric_string(val), "次數/公分"
            final_medal = judge_medal(fit_item, stu['性別'], stu['年齡'], val)
        note = ""
    else:
        final_score, fmt = "N/A", "特殊判定"
        final_medal, note = ("銅牌" if "身障" in status else "待加強"), status

# --- 📊 數據報表查詢 (保留原所有功能) ---
elif mode == "📊 數據報表查詢":
    tab1, tab2, tab3 = st.tabs(["👤 個人成績單", "👥 班級總覽", "⚙️ 系統維護工具"])
    
    with tab1:
        st.subheader(f"🔍 {sel_name} 的個人測驗紀錄")
        personal_data = scores_df[scores_df['姓名'] == sel_name].copy()
        if not personal_data.empty:
            c1, c2 = st.columns(2)
            with c1: p_cat = st.selectbox("🗂️ 篩選測驗類別", ["顯示全部"] + list(personal_data['測驗類別'].unique()), key="p_cat")
            with c2:
                p_items = personal_data['項目'].unique() if p_cat == "顯示全部" else personal_data[personal_data['測驗類別'] == p_cat]['項目'].unique()
                p_item = st.selectbox("🎯 篩選檢測項目", ["顯示全部"] + list(p_items), key="p_item")
            df_to_show = personal_data.copy()
            if p_cat != "顯示全部": df_to_show = df_to_show[df_to_show['測驗類別'] == p_cat]
            if p_item != "顯示全部": df_to_show = df_to_show[df_to_show['項目'] == p_item]
            cols = ['座號', '測驗類別', '項目', '成績', '等第/獎牌', '紀錄時間', '備註']
            st.dataframe(df_to_show[[c for c in cols if c in df_to_show.columns]], use_container_width=True)
        else: st.info(f"💡 目前尚未有 {sel_name} 的測驗紀錄。")

    with tab2:
        st.subheader(f"📂 {sel_class} 班級成績彙整")
        class_data = scores_df[scores_df['班級'] == sel_class].copy()
        if not class_data.empty:
            c1, c2 = st.columns(2)
            with c1: cl_cat = st.selectbox("🗂️ 篩選測驗類別", ["顯示全部"] + list(class_data['測驗類別'].unique()), key="cl_cat")
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
        else: st.info(f"💡 目前該班級尚未有任何紀錄。")
    
    with tab3:
        # 新增：常模管理介面 (核心需求)
        st.markdown("### 📝 自定義常模管理中心")
        st.info("💡 您可以直接在下方表格修改各項測驗的評分標準，修改後請按『儲存』。")
        edited_norms = st.data_editor(norms_settings_df, num_rows="dynamic", use_container_width=True, key="norm_editor")
        if st.button("💾 儲存並同步常模設定"):
            conn.update(worksheet="Norms_Settings", data=edited_norms)
            st.success("常模數據已同步！系統現在將套用新規則。"); st.rerun()

        st.divider()
        st.subheader("🛠️ 全校成績重新判定工具")
        stu_info = student_list.set_index('姓名')[['性別', '年齡']].to_dict('index')
        
        # 功能 1: 體適能重算 (改用新引擎)
        st.markdown("### 1. 體適能獎牌重算")
        if st.button("🚀 開始全自動重新判定 (體適能)"):
            with st.spinner("計算中..."):
                updated_count = 0
                for idx, row in scores_df.iterrows():
                    if row['測驗類別'] == "體適能" and row['姓名'] in stu_info:
                        s_info = stu_info[row['姓名']]
                        new_medal = judge_medal(row['項目'], s_info['性別'], s_info['年齡'], row['成績'])
                        scores_df.at[idx, '等第/獎牌'] = new_medal
                        updated_count += 1
                conn.update(worksheet="Scores", data=scores_df.map(clean_numeric_string))
                st.success(f"🎊 完成！共更新 {updated_count} 筆。"); st.rerun()
        
        # 功能 2: 一般術科重算 (改用新引擎)
        st.markdown("### 2. 一般術科分數重算")
        if st.button("🎯 開始全自動重新換算 (術科分數)"):
            with st.spinner("換算中..."):
                updated_count = 0
                for idx, row in scores_df.iterrows():
                    if row['測驗類別'] != "體適能" and row['姓名'] in stu_info:
                        s_info = stu_info[row['姓名']]
                        new_score = judge_subject_score(row['項目'], s_info['性別'], row['成績'])
                        if new_score != "尚未判定":
                            scores_df.at[idx, '等第/獎牌'] = new_score
                            updated_count += 1
                conn.update(worksheet="Scores", data=scores_df.map(clean_numeric_string))
                st.success(f"🎊 完成！共更新 {updated_count} 筆。"); st.rerun()

# --- 7. 複測自動偵測與儲存 (保留原邏輯) ---
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
            updated_df = pd.concat([scores_df, pd.DataFrame([new_data])], ignore_index=True)
        
        conn.update(worksheet="Scores", data=updated_df.map(clean_numeric_string))
        st.balloons(); st.success("✅ 成績紀錄已成功同步！"); st.rerun()

if st.sidebar.button("🚪 登出系統"):
    st.session_state["password_correct"] = False
    st.rerun()
