import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_URLS = [
    u.strip() for u in os.getenv(
        "DEFAULT_URLS",
        "https://codenrock.com/communities,"
        "https://codenrock.com/global-rating/sport_programming,"
        "https://codenrock.com/discussions"
    ).split(",") if u.strip()
]


DB_DSN = os.getenv("DB_ADMIN", "postgresql://postgres:postgres@localhost:6432/hakaton")
NUM_WORKERS = int(os.getenv("NUM_WORKERS", "4"))

PARSER_SERVICE_URL = os.getenv("PARSER_SERVICE_URL", "http://parser:8000")

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

