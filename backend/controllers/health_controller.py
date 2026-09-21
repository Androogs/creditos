from fastapi import APIRouter

from backend.services.health_service import HealthService

router = APIRouter()
health_service = HealthService()


@router.get("/health")
def health_check():
    return health_service.get_status()
