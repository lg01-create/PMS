
import os, sqlite3
from urllib.parse import urlparse

def resolve_sqlite_path(default_path="data/app.db"):
    db_url = os.getenv("DATABASE_URL", "").strip()
    if not db_url:
        return default_path
    if not db_url.lower().startswith("sqlite:"):
        raise SystemExit("This helper only supports SQLite DATABASE_URL")
    parsed = urlparse(db_url)
    path = parsed.path.lstrip("/")
    if db_url.startswith("sqlite:///C:") or db_url.startswith("sqlite:///D:"):
        path = db_url.replace("sqlite:///", "")
    return path or default_path

def main():
    db_path = resolve_sqlite_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    print(f"[DB] Using SQLite file: {db_path}")
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(bookmark)")
        cols = [r[1] for r in cur.fetchall()]
        if "category" not in cols:
            print("[DB] Adding 'category' column to bookmark ...")
            cur.execute("ALTER TABLE bookmark ADD COLUMN category VARCHAR(20) DEFAULT 'other'")
            conn.commit()
            print("[DB] 'category' column added to bookmark")
        else:
            print("[DB] 'category' column already present")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
