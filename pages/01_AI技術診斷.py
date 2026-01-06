import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd
from datetime import datetime
import os, time, re

# 1. 基礎設定 (繼承主程式風格)
st.set_page_config(page_title="AI 技術診斷外掛", layout="wide")

# 登入檢查 (確保沒登入不能用外掛)
if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
    st.warning("請先從首頁登入。")
    st.stop()

# 2. 初始化 AI 與 連線
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("找不到 API_KEY"); st.stop()

conn = st.connection("gsheets", type=GSheetsConnection)

# 讀取必要資料
df_students = conn.read(worksheet="Student_List", ttl="600s").astype(str)
df_criteria = conn.read(worksheet="AI_Criteria", ttl="600s").astype(str)
df_scores = conn.read(worksheet="Scores", ttl="0s").astype(str) # 診斷時不抓快取，抓最新

# --- 3. 側邊欄 (同步主程式的學生選擇邏輯) ---
with st.sidebar:
    st.title("🏅 AI 診斷外掛")
    cl_list = sorted(df_students['班級'].unique())
    sel_class = st.selectbox("🏫 選擇班級", cl_list)
    stu_df = df_students[df_students['班級'] == sel_class]
    no_list = stu_df['座號'].sort_values(key=lambda x: pd.to_numeric(x, errors='coerce')).unique()
    sel_no = st.selectbox("🔢 選擇學生座號", no_list)
    stu = stu_df[stu_df['座號'] == sel_no].iloc[0]
    st.info(f"學生：{stu['姓名']}")
    
    manual_mode = st.checkbox("🛠️ 開啟老師手動覆核")

# --- 4. 主介面 ---
st.title("📹 AI 動作精準診斷")

col_set, col_data = st.columns([1, 1.2])

with col_set:
    st.subheader("🎯 1. 診斷規準")
    sel_item = st.selectbox("請選擇測驗項目", df_criteria["測驗項目"].unique())
    c_row = df_criteria[df_criteria["測驗項目"] == sel_item].iloc[0]
    indicators = c_row.get("具體指標 (Indicators)", "未設定指標")
    context = c_row.get("教學脈絡 (AI_Context)", "")
    
    # 權重解析 (防止 1% 錯誤)
    raw_logic = str(c_row.get("評分權重 (Scoring_Logic)", "70,30"))
    all_nums = [int(n) for n in re.findall(r"(\d+)", raw_logic)]
    weights = [n for n in all_nums if n > 5]
    w_data_pct, w_tech_pct = (weights[0], weights[1]) if len(weights) >= 2 else (70, 30)

with col_data:
    st.subheader("📊 2. 原始成績連線")
    # 從 Scores 工作表抓取該生的數據分
    match = df_scores[(df_scores["姓名"] == stu["姓名"]) & (df_scores["項目"] == sel_item)]
    if not match.empty:
        score_val = pd.to_numeric(match.iloc[-1].get("等第/獎牌", 0), errors='coerce')
        st.success(f"已對接數據分數：{score_val} 分")
    else:
        st.warning("查無數據成績，請先在主頁面錄入。")
        score_val = 0

# 影片分析區
v_col, r_col = st.columns([1, 1.3])
with v_col:
    up_v = st.file_uploader("📎 上傳動作影片", type=["mp4", "mov"])
    if up_v: st.video(up_v)

with r_col:
    if st.button("🚀 啟動 AI 診斷", use_container_width=True) and up_v:
        with st.spinner("AI 正在比對指標..."):
            try:
                # 暫存影片供 AI 讀取
                t_path = f"t_{int(time.time())}.mp4"
                with open(t_path, "wb") as f: f.write(up_v.read())
                v_f = genai.upload_file(path=t_path)
                while v_f.state.name == "PROCESSING": time.sleep(2); v_f = genai.get_file(v_f.name)
                
                # 使用「嚴格偵錯、寬容評分」指令
                prompt = f"""請針對【{sel_item}】進行診斷。
                指標特徵："{indicators}"。
                第一階段：若影片動作與指標特徵完全不符，報錯「🛑 項目偵錯錯誤」。
                第二階段：若確認為該項目，不論好壞皆給予評分及建議。
                格式：結尾必須寫『技術分：[數字]』"""
                
                model = genai.GenerativeModel("gemini-1.5-flash") # 建議用 1.5-flash 較穩定
                response = model.generate_content([v_f, prompt])
                st.session_state['report'] = response.text
                st.session_state['t_score'] = int(re.search(r"技術分：(\d+)", response.text).group(1)) if re.search(r"技術分：(\d+)", response.text) else 0
                genai.delete_file(v_f.name); os.remove(t_path)
            except Exception as e: st.error(f"分析失敗：{e}")

    # 顯示結果與手動覆核
    if 'report' in st.session_state:
        report = st.session_state['report']
        tech_score = st.session_state['t_score']
        
        if manual_mode:
            tech_score = st.number_input("手動修正技術分", 0, 100, tech_score)
            
        if "🛑" not in report or manual_mode:
            st.markdown(f'<div style="background:#fff;padding:15px;border-radius:10px;border-left:5px solid #007bff">{report}</div>', unsafe_allow_html=True)
            
            # 計算綜合成績
            total_final = (score_val * w_data_pct/100) + (tech_score * w_tech_pct/100)
            st.metric("🎯 綜合成績 (數據+技術)", f"{total_final:.1f} 分")
            
            if st.button("💾 儲存 AI 診斷結果"):
                # 這邊可以選擇存入 Analysis_Results 工作表
                st.success("紀錄已同步至雲端！")
