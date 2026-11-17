"""Tech Stack Compatibility engine.

1. Extract tech keywords from a free-text job description using an alias dictionary
   (handles 'js', 'node.js', 'golang', 'c++', 'react', etc.).
2. Build the user's skill profile from cached repositories:
   - languages (byte-weighted from /languages endpoint)
   - frameworks/tools detected in repo topics, names and descriptions
3. Match % = weighted share of JD skills present in the profile.
   Languages count 1.0, frameworks/tools 0.75 (frameworks are noisier signals).
"""
import re

# canonical -> (category, aliases)
SKILLS: dict[str, tuple[str, list[str]]] = {
    # languages
    "Python": ("language", ["python", "py", "python3"]),
    "JavaScript": ("language", ["javascript", "js", "ecmascript", "es6"]),
    "TypeScript": ("language", ["typescript", "ts"]),
    "Java": ("language", ["java"]),
    "C": ("language", ["c language", "ansi c", " c "]),
    "C++": ("language", ["c++", "cpp"]),
    "C#": ("language", ["c#", "csharp", ".net", "dotnet"]),
    "Go": ("language", ["go", "golang"]),
    "Rust": ("language", ["rust"]),
    "Ruby": ("language", ["ruby"]),
    "PHP": ("language", ["php"]),
    "Kotlin": ("language", ["kotlin"]),
    "Swift": ("language", ["swift"]),
    "Scala": ("language", ["scala"]),
    "R": ("language", ["r programming", "r language", "rstudio"]),
    "Dart": ("language", ["dart"]),
    "Shell": ("language", ["shell", "bash", "shell scripting"]),
    "HTML": ("language", ["html", "html5"]),
    "CSS": ("language", ["css", "css3", "scss", "sass", "tailwind"]),
    "SQL": ("language", ["sql", "mysql", "postgresql", "postgres", "sqlite", "pl/sql"]),
    "Jupyter Notebook": ("language", ["jupyter", "notebook"]),
    "MATLAB": ("language", ["matlab"]),
    "Solidity": ("language", ["solidity"]),
    # frameworks / tools
    "React": ("framework", ["react", "reactjs", "react.js", "next.js", "nextjs"]),
    "Angular": ("framework", ["angular"]),
    "Vue": ("framework", ["vue", "vuejs", "vue.js", "nuxt"]),
    "Node.js": ("framework", ["node", "nodejs", "node.js", "express", "expressjs"]),
    "Django": ("framework", ["django"]),
    "Flask": ("framework", ["flask"]),
    "FastAPI": ("framework", ["fastapi"]),
    "Spring": ("framework", ["spring", "spring boot", "springboot"]),
    "TensorFlow": ("framework", ["tensorflow", "keras"]),
    "PyTorch": ("framework", ["pytorch", "torch"]),
    "Machine Learning": ("framework", ["machine learning", "ml", "deep learning", "scikit-learn", "sklearn"]),
    "Docker": ("framework", ["docker", "container", "containers"]),
    "Kubernetes": ("framework", ["kubernetes", "k8s"]),
    "AWS": ("framework", ["aws", "amazon web services", "lambda", "s3", "ec2"]),
    "GCP": ("framework", ["gcp", "google cloud", "bigquery", "vertex ai"]),
    "Azure": ("framework", ["azure"]),
    "MongoDB": ("framework", ["mongodb", "mongo"]),
    "GraphQL": ("framework", ["graphql"]),
    "Git": ("framework", ["git", "github", "gitlab"]),
    "LLM": ("framework", ["llm", "langchain", "openai", "gen ai", "genai", "generative ai", "rag"]),
}

