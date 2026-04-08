import os
import sys
from pathlib import Path

# Папка с данными = папка рядом с EXE (при сборке) или корень проекта (при разработке)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = Path(os.getenv('FUELTRACKER_DATA', BASE_DIR))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_PATH = os.getenv('DATABASE_PATH', DATA_DIR / 'fuel_tracking.db')
SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
HOST = os.getenv('HOST', '127.0.0.1')
PORT = int(os.getenv('PORT', 5000))

# CORS
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
