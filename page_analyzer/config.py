import os
from os.path import join
from pydantic_settings import BaseSettings


BASE_DIR = os.path.abspath(__file__)
project_dir = os.path.dirname(os.path.dirname(BASE_DIR))
ENV_DIR = join(project_dir, '.env')


class BaseConfig(BaseSettings):
    class Config:
        env_file = '.env'
        extra = 'allow'


class AppConfig(BaseConfig):
    secret_key: str
    database_url: str

    class Config:
        env_file = ENV_DIR


class Config(BaseConfig):
    APP_CONFIG: AppConfig = AppConfig()


config = Config()
