# ingest.py
from sqlalchemy import text, create_engine
from dotenv import load_dotenv
import os, datetime as dt, re, json

load_dotenv()
uri = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(uri, pool_pre_ping=True)

def insert_access(rec: dict):
    q = text("""
        INSERT INTO access_logs
        (ip, ts, method, path, http_version, status, bytes, referer, user_agent, response_time_ms, user_id)
        VALUES (:ip, :ts, :method, :path, :http_version, :status, :bytes, :referer, :user_agent, :response_time_ms, :user_id)
    """)
    rec.setdefault("ts", dt.datetime.utcnow())
    with engine.begin() as conn:
        conn.execute(q, rec)

def insert_app(rec: dict):
    q = text("""
        INSERT INTO application_logs
        (ts, user_id, session_id, response_time_ms, service, level, event, status, message, warning_type, error_code, stack_trace)
        VALUES (:ts, :user_id, :session_id, :response_time_ms, :service, :level, :event, :status, :message, :warning_type, :error_code, :stack_trace)
    """)
    rec.setdefault("ts", dt.datetime.utcnow())
    with engine.begin() as conn:
        conn.execute(q, rec)

# Example: Common Log Format with response time at end: `... 200 123 "-" "UA" 45`
CLF = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[(?P<ts>.*?)\] "(?P<method>\S+)\s(?P<path>\S+)\s(?P<httpver>HTTP/\d\.\d)" (?P<status>\d{3}) (?P<bytes>\d+|-) "(?P<ref>[^"]*)" "(?P<ua>[^"]*)" (?P<rt>\d+)'
)

def parse_apache_line(line: str):
    m = CLF.search(line)
    if not m: return None
    # example ts: 10/Oct/2025:13:55:36 +0530
    ts_str = m.group('ts')
    ts = dt.datetime.strptime(ts_str[:20], "%d/%b/%Y:%H:%M:%S")  # ignores TZ; good enough for demo
    return {
        "ip": m.group('ip'),
        "ts": ts,
        "method": m.group('method'),
        "path": m.group('path'),
        "http_version": m.group('httpver'),
        "status": int(m.group('status')),
        "bytes": 0 if m.group('bytes') == '-' else int(m.group('bytes')),
        "referer": m.group('ref'),
        "user_agent": m.group('ua'),
        "response_time_ms": int(m.group('rt')),
        "user_id": None
    }

if __name__ == "__main__":
    # demo single inserts
    insert_access({
        "ip": "127.0.0.1", "method": "GET", "path": "/api/health",
        "http_version": "HTTP/1.1", "status": 200, "bytes": 321,
        "referer": "-", "user_agent": "curl/8.7", "response_time_ms": 12, "user_id": "userA"
    })
    insert_app({
        "user_id":"userA","session_id":"s1","response_time_ms":12,
        "service":"auth","level":"info","event":"login","status":200,
        "message":"ok","warning_type":None,"error_code":None,"stack_trace":None
    })
    print("✅ Demo inserts done.")
