# AutoDev AI - Multi-Agent Software Development Platform

AutoDev AI is a full-stack platform designed to orchestrate a pipeline of 8 specialized coding agents. By giving the system a simple project description (e.g. *"Build a Hospital Management System"*), users can watch the agents perform business analysis, planning, database design, backend coding, frontend development, code reviews, testing, and manual assembly live on a unified dashboard.

---

## 📁 Repository Structure

```text
AutoDev-AI/
├── frontend/                  # React (Vite) User Dashboard
│   ├── src/
│   │   ├── App.css            # Premium Custom CSS (Glassmorphism layout)
│   │   ├── App.jsx            # Multi-panel IDE Workspace
│   │   └── main.jsx           # Mounting entrypoint
│   ├── index.html
│   ├── package.json           # React dependencies
│   └── vite.config.js
├── backend/                   # FastAPI Web Server
│   ├── agents/                # Agent Modules
│   │   ├── base_agent.py      # Base agent class supporting LLM API requests
│   │   ├── templates.py       # Simulated output template engine
│   │   ├── requirement_agent.py
│   │   ├── planner_agent.py
│   │   ├── database_agent.py
│   │   ├── backend_agent.py
│   │   ├── frontend_agent.py
│   │   ├── review_agent.py
│   │   ├── testing_agent.py
│   │   └── documentation_agent.py
│   ├── api/
│   │   └── routes.py          # API endpoints (Runs, file reads/edits, zip exporter)
│   ├── services/
│   │   └── agent_runner.py    # Pipeline coordinator & logger
│   ├── database/              # Placeholder folders
│   ├── rag/
│   ├── vector_db/
│   └── main.py                # Server entrypoint
├── requirements.txt           # Backend libraries
└── README.md                  # This manual
```

---

## ⚡ Quick Start

### 1. Prerequisite Environments
- Python 3.10+ installed
- Node.js v18+ and npm installed

### 2. Backend Installation & Launch
Open a terminal in the root project folder:
```bash
# Install Python package requirements
pip install -r requirements.txt

# Start the FastAPI server using Uvicorn
python backend/main.py
```
*The API will start running at `http://127.0.0.1:8000`.*

### 3. Frontend Installation & Launch
Open a second terminal inside the `frontend/` directory:
```bash
# Navigate to frontend folder
cd frontend

# Install package dependencies
npm install

# Start the Vite local server
npm run dev
```
*The UI will start running at `http://localhost:3000`.*

---

## 🤖 LLM Operations
By default, the platform runs in **Simulated Mode**, allowing immediate usage without API setup. To connect a live LLM:
1. Open the header configurations dropdown in the browser.
2. Select **Gemini API**, **OpenAI API**, or **Ollama (Local LLM)**.
3. Supply your API Key (or local endpoint for Ollama) and select your target model.
4. Click **Deploy Agents** to start generating a fresh codebase live!
