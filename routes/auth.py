from fastapi import APIRouter, HTTPException
from database import users_collection
from models.user import RegisterModel, LoginModel
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from bson import ObjectId
import os

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("JWT_SECRET")

def create_token(user_id: str):
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

@router.post("/register")
async def register(data: RegisterModel):
    existing = await users_collection.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = pwd_context.hash(data.password)
    user = {"name": data.name, "email": data.email, "password": hashed}
    result = await users_collection.insert_one(user)
    token = create_token(str(result.inserted_id))
    return {"token": token, "user": {"id": str(result.inserted_id), "name": data.name, "email": data.email}}

@router.post("/login")
async def login(data: LoginModel):
    user = await users_collection.find_one({"email": data.email})
    if not user or not pwd_context.verify(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(str(user["_id"]))
    return {"token": token, "user": {"id": str(user["_id"]), "name": user["name"], "email": user["email"]}}

@router.get("/me")
async def get_me(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = await users_collection.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"id": str(user["_id"]), "name": user["name"], "email": user["email"]}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")