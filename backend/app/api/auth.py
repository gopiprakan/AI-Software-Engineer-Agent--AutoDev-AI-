from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pymongo.database import Database
from pymongo.errors import PyMongoError
from pydantic import BaseModel
import uuid

from app import database, security

router = APIRouter(prefix="/api/auth", tags=["auth"])

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: str
    username: str

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Database = Depends(database.get_db)):
    try:
        db_user = db.users.find_one({"username": user.username})
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        hashed_password = security.get_password_hash(user.password)
        user_id = str(uuid.uuid4())
        
        new_user = {
            "id": user_id,
            "username": user.username,
            "email": f"{user.username}@example.com",
            "password_hash": hashed_password
        }
        
        db.users.insert_one(new_user)
        return new_user
    except PyMongoError as e:
        print(f"Database error during registration: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error during registration: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Database = Depends(database.get_db)):
    user = db.users.find_one({"username": form_data.username})
    if not user or not security.verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: dict = Depends(security.get_current_user)):
    return current_user

