# auth-service/main.py — Production Ready with OTP + Signup + Last Login
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from contextlib import asynccontextmanager
import jwt, datetime, bcrypt, os, sqlite3, random, smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# ==========================================
# 🔒 SECRET KEY
# ==========================================
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY not set in .env file!")

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_HOURS = 24

# ==========================================
# 📧 EMAIL CONFIG — Load from .env
# ==========================================
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# ==========================================
# 🗄️ DATABASE SETUP
# ==========================================
def ensure_users_table_columns(conn: sqlite3.Connection):
    existing_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()
    }
    required_columns = {
        "full_name": "TEXT",
        "phone": "TEXT",
        "last_login": "TEXT",
        "created_at": "TEXT",
    }
    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            conn.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")


def ensure_failed_attempts_table_columns(conn: sqlite3.Connection):
    existing_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(failed_attempts)").fetchall()
    }
    if "locked_until" not in existing_columns:
        conn.execute("ALTER TABLE failed_attempts ADD COLUMN locked_until TEXT")


def init_db():
    conn = sqlite3.connect("users.db")
    
    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash BLOB,
            full_name TEXT,
            phone TEXT,
            last_login TEXT,
            created_at TEXT
        )
    """)

    ensure_users_table_columns(conn)
    
    # OTP table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS otp_store (
            username TEXT PRIMARY KEY,
            otp TEXT,
            expires_at TEXT
        )
    """)
    
    # Failed attempts table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS failed_attempts (
            username TEXT PRIMARY KEY,
            attempts INTEGER DEFAULT 0,
            locked_until TEXT
        )
    """)
    ensure_failed_attempts_table_columns(conn)
    
    # Revoked tokens table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS revoked_tokens (
            token TEXT PRIMARY KEY,
            revoked_at TEXT
        )
    """)

    # Add default admin if not exists
    existing = conn.execute(
        "SELECT * FROM users WHERE username=?", ("admin",)
    ).fetchone()
    if not existing:
        hashed = bcrypt.hashpw(b"securepass", bcrypt.gensalt())
        conn.execute(
            "INSERT INTO users (username, password_hash, full_name, created_at) VALUES (?, ?, ?, ?)",
            ("admin", hashed, "Admin User", datetime.datetime.utcnow().isoformat())
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

def update_last_login(username: str):
    conn = sqlite3.connect("users.db")
    conn.execute(
        "UPDATE users SET last_login=? WHERE username=?",
        (datetime.datetime.utcnow().isoformat(), username)
    )
    conn.commit()
    conn.close()

# ==========================================
# 🚀 LIFESPAN
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 🔐 BEARER SCHEME
# ==========================================
bearer_scheme = HTTPBearer(auto_error=True)

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
# 📧 OTP SENDER
# ==========================================
def send_otp_email(to_email: str, otp: str):
    if not EMAIL_USER or not EMAIL_PASS:
        print(f"[DEV MODE] OTP for {to_email}: {otp}")
        return True
    try:
        msg = MIMEText(f"""
        Your DePIN-Guard verification code is:
        
        {otp}
        
        This code expires in 10 minutes.
        Do not share this code with anyone.
        """)
        msg['Subject'] = 'DePIN-Guard OTP Verification'
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False

def generate_otp():
    return str(random.randint(100000, 999999))

def store_otp(username: str, otp: str):
    conn = sqlite3.connect("users.db")
    expires = (datetime.datetime.utcnow() + datetime.timedelta(minutes=10)).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO otp_store (username, otp, expires_at) VALUES (?, ?, ?)",
        (username, otp, expires)
    )
    conn.commit()
    conn.close()

def verify_otp(username: str, otp: str) -> bool:
    conn = sqlite3.connect("users.db")
    row = conn.execute(
        "SELECT otp, expires_at FROM otp_store WHERE username=?", (username,)
    ).fetchone()
    conn.close()
    if not row:
        return False
    stored_otp, expires_at = row
    if datetime.datetime.utcnow().isoformat() > expires_at:
        return False
    return stored_otp == otp

# ==========================================
# 🔍 TOKEN VERIFIER
# ==========================================
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    token = credentials.credentials
    # Check revoked tokens in DB
    conn = sqlite3.connect("users.db")
    revoked = conn.execute(
        "SELECT token FROM revoked_tokens WHERE token=?", (token,)
    ).fetchone()
    conn.close()
    if revoked:
        raise HTTPException(status_code=401, detail="Token has been logged out")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
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

