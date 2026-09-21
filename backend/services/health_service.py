from backend.models.health_model import HealthResponse
from backend.repositories.health_repository import HealthRepository


class HealthService:

    def __init__(self) -> None:
        self.repository = HealthRepository()

    def get_status(self) -> HealthResponse:
        return self.repository.get_status()