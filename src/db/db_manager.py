"""Класс для работы с данными в базе данных."""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class DBManager:
    """Класс для получения данных из БД."""

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
        # Используем RealDictCursor, чтобы результаты были в виде словарей
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)

    def close(self) -> None:
        """Закрытие соединения с БД."""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def get_companies_and_vacancies_count(self) -> List[Dict[str, Any]]:
        """
        Получает список всех компаний и количество вакансий у каждой компании.

        Returns:
            List[Dict[str, Any]]: Список компаний с количеством вакансий
        """
        query = """
            SELECT 
                c.name AS company_name,
                COUNT(v.vacancy_id) AS vacancies_count
            FROM companies c
            LEFT JOIN vacancies v ON c.company_id = v.company_id
            GROUP BY c.company_id, c.name
            ORDER BY vacancies_count DESC
        """
        self.cur.execute(query)
        return self.cur.fetchall()

    def get_all_vacancies(self) -> List[Dict[str, Any]]:
        """
        Получает список всех вакансий с указанием названия компании,
        названия вакансии, зарплаты и ссылки на вакансию.

        Returns:
            List[Dict[str, Any]]: Список вакансий
        """
        query = """
            SELECT 
                c.name AS company_name,
                v.name AS vacancy_name,
                v.salary_from,
                v.salary_to,
                v.currency,
                v.url
            FROM vacancies v
            JOIN companies c ON v.company_id = c.company_id
            ORDER BY c.name, v.name
        """
        self.cur.execute(query)
        return self.cur.fetchall()

    def get_avg_salary(self) -> float:
        """
        Получает среднюю зарплату по вакансиям.
        Учитывает вакансии, где указана зарплата.

        Returns:
            float: Средняя зарплата
        """
        query = """
            SELECT AVG(
                COALESCE(
                    (salary_from + salary_to) / 2.0,
                    salary_from,
                    salary_to
                )
            ) as avg_salary
            FROM vacancies
            WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL
        """
        self.cur.execute(query)
        result = self.cur.fetchone()
        return round(result['avg_salary'], 2) if result['avg_salary'] else 0

    def get_vacancies_with_higher_salary(self) -> List[Dict[str, Any]]:
        """
        Получает список всех вакансий, у которых зарплата выше средней.

        Returns:
            List[Dict[str, Any]]: Список вакансий с зарплатой выше средней
        """
        # Сначала получаем среднюю зарплату
        avg_salary = self.get_avg_salary()

        query = """
            SELECT 
                c.name AS company_name,
                v.name AS vacancy_name,
                COALESCE(
                    (v.salary_from + v.salary_to) / 2.0,
                    v.salary_from,
                    v.salary_to
                ) as avg_salary_calc,
                v.salary_from,
                v.salary_to,
                v.currency,
                v.url
            FROM vacancies v
            JOIN companies c ON v.company_id = c.company_id
            WHERE 
                (v.salary_from IS NOT NULL OR v.salary_to IS NOT NULL)
                AND COALESCE(
                    (v.salary_from + v.salary_to) / 2.0,
                    v.salary_from,
                    v.salary_to
                ) > %s
            ORDER BY avg_salary_calc DESC
        """
        self.cur.execute(query, (avg_salary,))
        return self.cur.fetchall()

    def get_vacancies_with_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Получает список всех вакансий, в названии которых содержатся
        переданные в метод слова (регистронезависимо).

        Args:
            keyword: Ключевое слово для поиска

        Returns:
            List[Dict[str, Any]]: Список вакансий
        """
        query = """
            SELECT 
                c.name AS company_name,
                v.name AS vacancy_name,
                v.salary_from,
                v.salary_to,
                v.currency,
                v.url
            FROM vacancies v
            JOIN companies c ON v.company_id = c.company_id
            WHERE v.name ILIKE %s
            ORDER BY c.name, v.name
        """
        self.cur.execute(query, (f'%{keyword}%',))
        return self.cur.fetchall()

    def get_vacancies_by_company(self, company_name: str) -> List[Dict[str, Any]]:
        """
        Получает список вакансий конкретной компании.

        Args:
            company_name: Название компании

        Returns:
            List[Dict[str, Any]]: Список вакансий компании
        """
        query = """
            SELECT 
                v.name AS vacancy_name,
                v.salary_from,
                v.salary_to,
                v.currency,
                v.url
            FROM vacancies v
            JOIN companies c ON v.company_id = c.company_id
            WHERE c.name ILIKE %s
            ORDER BY v.name
        """
        self.cur.execute(query, (f'%{company_name}%',))
        return self.cur.fetchall()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Получает общую статистику по базе данных.

        Returns:
            Dict[str, Any]: Словарь со статистикой
        """
        stats = {}

        # Количество компаний
        self.cur.execute("SELECT COUNT(*) FROM companies")
        stats['companies_count'] = self.cur.fetchone()['count']

        # Количество вакансий
        self.cur.execute("SELECT COUNT(*) FROM vacancies")
        stats['vacancies_count'] = self.cur.fetchone()['count']

        # Средняя зарплата
        stats['avg_salary'] = self.get_avg_salary()

        # Вакансии с зарплатой
        self.cur.execute("""
            SELECT 
                COUNT(*) as with_salary,
                COUNT(*) FILTER (WHERE salary_from IS NULL AND salary_to IS NULL) as without_salary
            FROM vacancies
        """)
        salary_stats = self.cur.fetchone()
        stats['vacancies_with_salary'] = salary_stats['with_salary'] - salary_stats['without_salary']
        stats['vacancies_without_salary'] = salary_stats['without_salary']

        return stats


