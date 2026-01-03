from config import DB_CONFIG
from src.db_manager import DBManager


def run_user_interface() -> None:
    """Функция для запуска интерфейса (не main())"""

    print("\n" + "=" * 50)
    print("ДОБРО ПОЖАЛОВАТЬ В МЕНЕДЖЕР ВАКАНСИЙ!")
    print("=" * 50)

    # Пробуем подключиться к БД
    try:
        db = DBManager(**DB_CONFIG)
        print("Подключение к базе данных успешно")
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        print("\nСначала создайте базу данных командой: python main.py")
        return

    # Главный цикл программы
    while True:
        print("\n" + "=" * 50)
        print("ГЛАВНОЕ МЕНЮ")
        print("=" * 50)
        print("1. Компании и количество вакансий")
        print("2. Показать все вакансии")
        print("3. Узнать среднюю зарплату")
        print("4. Вакансии с зарплатой выше средней")
        print("5. Поиск вакансий по ключевому слову")
        print("0. Выйти из программы")
        print("=" * 50)

        choice = input("\nВведите номер действия (0-5): ").strip()

        if choice == "0":
            print("\nДо свидания!")
            break
        elif choice == "1":
            show_companies(db)
        elif choice == "2":
            show_vacancies(db)
        elif choice == "3":
            show_avg_salary(db)
        elif choice == "4":
            show_high_salary_vacancies(db)
        elif choice == "5":
            search_vacancies(db)
        else:
            print("Неверный выбор.")

    db.close()


def show_companies(db) -> None:
    """Показать компании"""

    companies = db.get_companies_and_vacancies_count()
    if companies:
        for company in companies:
            print(f"{company['company_name']}: {company['vacancies_count']} вакансий")
    else:
        print("Нет компаний в базе.")


def show_vacancies(db) -> None:
    """Показать вакансии"""

    vacancies = db.get_all_vacancies()
    if vacancies:
        for vacancy in vacancies[:5]:
            print(f"{vacancy['company_name']} - {vacancy['vacancy_name']}")
    else:
        print("Нет вакансий в базе.")


def show_avg_salary(db) -> None:
    """Показать среднюю зарплату"""

    avg = db.get_avg_salary()
    print(f"Средняя зарплата: {avg:,.0f} руб.")


def show_high_salary_vacancies(db) -> None:
    """Показать вакансии с высокой зарплатой"""

    vacancies = db.get_vacancies_with_higher_salary()
    if vacancies:
        for vacancy in vacancies[:3]:
            print(f"{vacancy['company_name']} - {vacancy['vacancy_name']}")
    else:
        print("Нет вакансий с зарплатой выше средней.")


def search_vacancies(db) -> None:
    """Поиск вакансий"""

    keyword = input("Введите ключевое слово: ").strip()
    if keyword:
        vacancies = db.get_vacancies_with_keyword(keyword)
        if vacancies:
            for vacancy in vacancies[:3]:
                print(f"{vacancy['company_name']} - {vacancy['vacancy_name']}")
        else:
            print(f"Не найдено вакансий с '{keyword}'")
    else:
        print("Не введено ключевое слово.")
