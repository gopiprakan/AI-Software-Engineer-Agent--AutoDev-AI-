import io
import zipfile
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.services.agent_runner import AgentRunner
from app import models, database, security
import uuid

router = APIRouter(prefix="/api")
runner = AgentRunner()

class GenerateRequest(BaseModel):
    prompt: str
    settings: Dict[str, Any]
    agent_config_id: int

class SaveFileRequest(BaseModel):
    path: str
    content: str

class BuildLogResponse(BaseModel):
    id: str
    agent_config_id: int
    status: str
    error: str = None
    
    class Config:
        orm_mode = True

@router.post("/generate", response_model=BuildLogResponse)
def start_generation(req: GenerateRequest, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    agent = db.query(models.AgentConfig).filter(models.AgentConfig.id == req.agent_config_id, models.AgentConfig.user_id == current_user.id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent configuration not found")

    build_log = models.BuildLog(
        agent_config_id=agent.id,
        status="pending",
        logs=["[System] Task created"],
        files_json={}
    )
    db.add(build_log)
    db.commit()
    db.refresh(build_log)
    
    background_tasks.add_task(runner.run_task, build_log.id, req.prompt, req.settings)
    return build_log

@router.get("/status/{task_id}")
def get_task_status(task_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    build = db.query(models.BuildLog).filter(models.BuildLog.id == task_id).first()
    if not build:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Check if the build belongs to the user
    agent = db.query(models.AgentConfig).filter(models.AgentConfig.id == build.agent_config_id, models.AgentConfig.user_id == current_user.id).first()
    if not agent:
        raise HTTPException(status_code=403, detail="Not authorized to view this task")

    task_in_memory = runner.get_task(task_id)
    
    if task_in_memory:
        return {
            "id": task_id,
            "status": task_in_memory["status"],
            "current_agent_index": task_in_memory["current_agent_index"],
            "logs": task_in_memory["logs"],
            "files": list(task_in_memory["files"].keys()),
            "error": task_in_memory["error"]
        }
    else:
        # If not in memory, fetch from DB
        return {
            "id": task_id,
            "status": build.status,
            "current_agent_index": 9, # Assume completed
            "logs": build.logs,
            "files": list(build.files_json.keys()),
            "error": build.error
        }

@router.get("/dashboard/builds", response_model=List[BuildLogResponse])
def get_dashboard_builds(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    agents = db.query(models.AgentConfig).filter(models.AgentConfig.user_id == current_user.id).all()
    agent_ids = [a.id for a in agents]
    builds = db.query(models.BuildLog).filter(models.BuildLog.agent_config_id.in_(agent_ids)).order_by(models.BuildLog.id.desc()).all()
    return builds

@router.get("/file/{task_id}")
def get_file_content(task_id: str, path: str = Query(..., description="File path to read"), db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    build = db.query(models.BuildLog).filter(models.BuildLog.id == task_id).first()
    if not build:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task_in_memory = runner.get_task(task_id)
    files = task_in_memory["files"] if task_in_memory else build.files_json

    if path not in files:
        raise HTTPException(status_code=404, detail="File not found in task workspace")
        
    return {"path": path, "content": files[path]}

@router.put("/file/{task_id}")
def save_file_content(task_id: str, req: SaveFileRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    build = db.query(models.BuildLog).filter(models.BuildLog.id == task_id).first()
    if not build:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task_in_memory = runner.get_task(task_id)
    if task_in_memory:
        task_in_memory["files"][req.path] = req.content
        task_in_memory["logs"].append(f"[System] File '{req.path}' was edited and saved by user.")
    
    files = dict(build.files_json)
    files[req.path] = req.content
    build.files_json = files
    logs = list(build.logs)
    logs.append(f"[System] File '{req.path}' was edited and saved by user.")
    build.logs = logs
    db.commit()

    return {"message": "File updated successfully"}

@router.get("/export/{task_id}")
def export_workspace(task_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    build = db.query(models.BuildLog).filter(models.BuildLog.id == task_id).first()
    if not build:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task_in_memory = runner.get_task(task_id)
    files = task_in_memory["files"] if task_in_memory else build.files_json

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for filepath, content in files.items():
            zip_file.writestr(filepath, content)
            
    zip_buffer.seek(0)
    
    filename = f"autodev_project_{task_id}.zip"
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/forward-my-service")
async def forward_my_service(req: Dict[str, Any]):
    import os
    import httpx
    api_key = os.environ.get("API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API_KEY not configured on server")
    
    model = req.get("model", "gemini-1.5-flash")
    contents = req.get("contents")
    generation_config = req.get("generationConfig")
    
    if not contents:
        raise HTTPException(status_code=400, detail="Missing 'contents' in request body")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": contents
    }
    if generation_config:
        payload["generationConfig"] = generation_config
        
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"External service error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

