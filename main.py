import json, os

from config import CLEAN_EMPLOYERS_PATH
from config import CLEAN_VACANCIES_PATH
from config import COMPANIES
from config import DB_CONFIG
from config import RAW_EMPLOYERS_PATH
from config import RAW_VACANCIES_PATH
from src.database import Database
from src.hh_api import HHAPI
from src.transformers import DataTransformer


def collect_data_from_hh():
    """Сбор данных с hh.ru и сохранение в JSON файлы"""

    print("=" * 50)
    print("СБОР ДАННЫХ С HH.RU")
    print(f"Компаний для обработки: {len(COMPANIES)}")
    print("=" * 50)

    api = HHAPI()

    all_employers = []
    all_vacancies = []

    # Обрабатываем КАЖДУЮ компанию из списка
    for idx, (company_name, company_id) in enumerate(COMPANIES.items(), 1):
        print(f"\n[{idx}/{len(COMPANIES)}] {company_name} (ID: {company_id})")

        # Получаем данные компании
        employer = api.get_employer(company_id)

        if employer:
            all_employers.append(employer)
            print("Компания получена")

            # Получаем вакансии компании
            vacancies = api.get_vacancies_by_employer(company_id)

            # Добавляем имя компании в каждую вакансию
            for vacancy in vacancies:
                vacancy["employer_name"] = company_name
                all_vacancies.append(vacancy)

            print(f"Вакансий: {len(vacancies)}")
        else:
            print("Не удалось получить данные")

    # Сохраняем СЫРЫЕ данные (для истории)
    print("\n" + "=" * 50)
    print("СОХРАНЕНИЕ СЫРЫХ ДАННЫХ...")

    # КОНСТАНТЫ ИЗ CONFIG.PY
    with open(RAW_EMPLOYERS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_employers, f, ensure_ascii=False, indent=2)

    with open(RAW_VACANCIES_PATH, "w", encoding="utf-8") as f:
        json.dump(all_vacancies, f, ensure_ascii=False, indent=2)

    print("Сырые данные сохранены:")
    print(f"{RAW_EMPLOYERS_PATH}")
    print(f"{RAW_VACANCIES_PATH}")

    # ПРЕОБРАЗОВАНИЕ данных для БД
    print("\n" + "=" * 50)
    print("ПРЕОБРАЗОВАНИЕ ДАННЫХ ДЛЯ БАЗЫ ДАННЫХ...")

    transformed_data = DataTransformer.transform_all_data(all_employers, all_vacancies)

    print("Данные преобразованы")

    # Сохраняем ОЧИЩЕННЫЕ данные (для загрузки в PostgreSQL)
    print("\n" + "=" * 50)
    print("СОХРАНЕНИЕ ОЧИЩЕННЫХ ДАННЫХ...")

    # КОНСТАНТЫ ИЗ CONFIG.PY
    with open(CLEAN_EMPLOYERS_PATH, "w", encoding="utf-8") as f:
        json.dump(transformed_data["employers"], f, ensure_ascii=False, indent=2)

    with open(CLEAN_VACANCIES_PATH, "w", encoding="utf-8") as f:
        json.dump(transformed_data["vacancies"], f, ensure_ascii=False, indent=2)

    print("Очищенные данные сохранены:")
    print(f"   • {CLEAN_EMPLOYERS_PATH}")
    print(f"   • {CLEAN_VACANCIES_PATH}")

    # Итоговая статистика по сбору данных
    print("\n" + "=" * 50)
    print("ИТОГОВЫЙ РЕЗУЛЬТАТ СБОРА ДАННЫХ:")
    print("=" * 50)
    print(f"• Собрано компаний: {len(all_employers)}/{len(COMPANIES)}")
    print(f"• Собрано вакансий: {len(all_vacancies)}")
    print(f"• Очищено вакансий: {len(transformed_data['vacancies'])}")
    print("\nФайлы созданы в папке 'data/':")
    print("   • raw_employers.json    - сырые данные компаний")
    print("   • raw_vacancies.json    - сырые данные вакансий")
    print("   • clean_employers.json  - очищенные данные для БД")
    print("   • clean_vacancies.json  - очищенные данные для БД")
    print("=" * 50)

    return True


