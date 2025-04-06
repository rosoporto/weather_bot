from functools import lru_cache
import csv
import requests
from .logger import setup_logger


logger_dev = setup_logger()


@lru_cache()
def download_csv():
    url = "https://raw.githubusercontent.com/epogrebnyak/ru-cities/main/assets/towns.csv"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверка на ошибки HTTP
        return response.text.splitlines()
    except requests.exceptions.HTTPError as http_err:
        logger_dev.error(f"HTTP error occurred: {http_err}")  # Обработка ошибок HTTP
    except requests.exceptions.ConnectionError as conn_err:
        logger_dev.error(f"Connection error occurred: {conn_err}")  # Обработка ошибок соединения
    except requests.exceptions.Timeout as timeout_err:
        logger_dev.error(f"Timeout error occurred: {timeout_err}")  # Обработка таймаутов
    except requests.exceptions.RequestException as req_err:
        logger_dev.error(f"An error occurred: {req_err}")  # Обработка всех остальных ошибок
    return None  # Возвращаем None в случае ошибки


def read_csv(csv_data):
    reader = csv.DictReader(csv_data)
    return list(reader)


def search_city(query):
    csv_data = download_csv()
    cities = read_csv(csv_data)

    query = query.lower()
    try:
        return next(city for city in cities if query in city['city'].lower())
    except StopIteration:
        return None


if __name__ == "__main__":
    # Интерфейс поиска
    while True:
        query = input("Введите название города (или 'q' для выхода): ")
        if query.lower() == 'q':
            break

        city = search_city(query)

        if city:
            print(f"Город: {city['city']}")
            print(f"Население: {city['population']}")
            print(f"Координаты: {city['lat']}, {city['lon']}")
            print(f"Координаты (type): {type(city['lat'])}, {type(city['lon'])}")
        else:
            print("Город не найден.")