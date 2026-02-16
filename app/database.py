"""
Database configuration and session management
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base, Config

logger = logging.getLogger(__name__)

# Database URL from environment or default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mcp_server.db")

# Create engine
# For SQLite, we need check_same_thread=False to allow FastAPI's thread pool
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency for getting database session.
    Use with FastAPI's Depends() for automatic session management.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables and set default config
    """
    logger.info("Initializing database...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Initialize default config values if not present
    db = SessionLocal()
    try:
        # Check if config already has values
        existing_config = db.query(Config).first()
        
        if not existing_config:
            logger.info("Initializing default configuration...")
            
            # Add default config values
            default_configs = [
                {"key": "max_tasks", "value": 100},
                {"key": "default_priority", "value": "medium"}
            ]
            
            for config_data in default_configs:
                config = Config(**config_data)
                db.add(config)
            
            db.commit()
            logger.info("Default configuration initialized")
        else:
            logger.info("Configuration already initialized")
    
    except Exception as e:
        logger.error(f"Error initializing default config: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    logger.info("Database initialization complete")


def reset_db():
    """
    Reset database - drop all tables and recreate
    WARNING: This will delete all data!
    """
    logger.warning("Resetting database - all data will be lost!")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("Database reset complete")
