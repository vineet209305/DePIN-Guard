from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from contextlib import asynccontextmanager
import datetime
import os
import sqlite3
from typing import Optional

import bcrypt
import jwt


def _load_env_file(path: str):
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key and key not in os.environ:
                os.environ[key] = value.strip()


_load_env_file(os.path.join(os.path.dirname(__file__), ".env"))
_load_env_file(os.path.join(os.path.dirname(__file__), "..", ".env"))

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY not set in .env file!")

BOOTSTRAP_ADMIN_USER = os.getenv("BOOTSTRAP_ADMIN_USER")
BOOTSTRAP_ADMIN_PASSWORD = os.getenv("BOOTSTRAP_ADMIN_PASSWORD")

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_HOURS = 24

def init_db():
    conn = sqlite3.connect("users.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash BLOB
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS failed_attempts (
            username TEXT PRIMARY KEY,
            attempts INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS revoked_tokens (
            token TEXT PRIMARY KEY,
            revoked_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            username TEXT PRIMARY KEY,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            updated_at TEXT NOT NULL
        )
    """)

    if BOOTSTRAP_ADMIN_USER and BOOTSTRAP_ADMIN_PASSWORD:
        existing = conn.execute(
            "SELECT 1 FROM users WHERE username=?", (BOOTSTRAP_ADMIN_USER,)
        ).fetchone()
        if not existing:
            hashed = bcrypt.hashpw(BOOTSTRAP_ADMIN_PASSWORD.encode(), bcrypt.gensalt())
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (BOOTSTRAP_ADMIN_USER, hashed)
            )

    conn.commit()
    conn.close()


def token_is_revoked(token: str) -> bool:
    conn = sqlite3.connect("users.db")
    row = conn.execute("SELECT 1 FROM revoked_tokens WHERE token=?", (token,)).fetchone()
    conn.close()
    return row is not None


def revoke_token(token: str):
    conn = sqlite3.connect("users.db")
    conn.execute(
        "INSERT OR IGNORE INTO revoked_tokens (token, revoked_at) VALUES (?, ?)",
        (token, datetime.datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_failed_attempts(username: str) -> int:
    conn = sqlite3.connect("users.db")
    row = conn.execute("SELECT attempts FROM failed_attempts WHERE username=?", (username,)).fetchone()
    conn.close()
    if not row:
        return 0
    return int(row[0])


def set_failed_attempts(username: str, attempts: int):
    conn = sqlite3.connect("users.db")
    conn.execute(
        "INSERT INTO failed_attempts (username, attempts) VALUES (?, ?) "
        "ON CONFLICT(username) DO UPDATE SET attempts=excluded.attempts",
        (username, attempts),
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


def create_user(username: str, password: str):
    conn = sqlite3.connect("users.db")
    try:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hashed),
        )
        conn.commit()
    finally:
        conn.close()


def upsert_profile(username: str, full_name: str = None, email: str = None, phone: str = None):
    conn = sqlite3.connect("users.db")
    try:
        existing = conn.execute(
            "SELECT full_name, email, phone FROM profiles WHERE username=?",
            (username,),
        ).fetchone()
        current_full_name = full_name if full_name is not None else (existing[0] if existing else username)
        current_email = email if email is not None else (existing[1] if existing else username)
        current_phone = phone if phone is not None else (existing[2] if existing else "")
        conn.execute(
            """
            INSERT INTO profiles (username, full_name, email, phone, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                full_name=excluded.full_name,
                email=excluded.email,
                phone=excluded.phone,
                updated_at=excluded.updated_at
            """,
            (username, current_full_name, current_email, current_phone, datetime.datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def get_profile(username: str):
    conn = sqlite3.connect("users.db")
    profile = conn.execute(
        "SELECT username, full_name, email, phone, updated_at FROM profiles WHERE username=?",
        (username,),
    ).fetchone()
    conn.close()
    if profile:
        return {
            "username": profile[0],
            "full_name": profile[1],
            "email": profile[2],
            "phone": profile[3],
            "updated_at": profile[4],
        }
    return {
        "username": username,
        "full_name": username,
        "email": username,
        "phone": "",
        "updated_at": None,
    }

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

bearer_scheme = HTTPBearer(auto_error=True)

MAX_ATTEMPTS = 5

def validate_password(password: str):
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not any(c.isupper() for c in password):
        raise ValueError("Password must have at least 1 uppercase letter")
    if not any(c.isdigit() for c in password):
        raise ValueError("Password must have at least 1 number")
    return True

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    token = credentials.credentials
    if token_is_revoked(token):
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

class UserLogin(BaseModel):
    username: str
    password: str


class UserSignup(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "auth-service"}

@app.post("/signup")
def signup(user: UserSignup):
    username = user.username.strip().lower()
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    try:
        validate_password(user.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if get_user(username):
        raise HTTPException(status_code=409, detail="User already exists")

    create_user(username, user.password)
    upsert_profile(username, full_name=user.full_name or username, email=username)
    return {"message": "User created", "username": username}


@app.post("/login")
def login(user: UserLogin):
    username = user.username.strip().lower()

    attempts = get_failed_attempts(username)
    if attempts >= MAX_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail="Account locked — too many failed attempts"
        )

    db_user = get_user(username)
    if not db_user:
        set_failed_attempts(username, attempts + 1)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    password_ok = bcrypt.checkpw(
        user.password.encode(),
        db_user[2]
    )

    if not password_ok:
        set_failed_attempts(username, attempts + 1)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    set_failed_attempts(username, 0)
    profile = get_profile(username)

    access_token = jwt.encode({
        "sub": username,
        "type": "access",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }, SECRET_KEY, algorithm="HS256")

    refresh_token_val = jwt.encode({
        "sub": username,
        "type": "refresh",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=REFRESH_TOKEN_EXPIRE_HOURS)
    }, SECRET_KEY, algorithm="HS256")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_val,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "profile": profile,
    }


@app.get("/profile")
def read_profile(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    payload = verify_token(credentials)
    return {"profile": get_profile(payload["sub"])}


@app.post("/profile")
def update_profile(data: ProfileUpdate, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    payload = verify_token(credentials)
    upsert_profile(
        payload["sub"],
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
    )
    return {"message": "Profile saved", "profile": get_profile(payload["sub"])}


@app.post("/verify")
def verify_token_endpoint(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    if token_is_revoked(token):
        return {"valid": False, "reason": "Token has been logged out"}
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"valid": True, "user": decoded.get("sub")}
    except Exception:
        return {"valid": False}


@app.post("/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    revoke_token(credentials.credentials)
    return {"message": "Logged out successfully"}


@app.post("/refresh")
def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    if token_is_revoked(token):
        raise HTTPException(status_code=401, detail="Token has been logged out")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        revoke_token(token)
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