from typing import Dict, Any
from typing import List

import psycopg2


class DBManager:
    """Класс для выполнения запросов к базе данных вакансий"""

    def __init__(self, dbname: str, user: str, password: str, host: str = "localhost", port: str = "5432") -> None:
        """Инициализация подключение к БД PostgreSQL"""

        self.conn_params = {"dbname": dbname, "user": user, "password": password, "host": host, "port": port}
        self.connection = None

    def _connect(self) -> None:
        """Устанавливает соединение с БД (внутренний метод)"""

        # используется для всех методов класса и скрывает логику подключения для пользователя класса
        if not self.connection or self.connection.closed:
            self.connection = psycopg2.connect(**self.conn_params)

    def get_companies_and_vacancies_count(self) -> List[Dict]:
        """Получает список всех компаний и количество вакансий у каждой компании"""

        self._connect()
        with self.connection.cursor() as cursor:  # курсор может выполнять запросы и имеет метод 'execute'
            cursor.execute(
                """
                SELECT e.name as company_name, COUNT(v.id) as vacancies_count
                FROM employers e
                LEFT JOIN vacancies v ON e.id = v.employer_id
                GROUP BY e.id, e.name
                ORDER BY vacancies_count DESC
            """
            )

            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))  # zip создает пары: 1ый эл. из columns + 1ый эл. из row

            return results

    def get_all_vacancies(self) -> List[Dict]:
        """
        Получает список всех вакансий с указанием названия компании,
        названия вакансии, зарплаты и ссылки на вакансию.
        """
        self._connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    e.name as company_name,
                    v.name as vacancy_name,
                    v.salary_from,
                    v.salary_to,
                    v.currency,
                    v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.id
                ORDER BY e.name, v.salary_from DESC NULLS LAST
            """
            )

            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            return results

    def get_avg_salary(self) -> float:
        """Получает среднюю зарплату по вакансиям"""

        self._connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT AVG(
                    CASE
                        WHEN salary_from IS NOT NULL AND salary_to IS NOT NULL
                            THEN (salary_from + salary_to) / 2
                        WHEN salary_from IS NOT NULL AND salary_to IS NULL
                            THEN salary_from
                        WHEN salary_from IS NULL AND salary_to IS NOT NULL
                            THEN salary_to
                        ELSE NULL
                    END
                ) as avg_salary
                FROM vacancies
            """
            )

            result = cursor.fetchone()[0]
            return float(result) if result else 0.0

    def get_vacancies_with_higher_salary(self) -> List[Dict]:
        """Получает список всех вакансий, у которых зарплата выше средней по всем вакансиям"""

        avg_salary = self.get_avg_salary()

        self._connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    e.name as company_name,
                    v.name as vacancy_name,
                    v.salary_from,
                    v.salary_to,
                    v.currency,
                    v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.id
                WHERE (
                    CASE
                        WHEN salary_from IS NOT NULL AND salary_to IS NOT NULL
                            THEN (salary_from + salary_to) / 2
                        WHEN salary_from IS NOT NULL AND salary_to IS NULL
                            THEN salary_from
                        WHEN salary_from IS NULL AND salary_to IS NOT NULL
                            THEN salary_to
                        ELSE 0
                    END
                ) > %s
                ORDER BY (
                    CASE
                        WHEN salary_from IS NOT NULL AND salary_to IS NOT NULL
                            THEN (salary_from + salary_to) / 2
                        WHEN salary_from IS NOT NULL AND salary_to IS NULL
                            THEN salary_from
                        WHEN salary_from IS NULL AND salary_to IS NOT NULL
                            THEN salary_to
                        ELSE 0
                    END
                ) DESC
            """,
                (avg_salary,),
            )

            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            return results

    def get_vacancies_with_keyword(self, keyword: str) -> List[Dict]:
        """
        Получает список всех вакансий, в названии которых содержатся
        переданные в метод слова, без учета регистра.
        """
        self._connect()
        with self.connection.cursor() as cursor:
            search_pattern = f"%{keyword}%"
            cursor.execute(
                """
                SELECT
                    e.name as company_name,
                    v.name as vacancy_name,
                    v.salary_from,
                    v.salary_to,
                    v.currency,
                    v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.id
                WHERE v.name ILIKE %s
                ORDER BY v.salary_from DESC NULLS LAST
            """,
                (search_pattern,),
            )

            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            return results

    def close(self) -> None:
        """Закрывает соединение с БД"""
        if self.connection and not self.connection.closed:
            self.connection.close()

    def __enter__(self):
        """Поддержка контекстного менеджера"""
        self._connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Поддержка контекстного менеджера"""
        self.close()
