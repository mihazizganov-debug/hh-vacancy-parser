"""Класс для работы с API hh.ru."""

import time
from typing import Any, Dict, List, Optional

import requests


class HHAPI:
    """Класс для получения данных о компаниях и вакансиях с hh.ru."""

    BASE_URL = "https://api.hh.ru"

    # Список компаний с известными ID (берём сразу правильные)
    COMPANIES = [
        {"id": 9694561, "name": "Яндекс"},
        {"id": 3529, "name": "Сбер"},
        {"id": 78638, "name": "Тинькофф"},
        {"id": 15478, "name": "VK"},
        {"id": 2180, "name": "Ozon"},
        {"id": 87021, "name": "Wildberries"},
        {"id": 84585, "name": "Avito"},
        {"id": 1122462, "name": "Skyeng"},
        {"id": 1057, "name": "Лаборатория Касперского"},
        {"id": 1102681, "name": "Positive Technologies"},
    ]

    def __init__(self) -> None:
        """Инициализация клиента API."""
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "HH-Vacancy-Parser/1.0"})

    def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Выполнение HTTP-запроса с обработкой ошибок."""
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()  # type: ignore
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе {url}: {e}")
            return {}

    def get_company_by_id(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Получение информации о компании по ID."""
        url = f"{self.BASE_URL}/employers/{company_id}"
        return self._make_request(url)

    def get_company_vacancies(
        self, company_id: str, page: int = 0, per_page: int = 100
    ) -> Dict[str, Any]:
        """Получение вакансий компании."""
        url = f"{self.BASE_URL}/vacancies"
        params = {"employer_id": company_id, "page": page, "per_page": per_page}
        return self._make_request(url, params)

    def get_all_vacancies_for_company(self, company_id: str) -> List[Dict[str, Any]]:
        """Получение всех вакансий компании с пагинацией."""
        all_vacancies = []
        page = 0

        while True:
            data = self.get_company_vacancies(company_id, page)
            items = data.get("items", [])

            if not items:
                break

            all_vacancies.extend(items)
            page += 1

            # Проверяем, есть ли следующая страница
            if page >= data.get("pages", 1):
                break

            # Небольшая задержка, чтобы не нагружать API
            time.sleep(0.2)

        return all_vacancies

    def get_all_companies_data(self) -> List[Dict[str, Any]]:
        """Получение данных обо всех компаниях из списка."""
        companies_data = []

        for company in self.COMPANIES:
            print(f"Получаем данные о компании: {company['name']}...")

            # Получаем информацию о компании
            company_info = self.get_company_by_id(str(company["id"]))

            if company_info:
                companies_data.append(
                    {
                        "hh_id": company["id"],
                        "name": company_info.get("name", company["name"]),
                        "description": company_info.get("description"),
                        "site_url": company_info.get("site_url"),
                        "open_vacancies": company_info.get("open_vacancies", 0),
                    }
                )
                print(f"  ✅ Данные получены! Вакансий: {company_info.get('open_vacancies', 0)}")
            else:
                print("  ❌ Не удалось получить данные")

            time.sleep(0.5)

        return companies_data


if __name__ == "__main__":
    # Тестирование работы API
    api = HHAPI()

    print("=" * 60)
    print("ТЕСТИРОВАНИЕ HH.RU API")
    print("=" * 60)

    # Получаем данные о компаниях
    companies = api.get_all_companies_data()

    print(f"\n✅ Найдено компаний: {len(companies)}")

    # Получаем вакансии для первой компании
    if companies:
        company = companies[0]
        print(f"\n📊 Вакансии для компании {company['name']}:")

        vacancies = api.get_all_vacancies_for_company(company["hh_id"])
        print(f"  Всего вакансий: {len(vacancies)}")

        # Показываем первые 3 вакансии
        for i, vacancy in enumerate(vacancies[:3], 1):
            salary = vacancy.get("salary")
            salary_str = "не указана"
            if salary:
                salary_from = salary.get("from", "")
                salary_to = salary.get("to", "")
                currency = salary.get("currency", "")
                salary_str = f"{salary_from}-{salary_to} {currency}"

            print(f"\n  {i}. {vacancy['name']}")
            print(f"     Зарплата: {salary_str}")
            print(f"     Ссылка: {vacancy['alternate_url']}")
