import json
from pathlib import Path
from typing import Dict


import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class Database:
    """Класс для работы с базой данных PostgreSQL"""

    def __init__(self, dbname: str, user: str, password: str, host: str = "localhost", port: str = "5432"):
        """Инициализация подключения к БД"""

        self.db_params = {"dbname": dbname, "user": user, "password": password, "host": host, "port": port}
        self.connection = None
        self.cursor = None

    def connect(self) -> bool:
        """Устанавливает соединение с БД"""
        try:
            self.connection = psycopg2.connect(**self.db_params)
            self.cursor = self.connection.cursor()
            return True
        except psycopg2.OperationalError:
            return False

    def disconnect(self) -> None:
        """Закрывает соединение с БД"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def create_database(self) -> bool:
        """
        Создает базу данных если она не существует.
        Возвращает True если БД создана или уже существует.
        """
        try:
            # Подключение к БД postgres
            temp_params = self.db_params.copy()
            temp_params["dbname"] = "postgres"

            temp_conn = psycopg2.connect(**temp_params)
            temp_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            temp_cursor = temp_conn.cursor()

            # Проверка наличия БД
            temp_cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (self.db_params["dbname"],))

            if temp_cursor.fetchone():
                # БД уже существует
                result = True
            else:
                # Создаем новую БД
                temp_cursor.execute(f"CREATE DATABASE {self.db_params['dbname']}")
                result = True

            temp_cursor.close()
            temp_conn.close()
            return result

        except Exception:
            return False

    def create_tables(self) -> bool:
        """Создает таблицы в БД из SQL файла"""
        try:
            # Пробуем разные пути к SQL файлу
            possible_paths = [
                "sql/create_tables.sql",  # Относительно рабочей директории
                "../sql/create_tables.sql",  # На уровень выше
                Path(__file__).parent.parent / "sql" / "create_tables.sql",  # Абсолютный путь
            ]

            sql_file_path = None
            for path in possible_paths:
                if isinstance(path, str):
                    path_obj = Path(path)
                else:
                    path_obj = path

                if path_obj.exists():
                    sql_file_path = path_obj
                    print(f"SQL файл найден: {sql_file_path}")
                    break

            if not sql_file_path:
                print("SQL файл не найден по следующим путям:")
                for path in possible_paths:
                    print(f"    - {path}")
                return False

            # Читаем и выполняем SQL
            with open(sql_file_path, "r", encoding="utf-8") as f:
                sql_script = f.read()

            # Выполняем скрипт
            self.cursor.execute(sql_script)
            self.connection.commit()

            print("Таблицы созданы успешно")
            return True

        except Exception as e:
            print(f"Ошибка при создании таблиц: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def insert_employer(self, employer: Dict) -> bool:
        """Добавляет одну компанию в БД"""

        try:
            query = """
            INSERT INTO employers (id, name, open_vacancies, area, site_url,
                                   hh_url, description, industries)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """

            self.cursor.execute(
                query,
                (
                    employer["id"],  # обязательные поля, будут всегда
                    employer["name"],
                    employer["open_vacancies"],
                    employer.get("area"),  # необязательные поля, могут иметь пустое значение
                    employer.get("site_url"),
                    employer.get("hh_url"),
                    employer.get("description"),
                    employer.get("industries", []),
                ),
            )
            return True

        except Exception:
            return False

    def insert_vacancy(self, vacancy: Dict) -> bool:
        """Добавляет одну вакансию в БД"""

        try:
            query = """
            INSERT INTO vacancies (id, name, employer_id, salary_from, salary_to,
                                   currency, area, experience, employment, url,
                                   published_at, snippet_requirement, snippet_responsibility)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """

            self.cursor.execute(
                query,
                (
                    vacancy["id"],
                    vacancy["name"],
                    vacancy["employer_id"],
                    vacancy.get("salary_from"),
                    vacancy.get("salary_to"),
                    vacancy.get("currency"),
                    vacancy.get("area"),
                    vacancy.get("experience"),
                    vacancy.get("employment"),
                    vacancy.get("url"),
                    vacancy.get("published_at"),
                    vacancy.get("snippet_requirement"),
                    vacancy.get("snippet_responsibility"),
                ),
            )
            return True

        except Exception:
            return False

    def load_from_json(self, employers_path: str, vacancies_path: str) -> bool:
        """Загружает данные из JSON файлов в БД"""

        try:
            # Загружаем компании
            with open(employers_path, "r", encoding="utf-8") as f:
                employers = json.load(f)

            for employer in employers:
                self.insert_employer(employer)

            self.connection.commit()

            # Загружаем вакансии
            with open(vacancies_path, "r", encoding="utf-8") as f:
                vacancies = json.load(f)

            for vacancy in vacancies:
                self.insert_vacancy(vacancy)

            self.connection.commit()
            return True

        except Exception:
            self.connection.rollback()
            return False

    def check_tables_exist(self) -> bool:
        """Проверяет существуют ли таблицы в БД"""
        try:
            self.cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'employers'
                )
            """
            )
            employers_exists = self.cursor.fetchone()[0]

            self.cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'vacancies'
                )
            """
            )
            vacancies_exists = self.cursor.fetchone()[0]

            return employers_exists and vacancies_exists

        except Exception:
            return False

    def get_counts(self) -> Dict[str, int]:
        """Возвращает количество записей в таблицах"""

        try:
            self.cursor.execute("SELECT COUNT(*) FROM employers")
            employers_count = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT COUNT(*) FROM vacancies")
            vacancies_count = self.cursor.fetchone()[0]

            return {"employers": employers_count, "vacancies": vacancies_count}
        except Exception:
            return {"employers": 0, "vacancies": 0}
