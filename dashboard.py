# dashboard.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
# add at top
import streamlit as st, os
from sqlalchemy import create_engine

host = st.secrets.get("DB_HOST", os.getenv("DB_HOST"))
port = st.secrets.get("DB_PORT", os.getenv("DB_PORT", "3306"))
name = st.secrets.get("DB_NAME", os.getenv("DB_NAME"))
user = st.secrets.get("DB_USER", os.getenv("DB_USER"))
pw   = st.secrets.get("DB_PASS", os.getenv("DB_PASS"))

URI = f"mysql+pymysql://{user}:{pw}@{host}:{port}/{name}"
engine = create_engine(URI, pool_pre_ping=True)

# Load DB credentials from .env
load_dotenv()
URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(URI, pool_pre_ping=True)

st.set_page_config(page_title="Log Analytics Dashboard", layout="wide")
st.title("📊 Log Analytics Dashboard")

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    hours = st.slider("Last N hours", 1, 72, 24)
    st.divider()
    show = st.radio("Data type", ["Access Logs", "Application Logs"])

# Load data
@st.cache_data(ttl=60)
def load_data(table, hours):
    query = f"""
        SELECT * FROM {table}
        WHERE ts >= NOW() - INTERVAL {hours} HOUR
        ORDER BY ts DESC
        LIMIT 20000;
    """
    return pd.read_sql(query, engine)

table = "access_logs" if show == "Access Logs" else "application_logs"
df = load_data(table, hours)

if df.empty:
    st.warning("No records found for this time range.")
    st.stop()

st.metric("Rows Loaded", len(df))

# Display table
st.dataframe(df.head(1000), use_container_width=True)

# --- Basic KPIs ---
if show == "Access Logs":
    st.subheader("Performance Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Avg Response (ms)", round(df["response_time_ms"].mean(), 1))
    col2.metric("P95 (ms)", round(df["response_time_ms"].quantile(0.95), 1))
    col3.metric("4xx Errors", int((df["status"].between(400,499)).sum()))
    col4.metric("5xx Errors", int((df["status"]>=500).sum()))

    # Charts
    st.subheader("📈 Response Time Distribution")
    st.bar_chart(df["response_time_ms"])

    st.subheader("🕐 Requests Over Time")
    df["minute"] = pd.to_datetime(df["ts"]).dt.floor("T")
    st.line_chart(df.groupby("minute")["response_time_ms"].mean())

elif show == "Application Logs":
    st.subheader("Error Breakdown")
    err_df = df[df["level"].isin(["error","warn"])]
    st.bar_chart(err_df["level"].value_counts())

    st.subheader("Top Services by Errors")
    top = err_df.groupby("service")["level"].count().sort_values(ascending=False).head(10)
    st.bar_chart(top)

    st.subheader("Event Frequency")
    ev = df["event"].value_counts().head(20)
    st.bar_chart(ev)

st.success("✅ Dashboard loaded successfully.")

