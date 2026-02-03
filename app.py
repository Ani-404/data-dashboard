# Minimal Streamlit ] dashboard for quick testing
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Mini Internship Dashboard", layout="centered")
st.title("Mini Internship Dashboard (test)")

DATA_PATH = Path("data/sample_internships.csv")

@st.cache_data
def load_data(path=DATA_PATH):
    if not Path(path).exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df

df = load_data()

if df.empty:
    st.warning("No data found at data/sample_internships.csv. Add a CSV and refresh.")
    st.stop()

company_filter = st.text_input("Filter by company (contains):")
if company_filter:
    filtered = df[df["company"].str.contains(company_filter, case=False, na=False)]
else:
    filtered = df

st.markdown(f"**Showing {len(filtered)} listings**")

# Show only core columns to keep it compact
show_cols = [c for c in ["title", "company", "location", "stipend", "date_posted", "url"] if c in filtered.columns]
st.dataframe(filtered[show_cols].reset_index(drop=True), height=400)
