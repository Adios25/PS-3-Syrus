from fastapi import APIRouter

from .endpoints import users
from .endpoints import checklists

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    checklists.router,
    prefix="/users/{user_id}/checklists",
    tags=["checklists"],
)
