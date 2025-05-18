# config/settings.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database settings
DB_TYPE = os.getenv("DB_TYPE", "sqlite")
DB_NAME = os.getenv("DB_NAME", "ecommerce.db")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "")
DB_PORT = os.getenv("DB_PORT", "")

# Construct DATABASE_URL if not provided
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    if DB_TYPE == "sqlite":
        DATABASE_URL = f"sqlite:///{DB_NAME}"
    elif DB_TYPE == "postgresql":
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    elif DB_TYPE == "mysql":
        DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Google API settings
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"

# JWT settings
JWT_SECRET = os.getenv("JWT_SECRET", "default_secret_key_change_in_production")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Agent settings
SYSTEM_USER_ID = "system"

# Debug mode
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")