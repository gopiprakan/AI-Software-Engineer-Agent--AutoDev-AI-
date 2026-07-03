import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as api_router

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
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
