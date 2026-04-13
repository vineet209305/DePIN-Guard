# auth-service/main.py — MongoDB Version with JWT + Signup + Login
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient as AsyncClient
import jwt, datetime, bcrypt, os, random, smtplib, certifi
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
# 📧 EMAIL CONFIG
# ==========================================
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# ==========================================
# 🗄️ MONGODB SETUP
# ==========================================
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/depin_guard")
mongodb_client = None
db = None

async def connect_to_mongo():
    """Connect to MongoDB"""
    global mongodb_client, db
    try:
        if "mongodb+srv://" in MONGODB_URI:
            mongodb_client = AsyncClient(
                MONGODB_URI,
                tls=True,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=5000,
            )
        else:
            mongodb_client = AsyncClient(MONGODB_URI)
        
        await mongodb_client.admin.command('ping')
        db = mongodb_client["depin_guard"]
        
        # Create indexes
        users_collection = db["users"]
        await users_collection.create_index("email", unique=True)
        await users_collection.create_index("created_at")
        
        revoked_collection = db["revoked_tokens"]
        await revoked_collection.create_index("revoked_at", expireAfterSeconds=86400)
        
        print("✅ Connected to MongoDB Auth Service")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        raise

async def close_mongo_connection():
    """Close MongoDB connection"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        print("🔌 MongoDB connection closed")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan events"""
    await connect_to_mongo()
    yield
    await close_mongo_connection()

# ==========================================
# 📊 PYDANTIC MODELS
# ==========================================
class UserSignup(BaseModel):
    email: str
    password: str
    full_name: str = None
    phone: str = None

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_email: str
    full_name: str = None

class UserProfile(BaseModel):
    email: str
    full_name: str = None
    phone: str = None
    created_at: str = None
    last_login: str = None

