
import sqlite3
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil
from typing import Optional, List
from auth import verify_password, get_password_hash, create_access_token, decode_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from brain import SecureRAG

DB_FILE = 'enterprise.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT,
                role TEXT
              )''')
    # Sessions Table
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                created_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
              )''')
    # Messages Table
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                role TEXT,
                content TEXT,
                created_at TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
              )''')
    # Audit Logs
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  timestamp TEXT, role TEXT, query TEXT, status_code INTEGER)''')
    conn.commit()
    conn.close()

init_db()

def log_query(role: str, query: str, status_code: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO audit_logs (timestamp, role, query, status_code) VALUES (?, ?, ?, ?)",
              (datetime.now().isoformat(), role if role else "UNKNOWN", query, status_code))
    conn.commit()
    conn.close()

app = FastAPI(title="Enterprise Secure RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag = SecureRAG()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    username: str = payload.get("sub")
    role: str = payload.get("role")
    user_id: int = payload.get("user_id")
    if username is None or role is None or user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    # Verify user exists
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
        
    return {"user_id": user_id, "username": username, "role": role}

# --- Pydantic Models ---
class UserCreate(BaseModel):
    username: str
    password: str
    admin_passkey: Optional[str] = None

class QueryRequest(BaseModel):
    session_id: Optional[int] = None
    question: str

# --- AUTH ENDPOINTS ---
@app.post("/register")
def register(user: UserCreate):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (user.username,))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check Admin Passkey
    role = "employee"
    if user.admin_passkey:
        if user.admin_passkey == "ELEVATE2026":
            role = "admin"
        else:
            conn.close()
            raise HTTPException(status_code=400, detail="Invalid Admin Passkey")
            
    hashed_password = get_password_hash(user.password)
    c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
              (user.username, hashed_password, role))
    conn.commit()
    conn.close()
    return {"message": "User registered successfully", "role": role}

@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, username, password_hash, role FROM users WHERE username=?", (form_data.username,))
    user = c.fetchone()
    conn.close()

    if not user or not verify_password(form_data.password, user[2]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user[1], "role": user[3], "user_id": user[0]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user[3]}

# --- CHAT & RAG ENDPOINTS ---

