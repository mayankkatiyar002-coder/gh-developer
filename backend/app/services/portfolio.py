"""Orchestrates cache-first data loading."""
from .. import db
from . import github_client as gh
from .stats import build_heatmap, summarise


async def get_repos(username: str, refresh: bool = False) -> list[dict]:
    key = f"repos:{username.lower()}"
    if not refresh and db.cache_get(key) is not None:
        cached = db.load_repositories(username)
        if cached:
            return cached
    repos = await gh.fetch_repositories(username)
    db.save_repositories(username, repos)
    db.cache_set(key, {"count": len(repos)})
    return db.load_repositories(username)


async def get_profile(username: str, refresh: bool = False) -> dict:
    key = f"profile:{username.lower()}"
    profile = None if refresh else db.cache_get(key)
    if profile is None:
        profile = await gh.fetch_profile(username)
        db.cache_set(key, profile)
    repos = await get_repos(username, refresh)
    return summarise(profile, repos)


async def get_contributions(username: str, refresh: bool = False) -> dict:
    key = f"contrib:{username.lower()}"
    contrib = None if refresh else db.cache_get(key)
    if contrib is None:
        contrib = await gh.fetch_contributions(username)
        db.cache_set(key, contrib)
    return build_heatmap(contrib)