def print_vacancies(vacancies: List[Dict[str, Any]], title: str = "") -> None:
    """Красивый вывод списка вакансий."""
    if title:
        print(f"\n{title}")
        print("-" * 60)

    if not vacancies:
        print("  ❌ Ничего не найдено")
        return

    for i, v in enumerate(vacancies, 1):
        print(f"\n  {i}. {v.get('company_name', '')} — {v['vacancy_name']}")

        salary_parts = []
        if v.get('salary_from'):
            salary_parts.append(f"от {v['salary_from']}")
        if v.get('salary_to'):
            salary_parts.append(f"до {v['salary_to']}")

        if salary_parts:
            salary_str = " ".join(salary_parts)
            if v.get('currency'):
                salary_str += f" {v['currency']}"
            print(f"     Зарплата: {salary_str}")

        if v.get('url'):
            print(f"     Ссылка: {v['url']}")


if __name__ == "__main__":
    # Тестирование DBManager
    db = DBManager()
    db.connect()

    print("=" * 60)
    print("ТЕСТИРОВАНИЕ DBManager")
    print("=" * 60)

    # 1. Компании и количество вакансий
    print("\n1. КОМПАНИИ И КОЛИЧЕСТВО ВАКАНСИЙ:")
    companies = db.get_companies_and_vacancies_count()
    for c in companies:
        print(f"  {c['company_name']}: {c['vacancies_count']} вакансий")

    # 2. Все вакансии (первые 5)
    print("\n2. ПЕРВЫЕ 5 ВАКАНСИЙ:")
    vacancies = db.get_all_vacancies()
    for i, v in enumerate(vacancies[:5], 1):
        print(f"  {i}. {v['company_name']} — {v['vacancy_name']}")
        print(f"     {v.get('salary_from', '')} {v.get('salary_to', '')} {v.get('currency', '')}")

    # 3. Средняя зарплата
    avg = db.get_avg_salary()
    print(f"\n3. СРЕДНЯЯ ЗАРПЛАТА: {avg} руб.")

    # 4. Вакансии с зарплатой выше средней (первые 5)
    print("\n4. ВАКАНСИИ С ЗАРПЛАТОЙ ВЫШЕ СРЕДНЕЙ (первые 5):")
    high_salary = db.get_vacancies_with_higher_salary()
    for i, v in enumerate(high_salary[:5], 1):
        print(f"  {i}. {v['company_name']} — {v['vacancy_name']}")

    # 5. Поиск по ключевому слову
    keyword = input("\n5. Введите ключевое слово для поиска (например, Python): ")
    found = db.get_vacancies_with_keyword(keyword)
    print(f"  Найдено вакансий: {len(found)}")

    # 6. Статистика
    print("\n6. ОБЩАЯ СТАТИСТИКА:")
    stats = db.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    db.close()