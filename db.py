# db.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "log_analytics")
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASS = os.getenv("DB_PASS", "1234")

URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(URI, pool_pre_ping=True)

def init_schema():
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS access_logs (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
            ip VARCHAR(45),
            ts DATETIME(6) NOT NULL,
            method VARCHAR(10),
            path TEXT,
            http_version VARCHAR(10),
            status INT,
            bytes INT,
            referer TEXT,
            user_agent TEXT,
            response_time_ms INT,
            user_id VARCHAR(64),
            INDEX (ts),
            INDEX (status),
            INDEX (ip)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """))
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS application_logs (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
            ts DATETIME(6) NOT NULL,
            user_id VARCHAR(64),
            session_id VARCHAR(64),
            response_time_ms INT,
            service VARCHAR(128),
            level ENUM('debug','info','warn','error') DEFAULT 'info',
            event VARCHAR(128),
            status INT,
            message TEXT,
            warning_type VARCHAR(128),
            error_code VARCHAR(128),
            stack_trace TEXT,
            INDEX (ts),
            INDEX (level),
            INDEX (event),
            INDEX (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """))
    print("✅ Schema ready.")