class UserSignup(BaseModel):
    username: str
    password: str
    full_name: str
    phone: str = None

class OTPVerify(BaseModel):
    username: str
    otp: str

class OTPRequest(BaseModel):
    username: str

# ==========================================
# 🏥 HEALTH CHECK
# ==========================================
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "auth-service"}

# ==========================================
# 📝 SIGNUP
# ==========================================
@app.post("/signup")
def signup(user: UserSignup):
    # Validate password
    try:
        validate_password(user.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Check if user exists
    existing = get_user(user.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")

    # Hash password and save
    hashed = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
    conn = sqlite3.connect("users.db")
    conn.execute(
        "INSERT INTO users (username, password_hash, full_name, phone, created_at) VALUES (?, ?, ?, ?, ?)",
        (user.username, hashed, user.full_name, user.phone, datetime.datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

    return {"message": f"Account created successfully! Welcome {user.full_name}"}

# ==========================================
# 🔐 LOGIN
# ==========================================
@app.post("/login")
def login(user: UserLogin):
    # Check failed attempts from DB
    conn = sqlite3.connect("users.db")
    attempt_row = conn.execute(
        "SELECT attempts, locked_until FROM failed_attempts WHERE username=?",
        (user.username,)
    ).fetchone()
    conn.close()

    if attempt_row:
        attempts, locked_until = attempt_row
        if locked_until and datetime.datetime.utcnow().isoformat() < locked_until:
            raise HTTPException(
                status_code=429,
                detail="Account locked — too many failed attempts. Try after 15 minutes."
            )

    # Get user
    db_user = get_user(user.username)
    if not db_user:
        _increment_failed(user.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Verify password
    password_ok = bcrypt.checkpw(user.password.encode(), db_user[2])
    if not password_ok:
        _increment_failed(user.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Reset failed attempts
    _reset_failed(user.username)

    # Update last login
    update_last_login(user.username)

    # Generate tokens
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
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "full_name": db_user[3],
        "last_login": db_user[5]
    }

# ==========================================
# 📧 SEND OTP
# ==========================================
@app.post("/send-otp")
def send_otp(request: OTPRequest):
    user = get_user(request.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    otp = generate_otp()
    store_otp(request.username, otp)
    success = send_otp_email(request.username, otp)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send OTP")
    return {"message": "OTP sent successfully to your email"}

# ==========================================
# ✅ VERIFY OTP
# ==========================================
@app.post("/verify-otp")
def verify_otp_endpoint(data: OTPVerify):
    if not verify_otp(data.username, data.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    return {"message": "OTP verified successfully", "verified": True}

# ==========================================
# 👤 GET PROFILE
# ==========================================
@app.get("/profile")
def get_profile(user: dict = Depends(verify_token)):
    db_user = get_user(user["sub"])
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "username": db_user[0],
        "full_name": db_user[3],
        "phone": db_user[4],
        "last_login": db_user[5],
        "created_at": db_user[6]
    }

# ==========================================
# 🔓 VERIFY TOKEN
# ==========================================
@app.post("/verify")
def verify_token_endpoint(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"valid": True, "user": decoded.get("sub")}
    except Exception:
        return {"valid": False}

# ==========================================
# 🚪 LOGOUT
# ==========================================
@app.post("/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    conn = sqlite3.connect("users.db")
    conn.execute(
        "INSERT OR IGNORE INTO revoked_tokens (token, revoked_at) VALUES (?, ?)",
        (token, datetime.datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
    return {"message": "Logged out successfully"}

# ==========================================
# 🔄 REFRESH TOKEN
# ==========================================
@app.post("/refresh")
def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
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

# ==========================================
# 🔧 HELPER FUNCTIONS
# ==========================================
def _increment_failed(username: str):
    conn = sqlite3.connect("users.db")
    row = conn.execute(
        "SELECT attempts FROM failed_attempts WHERE username=?", (username,)
    ).fetchone()
    attempts = (row[0] if row else 0) + 1
    locked_until = None
    if attempts >= 5:
        locked_until = (datetime.datetime.utcnow() + datetime.timedelta(minutes=15)).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO failed_attempts (username, attempts, locked_until) VALUES (?, ?, ?)",
        (username, attempts, locked_until)
    )
    conn.commit()
    conn.close()

def _reset_failed(username: str):
    conn = sqlite3.connect("users.db")
    conn.execute("DELETE FROM failed_attempts WHERE username=?", (username,))
    conn.commit()
    conn.close()