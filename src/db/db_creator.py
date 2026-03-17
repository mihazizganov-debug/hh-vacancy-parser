"""Создание базы данных и таблиц для проекта."""

import psycopg2
from psycopg2 import sql
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class DBCreator:
    """Класс для создания базы данных и таблиц."""

    def __init__(self) -> None:
        """Инициализация с параметрами подключения из .env."""
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.dbname = os.getenv('DB_NAME', 'hh_vacancy_parser')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', '')

    def create_database(self) -> None:
        """Создание базы данных, если она не существует."""
        try:
            # Подключаемся к стандартной базе postgres
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname='postgres',
                user=self.user,
                password=self.password
            )
            conn.autocommit = True
            cur = conn.cursor()

            # Проверяем, существует ли база
            cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (self.dbname,))
            exists = cur.fetchone()

            if not exists:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(self.dbname)
                ))
                print(f"✅ База данных '{self.dbname}' создана")
            else:
                print(f"ℹ️ База данных '{self.dbname}' уже существует")

            cur.close()
            conn.close()

        except Exception as e:
            print(f"❌ Ошибка при создании базы данных: {e}")

    def create_tables(self) -> None:
        """Создание таблиц companies и vacancies."""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password
            )
            cur = conn.cursor()

            # Создание таблицы companies
            cur.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    company_id SERIAL PRIMARY KEY,
                    hh_id INTEGER UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    site_url VARCHAR(255),
                    open_vacancies INTEGER DEFAULT 0
                )
            """)
            print("✅ Таблица 'companies' создана/проверена")

            # Создание таблицы vacancies
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vacancies (
                    vacancy_id SERIAL PRIMARY KEY,
                    hh_id VARCHAR(50) UNIQUE NOT NULL,
                    company_id INTEGER REFERENCES companies(company_id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    salary_from INTEGER,
                    salary_to INTEGER,
                    currency VARCHAR(10),
                    url VARCHAR(255) NOT NULL,
                    description TEXT,
                    published_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Таблица 'vacancies' создана/проверена")

            # Создание индекса для быстрого поиска по компаниям
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_vacancies_company 
                ON vacancies(company_id)
            """)
            print("✅ Индексы созданы")

            conn.commit()
            cur.close()
            conn.close()

        except Exception as e:
            print(f"❌ Ошибка при создании таблиц: {e}")


if __name__ == "__main__":
    # Тестирование создания БД и таблиц
    creator = DBCreator()
    creator.create_database()
    creator.create_tables()