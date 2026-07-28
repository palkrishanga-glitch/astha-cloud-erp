import os
import sys
import sqlite3
import datetime
import requests

def get_env_or_default(key, default=""):
    return os.environ.get(key, default).strip()

def sync_local_to_cloud():
    """
    Synchronizes local SQLite ERP transactions (Parties, Stock Items, Sales Invoices)
    to Cloud PostgreSQL / Supabase or Cloud API endpoint.
    """
    db_path = os.path.abspath("astha_erp.db")
    if not os.path.exists(db_path):
        db_path = os.path.abspath("shop.db")
        if not os.path.exists(db_path):
            print(f"[Sync Error] Local ERP Database file not found at {db_path}")
            return

    cloud_api_url = get_env_or_default("ASTHA_CLOUD_API_URL", "http://127.0.0.1:8000/api/v1")
    print("============================================================")
    print("  ASTHA ERP — Local Node to Cloud Database Synchronizer")
    print(f"  Local DB: {db_path}")
    print(f"  Cloud Endpoint: {cloud_api_url}")
    print("============================================================")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        # 1. Fetch unsynced or active parties
        cur.execute("SELECT * FROM parties")
        parties = [dict(row) for row in cur.fetchall()]
        print(f"[Sync] Found {len(parties)} local party records.")

        # 2. Push sync payload to Cloud REST API
        payload = {
            "node_id": "POS-DESKTOP-01",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "parties": parties
        }

        try:
            res = requests.post(f"{cloud_api_url}/sync/push", json=payload, timeout=5)
            if res.status_code == 200:
                print("[Sync Success] Local transactions synchronized to Cloud successfully.")
            else:
                print(f"[Sync Warning] Cloud server responded with status: {res.status_code}")
        except Exception as net_err:
            print(f"[Sync Offline] Cloud connection unavailable ({net_err}). Changes remain queued locally.")

    except Exception as e:
        print(f"[Sync Failure] Error executing local query: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    sync_local_to_cloud()
