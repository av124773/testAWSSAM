import os
from pydantic_settings import BaseSettings

class Setting(BaseSettings):
    AWS_REGION_NAME: str
    DYNAMODB_TABLE_NAME: str
    OPENAI_API_KEY_SECRET_NAME: str

    class Config:
        case_sensitive = True

settings = Settings()
