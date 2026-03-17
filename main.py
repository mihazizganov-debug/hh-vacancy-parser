#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Главный модуль программы. Точка входа."""

from src.db.db_manager import DBManager, print_vacancies


def print_menu() -> None:
    """Вывод меню."""
    print("\n" + "=" * 60)
    print("HH VACANCY PARSER - МЕНЮ")
    print("=" * 60)
    print("1. Список компаний и количество вакансий")
    print("2. Список всех вакансий")
    print("3. Средняя зарплата по вакансиям")
    print("4. Вакансии с зарплатой выше средней")
    print("5. Поиск вакансий по ключевому слову")
    print("6. Статистика по базе данных")
    print("7. Вакансии конкретной компании")
    print("0. Выход")
    print("-" * 60)


def main():
    """Главная функция."""
    db = DBManager()
    db.connect()

    print("=" * 60)
    print("ДОБРО ПОЖАЛОВАТЬ В HH VACANCY PARSER")
    print("=" * 60)
    print(f"\n📊 В базе данных: {db.get_statistics()['vacancies_count']} вакансий")

    while True:
        print_menu()
        choice = input("Ваш выбор (0-7): ")

        if choice == "0":
            print("\n👋 До свидания!")
            break

        elif choice == "1":
            companies = db.get_companies_and_vacancies_count()
            print("\n📊 КОМПАНИИ И КОЛИЧЕСТВО ВАКАНСИЙ:")
            for c in companies:
                print(f"  {c['company_name']}: {c['vacancies_count']} вакансий")

        elif choice == "2":
            vacancies = db.get_all_vacancies()
            print(f"\n📋 ВСЕГО ВАКАНСИЙ: {len(vacancies)}")
            limit = input("Сколько показать? (Enter — все): ")
            try:
                n = int(limit) if limit else len(vacancies)
                print_vacancies(vacancies[:n], f"ПЕРВЫЕ {n} ВАКАНСИЙ")
            except ValueError:
                print_vacancies(vacancies, "ВСЕ ВАКАНСИИ")

        elif choice == "3":
            avg = db.get_avg_salary()
            print(f"\n💰 СРЕДНЯЯ ЗАРПЛАТА: {avg:,.2f} руб.")

        elif choice == "4":
            vacancies = db.get_vacancies_with_higher_salary()
            print_vacancies(vacancies, f"ВАКАНСИИ С ЗАРПЛАТОЙ ВЫШЕ СРЕДНЕЙ ({len(vacancies)} шт.)")

        elif choice == "5":
            keyword = input("\n🔍 Введите ключевое слово для поиска: ")
            vacancies = db.get_vacancies_with_keyword(keyword)
            print_vacancies(vacancies, f"ВАКАНСИИ ПО КЛЮЧЕВОМУ СЛОВУ '{keyword}' ({len(vacancies)} шт.)")

        elif choice == "6":
            stats = db.get_statistics()
            print("\n📊 ОБЩАЯ СТАТИСТИКА:")
            print(f"  Компаний: {stats['companies_count']}")
            print(f"  Вакансий всего: {stats['vacancies_count']}")
            print(f"  Средняя зарплата: {stats['avg_salary']:,.2f} руб.")
            print(f"  Вакансий с зарплатой: {stats['vacancies_with_salary']}")
            print(f"  Вакансий без зарплаты: {stats['vacancies_without_salary']}")

        elif choice == "7":
            company = input("\n🏢 Введите название компании: ")
            vacancies = db.get_vacancies_by_company(company)
            print_vacancies(vacancies, f"ВАКАНСИИ КОМПАНИИ '{company}' ({len(vacancies)} шт.)")

        else:
            print("⚠️ Неверный выбор. Попробуйте снова.")

        input("\nНажмите Enter, чтобы продолжить...")

    db.close()


if __name__ == "__main__":
    main()