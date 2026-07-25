from fastapi import FastAPI
from routers.search_router import router as search_router

app = FastAPI(title="ScoutAI")

app.include_router(search_router)


@app.get("/")
def home():
    return {"message": "ScoutAI is running!"}