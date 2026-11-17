"""Server-side computations: totals, top languages, streaks, heatmap intensity."""
from collections import defaultdict
from datetime import date


def top_languages(repos: list[dict], limit: int = 6) -> list[dict]:
    """Aggregate language bytes across repos -> percentage share."""
    totals: dict[str, int] = defaultdict(int)
    for r in repos:
        for lang, b in (r.get("languages") or {}).items():
            totals[lang] += b
    grand = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    top = ranked[:limit]
    other = sum(b for _, b in ranked[limit:])
    result = [{"language": l, "bytes": b, "percent": round(b * 100 / grand, 1)} for l, b in top]
    if other:
        result.append({"language": "Other", "bytes": other, "percent": round(other * 100 / grand, 1)})
    return result


def intensity_level(count: int, max_count: int) -> int:
    """Map a day's count to 0-4 intensity (GitHub-style quartiles)."""
    if count <= 0 or max_count <= 0:
        return 0
    ratio = count / max_count
    if ratio <= 0.25:
        return 1
    if ratio <= 0.5:
        return 2
    if ratio <= 0.75:
        return 3
    return 4


def compute_streaks(days: list[dict]) -> dict:
    """Current and longest streak of consecutive active days."""
    ordered = sorted(days, key=lambda d: d["date"])
    longest = run = 0
    for d in ordered:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    current = 0
    today = date.today().isoformat()
    for i, d in enumerate(reversed(ordered)):
        if d["count"] > 0:
            current += 1
        elif i == 0 and d["date"] >= today:
            continue  # today not yet active: don't break streak
        else:
            break
    active = sum(1 for d in ordered if d["count"] > 0)
    return {"current": current, "longest": longest, "active_days": active}


def build_heatmap(contrib: dict) -> dict:
    days = contrib["days"]
    max_count = max((d["count"] for d in days), default=0)
    cells = [{**d, "level": intensity_level(d["count"], max_count)} for d in days]
    return {
        "source": contrib["source"],
        "total": contrib["total"],
        "max": max_count,
        "days": cells,
        "streaks": compute_streaks(days),
    }


def summarise(profile: dict, repos: list[dict]) -> dict:
    return {
        **profile,
        "total_stars": sum(r["stars"] for r in repos),
        "total_forks": sum(r["forks"] for r in repos),
        "repo_count": len(repos),
        "top_languages": top_languages(repos),
    }
