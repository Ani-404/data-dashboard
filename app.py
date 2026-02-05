# Minimal Streamlit ] dashboard for quick testing
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Internship Dashboard", layout="wide")
st.title("Internship Dashboard")
st.markdown("A compact, demo-friendly app to browse internship listings.")

DATA_PATH = Path("data/internships.csv")  # put your CSV here

@st.cache_data
def load_data(path=DATA_PATH):
    if not Path(path).exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df

def to_numeric_series(s):
    # keep digits and dots, then coerce
    tmp = s.astype(str).str.replace(r"[^\d\.]", "", regex=True)
    return pd.to_numeric(tmp, errors="coerce")

df = load_data()

# sidebar: upload + filters
with st.sidebar:
    st.header("Controls")
    st.write("Upload a CSV or use the sample file at `data/internships.csv`.")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded:
        uploaded_df = pd.read_csv(uploaded)
        uploaded_df.columns = [c.strip().lower().replace(" ", "_") for c in uploaded_df.columns]
        uploaded_df.to_csv(DATA_PATH, index=False)
        st.success("Saved to data/internships.csv. Refresh the page to load it.")
    st.markdown("---")
    st.subheader("Filters (optional)")
    company_q = st.text_input("Company contains")
    role_q = st.text_input("Role / Title contains")
    loc_q = None
    if "location" in df.columns:
        locs = sorted(df["location"].dropna().unique().tolist())
        loc_q = st.multiselect("Location", options=locs)
    min_stipend = st.text_input("Min stipend (digits only)", value="")

if df.empty:
    st.warning("No data found at data/internships.csv. Upload a CSV in the sidebar or add a file and refresh.")
    st.stop()

# apply filters
filtered = df.copy()

if company_q:
    if "company" in filtered.columns:
        filtered = filtered[filtered["company"].astype(str).str.contains(company_q, case=False, na=False)]

if role_q:
    title_cols = [c for c in filtered.columns if "title" in c or "role" in c or "position" in c]
    if title_cols:
        combined = filtered[title_cols].astype(str).agg(" ".join, axis=1)
        filtered = filtered[combined.str.contains(role_q, case=False, na=False)]
    else:
        combined = filtered.astype(str).agg(" ".join, axis=1)
        filtered = filtered[combined.str.contains(role_q, case=False, na=False)]

if loc_q:
    if "location" in filtered.columns:
        filtered = filtered[filtered["location"].isin(loc_q)]

if min_stipend.strip():
    try:
        min_val = float("".join(ch for ch in min_stipend if (ch.isdigit() or ch == ".")))
        if "stipend" in filtered.columns:
            s_num = to_numeric_series(filtered["stipend"])
            filtered = filtered[s_num >= min_val]
    except Exception:
        # keep simple: ignore parsing errors
        pass

# top row of metrics
c1, c2, c3 = st.columns(3)
c1.metric("Total listings", len(filtered))
c2.metric("Unique companies", int(filtered["company"].nunique()) if "company" in filtered.columns else "n/a")
c3.metric("Unique locations", int(filtered["location"].nunique()) if "location" in filtered.columns else "n/a")

st.markdown("")


