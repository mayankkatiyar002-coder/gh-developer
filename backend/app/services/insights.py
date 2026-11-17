"""Extra feature #2: AI Career Insights.

- generate_bio: auto-written, recruiter-ready summary paragraph for personal branding.
- skill_gap_roadmap: for skills missing from the last job-description match, suggests
  a concrete starter project and learning resource so the developer can close the gap.
- profile_score: a 0-100 "portfolio strength" score with actionable tips.
"""
from .stats import top_languages

ROADMAP = {
    "React": ("Build a GitHub-stats dashboard SPA with React + Vite", "https://react.dev/learn"),
    "TypeScript": ("Port an existing JS project to TypeScript with strict mode", "https://www.typescriptlang.org/docs/"),
    "Docker": ("Containerise one of your APIs with a multi-stage Dockerfile + compose", "https://docs.docker.com/get-started/"),
    "Kubernetes": ("Deploy a 2-service app on minikube with a Helm chart", "https://kubernetes.io/docs/tutorials/"),
    "AWS": ("Deploy a serverless API using Lambda + API Gateway + DynamoDB", "https://aws.amazon.com/getting-started/"),
    "GCP": ("Deploy a FastAPI service on Cloud Run with CI from GitHub", "https://cloud.google.com/run/docs/quickstarts"),
    "Azure": ("Host a web app on Azure App Service with GitHub Actions", "https://learn.microsoft.com/azure/"),
    "Java": ("Write a REST API with Spring Boot and JPA", "https://spring.io/guides"),
    "Spring": ("Write a REST API with Spring Boot and JPA", "https://spring.io/guides"),
    "Go": ("Build a concurrent URL health-checker CLI in Go", "https://go.dev/tour/"),
    "Rust": ("Write a CLI tool (e.g. grep clone) in Rust", "https://doc.rust-lang.org/book/"),
    "Node.js": ("Build a REST API with Express + JWT auth", "https://nodejs.org/en/learn"),
    "SQL": ("Design a normalised schema and analytics queries for a sample dataset", "https://sqlbolt.com/"),
    "PyTorch": ("Train and publish an image classifier with PyTorch", "https://pytorch.org/tutorials/"),
    "TensorFlow": ("Train a text classifier with Keras and export to TF Lite", "https://www.tensorflow.org/tutorials"),
    "Machine Learning": ("Publish an end-to-end ML notebook with EDA, model and evaluation", "https://scikit-learn.org/stable/tutorial/"),
    "LLM": ("Build a RAG chatbot over your own docs with an open LLM", "https://python.langchain.com/docs/tutorials/"),
    "GraphQL": ("Add a GraphQL layer over an existing REST API", "https://graphql.org/learn/"),
    "MongoDB": ("Build a CRUD API backed by MongoDB Atlas", "https://www.mongodb.com/docs/"),
}


def generate_bio(profile: dict, repos: list[dict], heatmap: dict) -> str:
    name = profile.get("name") or profile.get("login")
    langs = [l["language"] for l in top_languages(repos, 3) if l["language"] != "Other"]
    top = repos[0] if repos else None
    parts = [f"{name} is a developer"]
    if profile.get("location"):
        parts[0] += f" based in {profile['location']}"
    if langs:
        parts[0] += f" working primarily with {', '.join(langs[:-1]) + ' and ' + langs[-1] if len(langs) > 1 else langs[0]}"
    parts[0] += "."
    parts.append(f"They maintain {len(repos)} public projects that have earned "
                 f"{profile.get('total_stars', 0)} stars and {profile.get('total_forks', 0)} forks.")
    if top:
        parts.append(f"Their flagship project, {top['name']}, "
                     f"{('— ' + top['description'].rstrip('.') + ' — ') if top.get('description') else ''}"
                     f"leads with {top['stars']} stars.")
    s = heatmap.get("streaks", {})
    if heatmap.get("total"):
        parts.append(f"With {heatmap['total']} recent contributions and a longest streak of "
                     f"{s.get('longest', 0)} days, they code consistently.")
    return " ".join(parts)


def skill_gap_roadmap(missing: list[str]) -> list[dict]:
    out = []
    for skill in missing:
        project, link = ROADMAP.get(skill, (f"Build a small project that showcases {skill}", None))
        out.append({"skill": skill, "starter_project": project, "resource": link})
    return out


def profile_score(profile: dict, repos: list[dict], heatmap: dict) -> dict:
    tips, score = [], 0
    described = sum(1 for r in repos if r.get("description"))
    if repos:
        ratio = described / len(repos)
        score += round(20 * ratio)
        if ratio < 0.8:
            tips.append(f"Add descriptions to {len(repos) - described} repositories.")
    topics = sum(1 for r in repos if r.get("topics"))
    score += round(15 * (topics / len(repos))) if repos else 0
    if repos and topics / len(repos) < 0.5:
        tips.append("Tag repositories with topics to improve discoverability.")
    if profile.get("bio"):
        score += 10
    else:
        tips.append("Write a GitHub bio — it is the first thing recruiters read.")
    langs = len([l for l in top_languages(repos, 10) if l["language"] != "Other"])
    score += min(langs, 5) * 3
    if langs < 3:
        tips.append("Showcase breadth: publish a project in another language.")
    active = heatmap.get("streaks", {}).get("active_days", 0)
    score += min(active, 100) * 0.25
    if active < 50:
        tips.append("Commit more regularly to build a visible contribution streak.")
    score += min(profile.get("total_stars", 0), 50) * 0.2
    return {"score": min(round(score), 100), "tips": tips}
