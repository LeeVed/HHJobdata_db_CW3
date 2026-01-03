-- Таблица компаний
CREATE TABLE employers (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    open_vacancies INTEGER DEFAULT 0,
    area VARCHAR(100),
    site_url TEXT,
    hh_url TEXT,
    description TEXT,
    industries TEXT[]
);

-- Таблица вакансий
CREATE TABLE vacancies (
    id INTEGER PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    employer_id INTEGER REFERENCES employers(id),
    salary_from INTEGER,
    salary_to INTEGER,
    currency VARCHAR(10),
    area VARCHAR(100),
    experience VARCHAR(100),
    employment VARCHAR(100),
    url TEXT UNIQUE,
    published_at TIMESTAMP,
    snippet_requirement TEXT,
    snippet_responsibility TEXT
);

-- Оптимизация (индексы для ускорения запросов)
CREATE INDEX idx_vacancies_employer_id ON vacancies(employer_id);        -- самый частый запрос
CREATE INDEX idx_vacancies_salary ON vacancies(salary_from, salary_to);  -- анализ зарплат в DBManager
CREATE INDEX idx_vacancies_published ON vacancies(published_at DESC);    -- свежие вакансии
CREATE INDEX idx_vacancies_area ON vacancies(area);                      -- фильтрация по городу
