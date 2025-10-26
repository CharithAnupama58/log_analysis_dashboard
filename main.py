# main.py
from db import init_schema
from ingest import insert_access_log, insert_app_log

if __name__ == "__main__":
    init_schema()
    insert_access_log({
        "ip": "192.168.1.10",
        "timestamp": "2025-10-26T09:05:00.123Z",
        "method": "GET",
        "path": "/api/health",
        "httpVersion": "HTTP/1.1",
        "status": 200,
        "bytes": 1234,
        "referer": "-",
        "userAgent": "curl/8.0",
        "responseTime": 12,
        "userId": "user_test"
    })
    insert_app_log({
        "timestamp": "2025-10-26T09:05:00.456Z",
        "user_id": "user_test",
        "session_id": "abc123",
        "response_time_ms": 12,
        "service": "simulator-app",
        "level": "info",
        "event": "health_check",
        "status": 200,
        "message": "OK",
        "warning_type": None,
        "error_code": None,
        "stack_trace": None
    })
    print("✅ Test inserts done.")
