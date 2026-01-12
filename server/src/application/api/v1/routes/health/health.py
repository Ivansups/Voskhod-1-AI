from fastapi import APIRouter, Request, HTTPException
from httpx import AsyncClient
from application.services.git_sync import GitSyncService
from application.core.config import settings

router = APIRouter(tags=["health"])

git_sync_service = None
if settings.GIT_REPO_URL:
    try:
        git_sync_service = GitSyncService()
    except Exception as e:
        pass


@router.get("/health")
async def health(request: Request):
    """
    Проверяет здоровье системы и статус синхронизации.
    """
    try:
        sync_status = {}
        if git_sync_service:
            try:
                sync_status = await git_sync_service.get_sync_status()
            except Exception:
                sync_status = {"error": "Git sync service error"}

        ollama_status = "unknown"
        try:
            async with AsyncClient(timeout=2.0) as client:
                response = await client.get(
                    f"{settings.OLLAMA_EMBEDDING_BASE_URL}/api/tags"
                )
                ollama_status = (
                    "healthy" if response.status_code == 200 else "unhealthy"
                )
        except Exception:
            ollama_status = "unavailable"

        qdrant_status = "unknown"
        try:
            async with AsyncClient(timeout=2.0) as client:
                response = await client.get("http://qdrant:6333/healthz")
                qdrant_status = (
                    "healthy" if response.status_code == 200 else "unhealthy"
                )
        except Exception:
            qdrant_status = "unavailable"

        return {
            "status": "ok",
            "timestamp": sync_status.get("last_sync_time"),
            "services": {"ollama": ollama_status, "qdrant": qdrant_status},
            "sync_status": sync_status,
            "ready_for_work": sync_status.get("ready_for_work", False),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/health/sync-progress")
async def sync_progress(request: Request):
    """
    Возвращает детальный прогресс текущей синхронизации.
    """
    try:
        if not git_sync_service:
            return {
                "error": "Git sync service not configured",
                "phase": "not_configured",
                "progress": 0,
                "current_file": None,
                "files_processed": 0,
                "total_files": 0,
                "estimated_time_remaining": None,
                "last_sync_time": None,
                "error_message": "GIT_REPO_URL not set",
            }

        sync_status = await git_sync_service.get_sync_status()

        estimated_time_remaining = None
        if (
            sync_status.get("total_files", 0) > 0
            and sync_status.get("files_processed", 0) > 0
        ):
            remaining_files = (
                sync_status["total_files"] - sync_status["files_processed"]
            )
            avg_time_per_file = 2.0
            estimated_time_remaining = (
                f"~{int(remaining_files * avg_time_per_file)} сек"
            )

        return {
            "phase": sync_status.get("phase", "unknown"),
            "progress": sync_status.get("progress", 0),
            "current_file": sync_status.get("current_file"),
            "files_processed": sync_status.get("files_processed", 0),
            "total_files": sync_status.get("total_files", 0),
            "estimated_time_remaining": estimated_time_remaining,
            "last_sync_time": sync_status.get("last_sync_time"),
            "error_message": sync_status.get("error_message"),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Sync progress check failed: {str(e)}"
        )
