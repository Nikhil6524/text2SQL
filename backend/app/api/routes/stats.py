from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.schemas import ProductStatsResponse
from app.services.stats_service import get_product_stats


router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/products", response_model=ProductStatsResponse)
def product_stats(username: str = Depends(get_current_user)) -> ProductStatsResponse:
    _ = username
    return ProductStatsResponse(**get_product_stats())
