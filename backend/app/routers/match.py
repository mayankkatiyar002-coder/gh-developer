from fastapi import APIRouter

from .. import db
from ..schemas import MatchRequest
from ..services import portfolio as svc
from ..services.matcher import compute_match

router = APIRouter(prefix="/api/users/{username}", tags=["match"])


@router.post("/match")
async def match(username: str, body: MatchRequest):
    repos = await svc.get_repos(username)  # cache-first (SQLite)
    result = compute_match(body.job_description, repos)
    db.set_setting(username, "last_job_description", body.job_description)
    db.set_setting(username, "last_match_percentage", str(result["match_percentage"]))
    return result


@router.get("/settings")
def settings(username: str):
    return db.get_settings(username)
