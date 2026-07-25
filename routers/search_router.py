from fastapi import APIRouter
from services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/")
def search(query: str):
    return SearchService.search(query)