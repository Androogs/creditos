from backend.models.health_model import HealthResponse


class HealthRepository:

    def get_status(self) -> HealthResponse:
        return HealthResponse(status="ok")