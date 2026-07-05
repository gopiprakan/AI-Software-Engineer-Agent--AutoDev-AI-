import io
import zipfile
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any
from app.services.agent_runner import AgentRunner

router = APIRouter(prefix="/api")
runner = AgentRunner()

class GenerateRequest(BaseModel):
    prompt: str
    settings: Dict[str, Any]

class SaveFileRequest(BaseModel):
    path: str
    content: str

@router.post("/generate")
def start_generation(req: GenerateRequest, background_tasks: BackgroundTasks):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    task_id = runner.create_task(req.prompt, req.settings)
    background_tasks.add_task(runner.run_task, task_id)
    return {"task_id": task_id}

@router.get("/status/{task_id}")
def get_task_status(task_id: str):
    task = runner.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Return everything except full file contents to keep response lightweight,
    # or just return filenames for the tree explorer.
    file_list = list(task["files"].keys())
    return {
        "id": task["id"],
        "status": task["status"],
        "current_agent_index": task["current_agent_index"],
        "logs": task["logs"],
        "files": file_list,
        "error": task["error"]
    }

@router.get("/file/{task_id}")
def get_file_content(task_id: str, path: str = Query(..., description="File path to read")):
    task = runner.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if path not in task["files"]:
        raise HTTPException(status_code=404, detail="File not found in task workspace")
        
    return {"path": path, "content": task["files"][path]}

@router.put("/file/{task_id}")
def save_file_content(task_id: str, req: SaveFileRequest):
    task = runner.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task["files"][req.path] = req.content
    task["logs"].append(f"[System] File '{req.path}' was edited and saved by user.")
    return {"message": "File updated successfully"}

@router.get("/export/{task_id}")
def export_workspace(task_id: str):
    task = runner.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Create an in-memory zip file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for filepath, content in task["files"].items():
            zip_file.writestr(filepath, content)
            
    zip_buffer.seek(0)
    
    # Generate a clean name
    safe_title = "".join(c for c in task["prompt"] if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    filename = f"{safe_title or 'autodev_project'}.zip"
    
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

