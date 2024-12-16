from fastapi import APIRouter, HTTPException, Query, Path, Body
from typing import Optional, Dict
import requests
from services.calendar_service import GoogleCalendarService
from utils.datetime_utils import convert_to_rfc3339

router = APIRouter()


calendar_service: GoogleCalendarService = None


@router.get("/events")
def get_events(
    name_company: str = Query(..., description="Company name"),
    time_min: Optional[str] = Query(
        None, description="Date 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DDTHH:MM'"
    ),
):
    try:
        if time_min:
            try:
                time_min_rfc3339 = convert_to_rfc3339(time_min)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        else:
            time_min_rfc3339 = None

        events = calendar_service.list_events(
            name_company=name_company, time_min=time_min_rfc3339
        )
        return events
    except requests.HTTPError as http_err:
        raise HTTPException(status_code=500, detail=f"HTTP Error: {http_err}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/{event_id}")
def read_event(
    event_id: str = Path(..., description="Event ID"),
    name_company: str = Query(..., description="Company name"),
):
    try:
        event = calendar_service.get_event(name_company=name_company, event_id=event_id)
        return event
    except requests.HTTPError as http_err:
        raise HTTPException(status_code=500, detail=f"HTTP Error: {http_err}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events")
def create_event(
    name_company: str = Query(..., description="Nombre de la empresa"),
    start_time: str = Body(
        ...,
        embed=True,
        description="Hora de inicio en formato RFC3339 (e.g., '2024-12-16T08:00:00-05:00')",
    ),
    assistant_email: str = Body(
        ..., embed=True, description="Correo electrónico del asistente"
    ),
    usuario: str = Body(..., embed=True, description="Numero de telefono"),
    nombre: str = Body(..., embed=True, description="Nombre del cliente"),
):
    """
    Crea un evento en Google Calendar.
    """
    try:
        event = calendar_service.create_event(
            name_company=name_company,
            start_time=start_time,
            assistant_email=assistant_email,
            usuario=usuario,
            nombre=nombre,
        )
        return event
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/events/{event_id}")
def update_event(
    event_id: str = Path(..., description="Event ID"),
    name_company: str = Query(..., description="Company name"),
    event: Dict = Body(...),
):
    try:
        updated_event = calendar_service.update_event(
            name_company=name_company, event_id=event_id, event=event
        )
        return updated_event
    except requests.HTTPError as http_err:
        raise HTTPException(status_code=500, detail=f"HTTP Error: {http_err}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/events/{event_id}")
def delete_event(
    event_id: str = Path(..., description="Event ID"),
    name_company: str = Query(..., description="Company name"),
):
    try:
        result = calendar_service.delete_event(
            name_company=name_company, event_id=event_id
        )
        return result
    except requests.HTTPError as http_err:
        raise HTTPException(status_code=500, detail=f"HTTP Error: {http_err}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
