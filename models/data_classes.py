from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo
from typing import Optional, Dict, List


class OAuthCredentials:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri


class UserTokenData:
    def __init__(
        self,
        name_company: str,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        scope: str,
        token_type: str,
        user_id: Optional[str] = None,
    ):
        self.name_company = name_company
        self.user_id = user_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.scope = scope
        self.token_type = token_type
        self.expiry_time = datetime.utcnow() + timedelta(seconds=expires_in)

    def is_expired(self) -> bool:
        if self.expiry_time.tzinfo is None:
            self.expiry_time = self.expiry_time.replace(tzinfo=timezone.utc)
        now_local = datetime.now(ZoneInfo("America/Caracas"))
        return now_local >= self.expiry_time


class ConfiguracionCalendar:

    def __init__(
        self,
        user_id: str,
        hora_inicio: str,
        hora_fin: str,
        tiempoSesion: int,
        dia_disponibles: int,
        hora_bloqueada_list: List[str],
        all_day: bool,
        days: Dict[str, List[str]],
        time_global: bool,
        titulo_evento: str,
        calendar_id: str,
        description_event: str,
    ):
        self.user_id = user_id
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.tiempoSesion = tiempoSesion
        self.dia_disponibles = dia_disponibles
        self.hora_bloqueada_list = hora_bloqueada_list
        self.all_day = all_day
        self.days = days
        self.time_global = time_global
        self.titulo_evento = titulo_evento
        self.calendar_id = calendar_id
        self.description_event = description_event


class Cita:
    def __init__(
        self,
        usuario: str,
        email: str,
        nombre: str,
        tipo_cita: str,
        fecha: datetime,
        user_id: str,
    ):
        self.usuario = usuario
        self.email = email
        self.nombre = nombre
        self.tipo_cita = tipo_cita
        self.fecha = fecha
        self.user_id = user_id


class Company:
    def __init__(
        self,
        name_company: str,
        user_id: str,
    ):
        self.name_company = name_company
        self.user_id = user_id
