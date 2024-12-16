from typing import Optional, Dict, List
from models.data_classes import UserTokenData, ConfiguracionCalendar, Cita


class ITokenStorage:
    def save_token(self, token_data: UserTokenData):
        raise NotImplementedError

    def get_token(self, name_company: str) -> Optional[UserTokenData]:
        raise NotImplementedError

    def update_token(self, name_company: str, access_token: str, expires_in: int):
        raise NotImplementedError


class IOAuthService:
    def refresh_access_token(self, name_company: str) -> UserTokenData:
        raise NotImplementedError


class ICalendarService:
    def list_events(
        self,
        name_company: str,
        time_min: Optional[str] = None,
        calendar_id: str = "primary",
    ) -> Dict:
        raise NotImplementedError

    def get_event(
        self, name_company: str, event_id: str, calendar_id: str = "primary"
    ) -> Dict:
        raise NotImplementedError

    def create_event(
        self, name_company: str, start_time: str, assistant_email: str
    ) -> Dict:
        raise NotImplementedError

    def update_event(
        self,
        name_company: str,
        event_id: str,
        event: Dict,
        calendar_id: str = "primary",
    ) -> Dict:
        raise NotImplementedError

    def delete_event(
        self, name_company: str, event_id: str, calendar_id: str = "primary"
    ) -> Dict:
        raise NotImplementedError


class IDaysAvailableService:

    def get_available_days(self, name_company: str) -> List[str]:
        raise NotImplementedError


class IHoursAvailableService:

    def get_available_hours(
        self, name_company: str, date_select: str, time_zone: str
    ) -> List[Dict]:
        raise NotImplementedError
