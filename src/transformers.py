import re
from typing import Any
from typing import Dict
from typing import List
from typing import Optional


class DataTransformer:
    """Класс для преобразования данных из формата API в формат БД"""

    @staticmethod
    def clean_html(text: Optional[str]) -> Optional[str]:
        """Удаляет HTML теги из текста"""
        if not text:
            return text

        # Удаляем HTML теги (включая самозакрывающиеся)
        clean = re.sub(r"<[^>]+>", "", text)

        # Заменяем HTML сущности
        replacements = {
            "&nbsp;": " ",
            "&amp;": "&",
            "&lt;": "<",
            "&gt;": ">",
            "&quot;": '"',
            "&#39;": "'",
            "&mdash;": "—",
            "&laquo;": "«",
            "&raquo;": "»",
        }

        for html_entity, replacement in replacements.items():
            clean = clean.replace(html_entity, replacement)

        # Удаляем лишние пробелы и переносы
        clean = re.sub(r"\s+", " ", clean).strip()

        return clean

    @staticmethod
    def transform_employer(raw_employer: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Извлекает нужные поля из данных компании API hh.ru"""

        try:
            # Проверяем обязательные поля
            if not raw_employer or "id" not in raw_employer:
                return None

            # Преобразуем ID в число (API возвращает строку)
            employer_id = int(raw_employer["id"])
            # ВЫЗЫВАЕМ clean_html!
            description = DataTransformer.clean_html(raw_employer.get("description"))

            return {
                "id": employer_id,
                "name": raw_employer.get("name", "").strip(),
                "open_vacancies": raw_employer.get("open_vacancies", 0),
                "area": raw_employer.get("area", {}).get("name"),
                "site_url": raw_employer.get("site_url", "").strip(),
                "hh_url": raw_employer.get("alternate_url", "").strip(),
                "description": description,
                "industries": [
                    industry.get("name") for industry in raw_employer.get("industries", []) if industry.get("name")
                ],
            }
        except (ValueError, KeyError, AttributeError):
            return None

    @staticmethod
    def transform_vacancy(raw_vacancy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Извлекает нужные поля из данных вакансии API hh.ru"""

        try:
            # Проверяем обязательные поля
            if not raw_vacancy or "id" not in raw_vacancy:
                return None

            # ID вакансии
            vacancy_id = int(raw_vacancy["id"])

            # Обработка зарплаты (может быть null)
            salary = raw_vacancy.get("salary")
            salary_from = salary_to = currency = None

            if salary and isinstance(salary, dict):
                salary_from = salary.get("from")
                salary_to = salary.get("to")
                currency = salary.get("currency")

            # Обработка работодателя
            employer = raw_vacancy.get("employer", {})
            employer_id = int(employer.get("id")) if employer.get("id") else None

            if not employer_id:
                return None

            # Очищаем snippet от HTML!
            snippet = raw_vacancy.get("snippet", {})
            requirement = DataTransformer.clean_html(snippet.get("requirement"))
            responsibility = DataTransformer.clean_html(snippet.get("responsibility"))

            # Дата публикации (приводим к строке)
            published_at = raw_vacancy.get("published_at")

            return {
                "id": vacancy_id,
                "name": raw_vacancy.get("name", "").strip(),
                "employer_id": employer_id,
                "salary_from": salary_from,
                "salary_to": salary_to,
                "currency": currency,
                "area": raw_vacancy.get("area", {}).get("name"),
                "experience": raw_vacancy.get("experience", {}).get("name"),
                "employment": raw_vacancy.get("employment", {}).get("name"),
                "url": raw_vacancy.get("alternate_url", "").strip(),
                "published_at": published_at,  # ← ВОТ ОНА!
                "snippet_requirement": requirement,
                "snippet_responsibility": responsibility,
            }
        except (ValueError, KeyError, AttributeError):
            return None

    @staticmethod
    def transform_all_data(
        raw_employers: List[Dict[str, Any]], raw_vacancies: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Преобразует все сырые данные в формат для БД"""

        transformed_employers = []
        transformed_vacancies = []

        # Преобразуем компании
        for raw_employer in raw_employers:
            employer = DataTransformer.transform_employer(raw_employer)
            if employer:
                transformed_employers.append(employer)

        # Преобразуем вакансии
        for raw_vacancy in raw_vacancies:
            vacancy = DataTransformer.transform_vacancy(raw_vacancy)
            if vacancy:
                transformed_vacancies.append(vacancy)

        return {"employers": transformed_employers, "vacancies": transformed_vacancies}
