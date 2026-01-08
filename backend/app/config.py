import os
from dotenv import load_dotenv

load_dotenv(".env")


class Settings:
    SUPABASE_DB_URL: str = os.getenv("SUPABASE_DB_URL")
    ZENDESK_API_TOKEN: str = os.getenv("ZENDESK_API_TOKEN")
    ZENDESK_EMAIL: str = os.getenv("ZENDESK_EMAIL")
    ZENDESK_SUBDOMAIN: str = os.getenv("ZENDESK_SUBDOMAIN")


settings = Settings()
"""
Configuration loader for environment variables.
Reads settings from .env file for database and app config.
"""
