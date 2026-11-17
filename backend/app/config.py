"""Central configuration loaded from environment variables."""
import os
from pathlib import Path


def _load_dotenv() -> None:
    """Minimal .env loader (avoids extra dependency)."""
    for candidate in (Path(".env"), Path(__file__).resolve().parents[2] / ".env"):
        if candidate.exists():
            for line in candidate.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
            break


_load_dotenv()

GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))
DB_PATH: str = os.getenv("DB_PATH", "portfolio_cache.db")
GITHUB_REST = "https://api.github.com"
GITHUB_GRAPHQL = "https://api.github.com/graphql"
