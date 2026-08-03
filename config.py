import os
from pathlib import Path


class Config:
    BASE_DIR = Path(__file__).resolve().parent
    INSTANCE_DIR = BASE_DIR / "instance"
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-before-demo")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{(INSTANCE_DIR / 'trekking.db').as_posix()}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ADMIN_NAME = os.environ.get("ADMIN_NAME", "System Administrator")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@trek.local")
    ADMIN_PHONE = os.environ.get("ADMIN_PHONE", "9999999999")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@123")
