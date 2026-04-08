import os
import sys
from pathlib import Path

# Папка с данными: C:\FuelTracker (создаётся setup-ом)
# Если запуск из исходников — используем корень проекта
DATA_DIR = Path(os.getenv('FUELTRACKER_DATA', r'C:\FuelTracker'))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Если собрано PyInstaller — exe рядом с данными
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

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
