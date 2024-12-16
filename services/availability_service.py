from typing import List, Dict
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from models.interfaces import IDaysAvailableService, IHoursAvailableService
from models.data_classes import ConfiguracionCalendar, Cita, UserTokenData
from utils.datetime_utils import convert_to_rfc3339
from bson.objectid import ObjectId
from fastapi import HTTPException
from zoneinfo import ZoneInfo


class AvailabilityService(IDaysAvailableService, IHoursAvailableService):
    def __init__(self, mongo_uri: str):
        self.client = MongoClient(mongo_uri)
        self.db = self.client["calendar_app"]
        self.config_collection = self.db["configuracion_calendar"]
        self.citas_collection = self.db["citas"]
        self.credentials_collection = self.db["credentials"]
        self.credentials_cache = {}

    def get_credentials(self, name_company: str) -> UserTokenData:
        """
        Obtiene las credenciales de una empresa basada en name_company.
        Utiliza una cache para evitar múltiples consultas a la base de datos.
        """
        if name_company in self.credentials_cache:
            return self.credentials_cache[name_company]

        credential_doc = self.credentials_collection.find_one(
            {"name_company": name_company}
        )
        if not credential_doc:
            raise HTTPException(
                status_code=404,
                detail=f"Credentials for company '{name_company}' not found.",
            )

        token_data = UserTokenData(
            name_company=credential_doc["name_company"],
            user_id=credential_doc["user_id"],
            access_token=credential_doc["access_token"],
            refresh_token=credential_doc.get("refresh_token"),
            scope=credential_doc["scope"],
            token_type=credential_doc["token_type"],
            expires_in=credential_doc.get("expires_in", 3600),
        )
        self.credentials_cache[name_company] = token_data
        return token_data

    def get_configuracion(self, user_id: str) -> ConfiguracionCalendar:
        config = self.config_collection.find_one({"user_id": user_id})
        if not config:
            raise HTTPException(status_code=404, detail="Configuración no encontrada.")
        return ConfiguracionCalendar(
            user_id=config["user_id"],
            hora_inicio=config["hora_inicio"],
            hora_fin=config["hora_fin"],
            tiempoSesion=config["tiempoSesion"],
            dia_disponibles=config["dia_disponibles"],
            hora_bloqueada_list=config.get("hora_bloqueada_list", []),
            all_day=config["all_day"],
            days=config.get("days", {}),
            time_global=config.get("time_global", False),
            titulo_evento=config.get("titulo_evento", ""),
            calendar_id=config.get("calendar_id", ""),
            description_event=config.get("description_event", ""),
        )

    def is_workday_with_specific_hours(
        self, day: datetime.date, config: ConfiguracionCalendar
    ) -> List[str]:
        days_map = [
            "lunes",
            "martes",
            "miercoles",
            "jueves",
            "viernes",
            "sabado",
            "domingo",
        ]
        day_name = days_map[day.weekday()]
        print(day_name, "estoy pot aca")
        # Verifica si el día está en las claves de config.days
        if day_name not in config.days:
            return []

        if config.time_global:
            # Si time_global es True, usar las horas globales para cualquier día presente en config.days
            return [f"{config.hora_inicio}-{config.hora_fin}"]
        else:
            # Si time_global es False, usar las horas específicas definidas en config.days[day_name]
            return config.days.get(day_name, [])

    def get_available_hours_day(
        self,
        day: datetime.date,
        specific_hours: List[str],
        interval_minutes: int,
        blocked_times: List[str],
        used_hours: List[str],
        time_zone: str,
    ) -> List[Dict]:
        available_hours = []
        if not specific_hours:
            return available_hours

        tz = ZoneInfo(time_zone)

        for hour_range in specific_hours:
            try:
                start_str, end_str = hour_range.split("-")
                start_h, start_m = map(int, start_str.split(":"))
                end_h, end_m = map(int, end_str.split(":"))
            except ValueError:
                print(f"Formato de hora inválido en {hour_range}")
                continue  # Saltar rangos de horas mal formateados

            # Creamos datetime para el día actual con tz
            start_time = datetime(
                day.year, day.month, day.day, start_h, start_m, tzinfo=tz
            )
            end_time = datetime(day.year, day.month, day.day, end_h, end_m, tzinfo=tz)

            current_time = start_time
            while current_time + timedelta(minutes=interval_minutes) <= end_time:
                hour_str = current_time.strftime("%H:%M:%S")

                # Verificar si la hora está bloqueada
                is_blocked = False
                for block in blocked_times:
                    try:
                        block_start, block_end = block.split("-")
                        bs_h, bs_m = map(int, block_start.strip().split(":"))
                        be_h, be_m = map(int, block_end.strip().split(":"))
                        block_start_dt = datetime(
                            day.year, day.month, day.day, bs_h, bs_m, tzinfo=tz
                        )
                        block_end_dt = datetime(
                            day.year, day.month, day.day, be_h, be_m, tzinfo=tz
                        )
                        if block_start_dt <= current_time < block_end_dt:
                            is_blocked = True
                            break
                    except ValueError:
                        print(f"Formato de hora bloqueada inválido en {block}")
                        continue  # Saltar bloques de horas mal formateados

                if not is_blocked and hour_str not in used_hours:
                    available_hours.append(
                        {
                            "id": len(available_hours) + 1,
                            "hora": hour_str,
                            "horaFormat": self.convert_to_12_hour_format(hour_str),
                        }
                    )

                current_time += timedelta(minutes=interval_minutes)

        return available_hours

    def get_citas(self, user_id: str, date_select: str) -> List[Cita]:
        """
        Obtiene las citas para un usuario en una fecha específica.
        """
        try:
            fecha_inicio = datetime.strptime(date_select, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
            fecha_fin = fecha_inicio + timedelta(days=1)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Formato de date_select inválido. Use YYYY-MM-DD.",
            )

        citas_cursor = self.citas_collection.find(
            {"user_id": user_id, "fecha": {"$gte": fecha_inicio, "$lt": fecha_fin}}
        )
        citas = []
        for cita in citas_cursor:
            print(cita, "esta es la cita")
            # Asegúrate de que el documento tenga el campo 'fecha'
            if "fecha" not in cita:
                print("Cita sin fecha encontrada y será ignorada.")
                continue  # O manejar el error según se desee
            citas.append(
                Cita(
                    usuario=cita["usuario"],
                    email=cita["email"],
                    nombre=cita["nombre"],
                    tipo_cita=cita["tipo_cita"],
                    fecha=cita["fecha"],
                    user_id=cita["user_id"],
                )
            )
        return citas

    def get_available_days(
        self, name_company: str, time_zone: str = "America/Guayaquil"
    ) -> List[Dict]:
        """
        Obtiene los días disponibles para una empresa en base a la configuración y las citas existentes.
        """
        credentials = self.get_credentials(name_company)
        user_id = credentials.user_id
        config = self.get_configuracion(user_id)
        dias_disponibles = config.dia_disponibles
        today = datetime.now(timezone.utc).astimezone(ZoneInfo(time_zone)).date()
        available_days = []

        interval_minutes = config.tiempoSesion
        blocked_times = config.hora_bloqueada_list

        daysChecked = 0
        while len(available_days) < dias_disponibles:
            day = today + timedelta(days=daysChecked + 1)
            daysChecked += 1

            day_str = day.isoformat()
            specific_hours = self.is_workday_with_specific_hours(day, config)

            # Si specific_hours está vacío, significa que el día no está habilitado según config.days
            if not specific_hours:
                # Pasar al siguiente día sin procesar más
                continue

            # Solo llamamos a get_citas si el día es válido
            citas = self.get_citas(user_id, day_str)

            # Manejo de casos donde citas podrían no tener la estructura esperada
            # Si get_citas retorna objetos Cita, asegurarnos de que c.fecha existe
            used_hours = []
            for c in citas:
                print(c, "esta es la cita")
                # Verificar que c.fecha no sea None
                if c.fecha is None:
                    # Si hay un documento sin fecha, lo ignoramos o provocamos un error controlado
                    print("Cita con fecha None encontrada y será ignorada.")
                    continue
                # Convertir la fecha de UTC a la zona horaria especificada
                if c.fecha.tzinfo is None:
                    # Asignar UTC si no tiene tzinfo
                    cita_utc = c.fecha.replace(tzinfo=timezone.utc)
                else:
                    cita_utc = c.fecha

                fecha_local = cita_utc.astimezone(ZoneInfo(time_zone))
                used_hours.append(fecha_local.strftime("%H:%M:%S"))

            # Calcular horas disponibles
            available_hours = self.get_available_hours_day(
                day,
                specific_hours,
                interval_minutes,
                blocked_times,
                used_hours,
                time_zone,
            )

            print(specific_hours, available_hours, day_str, used_hours)

            if len(available_hours) > 0:
                date_format = day.strftime("%d/%m/%Y")
                available_days.append(day_str)

        return available_days

    def get_available_hours(
        self, name_company: str, date_select: str, time_zone: str
    ) -> List[Dict]:
        """
        Obtiene las horas disponibles para una fecha específica y una empresa, considerando la zona horaria.
        """
        credentials = self.get_credentials(name_company)
        user_id = credentials.user_id
        config = self.get_configuracion(user_id)
        citas = self.get_citas(user_id, date_select)

        # Parsear la zona horaria especificada
        try:
            tz = ZoneInfo(time_zone)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Zona horaria inválida: {time_zone}"
            )

        # Obtener el día seleccionado sin hora, se asume sin zona horaria
        try:
            day = datetime.strptime(date_select, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Formato de date_select inválido. Use YYYY-MM-DD.",
            )

        day_of_week = day.weekday()  # Monday is 0
        days_map = [
            "lunes",
            "martes",
            "miercoles",
            "jueves",
            "viernes",
            "sabado",
            "domingo",
        ]
        day_name = days_map[day_of_week]

        if config.time_global:
            working_hours = [f"{config.hora_inicio}-{config.hora_fin}"]
        else:
            working_hours = config.days.get(day_name, [])

        if not working_hours:
            return []

        # Horas bloqueadas
        blocked_times = config.hora_bloqueada_list or []

        # Intervalo de la sesión en minutos
        interval_minutes = config.tiempoSesion

        # Convertir las citas de UTC a la zona horaria especificada
        used_hours = []
        for cita in citas:
            # Verificar si cita.fecha tiene información de zona horaria
            if cita.fecha is None:
                print("Cita con fecha None encontrada y será ignorada.")
                continue

            if cita.fecha.tzinfo is None:
                # Asignar UTC si no tiene tzinfo
                cita_utc = cita.fecha.replace(tzinfo=timezone.utc)
            else:
                cita_utc = cita.fecha

            # Convertir de UTC a la zona horaria especificada
            try:
                fecha_local = cita_utc.astimezone(tz)
                used_hours.append(fecha_local.strftime("%H:%M:%S"))
            except Exception as e:
                print(f"Error al convertir la fecha de la cita: {cita.fecha} - {e}")
                continue

        print(f"Used hours: {used_hours}")
        available_hours = []

        for hour_range in working_hours:
            try:
                start_str, end_str = hour_range.split("-")
                start_time = datetime.strptime(start_str, "%H:%M").replace(
                    year=day.year, month=day.month, day=day.day, tzinfo=tz
                )
                end_time = datetime.strptime(end_str, "%H:%M").replace(
                    year=day.year, month=day.month, day=day.day, tzinfo=tz
                )
            except ValueError:
                print(f"Formato de hora inválido en {hour_range}")
                continue  # Saltar rangos de horas mal formateados

            current_time = start_time
            while current_time + timedelta(minutes=interval_minutes) <= end_time:
                hour_str = current_time.strftime("%H:%M:%S")

                # Verificar si la hora está bloqueada
                is_blocked = False
                for block in blocked_times:
                    try:
                        block_start, block_end = block.split("-")
                        block_start_dt = datetime.strptime(
                            block_start, "%H:%M"
                        ).replace(
                            year=day.year, month=day.month, day=day.day, tzinfo=tz
                        )
                        block_end_dt = datetime.strptime(block_end, "%H:%M").replace(
                            year=day.year, month=day.month, day=day.day, tzinfo=tz
                        )
                        if block_start_dt <= current_time < block_end_dt:
                            is_blocked = True
                            break
                    except ValueError:
                        print(f"Formato de hora bloqueada inválido en {block}")
                        continue  # Saltar bloques de horas mal formateados

                if not is_blocked and hour_str not in used_hours:
                    available_hours.append(
                        {
                            "id": len(available_hours) + 1,
                            "hora": hour_str,
                            "horaFormat": self.convert_to_12_hour_format(hour_str),
                        }
                    )

                current_time += timedelta(minutes=interval_minutes)

        return available_hours

    @staticmethod
    def convert_to_12_hour_format(hour: str) -> str:
        """
        Convierte una hora en formato 24 horas a formato 12 horas con AM/PM.
        """
        try:
            time_obj = datetime.strptime(hour, "%H:%M:%S")
            return time_obj.strftime("%I:%M %p")
        except ValueError:
            print(f"Formato de hora inválido para conversión: {hour}")
            return hour  # Retornar la hora sin cambios si el formato es inválido
