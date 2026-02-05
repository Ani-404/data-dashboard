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

