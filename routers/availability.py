from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict
from services.availability_service import AvailabilityService
from config import MONGO_URI
from models.interfaces import IDaysAvailableService, IHoursAvailableService


router = APIRouter(prefix="/availability", tags=["Availability"])


@router.get("/test", response_model=str)
def test_endpoint():
    return "Availability Router is working!"


def get_availability_service() -> AvailabilityService:
    return AvailabilityService(mongo_uri=MONGO_URI)


@router.get("/days", response_model=List[str])
def get_available_days(
    name_company: str = Query(..., description="Nombre de la empresa"),
    service: IDaysAvailableService = Depends(get_availability_service),
):
    try:
        available_days = service.get_available_days(name_company)
        return available_days
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hours", response_model=List[Dict])
def get_available_hours(
    name_company: str = Query(..., description="Nombre de la empresa"),
    date_select: str = Query(
        ..., description="Fecha seleccionada en formato YYYY-MM-DD"
    ),
    time_zone: str = Query(..., description="Zona horaria ,ejemplo America/Bogota"),
    service: IHoursAvailableService = Depends(get_availability_service),
):
    try:
        available_hours = service.get_available_hours(
            name_company, date_select, time_zone
        )
        return available_hours
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
