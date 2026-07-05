import sys
import os

# Load environment variables from .env file if it exists
def load_dotenv():
    possible_paths = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(__file__), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ[k.strip()] = v.strip()
                break
            except Exception:
                pass

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router

app = FastAPI(
    title="AutoDev AI Multi-Agent Platform",
    description="Backend orchestration services for multi-agent software development pipelines.",
    version="1.0.0"
)

# Enable CORS for frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include core routes
app.include_router(api_router)

@app.get("/")
def home():
    return {
        "message": "Welcome to AutoDev AI Backend API Server!",
        "status": "online",
        "endpoints": {
            "generate": "/api/generate",
            "status": "/api/status/{task_id}",
            "file": "/api/file/{task_id}",
            "export": "/api/export/{task_id}"
        }
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