@app.get("/sessions")
def get_sessions(current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, title, created_at FROM sessions WHERE user_id=? ORDER BY created_at DESC", (current_user["user_id"],))
    sessions = [{"id": row[0], "title": row[1], "created_at": row[2]} for row in c.fetchall()]
    conn.close()
    return {"sessions": sessions}

@app.get("/sessions/{session_id}/messages")
def get_messages(session_id: int, current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # verify ownership
    c.execute("SELECT id FROM sessions WHERE id=? AND user_id=?", (session_id, current_user["user_id"]))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="Session not found or forbidden")
        
    c.execute("SELECT id, role, content, created_at FROM messages WHERE session_id=? ORDER BY id ASC", (session_id,))
    messages = [{"id": row[0], "role": row[1], "content": row[2], "created_at": row[3]} for row in c.fetchall()]
    conn.close()
    return {"messages": messages}

@app.post("/ask")
def ask_question(request: QueryRequest, current_user: dict = Depends(get_current_user)):
    role = current_user["role"]
    user_id = current_user["user_id"]
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    session_id = request.session_id
    if not session_id:
        # Create new session
        title = request.question[:30] + "..." if len(request.question) > 30 else request.question
        timestamp = datetime.now().isoformat()
        c.execute("INSERT INTO sessions (user_id, title, created_at) VALUES (?, ?, ?)", (user_id, title, timestamp))
        session_id = c.lastrowid
        chat_history = []
    else:
        # Verify ownership
        c.execute("SELECT id FROM sessions WHERE id=? AND user_id=?", (session_id, user_id))
        if not c.fetchone():
            conn.close()
            log_query(role, request.question, 403)
            raise HTTPException(status_code=403, detail="Session forbidden")
        
        # Load last N messages for context
        c.execute("SELECT role, content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT 6", (session_id,))
        rows = c.fetchall()
        chat_history = [{"role": row[0], "content": row[1]} for row in reversed(rows)]

    # save user msg
    timestamp = datetime.now().isoformat()
    c.execute("INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
              (session_id, "user", request.question, timestamp))
    conn.commit()

    try:
        # Process via Secure Brain (Pass history)
        result = rag.query(request.question, role, chat_history)
        answer = result["answer"]
        sources = result["sources"]

        # save assistant msg
        timestamp2 = datetime.now().isoformat()
        c.execute("INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                  (session_id, "assistant", answer, timestamp2))
        conn.commit()

        log_query(role, request.question, 200)
        return {"session_id": session_id, "role_used": role, "answer": answer, "sources": sources}
    except Exception as e:
        log_query(role, request.question, 500)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/upload")
def upload_document(
    file: UploadFile = File(...), 
    target_role: str = Form(...), 
    current_user: dict = Depends(get_current_user)
):
    requester_role = current_user["role"]
    if requester_role != "admin":
        log_query(requester_role, f"Attempted to upload {file.filename}", 403)
        raise HTTPException(status_code=403, detail="Only Admins can upload documents")
    
    role = target_role.strip().lower()
    if role not in ["admin", "manager", "employee", "auto"]:
        raise HTTPException(status_code=400, detail="Invalid Target Role")

    safe_name = os.path.basename(file.filename or "").strip()
    if not safe_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
    os.makedirs("data/uploads", exist_ok=True)
    file_path = os.path.join("data", "uploads", safe_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        final_role = rag.ingest_document(file_path, role)
        log_query(requester_role, f"Uploaded {safe_name} (Auto-Classified: {final_role})", 200)
        return {
            "status": "success", 
            "message": f"Successfully ingested {safe_name}",
            "detected_role": final_role
        }
    except Exception as e:
        log_query(requester_role, f"Failed to upload {safe_name}", 500)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audit_logs")
def get_audit_logs(current_user: dict = Depends(get_current_user)):
    # Returns last 10 logs for the dashboard
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT timestamp, role, event, status_code FROM audit_logs ORDER BY id DESC LIMIT 10")
    logs = [{"timestamp": r[0], "role": r[1], "event": r[2], "status": r[3]} for r in c.fetchall()]
    conn.close()
    return logs

@app.get("/admin/stats")
def get_admin_stats(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM audit_logs")
    total_queries = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM audit_logs WHERE status_code = 403")
    total_blocks = c.fetchone()[0]
    
    # Active Users (count distinct valid users in db)
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    conn.close()
    
    return {
        "total_queries": total_queries,
        "total_blocks": total_blocks,
        "total_users": total_users
    }

@app.get("/documents")
def get_documents(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    collection = rag.vector_db.get(include=["metadatas"])
    metadatas = collection.get("metadatas", [])
    
    # Extract unique files and their clearance
    docs_map = {}
    for meta in metadatas:
        if meta and "source" in meta:
            src = meta["source"]
            role = meta.get("allowed_role", "unknown")
            if src not in docs_map:
                docs_map[src] = {"filename": os.path.basename(src), "path": src, "roles": set()}
            docs_map[src]["roles"].add(role)
            
    # Serialize
    result = []
    for src, data in docs_map.items():
        role_label = list(data["roles"])[0] if len(data["roles"]) == 1 else "mixed_clearance"
        result.append({
            "filename": data["filename"],
            "path": data["path"],
            "classification": role_label
        })
    return result

@app.delete("/documents")
def delete_document(path: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    # Delete from vector DB using direct collection where clause
    collection = rag.vector_db._collection
    collection.delete(where={"source": path})
    
    if hasattr(rag.vector_db, "persist"):
        rag.vector_db.persist()
        
    return {"status": "success", "message": f"Deleted {path}"}
