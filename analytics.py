# analytics.py
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os, numpy as np, pandas as pd

load_dotenv()
uri = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(uri, pool_pre_ping=True)

with engine.begin() as conn:
    df = pd.read_sql(text("""
        SELECT response_time_ms FROM access_logs
        WHERE ts >= NOW() - INTERVAL 1 DAY AND response_time_ms IS NOT NULL
    """), conn)

if df.empty:
    print("No data in last 24h")
else:
    p95 = float(np.percentile(df['response_time_ms'], 95))
    print(f"p95 response time (24h): {p95:.1f} ms")
