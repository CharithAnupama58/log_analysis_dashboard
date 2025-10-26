# init_schema.py
from sqlalchemy import text
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()
uri = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(uri, pool_pre_ping=True)

DDL = """
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
"""

if __name__ == "__main__":
  with engine.begin() as conn:
      for stmt in [s.strip()+";" for s in DDL.split(";") if s.strip()]:
          conn.execute(text(stmt))
  print("✅ Schema ready (access_logs, application_logs).")
