# dashboard.py
# Streamlit dashboard that reads logs from an HTTP API and renders analytics.
# - Auto-refresh via streamlit-autorefresh
# - Flexible FIELD_MAP so you can map your API's JSON keys
# - Uses use_container_width for layout friendliness
# - Uses floor('min') for minute binning

import os
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# ========== CONFIG ==========
API_URL = os.getenv("API_URL", "http://139.99.236.174:4000/api/logs/latest")

API_HEADERS = {}
# Example:
# API_HEADERS = {"x-api-key": st.secrets.get("API_KEY", os.getenv("API_KEY", ""))}

st.set_page_config(page_title="Log Dashboard (API)", layout="wide")
st.title("📊 Log Dashboard via API")

# === CONFIGURABLE FIELD MAPPING ===
FIELD_MAP = {
    "timestamp": ["ts", "timestamp", "time", "createdAt", "@timestamp"],
    "status":    ["status", "statusCode", "code", "http_status"],
    "path":      ["path", "endpoint", "url", "route", "request_path"],
    "method":    ["method", "httpMethod"],
    "latency":   ["response_time_ms", "latency_ms", "duration_ms", "responseTime", "response_time", "rt_ms", "latency", "duration"],
    "service":   ["service", "svc", "module"],
    "level":     ["level", "severity"],
    "event":     ["event", "event_name", "action"],
    "user":      ["user_id", "userId", "user", "uid"],
    "session":   ["session_id", "sessionId", "session"],
}

