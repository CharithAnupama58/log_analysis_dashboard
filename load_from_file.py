# load_from_file.py
import os, json, datetime as dt
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(URI, pool_pre_ping=True)

def iso_to_dt(s):
    # handles "2025-10-26T03:08:23.121Z" -> naive UTC datetime
    if not s: return None
    s = s.replace("Z", "+00:00")
    return dt.datetime.fromisoformat(s).replace(tzinfo=None)

def insert_access(conn, d):
    q = text("""
        INSERT INTO access_logs
        (ip, ts, method, path, http_version, status, bytes, referer, user_agent, response_time_ms, user_id)
        VALUES (:ip, :ts, :method, :path, :http_version, :status, :bytes, :referer, :user_agent, :response_time_ms, :user_id)
    """)
    conn.execute(q, {
        "ip": d.get("ip"),
        "ts": iso_to_dt(d.get("timestamp")),
        "method": d.get("method"),
        "path": d.get("path"),
        "http_version": d.get("httpVersion"),
        "status": d.get("status"),
        "bytes": d.get("bytes") or 0,
        "referer": d.get("referer"),
        "user_agent": d.get("userAgent"),
        "response_time_ms": d.get("responseTime"),
        "user_id": d.get("userId"),
    })

def insert_app(conn, d):
    q = text("""
        INSERT INTO application_logs
        (ts, user_id, session_id, response_time_ms, service, level, event, status, message, warning_type, error_code, stack_trace)
        VALUES (:ts, :user_id, :session_id, :response_time_ms, :service, :level, :event, :status, :message, :warning_type, :error_code, :stack_trace)
    """)
    conn.execute(q, {
        "ts": iso_to_dt(d.get("timestamp")),
        "user_id": d.get("user_id"),
        "session_id": d.get("session_id"),
        "response_time_ms": d.get("response_time_ms"),
        "service": d.get("service"),
        "level": d.get("level"),
        "event": d.get("event"),
        "status": d.get("status"),
        "message": d.get("message"),
        "warning_type": d.get("warning_type"),
        "error_code": d.get("error_code"),
        "stack_trace": d.get("stack_trace"),
    })

def load_logs(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        blob = json.load(f)

    logs = blob.get("logs", []) if isinstance(blob, dict) else blob
    n_access = n_app = 0
    with engine.begin() as conn:
        for item in logs:
            kind = item.get("log_type")
            data = item.get("data", {})
            if kind == "access":
                insert_access(conn, data); n_access += 1
            elif kind == "application":
                insert_app(conn, data); n_app += 1
    print(f"✅ Loaded: access={n_access}, application={n_app}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python load_from_file.py <path-to-json>")
        raise SystemExit(2)
    load_logs(sys.argv[1])
