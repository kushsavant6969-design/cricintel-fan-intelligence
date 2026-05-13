"""
CricIntel Fan Intelligence
Cricket fan segmentation and intelligence platform for county cricket clubs.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import io, random, os
from fpdf import FPDF
from generate_sample import generate_sample_data

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CricIntel Fan Intelligence",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

[data-testid="stAppViewContainer"] { background: #0A0A0A !important; }
[data-testid="stHeader"]           { background: #0A0A0A !important; border-bottom: 1px solid #1A2E0A; }
section[data-testid="stSidebar"]   { display: none; }
.block-container { padding: 0 2rem 2rem !important; max-width: 100% !important; }

/* ── Tabs ── */
[data-testid="stTabs"] > div:first-child { border-bottom: 2px solid #2D5016; }
button[data-baseweb="tab"] {
    color: #888 !important; font-size: 13px !important; font-weight: 500 !important;
    padding: 10px 20px !important; border-radius: 6px 6px 0 0 !important;
    border: none !important; background: transparent !important;
}
button[data-baseweb="tab"]:hover { color: #C9A84C !important; }
button[data-baseweb="tab"][aria-selected="true"] {
    color: #C9A84C !important; border-bottom: 2px solid #C9A84C !important;
    background: #0F1F06 !important; font-weight: 700 !important;
}
[data-testid="stTabsContent"] { padding-top: 1.5rem !important; }

/* ── Inputs ── */
[data-testid="stTextInput"] input, [data-testid="stSelectbox"] > div > div,
.stMultiSelect > div > div {
    background: #1A1A1A !important; color: #FFF !important;
    border: 1px solid #2D5016 !important; border-radius: 6px !important;
}
[data-testid="stFileUploader"] {
    background: #111 !important; border: 1px dashed #2D5016 !important;
    border-radius: 8px !important; padding: 1rem !important;
}
[data-testid="stFileUploader"] label { color: #C9A84C !important; }

/* ── Buttons ── */
[data-testid="stDownloadButton"] > button, [data-testid="stButton"] > button {
    background: #2D5016 !important; color: #FFF !important;
    border: 1px solid #3D7020 !important; border-radius: 6px !important;
    font-weight: 600 !important; padding: 8px 20px !important;
}
[data-testid="stDownloadButton"] > button:hover, [data-testid="stButton"] > button:hover {
    background: #3D7020 !important; border-color: #C9A84C !important; color: #C9A84C !important;
}

/* ── DataFrames ── */
[data-testid="stDataFrame"] { background: #1A1A1A !important; border-radius: 8px !important; }

/* ── Warnings / info ── */
[data-testid="stAlert"] { border-radius: 8px !important; }

/* ── Expander ── */
details { background: #1A1A1A !important; border: 1px solid #2D5016 !important; border-radius: 8px !important; }
summary { color: #C9A84C !important; font-weight: 600 !important; }

/* ── Misc ── */
hr { border-color: #222 !important; }
label { color: #AAA !important; font-size: 12px !important; }
h1, h2, h3, h4 { color: #FFF !important; }
p, li { color: #CCC !important; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
PRIMARY  = "#2D5016"
ACCENT   = "#C9A84C"
BG       = "#0A0A0A"
CARD     = "#1A1A1A"
RED      = "#E74C3C"
ORANGE   = "#E67E22"
BLUE     = "#3498DB"

SEGMENT_COLORS = {
    "Loyal Members":  "#C9A84C",
    "High Potential": "#27AE60",
    "Win Back":       "#E74C3C",
    "Dormant":        "#555555",
    "Casual":         "#3498DB",
}

MEMBERSHIP_ORDER   = ["None", "Associate", "Full Member", "Life Member", "Surrey & England"]
MEMBERSHIP_WEIGHTS = {"None": 0, "Associate": 20, "Full Member": 50, "Life Member": 80, "Surrey & England": 100}
MEM_LTV            = {"None": 400, "Associate": 800, "Full Member": 1600, "Life Member": 2500, "Surrey & England": 4000}

CORE_COLUMNS = [
    "Fan_ID", "Age", "Gender", "County", "Membership_Category", "Fan_Type",
    "HAS_APP", "Email_Opens", "Email_Clicks", "Email_Campaigns_Received",
    "InApp_Opens", "InApp_Clicks", "InApp_Campaigns_Received",
    "Article_Views", "Ticket_Purchases", "Membership_Purchases",
    "Retail_Purchases", "Total_Revenue", "First_Purchase_Date",
    "Last_Purchase_Date", "First_App_Open", "Last_App_Open",
    "First_Email_Open", "Last_Email_Open", "Join_Date",
    "Match_Type_Preference", "Attendance_Frequency",
]

SEGMENT_INSIGHTS = {
    "Loyal Members": {
        "desc": "Long-tenure members with high commercial value and strong loyalty — your most valuable fans.",
        "action": "Retain & reward",
        "tactics": [
            "Exclusive member benefits and early ticket access windows",
            "Personal thank-you comms from club management each season",
            "Member-only events: net sessions, meet-the-players evenings",
            "Annual loyalty recognition awards and milestone celebrations",
        ],
    },
    "High Potential": {
        "desc": "Highly engaged fans not yet on a paid membership — your single biggest upgrade opportunity.",
        "action": "Convert to membership",
        "tactics": [
            "Targeted membership upgrade campaigns with limited-time offers",
            "Personalised email journeys showcasing exclusive member benefits",
            "Trial member experiences at select County Championship fixtures",
            "Friends-and-family referral incentives for membership sign-up",
        ],
    },
    "Win Back": {
        "desc": "Previously active fans who have gone quiet — high churn risk but recoverable with the right approach.",
        "action": "Re-engage immediately",
        "tactics": [
            "Win-back email series with exclusive re-engagement offers",
            "Discounted match ticket offer to bring them back to the ground",
            "Personal outreach calls for high-value lapsed members",
            "Season highlight content to reignite emotional connection",
        ],
    },
    "Dormant": {
        "desc": "Low activity across all channels — require significant re-activation effort.",
        "action": "Low-cost reactivation",
        "tactics": [
            "Free-to-attend community events and open days at the ground",
            "Season preview content and squad announcements to spark interest",
            "Short survey to understand barriers to re-engagement",
            "Complimentary family ticket to a low-demand fixture",
        ],
    },
    "Casual": {
        "desc": "Moderate engagement, infrequent attendees — fans with growth potential who need a stronger hook.",
        "action": "Build habit and frequency",
        "tactics": [
            "Match day reminder push notifications and email nudges",
            "Group and family ticket packages to increase attendance",
            "Gamification: loyalty points for attendance streaks",
            "Behind-the-scenes content to deepen emotional connection",
        ],
    },
}

SPONSOR_CATEGORIES = [
    {
        "category": "Sports Equipment",
        "brands": "Gray-Nicolls, Kookaburra, New Balance Cricket",
        "rationale": "High Avid/Family fan base with strong match attendance — premium product resonance.",
    },
    {
        "category": "Financial Services",
        "brands": "Barclays, Vitality, NatWest",
        "rationale": "35-60 age demographic dominance and Life/Full Member affluence aligns with FS targeting.",
    },
    {
        "category": "Travel & Hospitality",
        "brands": "National Express, Premier Inn, Expedia",
        "rationale": "Multi-county fan base with regular away-day travel and hospitality interest.",
    },
    {
        "category": "Tech & Media",
        "brands": "Sky Sports, BT Sport, AWS",
        "rationale": "High app adoption and digital engagement signals a tech-receptive audience.",
    },
    {
        "category": "Food & Beverage",
        "brands": "Greene King, Heineken, Pimm's",
        "rationale": "Matchday hospitality interest and attendance frequency justify premium F&B partnership.",
    },
]

TODAY_DT = datetime(2026, 5, 6)

# ── Helpers ────────────────────────────────────────────────────────────────────
def _pdf_safe(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    replacements = {
        "—": "-", "–": "-", "‘": "'", "’": "'",
        "“": '"', "”": '"', "•": "-", "…": "...",
        "°": "deg", "£": "GBP",
    }
    for ch, rep in replacements.items():
        text = text.replace(ch, rep)
    return text


def dark_layout(**extra):
    base = dict(
        plot_bgcolor=CARD, paper_bgcolor=BG,
        font=dict(color="#FFFFFF", family="Inter, sans-serif"),
        xaxis=dict(gridcolor="#2A2A2A", zerolinecolor="#333"),
        yaxis=dict(gridcolor="#2A2A2A", zerolinecolor="#333"),
        legend=dict(bgcolor=CARD, bordercolor="#333"),
        margin=dict(l=40, r=20, t=40, b=40),
    )
    base.update(extra)
    return base


def metric_card(label: str, value: str, sub: str = "", color: str = ACCENT) -> str:
    sub_html = f'<div style="font-size:11px;color:#888;margin-top:4px">{sub}</div>' if sub else ""
    return f"""
    <div style="background:{CARD};border:1px solid {PRIMARY};border-radius:10px;
                padding:18px 20px;text-align:center;height:100%">
        <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px">{label}</div>
        <div style="font-size:30px;font-weight:800;color:{color};line-height:1.1">{value}</div>
        {sub_html}
    </div>"""


def segment_badge(seg: str) -> str:
    c = SEGMENT_COLORS.get(seg, "#888")
    return f'<span style="background:{c}22;color:{c};border:1px solid {c};border-radius:4px;padding:2px 8px;font-size:11px;font-weight:600">{seg}</span>'


def churn_badge(level: str) -> str:
    colors = {"HIGH": RED, "MED": ORANGE, "LOW": "#27AE60"}
    c = colors.get(str(level), "#888")
    return f'<span style="color:{c};font-weight:700">{level}</span>'


def age_group(age: int) -> str:
    if age < 18:   return "Under 18"
    if age < 30:   return "18-29"
    if age < 45:   return "30-44"
    if age < 60:   return "45-59"
    return "60+"

AGE_GROUP_ORDER = ["Under 18", "18-29", "30-44", "45-59", "60+"]

# ── Schema validation ─────────────────────────────────────────────────────────
def validate_schema(df: pd.DataFrame):
    cols = set(df.columns)
    core = set(CORE_COLUMNS)
    present  = core & cols
    missing  = core - cols
    extra    = cols - core
    if not missing:
        level = "full"
    elif present:
        level = "partial"
    else:
        level = "custom"
    return level, sorted(present), sorted(missing), sorted(extra)


def fuzzy_match_columns(upload_cols, missing_core):
    """Return {core_col: [candidate_cols]} for similar-looking column names."""
    candidates = {}
    for mc in missing_core:
        mc_norm = mc.lower().replace("_", "")
        matches = []
        for uc in upload_cols:
            uc_norm = uc.lower().replace("_", "").replace(" ", "")
            if mc_norm in uc_norm or uc_norm in mc_norm:
                matches.append(uc)
        if matches:
            candidates[mc] = matches
    return candidates

# ── Scoring engine ────────────────────────────────────────────────────────────
def compute_scores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Parse dates
    for col in ["Last_Purchase_Date", "Last_App_Open", "Last_Email_Open", "Join_Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    def days_since(col, fallback=500):
        if col not in df.columns:
            return np.full(len(df), fallback, dtype=float)
        return (TODAY_DT - df[col]).dt.days.clip(lower=0).fillna(fallback).astype(float)

    ds_purchase = days_since("Last_Purchase_Date", 1000)
    ds_app      = np.where(
        df.get("HAS_APP", pd.Series(["No"] * len(df))) == "Yes",
        days_since("Last_App_Open", 500), 500.0
    ).astype(float)
    ds_email  = days_since("Last_Email_Open", 500)
    tenure_d  = days_since("Join_Date", 365) * -1 + 365  # invert: longer tenure → smaller days_since
    # Re-compute tenure as (TODAY - Join_Date).days
    if "Join_Date" in df.columns:
        tenure_d = (TODAY_DT - df["Join_Date"]).dt.days.clip(lower=0).fillna(365).astype(float)
    else:
        tenure_d = np.full(len(df), 365 * 5, dtype=float)

    def safe_rate(num_col, den_col, has_app_filter=False):
        if num_col not in df.columns or den_col not in df.columns:
            return np.zeros(len(df))
        den = df[den_col].astype(float).replace(0, np.nan)
        rate = (df[num_col].astype(float) / den).fillna(0).clip(0, 1).values
        if has_app_filter and "HAS_APP" in df.columns:
            rate = np.where(df["HAS_APP"] == "Yes", rate, 0.0)
        return rate

    email_click_rate  = safe_rate("Email_Clicks", "Email_Campaigns_Received")
    inapp_click_rate  = safe_rate("InApp_Clicks",  "InApp_Campaigns_Received", has_app_filter=True)
    email_open_rate   = safe_rate("Email_Opens",   "Email_Campaigns_Received")
    inapp_open_rate   = safe_rate("InApp_Opens",   "InApp_Campaigns_Received", has_app_filter=True)

    article_norm = (df.get("Article_Views", pd.Series(0, index=df.index)).astype(float) / 300).clip(0, 1).values
    app_recency  = np.where(
        df.get("HAS_APP", pd.Series("No", index=df.index)) == "Yes",
        np.clip(1 - ds_app / 365, 0, 1), 0.3
    )
    att_norm = (df.get("Attendance_Frequency", pd.Series(0, index=df.index)).astype(float) / 25).clip(0, 1).values

    # ── Engagement Score ──────────────────────────────────────────────────────
    engagement = (
        email_click_rate * 25
        + inapp_click_rate * 20
        + article_norm     * 20
        + app_recency      * 20
        + att_norm         * 15
    )
    df["Engagement_Score"] = engagement.round(1)

    # ── Commercial Score ──────────────────────────────────────────────────────
    rev_norm = (df.get("Total_Revenue", pd.Series(0, index=df.index)).astype(float) / 3000).clip(0, 1).values
    purch_ct = (
        df.get("Ticket_Purchases",     pd.Series(0, index=df.index)).astype(float)
        + df.get("Membership_Purchases", pd.Series(0, index=df.index)).astype(float)
        + df.get("Retail_Purchases",     pd.Series(0, index=df.index)).astype(float)
    ).values
    purch_norm = np.clip(purch_ct / 30, 0, 1)
    purch_rec  = np.clip(1 - ds_purchase / 730, 0, 1)
    mem_wt     = df.get("Membership_Category", pd.Series("None", index=df.index)).map(
        MEMBERSHIP_WEIGHTS).fillna(0).values / 100

    commercial = (
        rev_norm    * 40
        + purch_norm * 30
        + purch_rec  * 20
        + mem_wt     * 10
    )
    df["Commercial_Score"] = commercial.round(1)

    # ── Loyalty Score ─────────────────────────────────────────────────────────
    tenure_norm = np.clip(tenure_d / (365 * 10), 0, 1)
    sustained   = (email_click_rate * 0.5 + inapp_click_rate * 0.5)
    loyalty = (
        tenure_norm * 30
        + mem_wt    * 30
        + sustained * 20
        + att_norm  * 20
    )
    df["Loyalty_Score"] = loyalty.round(1)

    # ── Churn Risk (raw, then percentile-calibrated) ──────────────────────────
    pur_risk   = np.clip(ds_purchase / 730, 0, 1) * 35
    app_risk   = np.where(
        df.get("HAS_APP", pd.Series("No", index=df.index)) == "Yes",
        np.clip(ds_app / 365, 0, 1) * 25, 0.5 * 25
    )
    email_risk = np.clip(ds_email / 365, 0, 1) * 25
    eng_inv    = (1 - engagement / 100) * 15
    churn_raw  = pur_risk + app_risk + email_risk + eng_inv

    p33 = np.percentile(churn_raw, 33)
    p67 = np.percentile(churn_raw, 67)
    df["Churn_Risk_Score"] = churn_raw.round(1)
    df["Churn_Risk_Label"] = pd.cut(
        churn_raw, bins=[-np.inf, p33, p67, np.inf], labels=["LOW", "MED", "HIGH"]
    ).astype(str)

    # ── Conversion Probability ────────────────────────────────────────────────
    email_eng_pts = email_open_rate * 25
    inapp_eng_pts = inapp_open_rate * 25
    mem_gap_pts   = (1 - mem_wt) * 30
    conv_comm_pts = commercial / 100 * 20
    conversion = email_eng_pts + inapp_eng_pts + mem_gap_pts + conv_comm_pts
    df["Conversion_Score"] = conversion.round(1)

    # ── Composite ─────────────────────────────────────────────────────────────
    df["Composite_Score"] = (
        engagement  * 0.25
        + commercial * 0.30
        + loyalty    * 0.25
        + (100 - churn_raw) * 0.10
        + conversion * 0.10
    ).round(1)

    return df


# ── Segmentation & journey ────────────────────────────────────────────────────
def assign_segments(df: pd.DataFrame) -> pd.DataFrame:
    # Compute percentile thresholds so segmentation adapts to any score distribution
    p65_l = np.percentile(df["Loyalty_Score"],    65)
    p55_c = np.percentile(df["Commercial_Score"], 55)
    p50_e = np.percentile(df["Engagement_Score"], 50)
    p40_e = np.percentile(df["Engagement_Score"], 40)
    p35_c = np.percentile(df["Commercial_Score"], 35)
    p20_e = np.percentile(df["Engagement_Score"], 20)
    p20_c = np.percentile(df["Commercial_Score"], 20)

    def _seg(row):
        e, c, l = row["Engagement_Score"], row["Commercial_Score"], row["Loyalty_Score"]
        churn = row["Churn_Risk_Label"]
        mem   = row.get("Membership_Category", "None")
        # Loyal: strong loyalty + commercial + premium membership
        if l >= p65_l and c >= p55_c and mem in ("Life Member", "Surrey & England"):
            return "Loyal Members"
        # High Potential: above-median engagement but below-average commercial
        if e >= p50_e and c <= p35_c:
            return "High Potential"
        # Dormant: very low on both (checked before Win Back so truly inactive aren't misclassified)
        if e <= p20_e and c <= p20_c:
            return "Dormant"
        # Win Back: HIGH churn + below-average engagement or commercial
        if churn == "HIGH" and (e < p40_e or c < p35_c):
            return "Win Back"
        return "Casual"

    df["Segment"] = df.apply(_seg, axis=1)
    return df


def assign_journey_stage(df: pd.DataFrame) -> pd.DataFrame:
    def _stage(row):
        mem = row.get("Membership_Category", "None")
        e   = row["Engagement_Score"]
        if mem == "Surrey & England":  return 5
        if mem in ("Full Member", "Life Member"): return 4
        if mem == "Associate":          return 3
        if e >= 40:                     return 2
        return 1
    df["Journey_Stage"] = df.apply(_stage, axis=1)
    return df


def assign_channel(df: pd.DataFrame) -> pd.DataFrame:
    def _ch(row):
        has_email = row.get("Email_Opens", 0) > 0
        has_inapp = row.get("HAS_APP", "No") == "Yes" and row.get("InApp_Opens", 0) > 0
        if has_email and has_inapp: return "Both"
        if has_email:               return "Email"
        if has_inapp:               return "App"
        return "Neither"
    df["Channel_Preference"] = df.apply(_ch, axis=1)
    return df


def process_data(df: pd.DataFrame) -> pd.DataFrame:
    df = compute_scores(df)
    df = assign_segments(df)
    df = assign_journey_stage(df)
    df = assign_channel(df)
    if "Age" in df.columns:
        df["Age_Group"] = df["Age"].apply(age_group)
    return df

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Upload & Configure
# ══════════════════════════════════════════════════════════════════════════════
def render_upload_tab():
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{PRIMARY},{CARD});'
        f'padding:24px 30px;border-bottom:2px solid {ACCENT};margin:-16px -32px 24px">'
        f'<span style="font-size:28px;font-weight:800;color:{ACCENT}">🏏 CricIntel Fan Intelligence</span>'
        f'<span style="color:#888;font-size:13px;margin-left:16px">County Cricket Fan Segmentation Platform</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    col_up, col_conf = st.columns([3, 2], gap="large")

    with col_up:
        st.markdown(f'<div style="color:{ACCENT};font-weight:700;font-size:14px;margin-bottom:8px">UPLOAD FAN DATA</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload CSV file", type=["csv"], label_visibility="collapsed", key="file_uploader")

        # Template download
        tpl_df = generate_sample_data(5)
        tpl_csv = tpl_df.to_csv(index=False).encode()
        st.download_button(
            "⬇ Download CSV Template (5-row sample)",
            data=tpl_csv,
            file_name="cricintel_fan_template.csv",
            mime="text/csv",
            key="dl_template",
        )

        if uploaded:
            try:
                raw_df = pd.read_csv(uploaded)
                st.success(f"Loaded {len(raw_df):,} rows, {len(raw_df.columns)} columns.")

                level, present, missing, extra = validate_schema(raw_df)
                st.session_state["extra_cols"] = extra

                # Column mapping UI
                mapping = {}
                if level in ("partial", "custom") and missing:
                    fuzzy = fuzzy_match_columns(list(raw_df.columns), missing)
                    if fuzzy:
                        with st.expander("🔄 Column Mapping — similar names detected"):
                            for core_col, candidates in fuzzy.items():
                                opts = ["(skip)"] + candidates
                                choice = st.selectbox(f"Map `{core_col}` →", opts, key=f"map_{core_col}")
                                if choice != "(skip)":
                                    mapping[choice] = core_col

                if mapping:
                    raw_df = raw_df.rename(columns=mapping)
                    level, present, missing, extra = validate_schema(raw_df)

                if level == "full":
                    st.success("All core columns detected. Full dashboard unlocked.")
                elif level == "partial":
                    st.warning(
                        f"Partial match — {len(missing)} columns missing: "
                        + ", ".join(f"`{c}`" for c in missing)
                        + ". Some scores will be estimated."
                    )
                else:
                    st.info("Custom-only schema detected. Custom Metrics Explorer will be shown in the Report tab.")

                df_proc = process_data(raw_df)
                st.session_state["df"]         = df_proc
                st.session_state["match_level"]= level
                st.session_state["missing_cols"]= missing
                st.session_state["extra_cols"] = extra

            except Exception as exc:
                st.error(f"Could not read file: {exc}")

    with col_conf:
        st.markdown(f'<div style="color:{ACCENT};font-weight:700;font-size:14px;margin-bottom:8px">CONFIGURE</div>', unsafe_allow_html=True)
        club_name = st.text_input("Club Name", value=st.session_state.get("club_name", "Surrey CCC"), key="club_name_input")
        county_format = st.selectbox(
            "Primary Competition",
            ["County Championship", "T20 Blast", "The Hundred"],
            key="county_format_sel",
        )
        st.session_state["club_name"]     = club_name
        st.session_state["county_format"] = county_format

        if "df" in st.session_state:
            st.markdown("---")
            st.markdown(f'<div style="color:{ACCENT};font-weight:700;font-size:13px;margin-bottom:8px">QUICK SUMMARY</div>', unsafe_allow_html=True)
            df = st.session_state["df"]
            seg_counts = df["Segment"].value_counts()
            for seg, cnt in seg_counts.items():
                c = SEGMENT_COLORS.get(seg, "#888")
                pct = cnt / len(df) * 100
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #1A1A1A">'
                    f'<span style="color:{c};font-size:12px">{seg}</span>'
                    f'<span style="color:#888;font-size:12px">{cnt:,} ({pct:.0f}%)</span></div>',
                    unsafe_allow_html=True,
                )

    # Load sample data
    if "df" not in st.session_state:
        st.markdown("---")
        st.markdown(f'<div style="color:#666;text-align:center;padding:12px">No file uploaded yet.</div>', unsafe_allow_html=True)
        if st.button("Load 500-row sample dataset", key="load_sample"):
            df_sample = generate_sample_data(500)
            df_proc = process_data(df_sample)
            st.session_state["df"]          = df_proc
            st.session_state["club_name"]   = "Surrey CCC"
            st.session_state["county_format"] = "County Championship"
            st.session_state["match_level"] = "full"
            st.session_state["missing_cols"]= []
            st.session_state["extra_cols"]  = [
                "Favourite_Player", "Preferred_Stand", "Travel_Method",
                "Season_Ticket_Years", "Hospitality_Interest", "Corporate_Package",
            ]
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Fan Dashboard
# ══════════════════════════════════════════════════════════════════════════════
def render_dashboard_tab(df: pd.DataFrame, club_name: str):
    # County filter
    counties = ["All"] + sorted(df["County"].dropna().unique().tolist()) if "County" in df.columns else ["All"]
    sel_county = st.selectbox("Filter by County/Region", counties, key="dash_county_filter")
    if sel_county != "All" and "County" in df.columns:
        df = df[df["County"] == sel_county]

    st.markdown(f"### {club_name} — Fan Dashboard ({len(df):,} fans)")

    # ── Hero metrics ──────────────────────────────────────────────────────────
    h1, h2, h3, h4, h5 = st.columns(5, gap="small")
    high_churn   = (df["Churn_Risk_Label"] == "HIGH").sum()
    conv_cands   = df["Journey_Stage"].isin([2, 3]).sum()
    with h1: st.markdown(metric_card("Total Fans",          f"{len(df):,}"),                                   unsafe_allow_html=True)
    with h2: st.markdown(metric_card("Avg Engagement",      f"{df['Engagement_Score'].mean():.1f}"),           unsafe_allow_html=True)
    with h3: st.markdown(metric_card("Avg Commercial",      f"{df['Commercial_Score'].mean():.1f}"),           unsafe_allow_html=True)
    with h4: st.markdown(metric_card("High Churn Risk",     f"{high_churn:,}",  color=RED),                   unsafe_allow_html=True)
    with h5: st.markdown(metric_card("Conversion Candidates", f"{conv_cands:,}", color="#27AE60"),             unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 1: Segment donut + Age×Segment ───────────────────────────────────
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        seg_vc = df["Segment"].value_counts().reset_index()
        seg_vc.columns = ["Segment", "Count"]
        fig = px.pie(seg_vc, names="Segment", values="Count",
                     color="Segment", color_discrete_map=SEGMENT_COLORS,
                     hole=0.55, title="Fan Segment Distribution")
        fig.update_layout(**dark_layout(title_font_color=ACCENT))
        st.plotly_chart(fig, use_container_width=True, key="dash_seg_donut")

    with c2:
        if "Age_Group" in df.columns:
            ag_seg = df.groupby(["Age_Group", "Segment"]).size().reset_index(name="Count")
            fig = px.bar(ag_seg, x="Age_Group", y="Count", color="Segment",
                         color_discrete_map=SEGMENT_COLORS, barmode="stack",
                         category_orders={"Age_Group": AGE_GROUP_ORDER},
                         title="Age Group × Segment")
            fig.update_layout(**dark_layout(title_font_color=ACCENT))
            st.plotly_chart(fig, use_container_width=True, key="dash_age_seg")

    # ── Row 2: Scatter + Average scores by segment ────────────────────────────
    c3, c4 = st.columns(2, gap="medium")
    with c3:
        fig = px.scatter(df, x="Engagement_Score", y="Commercial_Score",
                         color="Loyalty_Score", color_continuous_scale=[[0, "#1A1A1A"], [0.5, PRIMARY], [1, ACCENT]],
                         hover_data=["Fan_ID", "Segment", "Membership_Category"] if "Fan_ID" in df.columns else ["Segment"],
                         title="Fan Landscape — Engagement vs Commercial (colour = Loyalty)")
        fig.update_layout(**dark_layout(title_font_color=ACCENT,
                                        coloraxis_colorbar=dict(bgcolor=CARD, tickfont=dict(color="#FFF"))))
        st.plotly_chart(fig, use_container_width=True, key="dash_scatter")

    with c4:
        score_cols = ["Engagement_Score", "Commercial_Score", "Loyalty_Score", "Conversion_Score"]
        avg_by_seg = df.groupby("Segment")[score_cols].mean().reset_index()
        avg_melt   = avg_by_seg.melt(id_vars="Segment", var_name="Score", value_name="Value")
        avg_melt["Score"] = avg_melt["Score"].str.replace("_Score", "")
        fig = px.bar(avg_melt, x="Segment", y="Value", color="Score",
                     barmode="group", title="Average Scores by Segment",
                     color_discrete_sequence=[ACCENT, PRIMARY, "#3498DB", "#27AE60"])
        fig.update_layout(**dark_layout(title_font_color=ACCENT))
        st.plotly_chart(fig, use_container_width=True, key="dash_avg_scores")

    # ── Row 3: Commercial by segment + Radar ─────────────────────────────────
    c5, c6 = st.columns(2, gap="medium")
    with c5:
        comm_seg = df.groupby("Segment")["Commercial_Score"].mean().reset_index().sort_values("Commercial_Score")
        fig = px.bar(comm_seg, x="Commercial_Score", y="Segment", orientation="h",
                     color="Segment", color_discrete_map=SEGMENT_COLORS,
                     title="Commercial Score by Segment")
        fig.update_layout(**dark_layout(title_font_color=ACCENT, showlegend=False))
        st.plotly_chart(fig, use_container_width=True, key="dash_comm_seg")

    with c6:
        if "Age_Group" in df.columns:
            radar_cols = ["Engagement_Score", "Commercial_Score", "Loyalty_Score", "Conversion_Score"]
            fig = go.Figure()
            palette = [ACCENT, "#27AE60", "#3498DB", RED, "#9B59B6"]
            for i, grp in enumerate(AGE_GROUP_ORDER):
                sub = df[df["Age_Group"] == grp]
                if sub.empty: continue
                vals = [sub[c].mean() for c in radar_cols] + [sub[radar_cols[0]].mean()]
                cats = [c.replace("_Score", "") for c in radar_cols] + [radar_cols[0].replace("_Score", "")]
                fig.add_trace(go.Scatterpolar(r=vals, theta=cats, name=grp,
                                              fill="toself", line_color=palette[i % len(palette)]))
            fig.update_layout(**dark_layout(title="Score Profile by Age Group", title_font_color=ACCENT,
                                            polar=dict(bgcolor=CARD,
                                                       radialaxis=dict(visible=True, range=[0, 100],
                                                                        gridcolor="#333", tickfont=dict(color="#888")))))
            st.plotly_chart(fig, use_container_width=True, key="dash_radar")

    # ── Row 4: Match Type Preference + Attendance Histogram ──────────────────
    c7, c8 = st.columns(2, gap="medium")
    with c7:
        if "Match_Type_Preference" in df.columns:
            mtp = df.groupby(["Match_Type_Preference", "Segment"]).size().reset_index(name="Count")
            fig = px.bar(mtp, x="Match_Type_Preference", y="Count", color="Segment",
                         color_discrete_map=SEGMENT_COLORS, barmode="stack",
                         title="Match Type Preference by Segment")
            fig.update_layout(**dark_layout(title_font_color=ACCENT))
            st.plotly_chart(fig, use_container_width=True, key="dash_mtp_seg")

    with c8:
        if "Attendance_Frequency" in df.columns:
            fig = px.histogram(df, x="Attendance_Frequency", nbins=25,
                               color_discrete_sequence=[PRIMARY],
                               title="Attendance Frequency Distribution (matches/season)")
            fig.update_layout(**dark_layout(title_font_color=ACCENT))
            st.plotly_chart(fig, use_container_width=True, key="dash_att_hist")

    # ── Channel Preference Index ──────────────────────────────────────────────
    ch_seg = df.groupby(["Segment", "Channel_Preference"]).size().reset_index(name="Count")
    fig = px.bar(ch_seg, x="Segment", y="Count", color="Channel_Preference",
                 barmode="stack", title="Channel Preference by Segment",
                 color_discrete_sequence=[ACCENT, PRIMARY, BLUE, "#888"])
    fig.update_layout(**dark_layout(title_font_color=ACCENT))
    st.plotly_chart(fig, use_container_width=True, key="dash_channel_pref")

    # ── Segment Insights Cards ────────────────────────────────────────────────
    st.markdown(f"<br><h4>Segment Insights & Recommended Actions</h4>", unsafe_allow_html=True)
    segs = list(SEGMENT_INSIGHTS.keys())
    row_a = st.columns(3, gap="medium")
    row_b = st.columns(2, gap="medium")
    all_cols = list(row_a) + list(row_b)
    for i, seg in enumerate(segs):
        info = SEGMENT_INSIGHTS[seg]
        sub  = df[df["Segment"] == seg]
        n_seg = len(sub)
        c = SEGMENT_COLORS.get(seg, "#888")
        avg_e = sub["Engagement_Score"].mean() if n_seg else 0
        avg_c = sub["Commercial_Score"].mean()  if n_seg else 0
        avg_l = sub["Loyalty_Score"].mean()     if n_seg else 0
        avg_ch = sub["Churn_Risk_Score"].mean() if n_seg else 0
        avg_cv = sub["Conversion_Score"].mean() if n_seg else 0
        tactics_html = "".join(f'<li style="color:#AAA;font-size:11px;margin-bottom:4px">{t}</li>' for t in info["tactics"])
        card_html = f"""
        <div style="background:{CARD};border:1px solid {c};border-radius:10px;padding:16px;height:100%">
            <div style="color:{c};font-weight:700;font-size:13px;margin-bottom:6px">{seg} &nbsp;<span style="color:#888;font-weight:400;font-size:11px">{n_seg:,} fans</span></div>
            <div style="color:#CCC;font-size:11px;margin-bottom:10px">{info['desc']}</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-bottom:10px;font-size:10px">
                <span style="color:#888">Engagement: <b style="color:{ACCENT}">{avg_e:.0f}</b></span>
                <span style="color:#888">Commercial: <b style="color:{ACCENT}">{avg_c:.0f}</b></span>
                <span style="color:#888">Loyalty: <b style="color:{ACCENT}">{avg_l:.0f}</b></span>
                <span style="color:#888">Churn Risk: <b style="color:{RED}">{avg_ch:.0f}</b></span>
                <span style="color:#888">Conversion: <b style="color:#27AE60">{avg_cv:.0f}</b></span>
            </div>
            <div style="color:{c};font-size:11px;font-weight:700;margin-bottom:6px">Action: {info['action']}</div>
            <ul style="padding-left:16px;margin:0">{tactics_html}</ul>
        </div>"""
        with all_cols[i]:
            st.markdown(card_html, unsafe_allow_html=True)

    # ── Top 20 Fans Table ─────────────────────────────────────────────────────
    st.markdown("<br><h4>Top 20 Fans by Composite Score</h4>", unsafe_allow_html=True)
    display_cols = [c for c in [
        "Fan_ID", "Age", "Membership_Category", "Segment",
        "Engagement_Score", "Commercial_Score", "Loyalty_Score",
        "Churn_Risk_Label", "Conversion_Score", "Composite_Score",
        "Journey_Stage", "Channel_Preference",
    ] if c in df.columns]
    top20 = df.nlargest(20, "Composite_Score")[display_cols]
    st.dataframe(top20, use_container_width=True, hide_index=True,
                 column_config={"Composite_Score": st.column_config.ProgressColumn(
                     "Composite", min_value=0, max_value=100, format="%.1f")})

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Membership Intelligence
# ══════════════════════════════════════════════════════════════════════════════
def render_membership_tab(df: pd.DataFrame, club_name: str):
    st.markdown(f"### {club_name} — Membership Intelligence")

    mem_col = "Membership_Category"
    if mem_col not in df.columns:
        st.warning("Membership_Category column not found in data.")
        return

    # ── Tier breakdown ────────────────────────────────────────────────────────
    mem_vc = df[mem_col].value_counts().reindex(MEMBERSHIP_ORDER, fill_value=0).reset_index()
    mem_vc.columns = ["Tier", "Count"]
    mem_vc["Pct"] = (mem_vc["Count"] / len(df) * 100).round(1)

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        fig = px.bar(mem_vc, x="Tier", y="Count", color="Tier",
                     color_discrete_sequence=[PRIMARY, "#3A7020", "#5A9030", ACCENT, "#E8C060"],
                     title="Membership Tier Breakdown",
                     category_orders={"Tier": MEMBERSHIP_ORDER})
        fig.update_layout(**dark_layout(title_font_color=ACCENT, showlegend=False))
        st.plotly_chart(fig, use_container_width=True, key="mem_tier_bar")
    with c2:
        fig = px.pie(mem_vc, names="Tier", values="Count",
                     color_discrete_sequence=[PRIMARY, "#3A7020", "#5A9030", ACCENT, "#E8C060"],
                     hole=0.5, title="Membership Mix %",
                     category_orders={"Tier": MEMBERSHIP_ORDER})
        fig.update_layout(**dark_layout(title_font_color=ACCENT))
        st.plotly_chart(fig, use_container_width=True, key="mem_tier_donut")

    # ── Revenue + LTV ─────────────────────────────────────────────────────────
    st.markdown("#### Membership Revenue & LTV Analysis")
    rev_by_mem = df.groupby(mem_col).agg(
        Count=(mem_col, "count"),
        Total_Revenue=("Total_Revenue", "sum") if "Total_Revenue" in df.columns else (mem_col, "count"),
        Avg_Revenue=("Total_Revenue", "mean") if "Total_Revenue" in df.columns else (mem_col, "count"),
    ).reindex(MEMBERSHIP_ORDER).reset_index()
    rev_by_mem.columns = ["Tier", "Count", "Total_Revenue", "Avg_Revenue"]

    # Add LTV
    if "Join_Date" in df.columns:
        df["_tenure_y"] = (TODAY_DT - pd.to_datetime(df["Join_Date"], errors="coerce")).dt.days / 365
        ltv_by_mem = df.groupby(mem_col).agg(
            Avg_Revenue=("Total_Revenue", "mean") if "Total_Revenue" in df.columns else (mem_col, "count"),
            Tenure_y=("_tenure_y", "mean"),
        ).reindex(MEMBERSHIP_ORDER).reset_index()
        ltv_by_mem.columns = ["Tier", "Avg_Revenue", "Avg_Tenure_y"]
        ltv_by_mem["Est_LTV"] = (ltv_by_mem["Avg_Revenue"] * ltv_by_mem["Avg_Tenure_y"]).round(0)
    else:
        ltv_by_mem = rev_by_mem[["Tier"]].copy()
        ltv_by_mem["Est_LTV"] = [MEM_LTV.get(t, 0) for t in ltv_by_mem["Tier"]]

    r1, r2 = st.columns(2, gap="medium")
    with r1:
        fig = px.bar(rev_by_mem, x="Tier", y="Total_Revenue",
                     color_discrete_sequence=[ACCENT], title="Estimated Total Revenue by Tier",
                     category_orders={"Tier": MEMBERSHIP_ORDER})
        fig.update_layout(**dark_layout(title_font_color=ACCENT, showlegend=False))
        st.plotly_chart(fig, use_container_width=True, key="mem_rev_bar")
    with r2:
        fig = px.bar(ltv_by_mem, x="Tier", y="Est_LTV",
                     color_discrete_sequence=[PRIMARY], title="Estimated LTV by Membership Tier",
                     category_orders={"Tier": MEMBERSHIP_ORDER})
        fig.update_layout(**dark_layout(title_font_color=ACCENT, showlegend=False))
        st.plotly_chart(fig, use_container_width=True, key="mem_ltv_bar")

    # ── Journey Funnel ────────────────────────────────────────────────────────
    st.markdown("#### Membership Journey Funnel")
    # Always render all 5 stages; missing stages get Count = 0
    _all_stages = [
        (1, "Stage 1 - No Membership, Low Engagement"),
        (2, "Stage 2 - Associate Member"),
        (3, "Stage 3 - Associate, High Engagement"),
        (4, "Stage 4 - Full / Life Member"),
        (5, "Stage 5 - Surrey & England Dual Member"),
    ]
    _stage_counts = df["Journey_Stage"].value_counts().to_dict()
    funnel_df = pd.DataFrame([
        {"Stage": s, "Label": lbl, "Count": _stage_counts.get(s, 0)}
        for s, lbl in _all_stages
    ])
    # Percentages relative to Stage 1 (top of funnel) — never exceed 100%
    _s1 = funnel_df.loc[funnel_df["Stage"] == 1, "Count"].values[0]
    if _s1 > 0:
        funnel_df["text"] = funnel_df["Count"].apply(
            lambda c: f"{int(c):,} ({min(c/_s1*100, 100):.0f}%)"
        )
    else:
        funnel_df["text"] = funnel_df["Count"].apply(lambda c: f"{int(c):,}")
    fig = go.Figure(go.Funnel(
        y=funnel_df["Label"],
        x=funnel_df["Count"],
        text=funnel_df["text"],
        textinfo="text",
        marker_color=[PRIMARY, "#3A7020", "#5A9030", ACCENT, "#E8C060"],
    ))
    fig.update_layout(**dark_layout(title="Fan Journey Funnel (Stage 1 to 5)", title_font_color=ACCENT))
    st.plotly_chart(fig, use_container_width=True, key="mem_funnel")

    # ── Renewal Risk Panel ────────────────────────────────────────────────────
    st.markdown("#### Renewal Risk Panel")
    renewal_risk = df[df["Churn_Risk_Label"] == "HIGH"].copy()
    if not renewal_risk.empty:
        tier_filter = st.selectbox("Filter by Tier", ["All"] + MEMBERSHIP_ORDER, key="mem_tier_filter")
        if tier_filter != "All":
            renewal_risk = renewal_risk[renewal_risk[mem_col] == tier_filter]
        rr_cols = [c for c in ["Fan_ID", "Membership_Category", "Last_Purchase_Date",
                                "Churn_Risk_Score", "Engagement_Score", "Commercial_Score"] if c in df.columns]
        st.markdown(f"**{len(renewal_risk):,} fans at HIGH churn risk**")
        st.dataframe(
            renewal_risk.nlargest(20, "Churn_Risk_Score")[rr_cols],
            use_container_width=True, hide_index=True,
            column_config={"Churn_Risk_Score": st.column_config.ProgressColumn(
                "Churn Risk", min_value=0, max_value=100, format="%.1f")},
        )
    else:
        st.info("No HIGH churn risk fans in this dataset.")

    # ── Upgrade Opportunity Panel ─────────────────────────────────────────────
    st.markdown("#### Upgrade Opportunity Panel")
    upgrade_cands = df[df["Journey_Stage"].isin([2, 3])].copy()
    if not upgrade_cands.empty:
        upgrade_cands["Next_Tier"] = upgrade_cands[mem_col].map({
            "None": "Associate", "Associate": "Full Member",
        }).fillna("Full Member")
        upgrade_cands["Est_Rev_Uplift"] = upgrade_cands["Next_Tier"].map({
            "Associate": 150, "Full Member": 400,
        }).fillna(200)
        up_cols = [c for c in ["Fan_ID", "Membership_Category", "Next_Tier",
                                "Conversion_Score", "Est_Rev_Uplift", "Channel_Preference"] if c in df.columns]
        st.dataframe(
            upgrade_cands.nlargest(20, "Conversion_Score")[up_cols],
            use_container_width=True, hide_index=True,
            column_config={"Conversion_Score": st.column_config.ProgressColumn(
                "Conversion Prob", min_value=0, max_value=100, format="%.1f")},
        )
        total_uplift = upgrade_cands["Est_Rev_Uplift"].sum()
        pct5 = int(len(upgrade_cands) * 0.05)
        uplift5 = upgrade_cands.nlargest(pct5, "Conversion_Score")["Est_Rev_Uplift"].sum() if pct5 else 0
        st.markdown(
            f'<div style="background:#0F2A06;border:1px solid {PRIMARY};border-radius:8px;padding:16px;margin-top:12px">'
            f'<span style="color:{ACCENT};font-weight:700">Revenue Opportunity:</span> '
            f'<span style="color:#CCC">Converting 5% of Stage 2-3 fans ({pct5:,} fans) to next membership tier = '
            f'<b style="color:{ACCENT}">~GBP{uplift5:,.0f}</b> estimated additional annual revenue.</span></div>',
            unsafe_allow_html=True,
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Sponsorship Intelligence
# ══════════════════════════════════════════════════════════════════════════════
def render_sponsorship_tab(df: pd.DataFrame, club_name: str):
    st.markdown(f"### {club_name} — Sponsorship Intelligence")

    # ── Sponsorship Pitch Score ───────────────────────────────────────────────
    loyal_pct   = (df["Segment"] == "Loyal Members").mean() * 100
    highpot_pct = (df["Segment"] == "High Potential").mean() * 100
    avg_comm    = df["Commercial_Score"].mean()
    demo_q      = ((df["Age"] >= 25) & (df["Age"] <= 54)).mean() * 100 if "Age" in df.columns else 50.0
    pitch_score = min(100, avg_comm * 0.40 + loyal_pct * 0.30 + highpot_pct * 0.15 + demo_q * 0.15)

    if pitch_score >= 70:  pitch_label, pitch_color = "Excellent", "#27AE60"
    elif pitch_score >= 50: pitch_label, pitch_color = "Strong",    ACCENT
    else:                   pitch_label, pitch_color = "Developing", ORANGE

    st.markdown(
        f'<div style="background:{CARD};border:2px solid {pitch_color};border-radius:12px;'
        f'padding:24px;text-align:center;margin-bottom:24px">'
        f'<div style="font-size:12px;color:#888;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">Sponsorship Pitch Score</div>'
        f'<div style="font-size:56px;font-weight:800;color:{pitch_color};line-height:1">{pitch_score:.0f}</div>'
        f'<div style="font-size:18px;color:{pitch_color};font-weight:700;margin-top:8px">{pitch_label}</div>'
        f'<div style="color:#888;font-size:12px;margin-top:8px">Based on commercial quality, loyal member %, demographic fit</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Demographics ──────────────────────────────────────────────────────────
    st.markdown("#### Audience Demographics (Sponsor View)")
    d1, d2, d3 = st.columns(3, gap="medium")
    with d1:
        if "Age_Group" in df.columns:
            ag_vc = df["Age_Group"].value_counts().reset_index()
            ag_vc.columns = ["Age Group", "Count"]
            fig = px.pie(ag_vc, names="Age Group", values="Count", hole=0.5,
                         title="Age Distribution",
                         color_discrete_sequence=[PRIMARY, "#3A7020", "#5A9030", ACCENT, "#E8C060"])
            fig.update_layout(**dark_layout(title_font_color=ACCENT))
            st.plotly_chart(fig, use_container_width=True, key="spons_age_donut")
    with d2:
        if "Gender" in df.columns:
            g_vc = df["Gender"].value_counts().reset_index()
            g_vc.columns = ["Gender", "Count"]
            fig = px.pie(g_vc, names="Gender", values="Count", hole=0.5,
                         title="Gender Split",
                         color_discrete_sequence=[ACCENT, PRIMARY, "#888"])
            fig.update_layout(**dark_layout(title_font_color=ACCENT))
            st.plotly_chart(fig, use_container_width=True, key="spons_gender_donut")
    with d3:
        if "County" in df.columns:
            co_vc = df["County"].value_counts().reset_index()
            co_vc.columns = ["County", "Count"]
            fig = px.bar(co_vc.head(8), x="Count", y="County", orientation="h",
                         color_discrete_sequence=[PRIMARY], title="Regional Distribution")
            fig.update_layout(**dark_layout(title_font_color=ACCENT, showlegend=False))
            st.plotly_chart(fig, use_container_width=True, key="spons_county_bar")

    # ── Commercial Score Distribution ─────────────────────────────────────────
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        fig = px.histogram(df, x="Commercial_Score", nbins=20, color_discrete_sequence=[PRIMARY],
                           title="Commercial Score Distribution")
        avg_c = df["Commercial_Score"].mean()
        fig.add_vline(x=avg_c, line_dash="dash", line_color=ACCENT,
                      annotation_text=f"Avg {avg_c:.1f}", annotation_font_color=ACCENT)
        fig.update_layout(**dark_layout(title_font_color=ACCENT))
        st.plotly_chart(fig, use_container_width=True, key="spons_comm_hist")
    with c2:
        aq = df.groupby("Segment")["Commercial_Score"].mean().reset_index().sort_values("Commercial_Score")
        fig = px.bar(aq, x="Commercial_Score", y="Segment", orientation="h",
                     color="Segment", color_discrete_map=SEGMENT_COLORS,
                     title="Audience Quality by Segment (Avg Commercial Score)")
        fig.update_layout(**dark_layout(title_font_color=ACCENT, showlegend=False))
        st.plotly_chart(fig, use_container_width=True, key="spons_aq_bar")

    # ── Sponsor Category Recommendations ─────────────────────────────────────
    st.markdown("#### Top Sponsor Category Recommendations")

    def _fit_rating(idx):
        if idx < 2:   return "HIGH", "#27AE60", "#0A2A0A"
        elif idx < 4: return "MED",  ACCENT,    "#2A1F00"
        else:         return "LOW",  ORANGE,    "#2A1000"

    # Filter out any None/empty entries before rendering
    valid_cats = [
        c for c in SPONSOR_CATEGORIES
        if c is not None
        and str(c.get("category", "")).strip() not in ("", "nan", "None")
        and str(c.get("brands",   "")).strip() not in ("", "nan", "None")
        and str(c.get("rationale","")).strip() not in ("", "nan", "None")
    ]

    if valid_cats:
        cat_cols = st.columns(len(valid_cats), gap="small")
        for i in range(len(valid_cats)):
            cat = valid_cats[i]
            fit, fit_col, bg = _fit_rating(i)
            _cat_name  = str(cat.get("category",  "") or "").strip()
            _brands    = str(cat.get("brands",    "") or "").strip()
            _rationale = str(cat.get("rationale", "") or "").strip()
            with cat_cols[i]:
                st.markdown(
                    f'<div style="background:{bg};border:1px solid {fit_col};border-radius:8px;padding:14px;height:100%">'
                    f'<div style="color:{fit_col};font-weight:700;font-size:12px;margin-bottom:6px">'
                    f'{_cat_name} &nbsp;'
                    f'<span style="font-size:10px;background:{fit_col}22;padding:2px 6px;border-radius:3px">{fit}</span></div>'
                    f'<div style="color:#888;font-size:10px;margin-bottom:6px">{_brands}</div>'
                    f'<div style="color:#AAA;font-size:10px">{_rationale}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ── Sponsorship Deck PDF Download ─────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    spons_pdf = generate_sponsorship_pdf(df, club_name, pitch_score, pitch_label)
    st.download_button(
        "⬇ Download Sponsorship Deck PDF",
        data=spons_pdf,
        file_name=f"CricIntel_{club_name.replace(' ', '_')}_Sponsorship_Deck.pdf",
        mime="application/pdf",
        key="dl_spons_pdf",
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — Match Intelligence
# ══════════════════════════════════════════════════════════════════════════════
def render_match_tab(df: pd.DataFrame, club_name: str):
    st.markdown(f"### {club_name} — Match Intelligence")

    # ── Estimated Matchday Revenue per Format ─────────────────────────────────
    st.markdown("#### Estimated Matchday Revenue by Format")
    format_rev = {"T20": 85, "County Championship": 55, "The Hundred": 75}
    if "Match_Type_Preference" in df.columns and "Total_Revenue" in df.columns:
        mf_rev = df.groupby("Match_Type_Preference").agg(
            Fan_Count=("Fan_ID" if "Fan_ID" in df.columns else "Composite_Score", "count"),
            Avg_Revenue=("Total_Revenue", "mean"),
        ).reset_index()
        mf_rev["Est_Matchday_Rev"] = mf_rev.apply(
            lambda r: r["Avg_Revenue"] * (r["Fan_Count"] / len(df)) * format_rev.get(r["Match_Type_Preference"], 70),
            axis=1,
        ).round(0)
    else:
        mf_rev = pd.DataFrame({
            "Match_Type_Preference": list(format_rev.keys()),
            "Est_Matchday_Rev": [f * 500 for f in format_rev.values()],
        })

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        fig = px.bar(mf_rev, x="Match_Type_Preference", y="Est_Matchday_Rev",
                     color="Match_Type_Preference",
                     color_discrete_sequence=[ACCENT, PRIMARY, "#3498DB"],
                     title="Est. Matchday Revenue Contribution by Format")
        fig.update_layout(**dark_layout(title_font_color=ACCENT, showlegend=False))
        st.plotly_chart(fig, use_container_width=True, key="match_format_rev")

    with c2:
        if "Match_Type_Preference" in df.columns:
            top_seg = df.groupby("Match_Type_Preference")["Commercial_Score"].agg(
                lambda x: df.loc[x.index, "Segment"].value_counts().index[0]
            ).reset_index()
            top_seg.columns = ["Format", "Top_Segment"]
            seg_comm = df.groupby(["Match_Type_Preference", "Segment"])["Commercial_Score"].mean().reset_index()
            fig = px.bar(seg_comm, x="Match_Type_Preference", y="Commercial_Score",
                         color="Segment", color_discrete_map=SEGMENT_COLORS,
                         barmode="group", title="Avg Commercial Score by Format & Segment")
            fig.update_layout(**dark_layout(title_font_color=ACCENT))
            st.plotly_chart(fig, use_container_width=True, key="match_comm_seg")

    # ── Pre/During/Post Engagement Windows ────────────────────────────────────
    st.markdown("#### Engagement Channel Activity by Match Format")
    if "Match_Type_Preference" in df.columns:
        eng_win = df.groupby("Match_Type_Preference").agg(
            Email_Eng=("Email_Clicks", "mean") if "Email_Clicks" in df.columns else ("Engagement_Score", "mean"),
            App_Eng=("InApp_Clicks", "mean") if "InApp_Clicks" in df.columns else ("Engagement_Score", "mean"),
            Article_Views=("Article_Views", "mean") if "Article_Views" in df.columns else ("Engagement_Score", "mean"),
        ).reset_index()
        eng_melt = eng_win.melt(id_vars="Match_Type_Preference", var_name="Channel", value_name="Avg_Activity")
        fig = px.bar(eng_melt, x="Channel", y="Avg_Activity", color="Match_Type_Preference",
                     barmode="group", title="Avg Channel Activity by Match Format",
                     color_discrete_sequence=[ACCENT, PRIMARY, BLUE])
        fig.update_layout(**dark_layout(title_font_color=ACCENT))
        st.plotly_chart(fig, use_container_width=True, key="match_eng_windows")

    # ── Attendance Gap Analysis ────────────────────────────────────────────────
    st.markdown("#### Attendance Gap — High Engagement, Low Attendance (Upsell Targets)")
    HIGH_ENG = df["Engagement_Score"].quantile(0.4)
    LOW_ATT  = 6
    if "Attendance_Frequency" in df.columns:
        att_gap = df[
            (df["Engagement_Score"] > HIGH_ENG) &
            (df["Attendance_Frequency"] < LOW_ATT)
        ].copy()
        st.markdown(
            f'<div style="background:#0A1520;border:1px solid {BLUE};border-radius:8px;padding:14px;margin-bottom:16px">'
            f'<span style="color:{BLUE};font-weight:700">{len(att_gap):,} fans</span>'
            f'<span style="color:#CCC"> have high engagement scores but attend fewer than 5 matches per season — prime upsell targets for match tickets.</span>'
            f'</div>', unsafe_allow_html=True
        )
        att_gap_cols = [c for c in ["Fan_ID", "Membership_Category", "Engagement_Score",
                                     "Attendance_Frequency", "Match_Type_Preference", "Conversion_Score"] if c in df.columns]
        st.dataframe(att_gap.nlargest(15, "Engagement_Score")[att_gap_cols],
                     use_container_width=True, hide_index=True)

        fig = px.scatter(att_gap, x="Attendance_Frequency", y="Engagement_Score",
                         color="Membership_Category" if "Membership_Category" in df.columns else "Segment",
                         size="Conversion_Score", title="Upsell Targets: Engagement vs Attendance",
                         color_discrete_sequence=[PRIMARY, "#3A7020", "#5A9030", ACCENT, "#E8C060"])
        fig.update_layout(**dark_layout(title_font_color=ACCENT))
        st.plotly_chart(fig, use_container_width=True, key="match_att_gap_scatter")

    # ── Hospitality Upsell ────────────────────────────────────────────────────
    st.markdown("#### Hospitality Upsell Targets")
    if "Hospitality_Interest" in df.columns:
        hosp_targets = df[df["Hospitality_Interest"] == "Yes"].copy()
        st.markdown(
            f'<div style="background:#0F2A06;border:1px solid {PRIMARY};border-radius:8px;padding:14px;margin-bottom:16px">'
            f'<span style="color:{ACCENT};font-weight:700">{len(hosp_targets):,} fans</span>'
            f'<span style="color:#CCC"> have expressed hospitality interest — ranked by conversion probability.</span>'
            f'</div>', unsafe_allow_html=True
        )
        hosp_cols = [c for c in ["Fan_ID", "Membership_Category", "Conversion_Score",
                                  "Commercial_Score", "Match_Type_Preference"] if c in df.columns]
        st.dataframe(hosp_targets.nlargest(20, "Conversion_Score")[hosp_cols],
                     use_container_width=True, hide_index=True,
                     column_config={"Conversion_Score": st.column_config.ProgressColumn(
                         "Conversion Prob", min_value=0, max_value=100, format="%.1f")})
    else:
        st.info("Hospitality_Interest column not found. Upload the full sample dataset to see hospitality targets.")

    # ── Corporate Packages ────────────────────────────────────────────────────
    st.markdown("#### Corporate Package Opportunities")
    if "Corporate_Package" in df.columns:
        corp = df[df["Corporate_Package"] == "Yes"].copy()
    else:
        corp = df[df["Commercial_Score"] > 60].copy()
    corp_cols = [c for c in ["Fan_ID", "Membership_Category", "Fan_Type",
                              "Commercial_Score", "Conversion_Score"] if c in df.columns]
    st.markdown(f"**{len(corp):,} corporate-interest fans identified**")
    st.dataframe(corp.nlargest(15, "Commercial_Score")[corp_cols],
                 use_container_width=True, hide_index=True)

    # ── Revenue Opportunity Callout ───────────────────────────────────────────
    if "Attendance_Frequency" in df.columns:
        high_potential_count = len(df[df["Segment"] == "High Potential"])
        conv_10pct           = int(high_potential_count * 0.10)
        rev_est              = conv_10pct * 35  # avg ticket ~£35
        st.markdown(
            f'<div style="background:#0F2A06;border:1px solid {ACCENT};border-radius:8px;padding:16px;margin-top:12px">'
            f'<span style="color:{ACCENT};font-weight:700">Revenue Opportunity:</span> '
            f'<span style="color:#CCC">Converting 10% of High Potential fans ({high_potential_count:,} fans) to matchday attendance = '
            f'<b style="color:{ACCENT}">~GBP{rev_est:,.0f}</b> additional per fixture.</span>'
            f'</div>', unsafe_allow_html=True
        )

# ══════════════════════════════════════════════════════════════════════════════
# PDF GENERATION
# ══════════════════════════════════════════════════════════════════════════════
class CricIntelPDF(FPDF):
    def __init__(self, club: str):
        super().__init__()
        self.club = club
        self.alias_nb_pages()

    def header(self):
        self.set_fill_color(45, 80, 22)
        self.set_text_color(201, 168, 76)
        self.set_font("Helvetica", "B", 13)
        self.cell(0, 11, _pdf_safe(f"CricIntel Fan Intelligence  |  {self.club}"), fill=True, ln=True, align="C")
        self.set_text_color(0, 0, 0)
        self.ln(3)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 8, _pdf_safe(f"Page {self.page_no()}/{{nb}}  |  CricIntel Fan Intelligence  |  Confidential"), align="C")

    def section_title(self, title: str):
        self.set_fill_color(45, 80, 22)
        self.set_text_color(201, 168, 76)
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 8, _pdf_safe(title), fill=True, ln=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def kv_row(self, key: str, value: str, bold_value: bool = False):
        self.set_font("Helvetica", "", 9)
        self.set_fill_color(240, 245, 235)
        self.cell(80, 6, _pdf_safe(key), border=0, ln=0)
        self.set_font("Helvetica", "B" if bold_value else "", 9)
        self.cell(0, 6, _pdf_safe(str(value)), border=0, ln=True)

    def table_header(self, cols, widths):
        self.set_fill_color(45, 80, 22)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 8)
        for col, w in zip(cols, widths):
            self.cell(w, 6, _pdf_safe(str(col)), border=1, align="C", fill=True)
        self.ln()
        self.set_text_color(0, 0, 0)

    def table_row(self, vals, widths, fill=False):
        self.set_fill_color(245, 250, 240) if fill else self.set_fill_color(255, 255, 255)
        self.set_font("Helvetica", "", 7)
        for v, w in zip(vals, widths):
            self.cell(w, 5, _pdf_safe(str(v))[:30], border=1, fill=fill)
        self.ln()


def generate_pdf(df: pd.DataFrame, club_name: str, county_format: str) -> bytes:
    pdf = CricIntelPDF(club_name)

    # ── Page 1: Executive Summary ─────────────────────────────────────────────
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(45, 80, 22)
    pdf.cell(0, 12, _pdf_safe(f"{club_name} - Fan Intelligence Report"), ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, _pdf_safe(f"Format: {county_format}  |  Generated: {date(2026, 5, 6).isoformat()}  |  Fans Analysed: {len(df):,}"), ln=True, align="C")
    pdf.ln(6)

    pdf.section_title("Executive Summary")
    high_churn = (df["Churn_Risk_Label"] == "HIGH").sum()
    conv_cands = df["Journey_Stage"].isin([2, 3]).sum()
    loyal_cnt  = (df["Segment"] == "Loyal Members").sum()
    pdf.kv_row("Total Fans Analysed", f"{len(df):,}")
    pdf.kv_row("Loyal Members",        f"{loyal_cnt:,} ({loyal_cnt/len(df)*100:.1f}%)")
    pdf.kv_row("High Churn Risk Fans", f"{high_churn:,} ({high_churn/len(df)*100:.1f}%)")
    pdf.kv_row("Conversion Candidates (Stage 2-3)", f"{conv_cands:,}")
    pdf.kv_row("Avg Engagement Score", f"{df['Engagement_Score'].mean():.1f} / 100")
    pdf.kv_row("Avg Commercial Score", f"{df['Commercial_Score'].mean():.1f} / 100")
    pdf.kv_row("Avg Loyalty Score",    f"{df['Loyalty_Score'].mean():.1f} / 100")
    pdf.ln(4)

    # ── Segment Summary ───────────────────────────────────────────────────────
    pdf.section_title("Segment Summary")
    seg_summary = df.groupby("Segment").agg(
        Count=("Segment", "count"),
        Avg_E=("Engagement_Score", "mean"),
        Avg_C=("Commercial_Score", "mean"),
        Avg_L=("Loyalty_Score", "mean"),
        Churn_HIGH=("Churn_Risk_Label", lambda x: (x == "HIGH").sum()),
    ).reset_index()
    cols = ["Segment", "Count", "Avg E", "Avg C", "Avg L", "High Churn"]
    widths = [46, 18, 18, 18, 18, 22]
    pdf.table_header(cols, widths)
    for i, row in seg_summary.iterrows():
        pdf.table_row([
            row["Segment"], int(row["Count"]),
            f"{row['Avg_E']:.1f}", f"{row['Avg_C']:.1f}", f"{row['Avg_L']:.1f}",
            int(row["Churn_HIGH"]),
        ], widths, fill=(i % 2 == 0))

    # ── Page 2: Membership ────────────────────────────────────────────────────
    pdf.add_page()
    pdf.section_title("Membership Tier Breakdown")
    mem_summary = df["Membership_Category"].value_counts().reindex(MEMBERSHIP_ORDER, fill_value=0)
    m_cols = ["Tier", "Count", "% of Base", "Avg Revenue"]
    m_widths = [50, 20, 25, 35]
    pdf.table_header(m_cols, m_widths)
    for i, (tier, cnt) in enumerate(mem_summary.items()):
        avg_rev = df[df["Membership_Category"] == tier]["Total_Revenue"].mean() if "Total_Revenue" in df.columns else 0
        pdf.table_row([tier, int(cnt), f"{cnt/len(df)*100:.1f}%", f"GBP{avg_rev:.0f}"], m_widths, fill=(i % 2 == 0))

    pdf.ln(6)
    pdf.section_title("Journey Stage Distribution")
    stage_labels = {1: "No Membership, Low Eng.", 2: "No Membership, Active",
                    3: "Associate Member", 4: "Full/Life Member", 5: "Surrey & England"}
    s_cols = ["Stage", "Description", "Count", "% of Base"]
    s_widths = [15, 70, 20, 25]
    pdf.table_header(s_cols, s_widths)
    stage_vc = df["Journey_Stage"].value_counts().sort_index()
    for i, (stg, cnt) in enumerate(stage_vc.items()):
        pdf.table_row([stg, stage_labels.get(stg, ""), int(cnt), f"{cnt/len(df)*100:.1f}%"],
                      s_widths, fill=(i % 2 == 0))

    # ── Page 3: Churn & Conversion ────────────────────────────────────────────
    pdf.add_page()
    pdf.section_title("Churn Risk Summary")
    churn_vc = df["Churn_Risk_Label"].value_counts()
    c_cols = ["Risk Level", "Count", "% of Base", "Action Required"]
    c_widths = [25, 20, 25, 60]
    pdf.table_header(c_cols, c_widths)
    actions = {"HIGH": "Immediate re-engagement campaign", "MED": "Monitor - proactive touchpoint", "LOW": "Maintain current programme"}
    for i, (level, cnt) in enumerate(churn_vc.items()):
        pdf.table_row([level, int(cnt), f"{cnt/len(df)*100:.1f}%", actions.get(level, "")],
                      c_widths, fill=(i % 2 == 0))

    pdf.ln(6)
    pdf.section_title("Conversion Opportunity Summary")
    upgrade_cands = df[df["Journey_Stage"].isin([2, 3])]
    pdf.kv_row("Stage 2-3 Fans (Conversion Targets)", f"{len(upgrade_cands):,}")
    pdf.kv_row("Avg Conversion Score",                f"{upgrade_cands['Conversion_Score'].mean():.1f}")
    top5_conv = upgrade_cands.nlargest(5, "Conversion_Score")
    pdf.kv_row("Top 5 Conversion Scores",              ", ".join(f"{s:.0f}" for s in top5_conv["Conversion_Score"].values))
    if "Total_Revenue" in df.columns:
        est_uplift = len(upgrade_cands) * 0.05 * 200
        pdf.kv_row("5% Conversion Est. Revenue Uplift", f"GBP{est_uplift:,.0f}")

    # ── Page 4: Sponsorship ───────────────────────────────────────────────────
    pdf.add_page()
    pdf.section_title("Sponsorship Intelligence")
    loyal_pct   = (df["Segment"] == "Loyal Members").mean() * 100
    highpot_pct = (df["Segment"] == "High Potential").mean() * 100
    avg_comm    = df["Commercial_Score"].mean()
    demo_q      = ((df["Age"] >= 25) & (df["Age"] <= 54)).mean() * 100 if "Age" in df.columns else 50.0
    pitch_score = min(100, avg_comm * 0.40 + loyal_pct * 0.30 + highpot_pct * 0.15 + demo_q * 0.15)
    pitch_label = "Excellent" if pitch_score >= 70 else "Strong" if pitch_score >= 50 else "Developing"
    pdf.kv_row("Sponsorship Pitch Score", f"{pitch_score:.0f} / 100 - {pitch_label}")
    pdf.kv_row("Loyal Members %",         f"{loyal_pct:.1f}%")
    pdf.kv_row("High Potential %",        f"{highpot_pct:.1f}%")
    pdf.kv_row("Key Demo (25-54) %",       f"{demo_q:.1f}%")
    pdf.ln(4)

    sp_cols = ["Category", "Brands", "Fit"]
    sp_widths = [40, 80, 20]
    pdf.table_header(sp_cols, sp_widths)
    fit_ratings = ["HIGH", "HIGH", "MED", "MED", "LOW"]
    for i, (cat, fit) in enumerate(zip(SPONSOR_CATEGORIES, fit_ratings)):
        pdf.table_row([cat["category"], cat["brands"], fit], sp_widths, fill=(i % 2 == 0))

    # ── Page 5: Match Intelligence ────────────────────────────────────────────
    pdf.add_page()
    pdf.section_title("Match Intelligence Summary")
    if "Attendance_Frequency" in df.columns:
        _high_eng = df["Engagement_Score"].quantile(0.4)
        att_gap_cnt = len(df[(df["Engagement_Score"] > _high_eng) & (df["Attendance_Frequency"] < 6)])
        pdf.kv_row("High Eng / Low Attendance (Upsell Targets)", f"{att_gap_cnt:,}")
        pdf.kv_row("Avg Attendance Frequency",                    f"{df['Attendance_Frequency'].mean():.1f} matches/season")
    if "Match_Type_Preference" in df.columns:
        mtp = df["Match_Type_Preference"].value_counts()
        for fmt, cnt in mtp.items():
            pdf.kv_row(f"{fmt} fans", f"{cnt:,} ({cnt/len(df)*100:.1f}%)")
    if "Hospitality_Interest" in df.columns:
        hosp = (df["Hospitality_Interest"] == "Yes").sum()
        pdf.kv_row("Hospitality Interest (Yes)", f"{hosp:,}")
    if "Corporate_Package" in df.columns:
        corp = (df["Corporate_Package"] == "Yes").sum()
        pdf.kv_row("Corporate Package Interest", f"{corp:,}")
    pdf.ln(4)

    # ── Page 6: Top 20 Fans ───────────────────────────────────────────────────
    pdf.add_page()
    pdf.section_title("Top 20 Fans by Composite Score")
    top20 = df.nlargest(20, "Composite_Score")
    t_cols = ["Fan ID", "Tier", "Segment", "Eng", "Comm", "Loyal", "Churn", "Conv", "Comp"]
    t_widths = [22, 28, 28, 12, 12, 12, 12, 12, 12]
    pdf.table_header(t_cols, t_widths)
    for i, row in top20.iterrows():
        pdf.table_row([
            row.get("Fan_ID", "-"), row.get("Membership_Category", "-"), row["Segment"],
            f"{row['Engagement_Score']:.0f}", f"{row['Commercial_Score']:.0f}",
            f"{row['Loyalty_Score']:.0f}", str(row["Churn_Risk_Label"]),
            f"{row['Conversion_Score']:.0f}", f"{row['Composite_Score']:.0f}",
        ], t_widths, fill=(i % 2 == 0))

    # ── Page 7: Recommendations ────────────────────────────────────────────────
    pdf.add_page()
    pdf.section_title("Retention and Commercial Recommendations")
    for seg, info in SEGMENT_INSIGHTS.items():
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(45, 80, 22)
        cnt = (df["Segment"] == seg).sum()
        pdf.cell(0, 6, _pdf_safe(f"{seg}  ({cnt:,} fans) - {info['action']}"), ln=True)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(50, 50, 50)
        for t in info["tactics"]:
            pdf.cell(8)
            pdf.cell(0, 5, _pdf_safe(f"- {t}"), ln=True)
        pdf.ln(2)

    return bytes(pdf.output())


def generate_sponsorship_pdf(df: pd.DataFrame, club_name: str, pitch_score: float, pitch_label: str) -> bytes:
    pdf = CricIntelPDF(club_name)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(45, 80, 22)
    pdf.cell(0, 14, _pdf_safe(f"{club_name}"), ln=True, align="C")
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "Sponsorship Intelligence Deck", ln=True, align="C")
    pdf.ln(8)
    pdf.section_title("Sponsorship Pitch Score")
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(201, 168, 76)
    pdf.cell(0, 16, _pdf_safe(f"{pitch_score:.0f} / 100 - {pitch_label}"), ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)
    pdf.section_title("Audience Highlights")
    loyal_pct = (df["Segment"] == "Loyal Members").mean() * 100
    if "Age" in df.columns:
        age_2554 = ((df["Age"] >= 25) & (df["Age"] <= 54)).mean() * 100
        pdf.kv_row("Key Demographic (25-54)", f"{age_2554:.1f}%")
    pdf.kv_row("Loyal Members",    f"{loyal_pct:.1f}%")
    pdf.kv_row("Total Fans",       f"{len(df):,}")
    pdf.kv_row("Avg Commercial Score", f"{df['Commercial_Score'].mean():.1f} / 100")
    pdf.ln(6)
    pdf.section_title("Recommended Sponsor Categories")
    sp_cols = ["Category", "Example Brands", "Fit Rating", "Rationale"]
    sp_widths = [35, 48, 18, 59]
    pdf.table_header(sp_cols, sp_widths)
    fits = ["HIGH", "HIGH", "MED", "MED", "LOW"]
    for i, (cat, fit) in enumerate(zip(SPONSOR_CATEGORIES, fits)):
        pdf.table_row([cat["category"], cat["brands"], fit, cat["rationale"][:55]], sp_widths, fill=(i % 2 == 0))
    return bytes(pdf.output())

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — Report
# ══════════════════════════════════════════════════════════════════════════════
def render_report_tab(df: pd.DataFrame, club_name: str, county_format: str, extra_cols: list):
    st.markdown(f"### {club_name} — Report & Downloads")

    # ── PDF Report ────────────────────────────────────────────────────────────
    st.markdown("#### Full Fan Intelligence PDF Report")
    if st.button("Generate PDF Report", key="gen_pdf_btn"):
        with st.spinner("Generating PDF..."):
            pdf_bytes = generate_pdf(df, club_name, county_format)
        st.download_button(
            "⬇ Download PDF Report",
            data=pdf_bytes,
            file_name=f"CricIntel_{club_name.replace(' ', '_')}_Report.pdf",
            mime="application/pdf",
            key="dl_full_pdf",
        )

    st.markdown("---")

    # ── CSV Downloads ─────────────────────────────────────────────────────────
    st.markdown("#### Data Downloads")
    dc1, dc2, dc3 = st.columns(3, gap="medium")
    with dc1:
        full_csv = df.to_csv(index=False).encode()
        st.download_button("⬇ Full Fan Data CSV", data=full_csv,
                           file_name=f"CricIntel_{club_name.replace(' ','_')}_fans.csv",
                           mime="text/csv", key="dl_full_csv")
    with dc2:
        seg_summary = df.groupby("Segment").agg(
            Count=("Segment", "count"),
            Avg_Engagement=("Engagement_Score", "mean"),
            Avg_Commercial=("Commercial_Score", "mean"),
            Avg_Loyalty=("Loyalty_Score", "mean"),
            High_Churn=("Churn_Risk_Label", lambda x: (x == "HIGH").sum()),
            Avg_Conversion=("Conversion_Score", "mean"),
        ).reset_index()
        seg_csv = seg_summary.to_csv(index=False).encode()
        st.download_button("⬇ Segment Summary CSV", data=seg_csv,
                           file_name=f"CricIntel_{club_name.replace(' ','_')}_segments.csv",
                           mime="text/csv", key="dl_seg_csv")
    with dc3:
        mem_summary = df.groupby("Membership_Category").agg(
            Count=("Membership_Category", "count"),
            Avg_Revenue=("Total_Revenue", "mean") if "Total_Revenue" in df.columns else ("Membership_Category", "count"),
            Total_Revenue=("Total_Revenue", "sum") if "Total_Revenue" in df.columns else ("Membership_Category", "count"),
            High_Churn=("Churn_Risk_Label", lambda x: (x == "HIGH").sum()),
        ).reset_index()
        mem_csv = mem_summary.to_csv(index=False).encode()
        st.download_button("⬇ Membership Analysis CSV", data=mem_csv,
                           file_name=f"CricIntel_{club_name.replace(' ','_')}_membership.csv",
                           mime="text/csv", key="dl_mem_csv")

    st.markdown("---")

    # ── Custom Metrics Explorer ───────────────────────────────────────────────
    custom_cols = [c for c in extra_cols if c in df.columns]
    if custom_cols:
        st.markdown("#### Custom Metrics Explorer")
        st.markdown(f"*{len(custom_cols)} extra columns detected: {', '.join(f'`{c}`' for c in custom_cols)}*")

        for col in custom_cols:
            with st.expander(f"📊 {col}", expanded=False):
                series = df[col]
                if pd.api.types.is_numeric_dtype(series):
                    c_l, c_r = st.columns(2, gap="medium")
                    with c_l:
                        fig = px.histogram(df, x=col, nbins=20, color_discrete_sequence=[PRIMARY],
                                           title=f"{col} — Distribution")
                        fig.update_layout(**dark_layout(title_font_color=ACCENT))
                        st.plotly_chart(fig, use_container_width=True, key=f"custom_hist_{col}")
                    with c_r:
                        corr_df = df[[col, "Composite_Score"]].dropna()
                        fig = px.scatter(corr_df, x=col, y="Composite_Score",
                                         color_discrete_sequence=[ACCENT],
                                         title=f"{col} vs Composite Score",
                                         trendline=None)
                        fig.update_layout(**dark_layout(title_font_color=ACCENT))
                        st.plotly_chart(fig, use_container_width=True, key=f"custom_scatter_{col}")
                else:
                    c_l, c_r = st.columns(2, gap="medium")
                    with c_l:
                        vc = series.value_counts().reset_index()
                        vc.columns = [col, "Count"]
                        fig = px.bar(vc, x=col, y="Count", color_discrete_sequence=[PRIMARY],
                                     title=f"{col} — Value Counts")
                        fig.update_layout(**dark_layout(title_font_color=ACCENT, showlegend=False))
                        st.plotly_chart(fig, use_container_width=True, key=f"custom_bar_{col}")
                    with c_r:
                        cross = df.groupby([col, "Segment"]).size().reset_index(name="Count")
                        fig = px.bar(cross, x=col, y="Count", color="Segment",
                                     color_discrete_map=SEGMENT_COLORS, barmode="stack",
                                     title=f"{col} × Segment")
                        fig.update_layout(**dark_layout(title_font_color=ACCENT))
                        st.plotly_chart(fig, use_container_width=True, key=f"custom_seg_{col}")
    else:
        st.info("No extra columns detected. Upload a file with additional columns beyond the core schema to see the Custom Metrics Explorer.")

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{PRIMARY} 0%,#1A3009 100%);'
        f'padding:20px 32px 16px;border-bottom:2px solid {ACCENT};margin:-16px -32px 8px">'
        f'<span style="font-size:26px;font-weight:800;color:{ACCENT}">🏏 CricIntel Fan Intelligence</span>'
        f'<span style="color:#888;font-size:12px;margin-left:18px">County Cricket Fan Segmentation Platform</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    tabs = st.tabs([
        "📁 Upload & Configure",
        "📊 Fan Dashboard",
        "🏅 Membership Intelligence",
        "🤝 Sponsorship Intelligence",
        "🏟 Match Intelligence",
        "📄 Report",
    ])

    with tabs[0]:
        render_upload_tab()

    df           = st.session_state.get("df")
    club_name    = st.session_state.get("club_name",     "Surrey CCC")
    county_format= st.session_state.get("county_format", "County Championship")
    extra_cols   = st.session_state.get("extra_cols",    [])

    if df is None:
        for tab in tabs[1:]:
            with tab:
                st.info("Upload a CSV file or load the sample dataset in the **Upload & Configure** tab to unlock this section.")
        return

    with tabs[1]:
        render_dashboard_tab(df.copy(), club_name)

    with tabs[2]:
        render_membership_tab(df.copy(), club_name)

    with tabs[3]:
        render_sponsorship_tab(df.copy(), club_name)

    with tabs[4]:
        render_match_tab(df.copy(), club_name)

    with tabs[5]:
        render_report_tab(df.copy(), club_name, county_format, extra_cols)


if __name__ == "__main__":
    main()
