# app.py — ג'ירף – איכויות מזון (מעודכן עם Claude AI ומבנה משופר)
from __future__ import annotations
import os
import pandas as pd
import streamlit as st
import altair as alt
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

# Import המודולים החדשים
from config import Config
from database import db_manager
from claude_service import ClaudeAnalysisService

# ===== Google Sheets (אופציונלי) =====
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSHEETS_AVAILABLE = True
except Exception:
    GSHEETS_AVAILABLE = False

# =========================
# ------- SETTINGS --------
# =========================
st.set_page_config(
    page_title="ג'ירף – איכויות מזון", 
    layout="wide",
    page_icon="🦒"
)

# אתחול שירותים
claude_service = ClaudeAnalysisService()

# =========================
# ---------- STYLE --------
# =========================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@300;400;500;700;900&display=swap');

:root{{
  --bg:#ffffff;
  --surface:#ffffff;
  --text:{Config.COLORS['text']};
  --border:{Config.COLORS['border']};
  --green-50:{Config.COLORS['green_50']};
  --tile-green:{Config.COLORS['tile_green']};
  --green-100:#d1fae5;
  --green-500:{Config.COLORS['primary']};
  --amber:{Config.COLORS['amber']};
}}

html, body, .main, .block-container{{direction:rtl; background:var(--bg);}}
.main .block-container{{font-family:"Rubik",-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;}}
body{{ border:4px solid #000; border-radius:16px; margin:10px; }}

/* כותרות */
.header-min{{
  background:var(--green-50);
  border:1px solid #000;
  border-radius:0;
  padding:16px;
  margin-bottom:14px;
  text-align:center;
  box-shadow:0 6px 22px rgba(0,0,0,.04);
}}
.header-landing{{
  background:var(--amber);
  border:1px solid #000;
  border-radius:0;
  padding:16px;
  margin-bottom:14px;
  text-align:center;
  box-shadow:0 6px 22px rgba(0,0,0,.04);
}}
.header-min .title, .header-landing .title{{font-size:26px; font-weight:900; color:#000; margin:0;}}

/* כרטיסים */
.card{{
  background:#fff;
  border:1px solid var(--border);
  border-radius:12px;
  padding:20px;
  margin:16px 0;
  box-shadow:0 4px 12px rgba(0,0,0,.05);
}}

.metric-card{{
  background:linear-gradient(135deg, var(--green-50), #fff);
  border:1px solid var(--green-500);
  border-radius:12px;
  padding:16px;
  text-align:center;
  margin:8px 0;
}}

.metric-value{{
  font-size:24px;
  font-weight:900;
  color:var(--green-500);
  margin:0;
}}

.metric-label{{
  font-size:14px;
  color:#666;
  margin:0;
}}

/* "מנה יומית לבדיקה" */
.daily-pick-login{{
  background:#fff; border:2px solid var(--green-500);
  border-radius:12px; padding:12px 16px;
  display:inline-block; width:min(720px, 92vw); text-align:center;
  margin:16px 0;
}}
.daily-pick-login .ttl{{font-weight:900; color:#065f46; margin:0 0 6px;}}
.daily-pick-login .dish{{font-weight:900; font-size:18px;}}
.daily-pick-login .avg{{color:var(--green-500); font-weight:800;}}

/* Grid 3×3 */
.branch-grid{{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin:20px 0; }}
@media (max-width:480px){{ .branch-grid{{ grid-template-columns:repeat(3,1fr);}} }}

a.branch-card, .branch-card:link, .branch-card:visited, .branch-card:hover, .branch-card:active{{
  color:#000 !important; text-decoration:none !important;
}}
.branch-card{{
  display:flex; align-items:center; justify-content:center;
  background:var(--tile-green);
  border:2px solid #000; border-radius:12px; padding:18px 8px;
  font-weight:900; min-height:64px; user-select:none;
  box-shadow:0 4px 14px rgba(0,0,0,.06);
  transition:transform 0.2s ease;
}}
.branch-card:hover{{
  transform:scale(1.05);
}}

/* מצב נוכחי */
.status-min{{
  display:flex; align-items:center; gap:10px; justify-content:center; 
  background:#fff; border:1px solid var(--border); border-radius:14px; 
  padding:10px 12px; margin:12px 0;
}}
.chip{{
  padding:6px 12px; border:1px solid var(--green-100); border-radius:999px;
  font-weight:800; font-size:12px; color:#065f46; background:var(--green-50);
}}

/* טפסים */
.stTextInput input, .stTextArea textarea{{
  background:#fff !important; color:#000 !important;
  border-radius:12px !important; border:1px solid var(--border) !important; 
  padding:10px 12px !important;
}}
.stTextArea textarea{{min-height:96px !important;}}
.stSelectbox div[data-baseweb="select"]{{
  background:#fff !important; color:#000 !important;
  border-radius:12px !important; border:1px solid var(--border) !important;
}}

/* טבלאות */
table.small {{width:100%; border-collapse:collapse; margin:16px 0;}}
table.small thead tr{{ background:var(--green-50); }}
table.small th, table.small td {{
  border-bottom:1px solid #f1f1f1; padding:8px; font-size:14px; text-align:center;
}}
table.small th {{font-weight:900; color:#000;}}
.num-green{{color:var(--green-500); font-weight:700;}}

/* התראות */
.alert-success{{
  background:#d1fae5; border:1px solid var(--green-500);
  border-radius:8px; padding:12px; margin:8px 0;
  color:#065f46;
}}

.alert-warning{{
  background:#fef3c7; border:1px solid #f59e0b;
  border-radius:8px; padding:12px; margin:8px 0;
  color:#92400e;
}}

/* הסתרת הודעות streamlit */
div[data-testid="stWidgetInstructions"]{{display:none !important;}}

/* כפתורים */
.stButton button{{
  background:var(--green-500) !important;
  color:white !important;
  border:none !important;
  border-radius:8px !important;
  padding:8px 16px !important;
  font-weight:600 !important;
}}
</style>
""", unsafe_allow_html=True)

# =========================
# -------- HELPERS --------
# =========================
def score_hint(x: int) -> str:
    """טקסט מסביר לציון"""
    if x <= 3: return "חלש"
    elif x <= 6: return "סביר"
    elif x <= 8: return "טוב"
    else: return "מצוין"

def last7_days(df: pd.DataFrame) -> pd.DataFrame:
    """נתונים מ-7 ימים אחרונים"""
    if df.empty: 
        return df
    start = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=7)
    return df[df["created_at"] >= start].copy()

def worst_network_dish_last7(df: pd.DataFrame, min_count: int = Config.MIN_DISH_WEEK_M
                             ) -> Tuple[Optional[str], Optional[float], int]:
    """מנה עם הציון הנמוך ביותר ברשת ב-7 ימים"""
    d = last7_days(df)
    if d.empty: 
        return None, None, 0
    g = d.groupby("dish_name").agg(
        n=("id","count"), 
        avg=("overall_score","mean")
    ).reset_index()
    g = g[g["n"] >= min_count]
    if g.empty: 
        return None, None, 0
    row = g.loc[g["avg"].idxmin()]
    return str(row["dish_name"]), float(row["avg"]), int(row["n"])

# =========================
# ------ QUERY PARAMS -----
# =========================
def qp_get(key: str) -> Optional[str]:
    try:
        return st.query_params.get(key)
    except Exception:
        q = st.experimental_get_query_params()
        vals = q.get(key, [])
        return vals[0] if vals else None

def qp_set(**kwargs):
    try:
        st.query_params.clear()
        st.query_params.update(kwargs)
    except Exception:
        st.experimental_set_query_params(**kwargs)

def qp_clear():
    try:
        st.query_params.clear()
    except Exception:
        st.experimental_set_query_params()

def safe_rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass

# =========================
# --- GOOGLE SHEETS -------
# =========================
def save_to_google_sheets(branch: str, chef: str, dish: str, score: int, notes: str, timestamp: str):
    """שמירה לגוגל שיטס"""
    if not GSHEETS_AVAILABLE: 
        return
    
    sheet_id = Config.get_google_sheet_id()
    creds_info = Config.get_service_account_info()
    
    if not (sheet_id and creds_info): 
        return
    
    try:
        credentials = Credentials.from_service_account_info(creds_info, scopes=Config.SCOPES)
        gc = gspread.authorize(credentials)
        gc.open_by_key(sheet_id).sheet1.append_row([timestamp, branch, chef, dish, score, notes or ""])
    except Exception as e:
        st.warning(f"לא ניתן לשמור בגוגל שיטס: {e}")

# =========================
# ------ LANDING ----------
# =========================
def render_landing():
    """עמוד הפתיחה"""
    st.markdown('<div class="header-landing"><p class="title">ג׳ירף – איכויות מזון</p></div>', 
                unsafe_allow_html=True)

    # מנה יומית טרייה
    df_fresh = db_manager.load_quality_checks_fresh()
    dish_name, avg_score, count = worst_network_dish_last7(df_fresh, Config.MIN_DISH_WEEK_M)
    
    if dish_name:
        st.markdown(
            f"""<div class='daily-pick-login'>
            <div class='ttl'>🎯 מנה יומית לבדיקה</div>
            <div class='dish'>{dish_name}</div>
            <div class='avg'>ממוצע רשת (7 ימים): {avg_score:.2f} · בדיקות: {count}</div>
            </div>""",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """<div class='daily-pick-login'>
            <div class='ttl'>🎯 מנה יומית לבדיקה</div>
            <div class='dish'>אין מספיק נתונים</div>
            </div>""",
            unsafe_allow_html=True
        )

    # קוביות בחירת סניף/מטה
    items = ["🏢 מטה"] + [f"🏪 {branch}" for branch in Config.BRANCHES]
    links = "".join([
        f"<a class='branch-card' href='?select={item.split(' ', 1)[1] if ' ' in item else item}'>{item}</a>" 
        for item in items
    ])
    st.markdown(f"<div class='branch-grid'>{links}</div>", unsafe_allow_html=True)

def consume_select_param():
    """טיפול בפרמטר בחירת סניף"""
    sel = qp_get("select")
    if not sel:
        return False
    
    if sel == "מטה":
        st.session_state.auth = {"role": "meta", "branch": None}
    elif sel in Config.BRANCHES:
        st.session_state.auth = {"role": "branch", "branch": sel}
    
    qp_clear()
    safe_rerun()
    return True

def require_auth() -> dict:
    """דרישת אימות"""
    if "auth" not in st.session_state:
        st.session_state.auth = {"role": None, "branch": None}
    
    auth = st.session_state.auth

    if consume_select_param():
        st.stop()

    if not auth["role"]:
        render_landing()
        st.stop()
    
    return auth

# =========================
# -------- MAIN UI --------
# =========================
auth = require_auth()

# כותרת ראשית
st.markdown('<div class="header-min"><p class="title">🦒 ג׳ירף – איכויות מזון</p></div>', 
            unsafe_allow_html=True)

# הצגת מצב נוכחי
chip_text = f"🏪 {auth['branch']}" if auth["role"] == "branch" else "🏢 מטה"
st.markdown(f'<div class="status-min"><span class="chip">{chip_text}</span></div>', 
            unsafe_allow_html=True)

# טעינת נתונים
df = db_manager.load_quality_checks()

# =========================
# ----- FORM SECTION ------
# =========================
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### 📝 הזנת בדיקת איכות")

# בחירת סניף עבור מטה
if auth["role"] == "meta":
    selected_branch = st.selectbox(
        "🏪 בחר סניף להזנה", 
        options=["— בחר סניף —"] + Config.BRANCHES, 
        index=0,
        key="meta_branch_select"
    )
else:
    selected_branch = auth["branch"]

with st.form("quality_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    
    # בחירת טבח
    with col1:
        chef_options = ["— בחר טבח —"]
        if selected_branch and selected_branch != "— בחר סניף —":
            chef_options += Config.CHEFS_BY_BRANCH.get(selected_branch, [])
        chef_choice = st.selectbox("👨‍🍳 טבח מרשימה", options=chef_options, index=0)
    
    with col2:
        chef_manual = st.text_input("👨‍🍳 שם טבח - הקלדה ידנית", value="", placeholder="אופציונלי")

    # בחירת מנה וציון
    col3, col4 = st.columns(2)
    with col3:
        dish = st.selectbox("🍽️ שם המנה *", options=["— בחר מנה —"] + Config.DISHES, index=0)
    
    with col4:
        overall_score = st.selectbox(
            "⭐ ציון כללי *",
            options=["— בחר ציון —"] + list(range(1, 11)),
            index=0,
            format_func=lambda x: f"{x} - {score_hint(x)}" if isinstance(x, int) else x,
        )

    # ציונים מפורטים (אופציונלי)
    st.markdown("#### ציונים מפורטים (אופציונלי)")
    score_cols = st.columns(5)
    
    with score_cols[0]:
        taste_score = st.selectbox("👅 טעם", options=[None] + list(range(1, 11)), index=0)
    with score_cols[1]:
        appearance_score = st.selectbox("👁️ מראה", options=[None] + list(range(1, 11)), index=0)
    with score_cols[2]:
        temperature_score = st.selectbox("🌡️ טמפרטורה", options=[None] + list(range(1, 11)), index=0)
    with score_cols[3]:
        prep_time_score = st.selectbox("⏱️ זמן הכנה", options=[None] + list(range(1, 11)), index=0)
    with score_cols[4]:
        portion_score = st.selectbox("🥄 כמות", options=[None] + list(range(1, 11)), index=0)

    # הערות ושם בודק
    notes = st.text_area("📝 הערות", value="", placeholder="הערות נוספות...")
    reviewer_name = st.text_input("👤 שם הבודק", value="", placeholder="שם הבודק (אופציונלי)")
    
    # כפתור שליחה
    submitted = st.form_submit_button("💾 שמור בדיקה", use_container_width=True)

if submitted:
    # ולידציה
    if auth["role"] == "meta" and (not selected_branch or selected_branch == "— בחר סניף —"):
        st.error("❌ נא לבחור סניף להזנה.")
    else:
        # קביעת שם הטבח הסופי
        chef_final = chef_manual.strip() if chef_manual.strip() else (
            chef_choice if chef_choice != "— בחר טבח —" else None
        )
        
        if not chef_final:
            st.error("❌ נא לבחור טבח מהרשימה או להקליד ידנית.")
        elif not dish or dish == "— בחר מנה —":
            st.error("❌ נא לבחור מנה.")
        elif not isinstance(overall_score, int):
            st.error("❌ נא לבחור ציון כללי.")
        else:
            # שמירה בבסיס הנתונים
            try:
                check_id = db_manager.insert_quality_check(
                    branch=selected_branch,
                    chef_name=chef_final,
                    dish_name=dish,
                    overall_score=int(overall_score),
                    taste_score=taste_score,
                    appearance_score=appearance_score,
                    temperature_score=temperature_score,
                    preparation_time_score=prep_time_score,
                    portion_size_score=portion_score,
                    notes=notes,
                    submitted_by=auth["role"],
                    reviewer_name=reviewer_name.strip() or None
                )
                
                # שמירה לגוגל שיטס
                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    save_to_google_sheets(selected_branch, chef_final, dish, int(overall_score), notes, timestamp)
                except Exception as e:
                    st.warning(f"⚠️ נשמר מקומית, אך לא לגיליון: {e}")
                
                # ניקוי cache ורענון
                db_manager.clear_cache()
                st.success(f"✅ בדיקה נשמרה בהצלחה! מספר בדיקה: {check_id}")
                
                # רישום פעילות
                db_manager.log_activity(
                    user_id=None, 
                    action=f"הוספת בדיקת איכות - {dish} - {chef_final}",
                    table_name="quality_checks",
                    record_id=check_id
                )
                
            except Exception as e:
                st.error(f"❌ שגיאה בשמירת הבדיקה: {e}")

st.markdown('</div>', unsafe_allow_html=True)

# =========================
# ----- ANALYTICS ---------
# =========================
if not df.empty:
    # KPI Cards
    if auth["role"] == "meta":
        st.markdown("### 📊 KPI רשת - 7 ימים אחרונים")
        
        recent_df = last7_days(df)
        if not recent_df.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_checks = len(recent_df)
                st.markdown(f"""
                <div class="metric-card">
                    <p class="metric-value">{total_checks}</p>
                    <p class="metric-label">בדיקות השבוע</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                avg_score = recent_df['overall_score'].mean()
                st.markdown(f"""
                <div class="metric-card">
                    <p class="metric-value">{avg_score:.1f}</p>
                    <p class="metric-label">ממוצע רשת</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                active_branches = recent_df['branch'].nunique()
                st.markdown(f"""
                <div class="metric-card">
                    <p class="metric-value">{active_branches}</p>
                    <p class="metric-label">סניפים פעילים</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                low_scores = len(recent_df[recent_df['overall_score'] <= 6])
                st.markdown(f"""
                <div class="metric-card">
                    <p class="metric-value">{low_scores}</p>
                    <p class="metric-label">ציונים נמוכים</p>
                </div>
                """, unsafe_allow_html=True)

# =========================
# ----- CLAUDE AI ---------
# =========================
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### 🤖 ניתוח חכם עם Claude AI")

if claude_service.is_available():
    analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs(
        ["📈 ניתוח מגמות", "❓ שאלות מותאמות", "📋 דוח שבועי"]
    )
    
    with analysis_tab1:
        st.markdown("#### ניתוח מגמות איכות אוטומטי")
        if st.button("🚀 הפעל ניתוח מגמות", key="trends_analysis"):
            if not df.empty:
                with st.spinner("🔍 Claude מנתח את הנתונים..."):
                    analysis = claude_service.analyze_quality_trends(df)
                st.markdown("##### 📊 תוצאות הניתוח:")
                st.write(analysis)
            else:
                st.info("ℹ️ אין מספיק נתונים לניתוח")
    
    with analysis_tab2:
        st.markdown("#### שאל את Claude על הנתונים")
        user_question = st.text_input(
            "💬 מה תרצה לדעת על נתוני האיכות?", 
            value="", 
            placeholder="לדוגמה: איזה סניף הכי טוב השבוע? מה הבעיות העיקריות במנות?"
        )
        
        if st.button("🎯 שלח שאלה", key="custom_question"):
            if not df.empty and user_question.strip():
                with st.spinner("🤔 Claude חושב על התשובה..."):
                    answer = claude_service.answer_custom_question(df, user_question)
                st.markdown("##### 💡 תשובת Claude:")
                st.write(answer)
            elif df.empty:
                st.warning("⚠️ אין נתונים לניתוח כרגע.")
            else:
                st.warning("⚠️ נא להזין שאלה.")
    
    with analysis_tab3:
        st.markdown("#### דוח שבועי מפורט")
        report_branch = None
        if auth["role"] == "branch":
            report_branch = auth["branch"]
        elif auth["role"] == "meta":
            report_branch = st.selectbox(
                "בחר סניף לדוח (או השאר ריק לדוח כלל רשת)", 
                options=["כל הרשת"] + Config.BRANCHES, 
                index=0
            )
            if report_branch == "כל הרשת":
                report_branch = None
        
        if st.button("📋 צור דוח שבועי", key="weekly_report"):
            if not df.empty:
                with st.spinner("📝 יוצר דוח מפורט..."):
                    report = claude_service.generate_weekly_report(df, report_branch)
                st.markdown("##### 📄 הדוח השבועי:")
                st.write(report)
            else:
                st.info("ℹ️ אין מספיק נתונים לדוח")

else:
    st.warning("⚠️ שירות Claude אינו זמין. נא להגדיר ANTHROPIC_API_KEY בהגדרות.")

st.markdown('</div>', unsafe_allow_html=True)

# =========================
# ----- DATA DISPLAY ------
# =========================
if not df.empty:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📋 בדיקות אחרונות")
    
    # פילטרים
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        branch_filter = st.selectbox(
            "סנן לפי סניף:", 
            options=["הכל"] + sorted(df['branch'].unique().tolist()),
            index=0
        )
    
    with filter_col2:
        days_filter = st.selectbox(
            "תקופה:", 
            options=["7 ימים", "30 ימים", "כל הנתונים"],
            index=0
        )
    
    with filter_col3:
        score_filter = st.selectbox(
            "סנן לפי ציון:",
            options=["הכל", "מעולה (9-10)", "טוב (7-8)", "סביר (5-6)", "חלש (1-4)"],
            index=0
        )
    
    # יישום פילטרים
    filtered_df = df.copy()
    
    if branch_filter != "הכל":
        filtered_df = filtered_df[filtered_df['branch'] == branch_filter]
    
    if days_filter == "7 ימים":
        filtered_df = last7_days(filtered_df)
    elif days_filter == "30 ימים":
        month_ago = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=30)
        filtered_df = filtered_df[filtered_df['created_at'] >= month_ago]
    
    if score_filter != "הכל":
        if score_filter == "מעולה (9-10)":
            filtered_df = filtered_df[filtered_df['overall_score'] >= 9]
        elif score_filter == "טוב (7-8)":
            filtered_df = filtered_df[(filtered_df['overall_score'] >= 7) & (filtered_df['overall_score'] <= 8)]
        elif score_filter == "סביר (5-6)":
            filtered_df = filtered_df[(filtered_df['overall_score'] >= 5) & (filtered_df['overall_score'] <= 6)]
        elif score_filter == "חלש (1-4)":
            filtered_df = filtered_df[filtered_df['overall_score'] <= 4]
    
    # הצגת הנתונים
    if not filtered_df.empty:
        # הכנת הנתונים לתצוגה
        display_df = filtered_df[['created_at', 'branch', 'chef_name', 'dish_name', '
