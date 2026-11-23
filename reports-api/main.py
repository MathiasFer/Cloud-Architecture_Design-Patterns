import json
import os
import sqlite3
import threading
import time
from datetime import datetime
from typing import Optional, Any, Dict
from fastapi import FastAPI
from pydantic import BaseModel
import httpx

app = FastAPI()

DB_PATH = os.getenv("DB_PATH", "reports.db")
FICHA_URL = os.getenv("FICHA_IA_URL", "http://ficha-ia:8001/ficha")

circuit_state = "CLOSED"
consecutive_failures = 0
last_state_change = 0.0
breaker_lock = threading.Lock()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            status TEXT,
            ficha TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

class ReportCreate(BaseModel):
    title: Optional[str] = "Pet Report"
    description: Optional[str] = ""

def fetch_ficha_with_resilience():
    global circuit_state, consecutive_failures, last_state_change
    with breaker_lock:
        if circuit_state == "OPEN":
            if time.time() - last_state_change >= 15.0:
                circuit_state = "HALF_OPEN"
                last_state_change = time.time()
                print("[CIRCUIT HALF_OPEN]", flush=True)
            else:
                print("[CIRCUIT OPEN]", flush=True)
                print("[FALLBACK]", flush=True)
                return None

    success = False
    ficha_result = None

    for attempt in range(1, 4):
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.post(FICHA_URL)
                if resp.status_code == 200:
                    ficha_result = resp.json()
                    success = True
                    break
                else:
                    if attempt < 3:
                        print(f"[RETRY {attempt}/3]", flush=True)
                        time.sleep(0.5 * (2 ** (attempt - 1)))
        except httpx.TimeoutException:
            print("[TIMEOUT]", flush=True)
            if attempt < 3:
                print(f"[RETRY {attempt}/3]", flush=True)
                time.sleep(0.5 * (2 ** (attempt - 1)))
        except Exception:
            if attempt < 3:
                print(f"[RETRY {attempt}/3]", flush=True)
                time.sleep(0.5 * (2 ** (attempt - 1)))

    with breaker_lock:
        if success:
            if circuit_state == "HALF_OPEN":
                circuit_state = "CLOSED"
                consecutive_failures = 0
                last_state_change = time.time()
                print("[CIRCUIT CLOSED]", flush=True)
            elif circuit_state == "CLOSED":
                consecutive_failures = 0
            return ficha_result
        else:
            if circuit_state == "HALF_OPEN":
                circuit_state = "OPEN"
                last_state_change = time.time()
                print("[CIRCUIT OPEN]", flush=True)
            else:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    circuit_state = "OPEN"
                    last_state_change = time.time()
                    print("[CIRCUIT OPEN]", flush=True)
            print("[FALLBACK]", flush=True)
            return None

@app.post("/reports")
def create_report(payload: ReportCreate):
    ficha = fetch_ficha_with_resilience()
    status = "completed" if ficha is not None else "pending"
    ficha_str = json.dumps(ficha) if ficha is not None else None
    created_at = datetime.utcnow().isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reports (title, description, status, ficha, created_at) VALUES (?, ?, ?, ?, ?)",
        (payload.title, payload.description, status, ficha_str, created_at)
    )
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": report_id,
        "title": payload.title,
        "description": payload.description,
        "status": status,
        "ficha": ficha,
        "created_at": created_at
    }

@app.get("/reports")
def list_reports():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, status, ficha, created_at FROM reports ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "id": r[0],
            "title": r[1],
            "description": r[2],
            "status": r[3],
            "ficha": json.loads(r[4]) if r[4] else None,
            "created_at": r[5]
        })
    return results

@app.get("/breaker")
def get_breaker():
    with breaker_lock:
        return {
            "state": circuit_state,
            "consecutive_failures": consecutive_failures,
            "last_state_change": last_state_change
        }

@app.get("/health")
def health():
    return {"status": "ok"}