# ==========================================
# 🔑 JWT HELPER FUNCTIONS
# ==========================================
def create_access_token(email: str, expires_delta: datetime.timedelta = None):
    """Create JWT access token"""
    if not expires_delta:
        expires_delta = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.datetime.utcnow() + expires_delta
    payload = {"sub": email, "type": "access", "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def create_refresh_token(email: str):
    """Create JWT refresh token"""
    expire = datetime.datetime.utcnow() + datetime.timedelta(hours=REFRESH_TOKEN_EXPIRE_HOURS)
    payload = {"sub": email, "type": "refresh", "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==========================================
# 🔐 PASSWORD HELPER FUNCTIONS
# ==========================================
def hash_password(password: str):
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def verify_password(password: str, password_hash: bytes):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash)

# ==========================================
# 📧 EMAIL HELPER FUNCTIONS
# ==========================================
def send_email(to_email: str, subject: str, body: str):
    """Send email via Gmail SMTP"""
    try:
        if not EMAIL_USER or not EMAIL_PASS:
            print(f"⚠️  Email not configured. Would send to {to_email}: {subject}")
            return True
        
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_USER
        msg["To"] = to_email
        
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

# ==========================================
# 🚀 FASTAPI APP
# ==========================================
app = FastAPI(title="DePIN Auth Service", version="2.0", lifespan=lifespan)

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
# 🏥 HEALTH CHECK
# ==========================================
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auth-service", "database": "mongodb"}

# ==========================================
# 📝 SIGNUP
# ==========================================
@app.post("/signup")
async def signup(user: UserSignup):
    """Create new user account"""
    # Validate email
    if not "@" in user.email:
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    if len(user.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Check if user exists
    users_collection = db["users"]
    existing = await users_collection.find_one({"email": user.email.lower()})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    # Hash password and save
    hashed = hash_password(user.password)
    new_user = {
        "email": user.email.lower(),
        "password_hash": hashed,
        "full_name": user.full_name or user.email.split("@")[0],
        "phone": user.phone,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "last_login": None
    }
    
    result = await users_collection.insert_one(new_user)
    
    # Send welcome email
    send_email(
        user.email,
        "Welcome to DePIN-Guard",
        f"Welcome {new_user['full_name']}! Your account has been created successfully."
    )
    
    return {
        "message": f"Account created successfully! Welcome {new_user['full_name']}",
        "email": user.email,
        "user_id": str(result.inserted_id)
    }

# ==========================================
# 🔐 LOGIN
# ==========================================
@app.post("/login")
async def login(user: UserLogin):
    """Login with email and password"""
    users_collection = db["users"]
    
    # Get user
    db_user = await users_collection.find_one({"email": user.email.lower()})
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last login
    await users_collection.update_one(
        {"_id": db_user["_id"]},
        {"$set": {"last_login": datetime.datetime.utcnow().isoformat()}}
    )
    
    # Generate tokens
    access_token = create_access_token(user.email.lower())
    refresh_token = create_refresh_token(user.email.lower())
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_email": user.email.lower(),
        "full_name": db_user.get("full_name")
    }

# ==========================================
# 👤 GET PROFILE
# ==========================================
@app.get("/profile")
async def get_profile(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """Get user profile"""
    email = verify_token(credentials.credentials)
    users_collection = db["users"]
    
    db_user = await users_collection.find_one({"email": email})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "profile": {
            "email": db_user["email"],
            "full_name": db_user.get("full_name"),
            "phone": db_user.get("phone"),
            "created_at": db_user.get("created_at"),
            "last_login": db_user.get("last_login"),
            "settings": db_user.get("settings", {})
        }
    }

# ==========================================
# 📝 UPDATE PROFILE & SETTINGS
# ==========================================
class ProfileUpdate(BaseModel):
    full_name: str = None
    phone: str = None
    email_notifications: bool = None
    sms_notifications: bool = None
    alert_notifications: bool = None
    auto_refresh: bool = None
    refresh_interval: str = None
    data_retention: str = None
    theme: str = None
    language: str = None

@app.post("/profile")
async def update_profile(update_data: ProfileUpdate, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """Update user profile and settings"""
    email = verify_token(credentials.credentials)
    users_collection = db["users"]
    
    db_user = await users_collection.find_one({"email": email})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prepare update data
    update_fields = {"updated_at": datetime.datetime.utcnow().isoformat()}
    
    # Update basic profile fields
    if update_data.full_name is not None:
        update_fields["full_name"] = update_data.full_name
    if update_data.phone is not None:
        update_fields["phone"] = update_data.phone
    
    # Build settings object
    settings = db_user.get("settings", {})
    if update_data.email_notifications is not None:
        settings["email_notifications"] = update_data.email_notifications
    if update_data.sms_notifications is not None:
        settings["sms_notifications"] = update_data.sms_notifications
    if update_data.alert_notifications is not None:
        settings["alert_notifications"] = update_data.alert_notifications
    if update_data.auto_refresh is not None:
        settings["auto_refresh"] = update_data.auto_refresh
    if update_data.refresh_interval is not None:
        settings["refresh_interval"] = update_data.refresh_interval
    if update_data.data_retention is not None:
        settings["data_retention"] = update_data.data_retention
    if update_data.theme is not None:
        settings["theme"] = update_data.theme
    if update_data.language is not None:
        settings["language"] = update_data.language
    
    update_fields["settings"] = settings
    
    # Update in database
    result = await users_collection.update_one(
        {"_id": db_user["_id"]},
        {"$set": update_fields}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Return updated profile
    updated_user = await users_collection.find_one({"_id": db_user["_id"]})
    return {
        "message": "Profile updated successfully",
        "profile": {
            "email": updated_user["email"],
            "full_name": updated_user.get("full_name"),
            "phone": updated_user.get("phone"),
            "created_at": updated_user.get("created_at"),
            "updated_at": updated_user.get("updated_at"),
            "settings": updated_user.get("settings", {})
        }
    }

# ==========================================
# 🔓 VERIFY TOKEN
# ==========================================
@app.post("/verify")
async def verify_token_endpoint(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """Verify JWT token validity"""
    token = credentials.credentials
    
    # Check if token is revoked
    revoked_collection = db["revoked_tokens"]
    is_revoked = await revoked_collection.find_one({"token": token})
    if is_revoked:
        raise HTTPException(status_code=401, detail="Token has been revoked")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return {
            "valid": True,
            "user": payload.get("sub"),
            "type": "access"
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==========================================
# 🚪 LOGOUT
# ==========================================
@app.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """Logout by revoking token"""
    token = credentials.credentials
    revoked_collection = db["revoked_tokens"]
    
    await revoked_collection.insert_one({
        "token": token,
        "revoked_at": datetime.datetime.utcnow().isoformat()
    })
    
    return {"message": "Logged out successfully"}

# ==========================================
# 🔄 REFRESH TOKEN
# ==========================================
@app.post("/refresh")
async def refresh_token_endpoint(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """Refresh access token using refresh token"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        email = payload.get("sub")
        new_access_token = create_access_token(email)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired — please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==========================================
# 🎯 ROOT
# ==========================================
@app.get("/")
async def root():
    return {
        "service": "DePIN-Guard Auth Service",
        "version": "2.0",
        "database": "MongoDB",
        "endpoints": [
            "POST /signup",
            "POST /login",
            "GET /profile",
            "POST /verify",
            "POST /logout",
            "POST /refresh",
            "GET /health"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8001)))