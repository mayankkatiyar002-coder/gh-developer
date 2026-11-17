from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .db import init_db
from .routers import assistant, match, portfolio
from .services.github_client import GitHubError

app = FastAPI(title="GitHub Developer Portfolio API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def _startup():
    init_db()


@app.exception_handler(GitHubError)
async def _gh_error(_: Request, exc: GitHubError):
    return JSONResponse(status_code=exc.status, content={"detail": exc.message})


app.include_router(portfolio.router)
app.include_router(match.router)
app.include_router(assistant.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")
