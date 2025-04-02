from locust import HttpUser, task, between
import random
import string

created_short_codes = []

def random_string(length=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

class ShortenerUser(HttpUser):
    wait_time = between(1, 3) 
    host = "http://app:8000"

    def on_start(self):
        pass

    @task(10)
    def create_link(self):
        original_url = f"https://{random_string(15)}.com/{random_string(10)}"
        payload = {"original_url": original_url}

        with self.client.post("/links/shorten", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    short_code = response.json().get("short_code")
                    if short_code:
                        created_short_codes.append(short_code)
                        response.success()
                    else:
                        response.failure("Short code not found in response")
                except Exception as e:
                    response.failure(f"Failed to parse response: {e}")
            else:
                response.failure(f"Failed to create link: {response.status_code} - {response.text}")

    @task(5) 
    def redirect_link(self):
        if not created_short_codes:
            return

        random_code = random.choice(created_short_codes)
        
        with self.client.get(f"/{random_code}", catch_response=True, allow_redirects=False) as response:
            if response.status_code == 307:
                response.success()
            elif response.status_code == 404:
                 response.failure(f"Link {random_code} not found (404)")
            else:
                response.failure(f"Redirect failed for {random_code}: {response.status_code} - {response.text}")