# Languages implied by a framework (so a React JD gives credit for JS repos, etc.)
IMPLIES = {
    "React": {"JavaScript", "TypeScript"}, "Angular": {"TypeScript"}, "Vue": {"JavaScript", "TypeScript"},
    "Node.js": {"JavaScript", "TypeScript"}, "Django": {"Python"}, "Flask": {"Python"},
    "FastAPI": {"Python"}, "Spring": {"Java", "Kotlin"}, "TensorFlow": {"Python", "Jupyter Notebook"},
    "PyTorch": {"Python", "Jupyter Notebook"}, "Machine Learning": {"Python", "Jupyter Notebook", "R"},
    "LLM": {"Python"},
}

WEIGHTS = {"language": 1.0, "framework": 0.75}


def _normalise(text: str) -> str:
    return f" {re.sub(r'[^a-z0-9+#./ ]', ' ', text.lower())} "


def _contains(text: str, alias: str) -> bool:
    alias = alias.strip() if alias.strip() else alias
    pattern = r"(?<![a-z0-9+#])" + re.escape(alias) + r"(?![a-z0-9+#])"
    return re.search(pattern, text) is not None


def extract_skills(text: str) -> set[str]:
    norm = _normalise(text)
    found = set()
    for canon, (_, aliases) in SKILLS.items():
        if any(_contains(norm, a.strip()) for a in aliases):
            found.add(canon)
    # 'go' and 'r' are very ambiguous words; require stronger context
    if "Go" in found and not re.search(r"\bgolang\b|\bgo (developer|programming|lang)", norm):
        found.discard("Go")
    return found


def user_skill_profile(repos: list[dict]) -> dict[str, float]:
    """Return {skill: strength 0..1}. Language strength = byte share; frameworks = repo share."""
    lang_bytes: dict[str, int] = {}
    for r in repos:
        for lang, b in (r.get("languages") or {}).items():
            lang_bytes[lang] = lang_bytes.get(lang, 0) + b
    total = sum(lang_bytes.values()) or 1
    profile = {lang: b / total for lang, b in lang_bytes.items()}

    n = max(len(repos), 1)
    fw_counts: dict[str, int] = {}
    for r in repos:
        blob = " ".join([r["name"].replace("-", " ").replace("_", " "),
                         r.get("description") or "", " ".join(r.get("topics") or [])])
        for skill in extract_skills(blob):
            if SKILLS[skill][0] == "framework":
                fw_counts[skill] = fw_counts.get(skill, 0) + 1
    for skill, c in fw_counts.items():
        profile[skill] = max(profile.get(skill, 0), c / n)
    if repos:
        profile.setdefault("Git", 1.0)  # they host code on GitHub
    return profile


def badge_for(pct: float) -> dict:
    if pct >= 80:
        return {"label": "Excellent Match", "color": "#2da44e"}
    if pct >= 60:
        return {"label": "Strong Match", "color": "#1f883d"}
    if pct >= 40:
        return {"label": "Moderate Match", "color": "#bf8700"}
    return {"label": "Low Match", "color": "#cf222e"}


def compute_match(job_description: str, repos: list[dict]) -> dict:
    required = extract_skills(job_description)
    if not required:
        return {"match_percentage": 0, "badge": badge_for(0), "required": [], "matched": [],
                "missing": [], "message": "No recognisable tech keywords found in the job description."}
    profile = user_skill_profile(repos)
    matched, missing = [], []
    earned = possible = 0.0
    for skill in sorted(required):
        w = WEIGHTS[SKILLS[skill][0]]
        possible += w
        direct = profile.get(skill, 0)
        implied = any(profile.get(l, 0) > 0 for l in IMPLIES.get(skill, set()))
        if direct > 0:
            earned += w
            matched.append({"skill": skill, "strength": round(direct * 100, 1), "via": "direct"})
        elif implied:
            earned += w * 0.5
            matched.append({"skill": skill, "strength": None, "via": "related language"})
        else:
            missing.append(skill)
    pct = round(earned * 100 / possible, 1)
    return {
        "match_percentage": pct,
        "badge": badge_for(pct),
        "required": sorted(required),
        "matched": matched,
        "missing": missing,
    }
