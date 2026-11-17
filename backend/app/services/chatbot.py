"""Extra feature #1: "Ask My Portfolio" chatbot.

Recruiters can ask natural-language questions about the developer. A lightweight
intent classifier (keyword scoring) routes the question to a handler that answers
from the SQLite-cached data, so answers are grounded and need no external LLM.
"""
import re
from datetime import datetime

from .matcher import SKILLS, extract_skills
from .stats import top_languages

INTENTS: dict[str, list[str]] = {
    "greeting": ["hi", "hello", "hey", "help", "what can you"],
    "top_repo": ["best", "top", "popular", "most starred", "famous", "highlight"],
    "languages": ["language", "languages", "stack", "tech", "technologies", "code in"],
    "streak": ["streak", "consistent", "active", "contribution", "commits", "activity"],
    "stars": ["stars", "star count", "forks", "followers", "how many"],
    "recent": ["recent", "latest", "currently", "working on", "new"],
    "skill_check": ["know", "experience", "worked with", "use", "familiar", "does"],
    "summary": ["who", "about", "summary", "summarize", "describe", "tell me"],
}


def classify(message: str) -> str:
    msg = message.lower()
    if extract_skills(msg) and re.search(r"\b(know|experience|worked|use|familiar|does|any)\b", msg):
        return "skill_check"
    scores = {k: sum(1 for kw in kws if kw in msg) for k, kws in INTENTS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "fallback"


def answer(message: str, profile: dict, repos: list[dict], heatmap: dict) -> dict:
    intent = classify(message)
    name = profile.get("name") or profile.get("login")
    langs = top_languages(repos, limit=5)

    if intent == "greeting":
        text = (f"Hi! I'm {name}'s portfolio assistant. Ask me about their top projects, "
                "languages, coding streak, recent work, or whether they know a technology.")
    elif intent == "top_repo":
        top = repos[:3]
        if not top:
            text = f"{name} has no public repositories yet."
        else:
            items = "; ".join(f"{r['name']} ({r['stars']}★, {r.get('language') or 'n/a'})" for r in top)
            text = f"{name}'s most popular projects: {items}."
    elif intent == "languages":
        text = (f"{name} mostly codes in " +
                ", ".join(f"{l['language']} ({l['percent']}%)" for l in langs) + "."
                if langs else f"No language data available for {name}.")
    elif intent == "streak":
        s = heatmap["streaks"]
        text = (f"{name} made {heatmap['total']} contributions in the tracked period, "
                f"with a current streak of {s['current']} days and a longest streak of "
                f"{s['longest']} days across {s['active_days']} active days.")
    elif intent == "stars":
        text = (f"{name} has {profile.get('followers', 0)} followers, "
                f"{profile.get('total_stars', 0)} total stars and "
                f"{profile.get('total_forks', 0)} forks across {len(repos)} repositories.")
    elif intent == "recent":
        recent = sorted(repos, key=lambda r: r.get("updated_at") or "", reverse=True)[:3]
        text = "Recently active repositories: " + "; ".join(
            f"{r['name']} (updated {(r.get('updated_at') or '')[:10]})" for r in recent) + "."
    elif intent == "skill_check":
        asked = extract_skills(message)
        lines = []
        for skill in sorted(asked):
            hits = [r["name"] for r in repos
                    if skill in (r.get("languages") or {})
                    or skill in extract_skills(f"{r['name']} {r.get('description') or ''} {' '.join(r.get('topics') or [])}")]
            if hits:
                lines.append(f"Yes — {skill} appears in {len(hits)} repo(s), e.g. {', '.join(hits[:3])}.")
            else:
                lines.append(f"I couldn't find {skill} in {name}'s public repositories.")
        text = " ".join(lines)
    elif intent == "summary":
        from .insights import generate_bio
        text = generate_bio(profile, repos, heatmap)
    else:
        text = ("I can answer questions about top projects, languages, streaks, stars, recent work, "
                "or specific skills (e.g. 'Does Mayank know React?').")
    return {"intent": intent, "reply": text, "timestamp": datetime.utcnow().isoformat() + "Z"}
