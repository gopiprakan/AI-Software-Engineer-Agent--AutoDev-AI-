from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database
from pydantic import BaseModel
from typing import List
import uuid

from app import database, security, encryption

router = APIRouter(prefix="/api/keys", tags=["keys"])

class ApiKeyCreate(BaseModel):
    category: str
    key_value: str

class ApiKeyResponse(BaseModel):
    id: str
    category: str

@router.post("/", response_model=ApiKeyResponse)
def add_api_key(key_data: ApiKeyCreate, db: Database = Depends(database.get_db), current_user: dict = Depends(security.get_current_user)):
    encrypted = encryption.encrypt_key(key_data.key_value)
    
    # Check if key for this category already exists for the user
    existing_key = db.api_keys.find_one({
        "user_id": current_user["id"],
        "category": key_data.category
    })

    if existing_key:
        db.api_keys.update_one(
            {"_id": existing_key["_id"]},
            {"$set": {"encrypted_key": encrypted}}
        )
        existing_key["encrypted_key"] = encrypted
        return existing_key
    else:
        new_key = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "category": key_data.category,
            "encrypted_key": encrypted
        }
        db.api_keys.insert_one(new_key)
        return new_key

@router.get("/", response_model=List[ApiKeyResponse])
def get_api_keys(db: Database = Depends(database.get_db), current_user: dict = Depends(security.get_current_user)):
    keys = list(db.api_keys.find({"user_id": current_user["id"]}))
    return keys

@router.delete("/{key_id}")
def delete_api_key(key_id: str, db: Database = Depends(database.get_db), current_user: dict = Depends(security.get_current_user)):
    result = db.api_keys.delete_one({"id": key_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"message": "Key deleted successfully"}

