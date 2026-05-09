from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    action: str
    blocked: bool
    sql_executed: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    rows_affected: Optional[int] = None


class MetricSummary(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    avg: Optional[float] = None


class ProductSummary(BaseModel):
    count: int
    cost: MetricSummary
    rating: MetricSummary
    depreciation_per_year: MetricSummary


class Histogram(BaseModel):
    bins: List[float]
    counts: List[int]


class Heatmap(BaseModel):
    labels: List[str]
    matrix: List[List[float]]


class ProductStatsResponse(BaseModel):
    summary: ProductSummary
    histograms: Dict[str, Histogram]
    heatmap: Heatmap
