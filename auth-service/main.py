# auth-service/main.py — Production Ready
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from contextlib import asynccontextmanager
import jwt, datetime, bcrypt, os, sqlite3

# ==========================================
# 🔒 SECRET KEY — Hard fail if not set
# ==========================================
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY not set in .env file!")

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_HOURS = 24

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

# ==========================================
# 🚀 LIFESPAN — Init DB on startup
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

# ==========================================
# 🔐 BEARER SCHEME
# ==========================================
bearer_scheme = HTTPBearer(auto_error=True)

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
# 🔍 TOKEN VERIFIER — HTTPBearer only
# ==========================================
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    token = credentials.credentials
    if token in blacklisted_tokens:
        raise HTTPException(status_code=401, detail="Token has been logged out")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Refresh tokens cannot authenticate API calls")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==========================================
# 📋 MODELS
# ==========================================
class UserLogin(BaseModel):
    username: str
    password: str

# ==========================================
# 🏥 HEALTH CHECK
# ==========================================
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "auth-service"}

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

    # 5. Generate access + refresh tokens
    access_token = jwt.encode({
        "sub": user.username,
        "type": "access",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }, SECRET_KEY, algorithm="HS256")

    refresh_token_val = jwt.encode({
        "sub": user.username,
        "type": "refresh",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=REFRESH_TOKEN_EXPIRE_HOURS)
    }, SECRET_KEY, algorithm="HS256")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_val,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@app.post("/verify")
def verify_token_endpoint(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    if token in blacklisted_tokens:
        return {"valid": False, "reason": "Token has been logged out"}
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"valid": True, "user": decoded.get("sub")}
    except Exception:
        return {"valid": False}


@app.post("/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    blacklisted_tokens.add(credentials.credentials)
    return {"message": "Logged out successfully"}


@app.post("/refresh")
def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    if token in blacklisted_tokens:
        raise HTTPException(status_code=401, detail="Token has been logged out")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        # Blacklist old token
        blacklisted_tokens.add(token)
        # Issue new access token
        new_access = jwt.encode({
            "sub": payload["sub"],
            "type": "access",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }, SECRET_KEY, algorithm="HS256")
        return {"access_token": new_access, "token_type": "bearer"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired — please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")