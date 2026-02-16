"""
Database models for MCP Server
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(String(50), default="user")
    user_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Task(Base):
    """Task model"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, default="")
    priority = Column(String(50), default="medium")
    status = Column(String(50), default="pending", index=True)
    assigned_to = Column(String(255), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Config(Base):
    """Configuration key-value store"""
    __tablename__ = "config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Log(Base):
    """Action log model"""
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    action = Column(String(255), nullable=False, index=True)
    payload = Column(JSON, default={})
    status = Column(String(50), default="success", index=True)


__all__ = ["Base", "User", "Task", "Config", "Log"]
