from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers.search_router import router as search_router
from routers.scout_router import router as scout_router

app = FastAPI(title="ScoutAI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)
app.include_router(scout_router)

# Look for frontend directory in parent or current folder
FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


@app.get("/")
def home():
    from fastapi.responses import RedirectResponse
    if FRONTEND_DIR.exists():
        return RedirectResponse(url="/ui")
    return {"message": "ScoutAI is running!", "ui": "/ui"}


if __name__ == "__main__":
    import uvicorn
    print("\nStarting ScoutAI Server at http://127.0.0.1:8000/ui\n")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
