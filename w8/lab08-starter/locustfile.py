
import random

from locust import HttpUser, task, between


class BooksUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def search_by_year(self):
        year = random.randint(2000, 2025)

        with self.client.get(
            "/books",
            params={"year": year},
            name="/books?year=[year]",
            catch_response=True,
        ) as response:

            # Simulate 1% failure in Locust.
            # This marks the request as failed in Locust;
            # it does NOT make the server return a real HTTP 500.
            if random.random() < 0.01:
                response.failure("Simulated HTTP 500 (Locust-side)")
            elif response.status_code >= 400:
                response.failure(
                    f"HTTP {response.status_code}"
                )
