"""Сохранение данных в базу данных."""

import psycopg2
from psycopg2 import sql
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class DBSaver:
    """Класс для сохранения данных о компаниях и вакансиях в БД."""

    def __init__(self) -> None:
        """Инициализация подключения к БД."""
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.dbname = os.getenv('DB_NAME', 'hh_vacancy_parser')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', '')
        self.conn = None
        self.cur = None

    def connect(self) -> None:
        """Подключение к базе данных."""
        self.conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password
        )
        self.cur = self.conn.cursor()

    def close(self) -> None:
        """Закрытие соединения с БД."""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def save_company(self, company_data: Dict[str, Any]) -> Optional[int]:
        """
        Сохранение компании в БД.

        Args:
            company_data: Данные компании

        Returns:
            Optional[int]: ID компании в БД или None
        """
        try:
            self.cur.execute("""
                INSERT INTO companies (hh_id, name, description, site_url, open_vacancies)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (hh_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    site_url = EXCLUDED.site_url,
                    open_vacancies = EXCLUDED.open_vacancies
                RETURNING company_id
            """, (
                company_data['hh_id'],
                company_data['name'],
                company_data.get('description'),
                company_data.get('site_url'),
                company_data.get('open_vacancies', 0)
            ))
            self.conn.commit()
            result = self.cur.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Ошибка при сохранении компании {company_data.get('name')}: {e}")
            self.conn.rollback()
            return None

    def save_vacancy(self, vacancy_data: Dict[str, Any], company_id: int) -> bool:
        """
        Сохранение вакансии в БД.

        Args:
            vacancy_data: Данные вакансии
            company_id: ID компании в БД

        Returns:
            bool: Успешно ли сохранено
        """
        try:
            salary = vacancy_data.get('salary', {})
            salary_from = salary.get('from') if salary else None
            salary_to = salary.get('to') if salary else None
            currency = salary.get('currency') if salary else None

            self.cur.execute("""
                INSERT INTO vacancies (
                    hh_id, company_id, name, salary_from, salary_to, 
                    currency, url, description, published_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (hh_id) DO NOTHING
            """, (
                vacancy_data['id'],
                company_id,
                vacancy_data['name'],
                salary_from,
                salary_to,
                currency,
                vacancy_data['alternate_url'],
                vacancy_data.get('description'),
                vacancy_data.get('published_at')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка при сохранении вакансии {vacancy_data.get('name')}: {e}")
            self.conn.rollback()
            return False

    def save_vacancies(self, vacancies: List[Dict[str, Any]], company_id: int) -> tuple[int, int]:
        """
        Сохранение списка вакансий.

        Args:
            vacancies: Список вакансий
            company_id: ID компании в БД

        Returns:
            tuple[int, int]: (сохранено, ошибок)
        """
        saved = 0
        errors = 0

        for vacancy in vacancies:
            if self.save_vacancy(vacancy, company_id):
                saved += 1
            else:
                errors += 1

        return saved, errors


if __name__ == "__main__":
    # Тестирование сохранения
    print("Тестирование DBSaver...")
    saver = DBSaver()
    saver.connect()

    # Тестовые данные
    test_company = {
        'hh_id': 123456,
        'name': 'Тестовая компания',
        'description': 'Описание',
        'site_url': 'https://test.ru',
        'open_vacancies': 5
    }

    company_id = saver.save_company(test_company)
    print(f"Компания сохранена с ID: {company_id}")

    saver.close()