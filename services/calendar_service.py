import requests
from typing import Optional, Dict
from fastapi import HTTPException
from models.interfaces import ICalendarService, IOAuthService, ITokenStorage
from models.data_classes import UserTokenData
from services.availability_service import AvailabilityService
from datetime import datetime, timedelta
import pytz  # Para manejo de zonas horarias


class GoogleCalendarService(ICalendarService):
    BASE_URL = "https://www.googleapis.com/calendar/v3"

    def __init__(
        self,
        oauth_service: IOAuthService,
        token_storage: ITokenStorage,
        availability_service: AvailabilityService,
    ):
        self.oauth_service = oauth_service
        self.token_storage = token_storage
        self.availability_service = availability_service

    def _get_valid_token(self, name_company: str) -> str:
        token_data = self.token_storage.get_token(name_company)
        if not token_data:
            raise HTTPException(
                status_code=401, detail="No access token found for this company."
            )

        if token_data.is_expired():
            try:
                token_data = self.oauth_service.refresh_access_token(name_company)
            except RuntimeError:
                raise HTTPException(
                    status_code=401,
                    detail="Cannot refresh token, company must authorize again.",
                )

        return token_data.access_token

    def list_events(
        self,
        name_company: str,
        time_min: Optional[str] = None,
        calendar_id: str = "primary",
    ) -> Dict:
        access_token = self._get_valid_token(name_company)
        url = f"{self.BASE_URL}/calendars/{calendar_id}/events"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {}
        if time_min:
            params["timeMin"] = time_min
            params["singleEvents"] = "true"
            params["orderBy"] = "startTime"

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_event(
        self, name_company: str, event_id: str, calendar_id: str = "primary"
    ) -> Dict:
        access_token = self._get_valid_token(name_company)
        url = f"{self.BASE_URL}/calendars/{calendar_id}/events/{event_id}"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def create_event(
        self,
        name_company: str,
        start_time: str,
        assistant_email: str,
        usuario: str,
        nombre: str,
    ) -> Dict:
        """
        Crea un evento en Google Calendar.

        :param name_company: Nombre de la empresa.
        :param start_time: Hora de inicio en formato RFC3339 (e.g., "2024-12-16T08:00:00-05:00").
        :param assistant_email: Correo electrónico del asistente.
        :return: Diccionario con los detalles del evento creado.
        """
        try:
            # Obtener las credenciales y configuraciones de la empresa
            credentials = self.availability_service.get_credentials(name_company)
            user_id = credentials.user_id

            # Obtener configuración de la empresa
            configuracion = self.availability_service.get_configuracion(user_id)
            tiempo_sesion = configuracion.tiempoSesion  # en minutos
            titulo_evento = configuracion.titulo_evento
            calendar_id = configuracion.calendar_id
            description_event = configuracion.description_event
            tipo_cita = titulo_evento
            # Convertir start_time a datetime
            try:
                start_dt = datetime.fromisoformat(start_time)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de start_time inválido. Use RFC3339.",
                )

            # Calcular end_time sumando tiempoSesion
            end_dt = start_dt + timedelta(minutes=tiempo_sesion)

            # Convertir a formato RFC3339
            start_rfc3339 = start_dt.isoformat()
            end_rfc3339 = end_dt.isoformat()

            # Preparar el payload para la API de Google Calendar
            event_payload = {
                "summary": titulo_evento,
                "description": description_event,
                "start": {
                    "dateTime": start_rfc3339,
                    "timeZone": "America/Caracas",  # Ajusta según tu zona horaria
                },
                "end": {
                    "dateTime": end_rfc3339,
                    "timeZone": "America/Caracas",
                },
                "attendees": [{"email": assistant_email}],
                "reminders": {"useDefault": True},
                "conferenceData": {
                    "createRequest": {
                        "requestId": "unique-request-id",
                        "conferenceSolutionKey": {"type": "hangoutsMeet"},
                    }
                },
            }

            # Hacer la solicitud a la API de Google Calendar
            headers = {
                "Authorization": f"Bearer {credentials.access_token}",
                "Content-Type": "application/json",
            }
            url_create = f"{self.BASE_URL}/calendars/{calendar_id}/events?conferenceDataVersion=1"

            response = requests.post(
                url_create,
                headers=headers,
                json=event_payload,
            )
            if response.status_code == 401:
                # Token expirado, intentar refrescar
                credentials = self.oauth_service.refresh_access_token(name_company)
                headers["Authorization"] = f"Bearer {credentials.access_token}"
                response = requests.post(
                    f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
                    headers=headers,
                    json=event_payload,
                )
            if response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=response.status_code, detail=response.text
                )

            event = response.json()

            # Obtener el enlace del evento (htmlLink)
            event_link = event.get("htmlLink", "")
            # Obtener enlace de la videollamada si está disponible
            # Por lo general está en event["conferenceData"]["entryPoints"][0]["uri"]
            meet_link = ""
            if event.get("conferenceData") and event["conferenceData"].get(
                "entryPoints"
            ):
                for ep in event["conferenceData"]["entryPoints"]:
                    if ep.get("entryPointType") == "video":
                        meet_link = ep.get("uri", "")
                        break

            # Actualizar la descripción para incluir el enlace del evento
            if event_link:
                updated_description = (
                    f"{description_event}\n\nEnlace del evento: {event_link}"
                )
                if meet_link:
                    updated_description += f"\nEnlace Meet: {meet_link}"

                update_payload = {"description": updated_description}

                update_response = requests.patch(
                    f"{self.BASE_URL}/calendars/{calendar_id}/events/{event['id']}",
                    headers=headers,
                    json=update_payload,
                )

                if update_response.status_code not in [200, 201]:
                    raise HTTPException(
                        status_code=update_response.status_code,
                        detail=f"No se pudo actualizar la descripción del evento: {update_response.text}",
                    )

                event = update_response.json()

            # Guardar el documento en la colección 'citas'
            # La fecha se debe guardar en UTC. start_dt ya está en ISO.
            # Asegúrate que start_dt sea UTC o ajusta la hora a UTC si es necesario.
            citas_collection = self.availability_service.db["citas"]
            cita_doc = {
                "usuario": usuario,
                "email": assistant_email,
                "nombre": nombre,
                "tipo_cita": tipo_cita,
                "fecha": start_dt,  # datetime en UTC, si es necesario ajusta start_dt a UTC
                "user_id": user_id,
            }
            citas_collection.insert_one(cita_doc)
            if response.status_code != 200 and response.status_code != 201:
                raise HTTPException(
                    status_code=response.status_code, detail=response.text
                )

            return event

        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def update_event(
        self,
        name_company: str,
        event_id: str,
        event: Dict,
        calendar_id: str = "primary",
    ) -> Dict:
        access_token = self._get_valid_token(name_company)
        url = f"{self.BASE_URL}/calendars/{calendar_id}/events/{event_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        response = requests.put(url, headers=headers, json=event)
        response.raise_for_status()
        return response.json()

    def delete_event(
        self, name_company: str, event_id: str, calendar_id: str = "primary"
    ) -> Dict:
        access_token = self._get_valid_token(name_company)
        url = f"{self.BASE_URL}/calendars/{calendar_id}/events/{event_id}"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return {"status": "deleted"}
