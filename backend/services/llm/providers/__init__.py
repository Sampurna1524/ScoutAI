import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from the backend/.env file regardless of the current working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")
