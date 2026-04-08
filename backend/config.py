import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', BASE_DIR / 'fuel_tracking.db')
SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
HOST = os.getenv('HOST', '127.0.0.1')
PORT = int(os.getenv('PORT', 5000))

# CORS configuration
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
