from fastapi import APIRouter, Query

from ..services import portfolio as svc

router = APIRouter(prefix="/api/users/{username}", tags=["portfolio"])


@router.get("/profile")
async def profile(username: str, refresh: bool = Query(False)):
    return await svc.get_profile(username, refresh)


@router.get("/repos")
async def repos(username: str, refresh: bool = Query(False),
                sort: str = Query("stars", pattern="^(stars|forks|updated|name)$")):
    data = await svc.get_repos(username, refresh)
    reverse = sort != "name"
    key = {"updated": "updated_at"}.get(sort, sort)
    return sorted(data, key=lambda r: (r.get(key) or ""), reverse=reverse)


@router.get("/contributions")
async def contributions(username: str, refresh: bool = Query(False)):
    return await svc.get_contributions(username, refresh)
