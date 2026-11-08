from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
 app_name:str="WorkFlow Production API"
 app_env:str="development"
 database_url:str="postgresql+psycopg://workflow_app:local-development-only@localhost:5432/workflow_production"
 cors_origins:str="http://localhost:3000,http://127.0.0.1:3000"
 model_config=SettingsConfigDict(env_file=".env",extra="ignore")
@lru_cache
def get_settings()->Settings:return Settings()
