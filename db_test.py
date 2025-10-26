# db_test.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "log_analytics")
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASS = os.getenv("DB_PASS", "1234")

uri = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(uri, pool_pre_ping=True)

def main():
    print("Connecting…")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ping (
                id INT PRIMARY KEY AUTO_INCREMENT,
                note VARCHAR(50) NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """))
        conn.execute(text("INSERT INTO ping (note) VALUES (:n)"), {"n": "ok"})
        rows = conn.execute(text("SELECT * FROM ping ORDER BY id DESC LIMIT 5")).fetchall()
        print("Last rows:", rows)
    print("✅ Python → MySQL path works!")

if __name__ == "__main__":
    main()
