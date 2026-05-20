from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    prompt: str
    style_count: int
    status: str = "pending" # pending, processing, completed, failed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    thumbnails: List["Thumbnail"] = Relationship(back_populates="job")

class Thumbnail(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    title: str
    prompt_used: str
    image_url: str
    
    job: Job = Relationship(back_populates="thumbnails")
