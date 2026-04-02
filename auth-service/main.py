# auth-service/main.py — Production Ready
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import jwt, datetime, bcrypt, os, sqlite3

app = FastAPI()

# ==========================================
# 🔒 SECRET KEY — Load from .env only
# ==========================================
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "my_super_secret_key")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY not set in .env file!")

# ==========================================
# 🗄️ DATABASE SETUP — SQLite
# ==========================================
def init_db():
    conn = sqlite3.connect("users.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash BLOB
        )
    """)
    existing = conn.execute(
        "SELECT * FROM users WHERE username=?", ("admin",)
    ).fetchone()
    if not existing:
        hashed = bcrypt.hashpw(b"securepass", bcrypt.gensalt())
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("admin", hashed)
        )
    conn.commit()
    conn.close()

def get_user(username: str):
    conn = sqlite3.connect("users.db")
    user = conn.execute(
        "SELECT * FROM users WHERE username=?", (username,)
    ).fetchone()
    conn.close()
    return user

init_db()

# ==========================================
# 🚫 TOKEN BLACKLIST — Logout System
# ==========================================
blacklisted_tokens = set()

# ==========================================
# 🔑 FAILED ATTEMPTS — Brute Force Protection
# ==========================================
failed_attempts = {}
MAX_ATTEMPTS = 5

# ==========================================
# ✅ PASSWORD VALIDATOR
# ==========================================
def validate_password(password: str):
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not any(c.isupper() for c in password):
        raise ValueError("Password must have at least 1 uppercase letter")
    if not any(c.isdigit() for c in password):
        raise ValueError("Password must have at least 1 number")
    return True

# ==========================================
# 📋 MODELS
# ==========================================
class UserLogin(BaseModel):
    username: str
    password: str

# ==========================================
# 🔐 ENDPOINTS
# ==========================================

@app.post("/login")
def login(user: UserLogin):
    # 1. Check failed attempts
    attempts = failed_attempts.get(user.username, 0)
    if attempts >= MAX_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail="Account locked — too many failed attempts"
        )

    # 2. Get user from database
    db_user = get_user(user.username)
    if not db_user:
        failed_attempts[user.username] = attempts + 1
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 3. Verify password with bcrypt
    password_ok = bcrypt.checkpw(
        user.password.encode(),
        db_user[2]
    )

    if not password_ok:
        failed_attempts[user.username] = attempts + 1
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 4. Reset failed attempts on success
    failed_attempts[user.username] = 0

    # 5. Generate JWT token
    token = jwt.encode(
        {
            "user": user.username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        },
        SECRET_KEY,
        algorithm="HS256"
    )
    return {"access_token": token, "token_type": "bearer"}


@app.post("/verify")
def verify_token(token: str):
    if token in blacklisted_tokens:
        return {"valid": False, "reason": "Token has been logged out"}
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"valid": True, "user": decoded["user"]}
    except Exception:
        return {"valid": False}


@app.post("/logout")
def logout(token: str):
    blacklisted_tokens.add(token)
    return {"message": "Logged out successfully"}


@app.post("/refresh")
def refresh_token(token: str):
    if token in blacklisted_tokens:
        raise HTTPException(status_code=401, detail="Token has been logged out")
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        blacklisted_tokens.add(token)
        new_token = jwt.encode(
            {
                "user": decoded["user"],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            },
            SECRET_KEY,
            algorithm="HS256"
        )
        return {"access_token": new_token, "token_type": "bearer"}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")