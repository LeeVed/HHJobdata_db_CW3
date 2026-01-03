import os
from pathlib import Path

from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Базовый путь проекта
BASE_DIR = Path(__file__).parent

# Пути к данным
DATA_DIR = BASE_DIR / "data"

# Пути к ОЧИЩЕННЫМ данным (для загрузки в БД)
CLEAN_EMPLOYERS_PATH = DATA_DIR / "clean_employers.json"
CLEAN_VACANCIES_PATH = DATA_DIR / "clean_vacancies.json"

# Пути к СЫРЫМ данным
RAW_EMPLOYERS_PATH = DATA_DIR / "raw_employers.json"
RAW_VACANCIES_PATH = DATA_DIR / "raw_vacancies.json"

# Создать папку
os.makedirs(DATA_DIR, exist_ok=True)

# Настройки БД из .env
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "hh_vacancies"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
}

# Список компаний для сбора данных
COMPANIES = {
    "Яндекс": 1740,
    "Тинькофф": 78638,
    "Ozon": 2180,
    "Сбер": 3529,
    "МТС": 3776,
    "Ростелеком": 2748,
    "Альфа-Банк": 80,
    "Wildberries": 87021,
    "Skyeng": 1122462,
    "MY.GAMES": 2324020,
}

# Настройки API
API_SETTINGS = {
    "base_url": "https://api.hh.ru",
    "user_agent": "HH-Vacancy-Collector/1.0",
    "per_page_default": 100,
    "request_delay": 0.05,
}
