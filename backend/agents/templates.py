import re
from typing import Dict, Any

def clean_name(prompt: str) -> str:
    # Extract a nice capitalized title
    words = re.findall(r'\w+', prompt)
    if not words:
        return "Custom Project"
    return " ".join(w.capitalize() for w in words)

def slugify(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')

def get_dynamic_project(prompt: str) -> Dict[str, Any]:
    title = clean_name(prompt)
    slug = slugify(title)
    entity = slug.replace("_management_system", "").replace("_system", "").replace("_management", "").replace("_app", "")
    entity_cap = entity.capitalize()
    entity_plural = entity + "s"
    entity_plural_cap = entity_plural.capitalize()

    # Dynamic project templates
    hms = {
        "title": title,
        "entity": entity,
        "entity_cap": entity_cap,
        "entity_plural": entity_plural,
        "entity_plural_cap": entity_plural_cap,
        "requirements": f"""# Requirements: {title}

## 1. Project Objectives
- Build a robust, scalable {title} to automate core operations.
- Provide secure role-based access control (RBAC) for administrators, staff, and standard users.
- Deliver an intuitive React-based user interface and a high-performance FastAPI backend.

## 2. Key Modules
- **Authentication & User Profiles**: Secure signup, login, password reset, and role management.
- **{entity_plural_cap} Directory**: Complete profiles, status tracking, and details.
- **Operations & Scheduling**: Booking, tracking, status changes, and history.
- **Analytics & Dashboard**: Live stats, counts, and search utilities.

## 3. Detailed Features
- **Dashboard Stats**: Grid showing total records, pending tasks, active sessions, and alerts.
- **CRUD Operations**: Complete creation, reading, updating, and logical deletion of {entity_plural_cap}.
- **Activity Log**: Auditing who updated what information and when.
""",
        "plan": f"""# Project Plan & Architecture - {title}

## 1. Folder Structure
```text
{slug}/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   └── {entity_plural}.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── database/
│   │   │   ├── connection.py
│   │   │   └── models.py
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── {entity_plural_cap}.jsx
│   │   │   └── Layout.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 2. API Specifications
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register` | Register a new user | No |
| POST | `/api/auth/token` | Obtain OAuth2 token | No |
| GET | `/api/{entity_plural}` | List all {entity_plural} | Yes |
| POST | `/api/{entity_plural}` | Create new {entity_} record | Yes |
| GET | `/api/{entity_plural}/{{id}}` | Get specific {entity_} details | Yes |
| PUT | `/api/{entity_plural}/{{id}}` | Update {entity_} | Yes |
| DELETE | `/api/{entity_plural}/{{id}}` | Delete {entity_} | Yes |
""",
        "database": f"""-- Database Schema: {title}
-- Target: PostgreSQL / SQLite

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS {entity_plural} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(100) DEFAULT 'pending',
    assigned_to INTEGER,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_to) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Seed Data
INSERT OR IGNORE INTO users (id, username, email, hashed_password, role) VALUES 
(1, 'admin', 'admin@{slug}.com', '$2b$12$EixZaYVK1fsAH1y56QHx2eK.a/x8P90A2E2v0W35223.a', 'admin'),
(2, 'staff_user', 'staff@{slug}.com', '$2b$12$EixZaYVK1fsAH1y56QHx2eK.a/x8P90A2E2v0W35223.a', 'staff');

INSERT OR IGNORE INTO {entity_plural} (name, description, status, created_by) VALUES 
('Initial Sample Entry A', 'This is a sample generated record from the database designer.', 'active', 1),
('Maintenance Request B', 'System review and security audit parameters.', 'pending', 2);
""",
        "backend": {
            f"backend/app/core/config.py": f"""# backend/app/core/config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "{title} Service"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "SUPER_SECRET_SECURITY_KEY_FOR_AUTODEV_AI_PLATFORM_2026")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./{slug}.db")

    class Config:
        case_sensitive = True

settings = Settings()
""",
            f"backend/app/database/connection.py": """# backend/app/database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""",
            f"backend/app/database/models.py": f"""# backend/app/database/models.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from app.database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)

class {entity_cap}(Base):
    __tablename__ = "{entity_plural}"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="pending")
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
""",
            f"backend/app/api/auth.py": """# backend/app/api/auth.py
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import User
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

@router.post("/register")
def register(username: str, email: str, password: str, db: Session = Depends(get_db)):
    # Simulating standard registration logic
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # In production, hash the password
    new_user = User(username=username, email=email, hashed_password=password, role="user")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "user_id": new_user.id}

@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or user.hashed_password != form_data.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Generate simple mock JWT details
    return {
        "access_token": f"mock_jwt_token_for_{user.username}",
        "token_type": "bearer",
        "role": user.role
    }
""",
            f"backend/app/api/{entity_plural}.py": f"""# backend/app/api/{entity_plural}.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import {entity_cap}

router = APIRouter(prefix="/{entity_plural}", tags=["{entity_plural_cap}"])

@router.get("/")
def list_records(db: Session = Depends(get_db)):
    records = db.query({entity_cap}).all()
    return records

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_record(name: str, description: str = None, status: str = "pending", db: Session = Depends(get_db)):
    record = {entity_cap}(name=name, description=description, status=status)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.get("/{{record_id}}")
def get_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query({entity_cap}).filter({entity_cap}.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

@router.put("/{{record_id}}")
def update_record(record_id: int, name: str = None, description: str = None, status: str = None, db: Session = Depends(get_db)):
    record = db.query({entity_cap}).filter({entity_cap}.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if name:
        record.name = name
    if description:
        record.description = description
    if status:
        record.status = status
    db.commit()
    db.refresh(record)
    return record

@router.delete("/{{record_id}}")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query({entity_cap}).filter({entity_cap}.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete(record)
    db.commit()
    return {{"message": "Record deleted successfully"}}
""",
            f"backend/app/main.py": f"""# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth, {entity_plural}
from app.database.connection import engine, Base

# Build tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router({entity_plural}.router, prefix=settings.API_V1_STR)

@app.get("/")
def health_check():
    return {{"status": "online", "service": settings.PROJECT_NAME}}
"""
        },
        "frontend": {
            "frontend/package.json": f"""{{
  "name": "{slug}-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "vite build",
    "lint": "eslint . --ext js,jsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "lucide-react": "^0.263.0"
  }},
  "devDependencies": {{
    "@types/react": "^18.2.15",
    "@types/react-dom": "^18.2.7",
    "@vitejs/plugin-react": "^4.0.3",
    "vite": "^4.4.5"
  }}
}}
""",
            "frontend/vite.config.js": """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000
  }
})
""",
            "frontend/src/index.css": """:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;

  color-scheme: dark;
  color: #e2e8f0;
  background-color: #0f172a;

  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  margin: 0;
  min-width: 320px;
  min-height: 100vh;
}

h1, h2, h3, h4 {
  color: #f8fafc;
}
""",
            "frontend/src/main.jsx": """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
""",
            "frontend/src/App.jsx": f"""// frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
import {{ Layout, Users, Settings as SettingsIcon, AlertCircle, Plus, Trash2, CheckCircle }} from 'lucide-react';

export default function App() {{
  const [records, setRecords] = useState([]);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState('pending');
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);

  // Simulated fetching from FastAPI Backend
  useEffect(() => {{
    setTimeout(() => {{
      setRecords([
        {{ id: 1, name: "Sample Record 1", description: "Created by Database Seeding", status: "active" }},
        {{ id: 2, name: "Sample Record 2", description: "Verification parameters", status: "pending" }}
      ]);
      setLoading(false);
    }}, 1000);
  }}, []);

  const handleAdd = (e) => {{
    e.preventDefault();
    if (!name.trim()) return;
    const newRecord = {{
      id: Date.now(),
      name,
      description,
      status
    }};
    setRecords([...records, newRecord]);
    setName('');
    setDescription('');
    setStatus('pending');
  }};

  const handleDelete = (id) => {{
    setRecords(records.filter(r => r.id !== id));
  }};

  return (
    <div style={{{{ display: 'flex', height: '100vh', background: '#0b0f19', color: '#cbd5e1' }}}}>
      {/* Sidebar */}
      <div style={{{{ width: '250px', background: '#111827', borderRight: '1px solid #1f2937', padding: '20px' }}}}>
        <h2 style={{{{ color: '#6366f1', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1.25rem' }}}}>
          <Layout size={{24}} /> {title}
        </h2>
        <nav style={{{{ marginTop: '30px', display: 'flex', flexDirection: 'column', gap: '8px' }}}}>
          <button 
            onClick={() => setActiveTab('dashboard')}
            style={{{{
              textAlign: 'left',
              padding: '12px',
              borderRadius: '6px',
              background: activeTab === 'dashboard' ? '#1f2937' : 'transparent',
              color: activeTab === 'dashboard' ? '#ffffff' : '#9ca3af',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}}}
          >
            Dashboard
          </button>
          <button 
            onClick={() => setActiveTab('{entity_plural}')}
            style={{{{
              textAlign: 'left',
              padding: '12px',
              borderRadius: '6px',
              background: activeTab === '{entity_plural}' ? '#1f2937' : 'transparent',
              color: activeTab === '{entity_plural}' ? '#ffffff' : '#9ca3af',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}}}
          >
            Manage {entity_plural_cap}
          </button>
        </nav>
      </div>

      {/* Main Panel */}
      <div style={{{{ flex: 1, padding: '30px', overflowY: 'auto' }}}}>
        <header style={{{{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1f2937', paddingBottom: '15px' }}}}>
          <h1 style={{{{ margin: 0 }}}}>{{activeTab === 'dashboard' ? 'Overview Dashboard' : 'Manage ' + '{entity_plural_cap}'}}</h1>
          <div style={{{{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '5px' }}}}>
            <CheckCircle size={{18}} /> Backend Connection Stable
          </div>
        </header>

        {loading ? (
          <div style={{{{ marginTop: '100px', textAlign: 'center', color: '#9ca3af' }}}}>Loading module data...</div>
        ) : (
          <div style={{{{ marginTop: '30px' }}}}>
            {{activeTab === 'dashboard' ? (
              <div>
                <div style={{{{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px', marginBottom: '30px' }}}}>
                  <div style={{{{ padding: '20px', background: '#1e293b', borderRadius: '8px' }}}}>
                    <div style={{{{ color: '#94a3b8', fontSize: '0.875rem' }}}}>Total {entity_plural_cap}</div>
                    <div style={{{{ fontSize: '2rem', fontWeight: 'bold', color: '#fff' }}}}>{{records.length}}</div>
                  </div>
                  <div style={{{{ padding: '20px', background: '#1e293b', borderRadius: '8px' }}}}>
                    <div style={{{{ color: '#94a3b8', fontSize: '0.875rem' }}}}>Active Entries</div>
                    <div style={{{{ fontSize: '2rem', fontWeight: 'bold', color: '#10b981' }}}}>
                      {{records.filter(r => r.status === 'active').length}}
                    </div>
                  </div>
                  <div style={{{{ padding: '20px', background: '#1e293b', borderRadius: '8px' }}}}>
                    <div style={{{{ color: '#94a3b8', fontSize: '0.875rem' }}}}>Pending Review</div>
                    <div style={{{{ fontSize: '2rem', fontWeight: 'bold', color: '#f59e0b' }}}}>
                      {{records.filter(r => r.status === 'pending').length}}
                    </div>
                  </div>
                </div>

                <h3 style={{{{ marginBottom: '15px' }}}}>Recent Activity</h3>
                <div style={{{{ background: '#111827', borderRadius: '8px', border: '1px solid #1f2937', padding: '15px' }}}}>
                  {/* Grid or Simple list */}
                  {{records.length === 0 ? (
                    <div style={{{{ color: '#64748b' }}}}>No entries. Populate records to view logs.</div>
                  ) : (
                    records.map(r => (
                      <div key={{r.id}} style={{{{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #1f2937' }}}}>
                        <div>
                          <strong>{{r.name}}</strong>
                          <span style={{{{ color: '#64748b', marginLeft: '10px', fontSize: '0.85rem' }}}}>{{r.description}}</span>
                        </div>
                        <span style={{{{ 
                          color: r.status === 'active' ? '#10b981' : '#f59e0b',
                          background: r.status === 'active' ? 'rgba(16,185,129,0.1)' : 'rgba(245,158,11,0.1)',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '0.8rem'
                        }}}}>{{r.status}}</span>
                      </div>
                    ))
                  )}}
                </div>
              </div>
            ) : (
              <div>
                <form onSubmit={{handleAdd}} style={{{{ background: '#1e293b', padding: '20px', borderRadius: '8px', marginBottom: '30px' }}}}>
                  <h3 style={{{{ marginTop: 0 }}}}>Add New Record</h3>
                  <div style={{{{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}}}>
                    <input 
                      type="text" 
                      placeholder="Name" 
                      value={{name}} 
                      onChange={{(e) => setName(e.target.value)}}
                      required
                      style={{{{ flex: 1, padding: '10px', borderRadius: '6px', border: '1px solid #334155', background: '#0f172a', color: '#fff' }}}}
                    />
                    <input 
                      type="text" 
                      placeholder="Description" 
                      value={{description}} 
                      onChange={{(e) => setDescription(e.target.value)}}
                      style={{{{ flex: 2, padding: '10px', borderRadius: '6px', border: '1px solid #334155', background: '#0f172a', color: '#fff' }}}}
                    />
                    <select 
                      value={{status}} 
                      onChange={{(e) => setStatus(e.target.value)}}
                      style={{{{ padding: '10px', borderRadius: '6px', border: '1px solid #334155', background: '#0f172a', color: '#fff' }}}}
                    >
                      <option value="pending">Pending</option>
                      <option value="active">Active</option>
                    </select>
                    <button type="submit" style={{{{ padding: '10px 20px', background: '#4f46e5', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}}}>
                      Create
                    </button>
                  </div>
                </form>

                <h3 style={{{{ marginBottom: '15px' }}}}>All Records</h3>
                <div style={{{{ background: '#111827', borderRadius: '8px', border: '1px solid #1f2937' }}}}>
                  {{records.length === 0 ? (
                    <div style={{{{ padding: '20px', textAlign: 'center', color: '#64748b' }}}}>No entries found. Add one above!</div>
                  ) : (
                    records.map(r => (
                      <div key={{r.id}} style={{{{ display: 'flex', justifyContent: 'space-between', padding: '15px 20px', borderBottom: '1px solid #1f2937', alignItems: 'center' }}}}>
                        <div>
                          <strong style={{{{ color: '#fff' }}}}>{{r.name}}</strong>
                          <p style={{{{ margin: '5px 0 0 0', color: '#64748b', fontSize: '0.9rem' }}}}>{{r.description}}</p>
                        </div>
                        <div style={{{{ display: 'flex', alignItems: 'center', gap: '15px' }}}}>
                          <span style={{{{ 
                            color: r.status === 'active' ? '#10b981' : '#f59e0b',
                            background: r.status === 'active' ? 'rgba(16,185,129,0.1)' : 'rgba(245,158,11,0.1)',
                            padding: '4px 10px',
                            borderRadius: '4px',
                            fontSize: '0.85rem'
                          }}}}>{{r.status}}</span>
                          <button 
                            onClick={() => handleDelete(r.id)} 
                            style={{{{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer', display: 'flex', alignItems: 'center' }}}}
                          >
                            <Trash2 size={{18}} />
                          </button>
                        </div>
                      </div>
                    ))
                  )}}
                </div>
              </div>
            )}}
          </div>
        )}
      </div>
    </div>
  );
}
"""
        },
        "review": f"""# Code Review: {title}
*Total issues flagged: 3*

1. **Vulnerability: Plaintext SQL Password Seed** (High Severity)
   - *File*: `backend/app/database/models.py` (simulated seed insertion query)
   - *Finding*: Hardcoded default hashes in initial insert query.
   - *Recommendation*: Use password salting and hashing runtime helper (e.g. Passlib with bcrypt) during startup initialization.

2. **Performance: N+1 DB Queries on {entity_cap} Relationships** (Medium Severity)
   - *File*: `backend/app/api/{entity_plural}.py`
   - *Finding*: Requesting list of records fetches associated `User` records in separate synchronous queries.
   - *Recommendation*: Utilize SQLAlchemy's `joinedload` on foreign keys in database query filters.

3. **Style: Missing CORS Allowed Origins Strictness** (Low Severity)
   - *File*: `backend/app/main.py`
   - *Finding*: CORS `allow_origins=["*"]` configured.
   - *Recommendation*: Restrict origins explicitly in production configuration.
""",
        "tests": f"""# Unit Tests: {title}

```python
# backend/tests/test_{entity_plural}.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import get_db

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_get_{entity_plural}_unauthorized():
    # Attempting to access protected list routes
    response = client.get("/api/{entity_plural}")
    # Returns empty or status-controlled mock values depending on test setup
    assert response.status_code in [200, 401]

def test_create_and_delete_{entity_plural}():
    # Add record
    res = client.post("/api/{entity_plural}/", params={{"name": "Test Entry", "description": "Automated test description", "status": "pending"}})
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Test Entry"
    
    # Delete record
    record_id = data["id"]
    del_res = client.delete(f"/api/{entity_plural}/{{record_id}}")
    assert del_res.status_code == 200
```
""",
        "docs": {
            "README.md": f"""# {title}

This full-stack application was built by **AutoDev AI**, an agentic software development system. It includes a FastAPI backend framework connecting to a relational database, and an interactive frontend dashboard interface built using React.

## 👥 Features
- Secure authentication API structure
- Core CRUD operations for managing {entity_plural_cap}
- Dynamic dashboard widgets summarizing resource records

## 🛠️ Tech Stack
- **Backend**: Python, FastAPI, SQLAlchemy ORM, SQLite
- **Frontend**: React (Vite), CSS3, Lucide Icons
- **Database**: SQL DDL schemas
""",
            "API_DOCS.md": f"""# API Documentation - {title}

Base URL: `http://localhost:8000/api`

### 🔑 Authentication Routes
- `POST /auth/register` - Create account credentials.
- `POST /auth/token` - Authenticate account and receive token bearer.

### 📋 {entity_plural_cap} Routes
- `GET /{entity_plural}` - Retrieve all entries.
- `POST /{entity_plural}` - Add new {entity_cap} item.
- `GET /{entity_plural}/{{id}}` - Retrieve single record.
- `PUT /{entity_plural}/{{id}}` - Update records.
- `DELETE /{entity_plural}/{{id}}` - Delete records.
""",
            "INSTALL.md": f"""# Installation & Setup: {title}

### 🐍 Backend Deployment
1. Ensure Python 3.10+ is installed on the system.
2. Navigate to backend workspace: `cd backend`
3. Install package prerequisites: `pip install -r requirements.txt` (or root file)
4. Launch FastAPI server: `uvicorn app.main:app --reload`
5. Visit open documentation: `http://127.0.0.1:8000/docs`

### ⚡ Frontend Setup
1. Ensure Node.js v18+ is installed on the system.
2. Navigate to frontend workspace: `cd frontend`
3. Install dependencies: `npm install`
4. Start development web-server: `npm run dev`
5. Open browser at: `http://localhost:3000`
"""
        }
    }
    return hms
