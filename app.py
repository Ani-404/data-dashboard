import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Internship Dashboard", layout="wide")
st.title("Internship Dashboard")
st.markdown("A compact, demo-friendly app to browse internship listings.")

DATA_PATH = Path("data/sample.csv")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df


@st.cache_data
def load_data(path: str, modified_ns: int | None):
    _ = modified_ns  # cache key input, value not used directly
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    return normalize_columns(pd.read_csv(p))


def to_numeric_series(s: pd.Series) -> pd.Series:
    tmp = s.astype(str).str.replace(r"[^\d\.]", "", regex=True)
    return pd.to_numeric(tmp, errors="coerce")


def detect_date_col(df: pd.DataFrame) -> str | None:
    for c in df.columns:
        parsed = pd.to_datetime(df[c], errors="coerce")
        if parsed.notna().mean() >= 0.6:
            return c
    return None


def safe_sorted_unique(values: pd.Series) -> list:
    items = values.dropna().astype(str).unique().tolist()
    return sorted(items, key=lambda x: x.lower())


file_mtime = DATA_PATH.stat().st_mtime_ns if DATA_PATH.exists() else None
base_df = load_data(str(DATA_PATH), file_mtime)

if "uploaded_df" not in st.session_state:
    st.session_state.uploaded_df = None
if "uploaded_name" not in st.session_state:
    st.session_state.uploaded_name = None

# sidebar: upload + filters
with st.sidebar:
    st.header("Controls")
    st.write(f"Upload a CSV or use the sample file at `{DATA_PATH}`.")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded is not None:
        try:
            uploaded_df = normalize_columns(pd.read_csv(uploaded))
            st.session_state.uploaded_df = uploaded_df
            st.session_state.uploaded_name = uploaded.name
            st.success(f"Loaded `{uploaded.name}`.")
            st.rerun()
        except Exception as e:
            st.error(f"Could not read CSV: {e}")

    if st.session_state.uploaded_df is not None:
        st.caption(f"Using uploaded file: `{st.session_state.uploaded_name}`")
        if st.button("Revert to sample data"):
            st.session_state.uploaded_df = None
            st.session_state.uploaded_name = None
            st.rerun()

    st.markdown("---")
    st.subheader("Filters (optional)")
    company_q = st.text_input("Company contains")
    role_q = st.text_input("Role / Title contains")
    global_q = st.text_input("Search any column")
    min_stipend = st.text_input("Min stipend (digits only)", value="")

# active dataframe source
if st.session_state.uploaded_df is not None:
    df = st.session_state.uploaded_df.copy()
else:
    df = base_df.copy()

if df.empty:
    st.warning(f"No data found at {DATA_PATH}. Upload a CSV in the sidebar or add a file and refresh.")
    st.stop()

# apply filters
filtered = df.copy()

if company_q and "company" in filtered.columns:
    filtered = filtered[filtered["company"].astype(str).str.contains(company_q, case=False, na=False)]

if role_q:
    title_cols = [c for c in filtered.columns if "title" in c or "role" in c or "position" in c]
    if title_cols:
        combined = filtered[title_cols].astype(str).agg(" ".join, axis=1)
        filtered = filtered[combined.str.contains(role_q, case=False, na=False)]
    else:
        combined = filtered.astype(str).agg(" ".join, axis=1)
        filtered = filtered[combined.str.contains(role_q, case=False, na=False)]

if global_q:
    combined = filtered.astype(str).agg(" ".join, axis=1)
    filtered = filtered[combined.str.contains(global_q, case=False, na=False)]

if min_stipend.strip() and "stipend" in filtered.columns:
    try:
        min_val = float("".join(ch for ch in min_stipend if (ch.isdigit() or ch == ".")))
        s_num = to_numeric_series(filtered["stipend"])
        filtered = filtered[s_num >= min_val]
    except Exception:
        pass

# optional location filter after df is known
with st.sidebar:
    if "location" in df.columns:
        locs = safe_sorted_unique(df["location"])
        loc_q = st.multiselect("Location", options=locs)
        if loc_q and "location" in filtered.columns:
            filtered = filtered[filtered["location"].astype(str).isin(loc_q)]

# top row of metrics
c1, c2, c3 = st.columns(3)
c1.metric("Total rows", len(filtered))

if "company" in filtered.columns:
    c2.metric("Unique companies", int(filtered["company"].nunique()))
else:
    c2.metric("Columns", len(filtered.columns))

if "location" in filtered.columns:
    c3.metric("Unique locations", int(filtered["location"].nunique()))
else:
    missing_cells = int(filtered.isna().sum().sum())
    c3.metric("Missing cells", missing_cells)

st.markdown("")

# two-column layout: charts + table
left, right = st.columns([2, 3])

with left:
    shown_chart = False
    if "company" in filtered.columns:
        st.subheader("Top companies")
        top_companies = filtered["company"].astype(str).value_counts().head(10)
        st.bar_chart(top_companies)
        shown_chart = True

    if "date_posted" in filtered.columns:
        try:
            st.subheader("Listings over time")
            tmp = filtered.copy()
            tmp["date_posted"] = pd.to_datetime(tmp["date_posted"], errors="coerce")
            counts = tmp.set_index("date_posted").resample("W").size()
            st.line_chart(counts)
            shown_chart = True
        except Exception:
            pass

    # generic fallback charts for non-internship CSVs
    if not shown_chart:
        cat_cols = [
            c for c in filtered.columns
            if filtered[c].dtype == "object" and 1 < filtered[c].nunique(dropna=True) <= 25
        ]
        if cat_cols:
            cat_col = cat_cols[0]
            st.subheader(f"Top values in {cat_col}")
            st.bar_chart(filtered[cat_col].astype(str).value_counts().head(10))
            shown_chart = True

    date_col = detect_date_col(filtered)
    numeric_cols = filtered.select_dtypes(include="number").columns.tolist()
    if date_col and numeric_cols:
        try:
            st.subheader(f"{numeric_cols[0]} over time")
            tmp = filtered[[date_col, numeric_cols[0]]].copy()
            tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
            tmp = tmp.dropna(subset=[date_col])
            series = tmp.set_index(date_col)[numeric_cols[0]].resample("W").mean()
            st.line_chart(series)
        except Exception:
            pass

    if not shown_chart:
        st.write("No chartable columns found in this CSV yet.")

with right:
    st.subheader("Listings")
    preferred_cols = ["title", "company", "location", "stipend", "date_posted", "url"]
    show_cols = [c for c in preferred_cols if c in filtered.columns]
    table_df = filtered[show_cols] if show_cols else filtered
    st.dataframe(table_df.reset_index(drop=True), height=520)

# download filtered CSV
csv_bytes = filtered.to_csv(index=False).encode("utf-8")
st.download_button("Download filtered CSV", data=csv_bytes, file_name="filtered_data.csv", mime="text/csv")

st.markdown("---")
st.caption(f"Simple demo: using `{DATA_PATH}` by default, or any uploaded CSV for this session.")