def _pick_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Return the first matching column from candidates (case-sensitive), also supports flattened keys."""
    for c in candidates:
        if c in df.columns:
            return c
        lc = c.lower()
        for col in df.columns:
            if col.lower() == lc or col.lower().endswith(f".{lc}"):
                return col
    return None

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("Filters")
    minutes = st.slider("Lookback (minutes)", 5, 240, 15, step=5)
    status_filter = st.selectbox("Status class", ["All", "2xx", "3xx", "4xx", "5xx"])
    level_filter = st.selectbox("Level (app logs)", ["All", "info", "warn", "error"])
    service_filter = st.text_input("Service contains", "")
    path_contains = st.text_input("Path contains", "")
    auto = st.toggle("Auto-refresh every 30s", value=False)
    st.caption(f"Endpoint: {API_URL}?minutes={minutes}")

if auto:
    st_autorefresh(interval=30_000, key="refresh")

# ========== FETCH ==========
@st.cache_data(ttl=20)
def fetch_logs(minutes: int):
    import requests
    url = f"{API_URL}?minutes={minutes}"
    r = requests.get(url, timeout=25, headers=API_HEADERS)
    r.raise_for_status()
    js = r.json()
    if isinstance(js, list):
        rows = js
    elif isinstance(js, dict):
        rows = js.get("rows") or js.get("data") or js.get("logs") or []
    else:
        rows = []
    return rows

try:
    rows = fetch_logs(minutes)
except Exception as e:
    st.error(f"Failed to fetch logs: {e}")
    st.stop()

if not rows:
    st.warning("No data returned for this time window.")
    st.stop()

df_raw = pd.json_normalize(rows)

with st.expander("Raw data (preview & columns)"):
    # FIX: st.write(..., width="stretch") -> st.dataframe(..., use_container_width=True)
    st.dataframe(df_raw.head(10), use_container_width=True)
    st.code("\n".join([str(c) for c in df_raw.columns]), language="text")

# ========== NORMALIZE ==========
df = df_raw.copy()

ts_col  = _pick_col(df, FIELD_MAP["timestamp"])
st_col  = _pick_col(df, FIELD_MAP["status"])
rt_col  = _pick_col(df, FIELD_MAP["latency"])
path_c  = _pick_col(df, FIELD_MAP["path"])
meth_c  = _pick_col(df, FIELD_MAP["method"])
svc_c   = _pick_col(df, FIELD_MAP["service"])
lvl_c   = _pick_col(df, FIELD_MAP["level"])
evt_c   = _pick_col(df, FIELD_MAP["event"])
usr_c   = _pick_col(df, FIELD_MAP["user"])
ses_c   = _pick_col(df, FIELD_MAP["session"])

# Standardized columns
df["ts"] = pd.to_datetime(df[ts_col], errors="coerce") if ts_col else pd.NaT
df["status"] = pd.to_numeric(df[st_col], errors="coerce") if st_col else pd.NA
df["response_time_ms"] = pd.to_numeric(df[rt_col], errors="coerce") if rt_col else pd.NA
df["path"]       = df[path_c] if path_c else pd.NA
df["method"]     = df[meth_c] if meth_c else pd.NA
df["service"]    = df[svc_c]  if svc_c  else pd.NA
df["level"]      = df[lvl_c]  if lvl_c  else pd.NA
df["event"]      = df[evt_c]  if evt_c  else pd.NA
df["user_id"]    = df[usr_c]  if usr_c  else pd.NA
df["session_id"] = df[ses_c]  if ses_c  else pd.NA

st.info(
    f"Using columns → ts: `{ts_col}`, status: `{st_col}`, latency: `{rt_col}`, "
    f"path: `{path_c}`, method: `{meth_c}`, service: `{svc_c}`, level: `{lvl_c}`, event: `{evt_c}`"
)

# ========== FILTERS ==========
F = df.copy()

# Status class filter
if status_filter != "All" and "status" in F.columns:
    if status_filter == "2xx": F = F[(F["status"]>=200) & (F["status"]<300)]
    if status_filter == "3xx": F = F[(F["status"]>=300) & (F["status"]<400)]
    if status_filter == "4xx": F = F[(F["status"]>=400) & (F["status"]<500)]
    if status_filter == "5xx": F = F[(F["status"]>=500)]

# Level filter
if level_filter != "All" and "level" in F.columns:
    F = F[F["level"].astype(str).str.lower() == level_filter.lower()]

# Contains filters
if service_filter and "service" in F.columns:
    F = F[F["service"].astype(str).str.contains(service_filter, case=False, na=False)]
if path_contains and "path" in F.columns:
    F = F[F["path"].astype(str).str.contains(path_contains, case=False, na=False)]

# ========== TABLE PREVIEW ==========
st.metric("Rows", len(F))
with st.expander("Filtered data (top 1000 rows)"):
    # FIX: width="stretch" -> use_container_width
    st.dataframe(F.head(1000), use_container_width=True)

# ========== KPIs ==========
k1, k2, k3, k4, k5 = st.columns(5)
# throughput
k1.metric("Throughput (rows/min)", round(len(F) / max(1, minutes), 2))

# latency
if "response_time_ms" in F.columns and F["response_time_ms"].notna().any():
    k2.metric("Avg RT (ms)", round(F["response_time_ms"].mean(), 1))
    k3.metric("P95 RT (ms)", round(F["response_time_ms"].quantile(0.95), 1))
else:
    k2.metric("Avg RT (ms)", "—")
    k3.metric("P95 RT (ms)", "—")

# errors
if "status" in F.columns and F["status"].notna().any():
    err4 = int(((F["status"]>=400) & (F["status"]<500)).sum())
    err5 = int((F["status"]>=500).sum())
    k4.metric("4xx", err4)
    k5.metric("5xx", err5)
else:
    k4.metric("4xx", "—")
    k5.metric("5xx", "—")

st.divider()

# ========== TRENDS ==========
if "ts" in F.columns and pd.api.types.is_datetime64_any_dtype(F["ts"]):
    T = F.dropna(subset=["ts"]).copy()
    if not T.empty:
        T["minute"] = T["ts"].dt.floor("min")
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Avg Response Time per Minute")
            if "response_time_ms" in T.columns and T["response_time_ms"].notna().any():
                rt = T.groupby("minute")["response_time_ms"].mean()
                if not rt.empty:
                    st.line_chart(rt)
                else:
                    st.info("No latency data to plot.")
            else:
                st.info("No latency column detected.")

        with c2:
            st.subheader("5xx Error Rate per Minute (%)")
            if "status" in T.columns and T["status"].notna().any():
                grp = T.groupby("minute")
                err = (grp.apply(lambda g: (g["status"]>=500).mean()*100)).rename("5xx %")
                if not err.empty:
                    st.line_chart(err)
                else:
                    st.info("No status data to plot.")
            else:
                st.info("No status column detected.")
else:
    st.info("No timestamp column detected; cannot draw trends.")

st.divider()

# ========== TOP ENDPOINTS ==========
if "path" in F.columns and F["path"].notna().any():
    st.subheader("Top Endpoints (min 5 hits)")
    agg = F.groupby("path").agg(
        n=("path","count"),
        avg_ms=("response_time_ms","mean"),
        p95_ms=("response_time_ms", lambda s: s.quantile(0.95) if s.notna().any() else None),
        err4xx=("status", lambda s: ((s>=400) & (s<500)).sum() if s.notna().any() else 0),
        err5xx=("status", lambda s: (s>=500).sum() if s.notna().any() else 0),
    ).sort_values(by=["p95_ms","avg_ms","n"], ascending=[False, False, False]).fillna(0)

    agg = agg[agg["n"] >= 5].head(25)
    # FIX: width="stretch" -> use_container_width
    st.dataframe(agg, use_container_width=True)
else:
    st.info("No 'path' column detected; skipping endpoint table.")
