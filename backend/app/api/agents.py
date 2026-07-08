from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Any, Dict

from app import models, database, security

router = APIRouter(prefix="/api/agents", tags=["agents"])

class AgentConfigCreate(BaseModel):
    name: str
    category: str
    api_selections: Dict[str, Any]
    behavior: str

class AgentConfigResponse(BaseModel):
    id: int
    name: str
    category: str
    api_selections: Dict[str, Any]
    behavior: str

    class Config:
        orm_mode = True

@router.post("/", response_model=AgentConfigResponse)
def create_agent(agent_data: AgentConfigCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    new_agent = models.AgentConfig(
        user_id=current_user.id,
        name=agent_data.name,
        category=agent_data.category,
        api_selections=agent_data.api_selections,
        behavior=agent_data.behavior
    )
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    return new_agent

@router.get("/", response_model=List[AgentConfigResponse])
def get_agents(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    return db.query(models.AgentConfig).filter(models.AgentConfig.user_id == current_user.id).all()

@router.delete("/{agent_id}")
def delete_agent(agent_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    agent = db.query(models.AgentConfig).filter(models.AgentConfig.id == agent_id, models.AgentConfig.user_id == current_user.id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    db.delete(agent)
    db.commit()
    return {"message": "Agent deleted successfully"}
