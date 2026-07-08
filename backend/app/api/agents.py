from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database
from pydantic import BaseModel
from typing import List, Any, Dict
import uuid

from app import database, security

router = APIRouter(prefix="/api/agents", tags=["agents"])

class AgentConfigCreate(BaseModel):
    name: str
    category: str
    api_selections: Dict[str, Any]
    behavior: str

class AgentConfigResponse(BaseModel):
    id: str
    name: str
    category: str
    api_selections: Dict[str, Any]
    behavior: str

@router.post("/", response_model=AgentConfigResponse)
def create_agent(agent_data: AgentConfigCreate, db: Database = Depends(database.get_db), current_user: dict = Depends(security.get_current_user)):
    new_agent = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "name": agent_data.name,
        "category": agent_data.category,
        "api_selections": agent_data.api_selections,
        "behavior": agent_data.behavior
    }
    db.agents.insert_one(new_agent)
    return new_agent

@router.get("/", response_model=List[AgentConfigResponse])
def get_agents(db: Database = Depends(database.get_db), current_user: dict = Depends(security.get_current_user)):
    agents = list(db.agents.find({"user_id": current_user["id"]}))
    return agents

@router.delete("/{agent_id}")
def delete_agent(agent_id: str, db: Database = Depends(database.get_db), current_user: dict = Depends(security.get_current_user)):
    result = db.agents.delete_one({"id": agent_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    return {"message": "Agent deleted successfully"}
