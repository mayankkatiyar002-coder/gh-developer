"""GitHub REST + GraphQL integration.

- REST: profile, repositories, per-repo language breakdown, public events.
- GraphQL: contribution calendar (requires GITHUB_TOKEN).
  Without a token we fall back to building a heatmap from public events (last ~90 days).
"""
from collections import Counter
from datetime import date, datetime, timedelta, timezone

import httpx

from ..config import GITHUB_GRAPHQL, GITHUB_REST, GITHUB_TOKEN


class GitHubError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def _headers() -> dict:
    h = {"Accept": "application/vnd.github+json", "User-Agent": "gh-dev-portfolio"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


async def _get(client: httpx.AsyncClient, path: str, params: dict | None = None):
    r = await client.get(f"{GITHUB_REST}{path}", headers=_headers(), params=params)
    if r.status_code == 404:
        raise GitHubError(404, "GitHub user or resource not found")
    if r.status_code == 403 and r.headers.get("x-ratelimit-remaining") == "0":
        raise GitHubError(429, "GitHub API rate limit exceeded. Add GITHUB_TOKEN or retry later.")
    if r.status_code >= 400:
        raise GitHubError(r.status_code, r.text[:200])
    return r.json()


async def fetch_profile(username: str) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        u = await _get(client, f"/users/{username}")
    return {
        "login": u["login"],
        "name": u.get("name") or u["login"],
        "avatar_url": u.get("avatar_url"),
        "bio": u.get("bio"),
        "location": u.get("location"),
        "blog": u.get("blog"),
        "html_url": u.get("html_url"),
        "followers": u.get("followers", 0),
        "following": u.get("following", 0),
        "public_repos": u.get("public_repos", 0),
        "created_at": u.get("created_at"),
    }


async def fetch_repositories(username: str, max_repos: int = 100) -> list[dict]:
    """Fetch owned, non-fork repos plus per-repo language byte counts."""
    async with httpx.AsyncClient(timeout=30) as client:
        raw = await _get(
            client, f"/users/{username}/repos",
            {"per_page": max_repos, "sort": "updated", "type": "owner"},
        )
        repos = []
        for r in raw:
            if r.get("fork"):
                continue
            try:
                langs = await _get(client, f"/repos/{username}/{r['name']}/languages")
            except GitHubError:
                langs = {r["language"]: 1} if r.get("language") else {}
            repos.append({
                "name": r["name"],
                "description": r.get("description") or "",
                "language": r.get("language"),
                "languages": langs,
                "topics": r.get("topics", []),
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "url": r.get("html_url"),
                "updated_at": r.get("pushed_at") or r.get("updated_at"),
            })
    return repos


CONTRIB_QUERY = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{
        totalContributions
        weeks{ contributionDays{ date contributionCount } }
      }
    }
  }
}"""


async def fetch_contributions(username: str) -> dict:
    """Return {'source': str, 'days': [{date, count}], 'total': int}."""
    if GITHUB_TOKEN:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                GITHUB_GRAPHQL, headers=_headers(),
                json={"query": CONTRIB_QUERY, "variables": {"login": username}},
            )
        data = r.json()
        if r.status_code == 200 and data.get("data", {}).get("user"):
            cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
            days = [
                {"date": d["date"], "count": d["contributionCount"]}
                for w in cal["weeks"] for d in w["contributionDays"]
            ]
            return {"source": "graphql", "days": days, "total": cal["totalContributions"]}

    # Fallback: public events API (max ~300 events / 90 days)
    counts: Counter = Counter()
    async with httpx.AsyncClient(timeout=30) as client:
        for page in (1, 2, 3):
            try:
                events = await _get(client, f"/users/{username}/events/public",
                                    {"per_page": 100, "page": page})
            except GitHubError:
                break
            if not events:
                break
            for e in events:
                weight = len(e.get("payload", {}).get("commits", [])) if e["type"] == "PushEvent" else 1
                counts[e["created_at"][:10]] += max(weight, 1)
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=364)
    days = [
        {"date": (start + timedelta(days=i)).isoformat(),
         "count": counts.get((start + timedelta(days=i)).isoformat(), 0)}
        for i in range(365)
    ]
    return {"source": "events", "days": days, "total": sum(counts.values())}
