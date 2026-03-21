"""Заполнение базы данных данными из hh.ru API."""

import time
from typing import Any, Dict, List

from src.api.hh_api import HHAPI
from src.db.db_saver import DBSaver


class DBFiller:
    """Класс для заполнения БД данными из API."""

    def __init__(self) -> None:
        """Инициализация API и DBSaver."""
        self.api = HHAPI()
        self.saver = DBSaver()

    def fill_companies_and_vacancies(self) -> Dict[str, Any]:
        """
        Заполнение БД компаниями и вакансиями.

        Returns:
            Dict[str, Any]: Статистика по заполнению
        """
        stats: Dict[str, Any] = {
            "total_companies": 0,
            "success_companies": 0,
            "total_vacancies": 0,
            "saved_vacancies": 0,
            "errors": 0,
            "companies": [],
        }

        try:
            # Подключаемся к БД
            self.saver.connect()

            # Получаем данные о компаниях
            companies_data = self.api.get_all_companies_data()
            stats["total_companies"] = len(companies_data)

            print("\n" + "=" * 60)
            print("ЗАПОЛНЕНИЕ БАЗЫ ДАННЫХ")
            print("=" * 60)

            for company_data in companies_data:
                print(f"\n📊 Обработка компании: {company_data['name']}")

                try:
                    # Сохраняем компанию
                    company_id = self.saver.save_company(company_data)
                    if company_id:
                        stats["success_companies"] += 1
                        company_stats = {
                            "name": company_data["name"],
                            "company_id": company_id,
                            "vacancies_found": 0,
                            "vacancies_saved": 0,
                        }

                        # Получаем вакансии компании
                        print("  Загрузка вакансий...")
                        vacancies = self.api.get_all_vacancies_for_company(company_data["hh_id"])
                        company_stats["vacancies_found"] = len(vacancies)
                        stats["total_vacancies"] += len(vacancies)

                        if vacancies:
                            # Сохраняем вакансии
                            saved, errors = self.saver.save_vacancies(vacancies, company_id)
                            company_stats["vacancies_saved"] = saved
                            stats["saved_vacancies"] += saved
                            stats["errors"] += errors

                            print("  ✅ Вакансий найдено:", len(vacancies))
                            print("  ✅ Сохранено:", saved)
                            if errors:
                                print(f"  ⚠️ Ошибок: {errors}")
                        else:
                            print("  ⚠️ Вакансий не найдено")

                        stats["companies"].append(company_stats)
                    else:
                        stats["errors"] += 1
                        print("  ❌ Ошибка при сохранении компании")

                except Exception as e:
                    stats["errors"] += 1
                    print(f"  ❌ Ошибка при обработке компании {company_data['name']}: {e}")

                # Небольшая задержка между компаниями
                time.sleep(0.5)

        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            stats["errors"] += 1
        finally:
            # Закрываем соединение с БД
            self.saver.close()

        return stats

    def print_stats(self, stats: Dict[str, Any]) -> None:
        """
        Вывод статистики заполнения.

        Args:
            stats: Статистика из fill_companies_and_vacancies
        """
        print("\n" + "=" * 60)
        print("СТАТИСТИКА ЗАПОЛНЕНИЯ БД")
        print("=" * 60)
        print("\n📊 Компании:")
        print(f"  Всего: {stats['total_companies']}")
        print(f"  Сохранено: {stats['success_companies']}")
        print("\n📊 Вакансии:")
        print(f"  Всего найдено: {stats['total_vacancies']}")
        print(f"  Сохранено в БД: {stats['saved_vacancies']}")
        print("\n📊 Ошибки:")
        print(f"  Всего: {stats['errors']}")

        if stats["companies"]:
            print("\n📊 По компаниям:")
            for company in stats["companies"]:
                print(f"  {company['name']}:")
                print(f"    Вакансий найдено: {company['vacancies_found']}")
                print(f"    Сохранено: {company['vacancies_saved']}")
