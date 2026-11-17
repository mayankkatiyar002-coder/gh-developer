# GitHub Developer Portfolio

A personal-branding dashboard that shows a developer's GitHub activity, repository stats and coding streaks. It also scores how well their tech stack fits a job description.

**Stack:** FastAPI (Python) · SQLite cache · Vanilla JS + Chart.js frontend

## Features
| Area | What it does |
|---|---|
| Contribution Graph | 365-day heatmap, colored by intensity (levels 0–4 computed on the server) |
| Repository Cards | Stars, forks, language tag and description; sortable |
| Profile Header | Followers, total stars, forks, current and longest streak, "Top Languages" pie chart |
| API Integration | GitHub REST (profile, repos, languages, events) + GraphQL (contribution calendar) |
| Caching Engine | SQLite: `cache` (TTL JSON), `repositories` (normalised metadata), `user_settings` |
| **Vibe Check: Tech Stack Compatibility** | Paste a JD → server pulls tech keywords out of it (alias dictionary) → compares them with the byte-weighted languages and frameworks in cached repos → **Match % badge** at the top of the profile |
| **Extra 1: "Ask My Portfolio" chatbot** | Recruiters ask questions in plain language ("Does he know React?", "top projects?"). A server-side intent classifier answers from cached data |
| **Extra 2: AI Career Insights** | Auto-written recruiter bio, a 0–100 portfolio-strength score with tips, and a **skill-gap roadmap** (starter project + resource for each skill the last JD match found missing) |

All business logic (stats, streaks, matching, scoring, chat) runs on the server. The frontend only renders.

## Architecture
```
backend/app/
  main.py            FastAPI app, routers, error handling, static hosting
  config.py          env config (.env)
  db.py              SQLite caching engine
  schemas.py         request validation (pydantic)
  routers/           portfolio.py · match.py · assistant.py
  services/
    github_client.py REST + GraphQL client (events fallback without token)
    portfolio.py     cache-first orchestration
    stats.py         top languages, streaks, heatmap intensity
    matcher.py       Tech Stack Compatibility engine
    chatbot.py       Ask-My-Portfolio intent bot
    insights.py      bio, strength score, skill-gap roadmap
backend/tests/       unit tests for the business logic
frontend/            index.html · styles.css · api.js · app.js
```

## Run
```bash
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env        # optional: add GITHUB_TOKEN for the full-year heatmap and 5000 req/hr
uvicorn app.main:app --reload
# open http://localhost:8000  →  enter a GitHub username
pytest -q tests
```

## API
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/users/{u}/profile?refresh=` | profile + totals + top languages |
| GET | `/api/users/{u}/repos?sort=stars\|forks\|updated\|name` | repository cards |
| GET | `/api/users/{u}/contributions` | heatmap cells + streaks |
| POST | `/api/users/{u}/match` `{job_description}` | match %, badge, matched/missing skills |
| POST | `/api/users/{u}/chat` `{message}` | chatbot reply |
| GET | `/api/users/{u}/insights` | bio, strength score, skill-gap roadmap |
| GET | `/api/users/{u}/settings` | cached user settings (last JD, last score) |

## Match % formula
`match = Σ weight(skill found) / Σ weight(skill required) × 100`. Languages have weight 1.0 and frameworks 0.75. A framework that is only implied by a related language (e.g. React via JavaScript) gets half credit.
Badges: ≥80 Excellent · ≥60 Strong · ≥40 Moderate · <40 Low.
