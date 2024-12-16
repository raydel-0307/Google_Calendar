# main.py

from fastapi import FastAPI
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, MONGO_URI
from models.data_classes import OAuthCredentials
from services.token_storage import MongoTokenStorage
from services.oauth_service import GoogleOAuthService
from services.availability_service import AvailabilityService
from services.calendar_service import GoogleCalendarService
from routers import (
    events,
    availability,
)  # Asegúrate de importar el router de availability

app = FastAPI()

# Inicializar dependencias
credentials = OAuthCredentials(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
token_storage = MongoTokenStorage(MONGO_URI)
oauth_service = GoogleOAuthService(credentials, token_storage)
availability_service = AvailabilityService(mongo_uri=MONGO_URI)
calendar_service = GoogleCalendarService(
    oauth_service, token_storage, availability_service
)

# Inyectar la instancia en el router de events
events.calendar_service = calendar_service
app.include_router(events.router)

# Incluir el router de availability
app.include_router(availability.router)