def setup_database():
    """Настройка и загрузка данных в БД"""
    print("\n" + "=" * 50)
    print("НАСТРОЙКА БАЗЫ ДАННЫХ")
    print("=" * 50)

    # 1. Создаем объект БД
    db = Database(**DB_CONFIG)

    # 2. Пробуем создать БД если не существует
    print("Проверка базы данных...")
    try:
        if db.create_database():
            print("База данных готова")
        else:
            print("Не удалось создать/проверить БД")
            return None
    except Exception as e:
        print(f"Ошибка при проверке БД: {e}")
        return None

    # 3. Подключаемся к БД
    print("Подключение к БД...")
    try:
        if not db.connect():
            print("Не удалось подключиться к БД")
            print("Проверьте:")
            print("1. Запущен ли PostgreSQL")
            print("2. Правильность данных в .env файле")
            print(f"3. Существует ли БД: {DB_CONFIG['dbname']}")
            return None
        print("Подключение установлено")
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        return None

    # 4. Создаем таблицы
    print("Создание таблиц...")
    try:
        if not db.create_tables():
            print("Не удалось создать таблицы")
            db.disconnect()
            return None
        print("Таблицы созданы")
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")
        db.disconnect()
        return None

    # 5. Загружаем данные
    print("Загрузка данных в БД...")
    print(f"   • Из файла: {CLEAN_EMPLOYERS_PATH}")
    print(f"   • Из файла: {CLEAN_VACANCIES_PATH}")

    try:
        if not db.load_from_json(str(CLEAN_EMPLOYERS_PATH), str(CLEAN_VACANCIES_PATH)):
            print("Не удалось загрузить данные в БД")
            db.disconnect()
            return None
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        db.disconnect()
        return None

    # 6. Получаем статистику
    try:
        counts = db.get_counts()
        print("Данные загружены:")
        print(f"   Компаний: {counts['employers']}")
        print(f"   Вакансий: {counts['vacancies']}")
    except Exception as e:
        print(f"Данные загружены, но не удалось получить статистику: {e}")

    # 7. Закрываем соединение
    try:
        db.disconnect()
        print("Соединение с БД закрыто")
    except Exception as e:
        print(f"Ошибка при закрытии соединения: {e}")

    return True


def check_env_file():
    """Проверка наличия .env файла"""

    if not os.path.exists(".env"):
        print("Файл .env не найден!")
        print("Создайте .env файл с настройками БД на основе .env.example")
        response = input("Продолжить без .env? (y/n): ")
        return response.lower() == "y"
    return True


def run_database_creation():
    """Запуск полного процесса создания БД"""

    try:
        # Проверка .env файла
        if not check_env_file():
            return False

        # Этап 1: Сбор и преобразование данных с hh.ru
        print("\n" + "=" * 50)
        print("ЭТАП 1: СБОР ДАННЫХ С HH.RU")
        print("=" * 50)
        if not collect_data_from_hh():
            print("Ошибка при сборе данных с hh.ru")
            return False

        # Этап 2: Настройка базы данных и загрузка данных
        print("\n" + "=" * 50)
        print("ЭТАП 2: НАСТРОЙКА БАЗЫ ДАННЫХ")
        print("=" * 50)
        if not setup_database():
            print("Ошибка при настройке базы данных")
            return False

        # Финальное сообщение
        print("\n" + "=" * 50)
        print("БАЗА ДАННЫХ УСПЕШНО СОЗДАНА!")
        print("=" * 50)
        print("✓ Данные собраны с hh.ru")
        print("✓ Данные очищены и сохранены")
        print("✓ База данных создана и заполнена")
        print("✓ DBManager готов к использованию")
        print("=" * 50)

        return True

    except KeyboardInterrupt:
        print("\n\nПрограмма прервана пользователем")
        return False
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
        import traceback

        traceback.print_exc()
        return False


def run_user_interface():
    """Запуск интерактивного интерфейса для работы с БД"""

    try:
        from user_interface import run_user_interface as ui_main

        ui_main()
        return True
    except ImportError:
        print("\nФайл user_interface.py не найден!")
        print("Создайте файл user_interface.py для работы с интерфейсом")
        return False
    except Exception as e:
        print(f"\nОшибка при запуске интерфейса: {e}")
        return False


def main():
    """Основная функция - единая точка входа в программу"""

    print("\n" + "=" * 50)
    print("МЕНЕДЖЕР ВАКАНСИЙ С HH.RU")
    print("=" * 50)

    print("\nБаза данных уже создана и заполнена.")
    print("Вы можете использовать интерактивный интерфейс.")

    while True:
        print("\nВыберите действие:")
        print("1.Запустить интерактивный интерфейс")
        print("0.Выйти из программы")
        print("=" * 50)

        choice = input("\nВведите номер действия (0-1): ").strip()

        if choice == "0":
            print("\nДо свидания!")
            break

        elif choice == "1":
            print("\n" + "=" * 50)
            print("ЗАПУСК ИНТЕРАКТИВНОГО ИНТЕРФЕЙСА")
            print("=" * 50)
            run_user_interface()

        else:
            print("Неверный выбор. Пожалуйста, введите 0 или 1.")


if __name__ == "__main__":
    main()
