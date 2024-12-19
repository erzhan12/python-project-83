from pydantic_settings import BaseSettings
import os
from os.path import join


BASE_DIR = os.path.abspath(__file__)
project_dir = os.path.dirname(os.path.dirname(BASE_DIR))
ENV_DIR = join(project_dir, '.env')


class AppConfig(BaseSettings):
    secret_key: str
    database_url: str

    class Config:
        env_file = ENV_DIR


class Config(BaseSettings):
    APP_CONFIG: AppConfig = AppConfig()


config = Config()
