import requests
from models.data_classes import UserTokenData, OAuthCredentials
from models.interfaces import IOAuthService, ITokenStorage


class GoogleOAuthService(IOAuthService):
    TOKEN_URL = "https://oauth2.googleapis.com/token"

    def __init__(self, credentials: OAuthCredentials, token_storage: ITokenStorage):
        self.credentials = credentials
        self.token_storage = token_storage

    def refresh_access_token(self, name_company: str) -> UserTokenData:
        token_data = self.token_storage.get_token(name_company)
        if not token_data or not token_data.refresh_token:
            raise RuntimeError(
                "No refresh token available, cannot refresh access token."
            )

        data = {
            "client_id": self.credentials.client_id,
            "client_secret": self.credentials.client_secret,
            "refresh_token": token_data.refresh_token,
            "grant_type": "refresh_token",
        }

        response = requests.post(self.TOKEN_URL, data=data)
        response.raise_for_status()
        token_info = response.json()
        new_expires_in = token_info["expires_in"]
        new_access_token = token_info["access_token"]
        self.token_storage.update_token(name_company, new_access_token, new_expires_in)

        updated_token = self.token_storage.get_token(name_company)
        return updated_token
