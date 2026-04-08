#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.config import SQLALCHEMY_DATABASE_URI

# Create engine
engine = create_engine(SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False})

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database - create all tables"""
    # Import models to register them with Base
    from backend import models
    Base.metadata.create_all(bind=engine)
    print("✓ Таблицы базы данных созданы")
