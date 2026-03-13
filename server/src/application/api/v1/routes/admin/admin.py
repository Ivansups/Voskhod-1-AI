from typing import Any, Dict

from application.core.config import settings
from application.services.git_sync import GitSyncService
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

router = APIRouter(tags=["admin"])


git_sync_service = None
if settings.GIT_REPO_URL:
    try:
        git_sync_service = GitSyncService()
    except Exception:
        pass


@router.post("/admin/sync")
async def admin_sync(
    background_tasks: BackgroundTasks, request: Request, force: bool = False
) -> Dict[str, Any]:
    """
    Запуск синхронизации Git репозитория и переиндексации документов.

    Синхронизация запускается в фоне через BackgroundTasks FastAPI.

    Args:
        force: Принудительная полная переиндексация (очищает всю коллекцию)
    """
    if not git_sync_service:
        raise HTTPException(
            status_code=503,
            detail="Git sync service not configured. Set GIT_REPO_URL to enable sync functionality.",
        )

    try:
        background_tasks.add_task(git_sync_service.sync_and_index, force)

        mode = "полной переиндексации" if force else "инкрементальной индексации"
        return {
            "message": f"Синхронизация ({mode}) запущена в фоне",
            "status": "running",
            "force_reindex": force,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка запуска синхронизации: {str(e)}"
        )


@router.get("/admin/sync/status")
async def admin_sync_status(request: Request) -> Dict[str, Any]:
    """
    Получение статуса Git репозитория и последней синхронизации.
    """
    if not git_sync_service:
        return {
            "error": "Git sync service not configured",
            "configured": False,
            "repo_url": None,
            "local_path": None,
            "branch": None,
        }

    try:
        status = await git_sync_service.get_sync_status()
        return {
            "sync_status": status,
            "repo_url": git_sync_service.repo_url,
            "local_path": str(git_sync_service.local_path),
            "branch": git_sync_service.branch,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения статуса синхронизации: {str(e)}"
        )


@router.get("/admin/stats")
async def admin_stats(request: Request) -> Dict[str, Any]:
    """Статистика системы (заглушка для будущей реализации)"""
    return {
        "message": "Статистика системы пока не реализована",
        "note": "В будущем здесь будет информация о запросах, пользователях и т.д.",
    }


@router.post("/admin/api-keys")
async def create_api_key(request: Request) -> Dict[str, Any]:
    """Создание нового API ключа (заглушка для будущей реализации)"""
    return {
        "message": "Создание API ключей пока не реализовано",
        "note": "В полной версии будет интеграция с БД",
    }


@router.get("/admin/api-keys")
async def list_api_keys(request: Request) -> Dict[str, Any]:
    """Список всех API ключей (заглушка для будущей реализации)"""
    return {
        "message": "Список API ключей пока не реализован",
        "note": "В полной версии будет интеграция с БД",
        "api_keys": [],
    }


@router.delete("/admin/api-keys/{key_id}")
async def delete_api_key(request: Request, key_id: str) -> Dict[str, Any]:
    """Деактивация API ключа (заглушка для будущей реализации)"""
    return {
        "message": f"Деактивация API ключа {key_id} пока не реализована",
        "note": "В полной версии будет интеграция с БД",
    }
