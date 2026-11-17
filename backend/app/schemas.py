from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    job_description: str = Field(..., min_length=10, max_length=20000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
