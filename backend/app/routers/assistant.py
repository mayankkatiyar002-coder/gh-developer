from fastapi import APIRouter

from .. import db
from ..schemas import ChatRequest
from ..services import portfolio as svc
from ..services.chatbot import answer
from ..services.insights import generate_bio, profile_score, skill_gap_roadmap
from ..services.matcher import compute_match

router = APIRouter(prefix="/api/users/{username}", tags=["assistant"])


@router.post("/chat")
async def chat(username: str, body: ChatRequest):
    profile = await svc.get_profile(username)
    repos = await svc.get_repos(username)
    heatmap = await svc.get_contributions(username)
    return answer(body.message, profile, repos, heatmap)


@router.get("/insights")
async def insights(username: str):
    profile = await svc.get_profile(username)
    repos = await svc.get_repos(username)
    heatmap = await svc.get_contributions(username)
    jd = db.get_settings(username).get("last_job_description")
    roadmap = skill_gap_roadmap(compute_match(jd, repos)["missing"]) if jd else []
    return {
        "bio": generate_bio(profile, repos, heatmap),
        "portfolio_strength": profile_score(profile, repos, heatmap),
        "skill_gap_roadmap": roadmap,
    }
