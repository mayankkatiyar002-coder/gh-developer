"""Unit tests for server-side business logic (no network needed)."""
from app.services.chatbot import answer, classify
from app.services.matcher import compute_match, extract_skills
from app.services.stats import compute_streaks, intensity_level, top_languages

REPOS = [
    {"name": "face-pad", "description": "Face anti-spoofing with PyTorch", "language": "Python",
     "languages": {"Python": 9000, "Jupyter Notebook": 1000}, "topics": ["deep-learning", "docker"],
     "stars": 12, "forks": 3, "url": "", "updated_at": "2026-11-01"},
    {"name": "portfolio-site", "description": "React portfolio", "language": "JavaScript",
     "languages": {"JavaScript": 3000, "CSS": 500, "HTML": 500}, "topics": [], "stars": 2, "forks": 0,
     "url": "", "updated_at": "2026-10-01"},
]


def test_extract_skills():
    s = extract_skills("Looking for a Python dev with React, Node.js, AWS and Docker. C++ a plus.")
    assert {"Python", "React", "Node.js", "AWS", "Docker", "C++"} <= s
    assert "Go" not in extract_skills("You will go above and beyond")


def test_match():
    m = compute_match("Python, PyTorch, Docker, Kubernetes engineer", REPOS)
    assert "Kubernetes" in m["missing"]
    assert 50 < m["match_percentage"] < 100


def test_stats():
    langs = top_languages(REPOS)
    assert langs[0]["language"] == "Python"
    assert intensity_level(0, 10) == 0 and intensity_level(10, 10) == 4
    days = [{"date": f"2026-01-0{i}", "count": c} for i, c in enumerate([1, 1, 0, 1, 1, 1], 1)]
    assert compute_streaks(days)["longest"] == 3


def test_chatbot():
    assert classify("Does he know React?") == "skill_check"
    hm = {"total": 5, "streaks": {"current": 1, "longest": 3, "active_days": 4}}
    r = answer("what are the top projects?", {"name": "X", "total_stars": 14}, REPOS, hm)
    assert "face-pad" in r["reply"]
