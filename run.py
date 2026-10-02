import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

# Ensure backend directory is first in sys.path
sys.path.insert(0, str(BACKEND_DIR))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("ScoutAI - Autonomous Job Hunting Agent & Portal Radar")
    print("Dashboard UI: http://127.0.0.1:8000/ui")
    print("=" * 60)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, app_dir=str(BACKEND_DIR))
