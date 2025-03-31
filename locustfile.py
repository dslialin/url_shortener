from locust import HttpUser, task, between
import random
import string

# Глобальная переменная для хранения созданных кодов, чтобы другие пользователи могли их использовать
created_short_codes = []

def random_string(length=10):
    """Генерирует случайную строку для URL."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

class ShortenerUser(HttpUser):
    """ 
    Класс пользователя Locust для тестирования URL Shortener.
    Имитирует:
    1. Создание новой короткой ссылки (POST /links/shorten).
    2. Переход по случайно выбранной из ранее созданных ссылок (GET /{short_code}).
    """
    wait_time = between(1, 3)  # Пауза между задачами от 1 до 3 секунд
    host = "http://app:8000"  # Указываем имя сервиса 'app' и порт внутри Docker сети

    # Атрибуты для хранения данных, уникальных для пользователя Locust (если потребуется)
    # short_code = None 
    
    def on_start(self):
        """ 
        Действия при старте "виртуального пользователя". 
        Здесь можно было бы реализовать логин, но для простоты пока не будем.
        """
        # self.login()
        pass

    # def login(self):
    #     # Примерная реализация логина (нужно адаптировать под ваше API)
    #     response = self.client.post("/token", data={"username": "testlocust", "password": "locustpass"})
    #     if response.status_code == 200:
    #         self.token = response.json()["access_token"]
    #         self.client.headers = {"Authorization": f"Bearer {self.token}"}
    #     else:
    #         print(f"Login failed: {response.status_code} - {response.text}")
    #         # Можно остановить тест или пользователя, если логин критичен

    @task(10) # Эта задача будет выполняться в 10 раз чаще
    def create_link(self):
        """Задача: Создание новой короткой ссылки."""
        original_url = f"https://{random_string(15)}.com/{random_string(10)}"
        payload = {"original_url": original_url}
        
        # Заголовки можно установить здесь, если логин не реализован в on_start
        # headers = {"Authorization": f"Bearer {self.token}"} if hasattr(self, 'token') else {}
        
        with self.client.post("/links/shorten", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    short_code = response.json().get("short_code")
                    if short_code:
                        created_short_codes.append(short_code) # Добавляем в общий список
                        response.success()
                    else:
                        response.failure("Short code not found in response")
                except Exception as e:
                    response.failure(f"Failed to parse response: {e}")
            else:
                response.failure(f"Failed to create link: {response.status_code} - {response.text}")

    @task(5) # Эта задача будет выполняться реже
    def redirect_link(self):
        """Задача: Переход по случайной короткой ссылке."""
        if not created_short_codes:
            # Если еще не создано ни одной ссылки, пропускаем задачу
            return

        # Выбираем случайный код из списка созданных
        random_code = random.choice(created_short_codes)
        
        # allow_redirects=False, чтобы сам Locust не переходил по редиректу
        with self.client.get(f"/{random_code}", catch_response=True, allow_redirects=False) as response:
            if response.status_code == 307: # Ожидаем редирект
                response.success()
            elif response.status_code == 404:
                 response.failure(f"Link {random_code} not found (404)")
                 # Можно удалить невалидный код из списка, если он часто встречается
                 # try:
                 #     created_short_codes.remove(random_code)
                 # except ValueError:
                 #     pass 
            else:
                response.failure(f"Redirect failed for {random_code}: {response.status_code} - {response.text}")

# Если нужно запустить Locust из командной строки без UI:
# locust -f locustfile.py --headless -u 100 -r 10 --run-time 1m --host http://localhost:8000
# -u 100: количество пользователей
# -r 10: скорость появления новых пользователей в секунду
# --run-time 1m: продолжительность теста (1 минута) 