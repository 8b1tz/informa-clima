from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from src.services import get_statistics_for_all_cities

router = APIRouter()


@router.get("/locations/rs", response_model=List[dict])
async def get_locations_rs() -> List[dict]:
    """
    Retorna todas as cidades do Rio Grande do Sul com suas estatísticas
    meteorológicas.
    """
    cities: List[dict] = await get_statistics_for_all_cities()
    if not cities:
        raise HTTPException(status_code=404, detail="No cities found")
    return cities


@router.get("/locations/rs/filter", response_model=List[dict])
async def filter_locations_rs(
    status: Optional[str] = Query(None, description="Status to filter by: SEGURO and PERIGO"),
    city: Optional[str] = Query(None, description="City to filter by (optional)")
) -> List[dict]:
    """
    Filtra as cidades do Rio Grande do Sul com base no status de risco e/ou nome da cidade.
    """
    cities: List[dict] = await get_statistics_for_all_cities()
    
    if status:
        cities = [city_data for city_data in cities if city_data.get("stats", {}).get("risk_level") == status]
    
    if city:
        cities = [city_data for city_data in cities if city_data.get("city").lower() == city.lower()]
    
    if not cities:
        raise HTTPException(status_code=404, detail="No cities match the criteria")
    
    return cities
