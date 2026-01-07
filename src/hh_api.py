import time
from typing import Dict
from typing import List
from typing import Optional

import requests


class HHAPI:
    """Класс для взаимодействия с API сайта hh.ru"""

    def __init__(self, base_url: str = "https://api.hh.ru") -> None:
        """Инициализация API клиента"""

        self.base_url = base_url  # cохраняет базовый url для использования в других методах
        self.session = requests.Session()  # cохраняет соединение между запросами
        self.session.headers.update(
            {  # установка заголовков
                "User-Agent": "MyHHparser/1.0",  # идентификатор клиента для сервера
                "Accept": "application/json",  # формат получения ответа
            }
        )

    def get_employer(self, employer_id: int) -> Optional[Dict]:
        """Получить информацию о компании по её ID"""

        url = f"{self.base_url}/employers/{employer_id}"

        try:
            response = self.session.get(url)
            response.raise_for_status()

            if response.status_code == 200:
                return response.json()
            return None

        except requests.exceptions.RequestException:
            # возвращаем None при любой ошибке
            return None

    def get_vacancies_by_employer(self, employer_id: int, per_page: int = 50) -> List[Dict]:
        """Получить все вакансии компании с учетом пагинации"""

        vacancies = []
        page = 0
        total_pages = 1

        per_page = max(1, min(per_page, 100))  # на 1 стр от 1 до 100 вакансий, неверное значение исправляется кодом

        while page < total_pages:
            url = f"{self.base_url}/vacancies"
            params = {
                "employer_id": employer_id,  # ID компании
                "per_page": per_page,  # Сколько вакансий на странице
                "page": page,  # Номер текущей страницы
            }

            try:
                response = self.session.get(url, params=params)
                # Проверяем HTTP статус
                if response.status_code != 200:
                    break
                # Пытаемся распарсить JSON
                try:
                    data = response.json()
                except ValueError:
                    # Ответ не в формате JSON
                    break

                vacancies.extend(data.get("items", []))

                # Обновляем информацию о пагинации
                total_pages = data.get("pages", 1)
                page += 1

                time.sleep(0.05)

            except requests.exceptions.RequestException:

                break

        return vacancies
