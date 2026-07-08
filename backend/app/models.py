from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)

    api_keys = relationship("ApiKey", back_populates="owner")
    agents = relationship("AgentConfig", back_populates="owner")

class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    category = Column(String, index=True) # e.g., 'OpenAI', 'Gemini', 'Anthropic'
    encrypted_key = Column(String)

    owner = relationship("User", back_populates="api_keys")

class AgentConfig(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    category = Column(String)
    api_selections = Column(JSON)
    behavior = Column(Text)

    owner = relationship("User", back_populates="agents")
    build_logs = relationship("BuildLog", back_populates="agent")

class BuildLog(Base):
    __tablename__ = "build_logs"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    agent_config_id = Column(Integer, ForeignKey("agents.id"))
    status = Column(String, default="pending")
    logs = Column(JSON, default=list)
    files_json = Column(JSON, default=dict)
    error = Column(String, nullable=True)

    agent = relationship("AgentConfig", back_populates="build_logs")
