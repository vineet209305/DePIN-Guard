# auth-service/main.py — Week 8 bcrypt upgrade
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import jwt, datetime, bcrypt, os

app = FastAPI()

# Load from .env — never hardcode
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "my_super_secret_key")

# Hashed demo password
HASHED_PASSWORD = bcrypt.hashpw(b"securepass", bcrypt.gensalt())

class UserLogin(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(user: UserLogin):
    password_ok = bcrypt.checkpw(user.password.encode(), HASHED_PASSWORD)
    if user.username == "admin" and password_ok:
        token = jwt.encode(
            {"user": user.username, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
            SECRET_KEY, algorithm="HS256"
        )
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/verify")
def verify_token(token: str):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"valid": True, "user": decoded["user"]}
    except Exception:
        return {"valid": False}