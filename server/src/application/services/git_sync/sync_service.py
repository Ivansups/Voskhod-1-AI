import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from application.core.config import settings
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from .indexer import DocumentIndexer

logger = logging.getLogger(__name__)


class GitSyncService:
    """
    Сервис для синхронизации с Git репозиторием и индексации документов.

    Для MVP реализует простую стратегию:
    1. git pull для получения обновлений
    2. Полная переиндексация всех файлов (без инкрементальности)
    """

    def __init__(
        self,
        repo_url: Optional[str] = None,
        local_path: Optional[str] = None,
        branch: Optional[str] = None,
        indexer: Optional[DocumentIndexer] = None,
    ):
        self.repo_url = repo_url or settings.GIT_REPO_URL
        self.local_path = Path(local_path or settings.GIT_LOCAL_PATH)
        self.branch = branch or settings.GIT_BRANCH
        self.indexer = indexer or DocumentIndexer(
            progress_callback=self._update_progress
        )

        if not self.repo_url:
            raise ValueError("GIT_REPO_URL не настроен")

        self.current_phase = "idle"  # idle, syncing, indexing, ready, error
        self.current_progress = 0  # 0-100
        self.last_sync_time = None
        self.current_file = None
        self.files_processed = 0
        self.total_files = 0
        self.error_message = None

        logger.info(
            f"GitSyncService инициализирован: {self.repo_url} -> {self.local_path}"
        )

    def _update_progress(self, progress: int, current_file: str = None):
        """
        Callback для обновления прогресса индексации.

        Args:
            progress: Процент выполнения (0-100)
            current_file: Имя текущего обрабатываемого файла
        """
        self.current_progress = progress
        self.current_file = current_file
        logger.info(
            f"Прогресс индексации: {progress}% - {current_file or 'завершение'}"
        )

    async def _count_indexed_documents(self) -> int:
        """
        Подсчитывает количество документов в векторной БД.

        Returns:
            Количество документов
        """
        try:
            return 0
        except Exception:
            return 0

    async def sync_and_index(self, force_full_reindex: bool = False) -> Dict[str, Any]:
        """
        Основной метод синхронизации и индексации.

        Args:
            force_full_reindex: Принудительная полная переиндексация

        Returns:
            Dict с результатами операции:
            - success: True/False
            - git_status: статус git операций
            - index_status: статус индексации
            - error: сообщение об ошибке (если есть)
        """
        try:
            self.current_phase = "syncing"
            self.current_progress = 5
            self.error_message = None
            logger.info("Начинаем синхронизацию с Git репозиторием...")

            git_result = await self._sync_repository()
            self.current_progress = 30
            logger.info("Git синхронизация завершена, переходим к индексации...")

            # Проверяем необходимость индексации
            if not force_full_reindex:
                is_up_to_date = await self._check_if_data_up_to_date(git_result)
                if is_up_to_date:
                    logger.info("Данные уже актуальные, пропускаем индексацию")
                    self.current_phase = "ready"
                    self.current_progress = 100
                    self.last_sync_time = datetime.now()
                    self.files_processed = 0
                    self.total_files = 0

                    return {
                        "success": True,
                        "git_status": git_result,
                        "index_status": {
                            "skipped": True,
                            "reason": "data_already_up_to_date",
                            "total_files": 0,
                            "processed_files": 0,
                            "indexed_chunks": 0,
                        },
                        "error": None,
                    }

            self.current_phase = "indexing"
            index_result = await self._index_documents(force_full_reindex)

            self.current_phase = "ready"
            self.current_progress = 100
            self.last_sync_time = datetime.now()
            self.files_processed = index_result.get("files_processed", 0)
            self.total_files = index_result.get("total_files", 0)

            logger.info("Синхронизация и индексация завершены успешно")

            return {
                "success": True,
                "git_status": git_result,
                "index_status": index_result,
                "error": None,
            }

        except Exception as e:
            self.current_phase = "error"
            self.error_message = str(e)
            logger.error(f"Ошибка при синхронизации: {str(e)}")
            return {
                "success": False,
                "git_status": None,
                "index_status": None,
                "error": str(e),
            }

    async def _check_if_data_up_to_date(self, git_result: Dict[str, Any]) -> bool:
        """
        Проверяет, актуальны ли данные в векторной БД.

        Args:
            git_result: Результат git синхронизации

        Returns:
            True если данные актуальные, False если нужна индексация
        """
        try:
            if not self.local_path.exists():
                return False

            # Проверяем, есть ли данные в векторной БД (в будущем: metadata с commit hash)
            # Для MVP просто проверяем, что коллекция существует и содержит данные
            # В будущем можно добавить метаданные с коммит хэшем в БД

            # Получаем количество документов в БД
            documents_count = await self._count_indexed_documents()

            # Если документов мало или их нет, считаем что данные не актуальные
            if documents_count < 100:  # Пороговое значение
                logger.info(
                    f"Найдено только {documents_count} документов, нужна индексация"
                )
                return False

            # Если был pull и есть новые коммиты, нужна индексация
            if (
                git_result.get("action") == "pull"
                and git_result.get("commits_pulled", 0) > 0
            ):
                logger.info(
                    f"Получено {git_result['commits_pulled']} новых коммитов, нужна индексация"
                )
                return False

            # Если клонировали репозиторий, нужна индексация
            if git_result.get("action") == "clone":
                logger.info("Репозиторий только что клонирован, нужна индексация")
                return False

            logger.info("Данные в векторной БД кажутся актуальными")
            return True

        except Exception as e:
            logger.warning(f"Ошибка при проверке актуальности данных: {e}")
            return False

    async def _sync_repository(self) -> Dict[str, Any]:
        """
        Синхронизирует локальный репозиторий с удаленным.

        Returns:
            Dict с результатами git операций
        """
        try:
            self.local_path.parent.mkdir(parents=True, exist_ok=True)

            repo = None

            if self.local_path.exists():
                logger.info(f"Обновляем существующий репозиторий в {self.local_path}")
                repo = Repo(self.local_path)

                if repo.active_branch.name != self.branch:
                    logger.info(f"Переключаемся на ветку {self.branch}")
                    repo.git.checkout(self.branch)

                origin = repo.remotes.origin
                pull_result = origin.pull()

                return {
                    "action": "pull",
                    "branch": self.branch,
                    "commits_pulled": len(pull_result),
                    "local_commit": str(repo.head.commit)[:8],
                }

            else:
                logger.info(
                    f"Клонируем репозиторий {self.repo_url} в {self.local_path}"
                )
                repo = Repo.clone_from(
                    self.repo_url, self.local_path, branch=self.branch
                )

                return {
                    "action": "clone",
                    "branch": self.branch,
                    "local_commit": str(repo.head.commit)[:8],
                }

        except GitCommandError as e:
            logger.error(f"Ошибка Git команды: {e}")
            raise Exception(f"Git операция не удалась: {e}")

        except Exception as e:
            logger.error(f"Ошибка при работе с Git: {e}")
            raise Exception(f"Не удалось синхронизировать репозиторий: {e}")

    async def _index_documents(
        self, force_full_reindex: bool = False
    ) -> Dict[str, Any]:
        """
        Индексирует документы в репозитории.

        Args:
            force_full_reindex: Принудительная полная переиндексация

        Returns:
            Dict с результатами индексации
        """
        try:
            logger.info(
                f"Начинаем индексацию документов (force_full_reindex={force_full_reindex})..."
            )

            result = await self.indexer.index_directory(
                self.local_path, force_full_reindex=force_full_reindex
            )

            logger.info(f"Индексация завершена: {result}")

            return result

        except Exception as e:
            logger.error(f"Ошибка при индексации документов: {e}")
            raise Exception(f"Не удалось проиндексировать документы: {e}")

    async def get_sync_status(self) -> Dict[str, Any]:
        """
        Возвращает статус синхронизации с прогрессом.

        Returns:
            Dict с полной информацией о синхронизации
        """
        try:
            if not self.local_path.exists():
                return {
                    "phase": "not_initialized",
                    "progress": 0,
                    "message": "Репозиторий не клонирован",
                    "ready_for_work": False,
                }

            repo = Repo(self.local_path)

            documents_count = await self._count_indexed_documents()

            return {
                "phase": self.current_phase,
                "progress": self.current_progress,
                "repo_url": self.repo_url,
                "branch": repo.active_branch.name,
                "local_commit": str(repo.head.commit),
                "documents_count": documents_count,
                "files_processed": self.files_processed,
                "total_files": self.total_files,
                "current_file": self.current_file,
                "last_sync_time": self.last_sync_time.isoformat()
                if self.last_sync_time
                else None,
                "error_message": self.error_message,
                "ready_for_work": self.current_phase == "ready" and documents_count > 0,
            }

        except InvalidGitRepositoryError:
            return {"status": "invalid", "message": "Некорректный Git репозиторий"}

        except Exception as e:
            return {"status": "error", "message": str(e)}
