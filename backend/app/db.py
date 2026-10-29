import hashlib, json, os, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from .core.config import DATA_DIR

DB=DATA_DIR/"local.db"

def connect():
    DATA_DIR.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT NOT NULL, role TEXT NOT NULL)")
    c.execute("CREATE TABLE IF NOT EXISTS analyses (id TEXT PRIMARY KEY, created_at TEXT, model TEXT, result_json TEXT, input_hash TEXT, case_id TEXT, feedback_json TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY AUTOINCREMENT, utc TEXT, actor TEXT, action TEXT, model_hash TEXT, case_id TEXT, input_hash TEXT, prev_hash TEXT, entry_hash TEXT)")
    c.commit(); return c

def audit(c,actor,action,model_hash="",case_id="",input_hash=""):
    prev=c.execute("SELECT entry_hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
    previous=prev[0] if prev else "0"*64
    utc=datetime.now(timezone.utc).isoformat()
    fields=[utc,actor,action,model_hash,case_id,input_hash,previous]
    digest=hashlib.sha256("\0".join(fields).encode()).hexdigest()
    c.execute("INSERT INTO audit(utc,actor,action,model_hash,case_id,input_hash,prev_hash,entry_hash) VALUES(?,?,?,?,?,?,?,?)",(*fields,digest)); c.commit()

def audit_valid(c):
    previous="0"*64
    for r in c.execute("SELECT * FROM audit ORDER BY seq"):
        fields=[r["utc"],r["actor"],r["action"],r["model_hash"],r["case_id"],r["input_hash"],previous]
        digest=hashlib.sha256("\0".join(fields).encode()).hexdigest()
        if r["prev_hash"]!=previous or r["entry_hash"]!=digest:return False
        previous=digest
    return True
