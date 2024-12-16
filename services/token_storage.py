from pymongo import MongoClient
from datetime import datetime, timedelta
from typing import Optional
from models.interfaces import ITokenStorage
from models.data_classes import UserTokenData


class MongoTokenStorage(ITokenStorage):
    def __init__(
        self,
        mongo_uri: str,
        db_name: str = "calendar_app",
        collection_name: str = "credentials",
    ):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def save_token(self, token_data: UserTokenData):
        self.collection.update_one(
            {"name_company": token_data.name_company},
            {
                "$set": {
                    "user_id": token_data.user_id,
                    "access_token": token_data.access_token,
                    "refresh_token": token_data.refresh_token,
                    "scope": token_data.scope,
                    "token_type": token_data.token_type,
                    "expiry_time": token_data.expiry_time,
                }
            },
            upsert=True,
        )

    def get_token(self, name_company: str) -> Optional[UserTokenData]:
        doc = self.collection.find_one({"name_company": name_company})
        if doc:
            expires_in = int((doc["expiry_time"] - datetime.utcnow()).total_seconds())
            return UserTokenData(
                name_company=doc["name_company"],
                user_id=doc.get("user_id"),
                access_token=doc["access_token"],
                refresh_token=doc["refresh_token"],
                expires_in=expires_in,
                scope=doc["scope"],
                token_type=doc["token_type"],
            )
        return None

    def update_token(self, name_company: str, access_token: str, expires_in: int):
        expiry_time = datetime.utcnow() + timedelta(seconds=expires_in)
        self.collection.update_one(
            {"name_company": name_company},
            {"$set": {"access_token": access_token, "expiry_time": expiry_time}},
        )
