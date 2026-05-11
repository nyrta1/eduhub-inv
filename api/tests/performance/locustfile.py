"""Lightweight Locust scenario for health endpoint (optional complement to k6)."""

from locust import HttpUser, between, task


class HealthUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task
    def live(self) -> None:
        self.client.get("/api/v1/health/live")
