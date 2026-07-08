import io
import zipfile
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from fastapi.responses import StreamingResponse
from pymongo.database import Database
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from app.services.agent_runner import AgentRunner
from app import database, security
import uuid

router = APIRouter(prefix="/api")
runner = AgentRunner()

class GenerateRequest(BaseModel):
    prompt: str
    settings: Dict[str, Any]
    agent_config_id: str

class SaveFileRequest(BaseModel):
    path: str
    content: str

class BuildLogResponse(BaseModel):
    id: str
    agent_config_id: str
    status: str
    error: Optional[str] = None
    
@router.post("/generate", response_model=BuildLogResponse)
def start_generation(req: GenerateRequest, background_tasks: BackgroundTasks, db: Database = Depends(database.get_db), current_user: dict = Depends(security.get_current_user)):
    import os
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    agent = db.agents.find_one({"id": req.agent_config_id, "user_id": current_user["id"]})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent configuration not found")

    build_log_id = str(uuid.uuid4())
    build_log = {
        "id": build_log_id,
        "agent_config_id": agent["id"],
        "status": "pending",
        "logs": ["[System] Task created"],
        "files_json": {},
        "error": None
    }
    db.build_logs.insert_one(build_log)
    
    # Construct settings from active agent configuration and database keys vault
    provider = agent.get("api_selections", {}).get("provider", "simulated")
    
    api_key_entry = db.api_keys.find_one({
        "user_id": current_user["id"],
        "category": provider
    })
    
    decrypted_key = ""
    if api_key_entry:
        from app.encryption import decrypt_key
        try:
            decrypted_key = decrypt_key(api_key_entry["encrypted_key"])
        except Exception:
            pass
            
    default_models = {
        "gemini": "gemini-1.5-flash",
        "openai": "gpt-4o-mini",
        "groq": "mixtral-8x7b-32768"
    }
    
    run_settings = dict(req.settings) if req.settings else {}
    if "provider" not in run_settings:
        run_settings["provider"] = provider
    if "apiKey" not in run_settings or not run_settings["apiKey"]:
        run_settings["apiKey"] = decrypted_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("API_KEY") or ""
    if "model" not in run_settings or not run_settings["model"]:
        run_settings["model"] = default_models.get(provider, "gemini-1.5-flash")
    
    background_tasks.add_task(runner.run_task, build_log_id, req.prompt, run_settings)
    return build_log

@router.get("/status/{task_id}")
def get_task_status(task_id: str, db: Database = Depends(database.get_db), current_user: dict = Depends(security.get_current_user)):
    build = db.build_logs.find_one({"id": task_id})
    if not build:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Check if the build belongs to the user
    agent = db.agents.find_one({"id": build["agent_config_id"], "user_id": current_user["id"]})
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
            "status": build.get("status", "completed"),
            "current_agent_index": 9, # Assume completed
            "logs": build.get("logs", []),
            "files": list(build.get("files_json", {}).keys()),
            "error": build.get("error")
        }

@router.get("/dashboard/builds", response_model=List[BuildLogResponse])
def get_dashboard_builds(db: Database = Depends(database.get_db), current_user: dict = Depends(security.get_current_user)):
    agents = list(db.agents.find({"user_id": current_user["id"]}))
    agent_ids = [a["id"] for a in agents]
    builds = list(db.build_logs.find({"agent_config_id": {"$in": agent_ids}}).sort("_id", -1))
    return builds

@router.get("/file/{task_id}")
def get_file_content(task_id: str, path: str = Query(..., description="File path to read"), db: Database = Depends(database.get_db), current_user: dict = Depends(security.get_current_user)):
    build = db.build_logs.find_one({"id": task_id})
    if not build:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task_in_memory = runner.get_task(task_id)
    files = task_in_memory["files"] if task_in_memory else build.get("files_json", {})

    if path not in files:
        raise HTTPException(status_code=404, detail="File not found in task workspace")
        
    return {"path": path, "content": files[path]}

@router.put("/file/{task_id}")
def save_file_content(task_id: str, req: SaveFileRequest, db: Database = Depends(database.get_db), current_user: dict = Depends(security.get_current_user)):
    build = db.build_logs.find_one({"id": task_id})
    if not build:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task_in_memory = runner.get_task(task_id)
    if task_in_memory:
        task_in_memory["files"][req.path] = req.content
        task_in_memory["logs"].append(f"[System] File '{req.path}' was edited and saved by user.")
    
    files = dict(build.get("files_json", {}))
    files[req.path] = req.content
    logs = list(build.get("logs", []))
    logs.append(f"[System] File '{req.path}' was edited and saved by user.")
    
    db.build_logs.update_one(
        {"id": task_id},
        {"$set": {"files_json": files, "logs": logs}}
    )

    return {"message": "File updated successfully"}

@router.get("/export/{task_id}")
def export_workspace(task_id: str, db: Database = Depends(database.get_db), current_user: dict = Depends(security.get_current_user)):
    build = db.build_logs.find_one({"id": task_id})
    if not build:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task_in_memory = runner.get_task(task_id)
    files = task_in_memory["files"] if task_in_memory else build.get("files_json", {})

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

