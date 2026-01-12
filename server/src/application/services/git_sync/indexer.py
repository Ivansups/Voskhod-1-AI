import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

from application.core.config import settings
from application.services.rag.embedding_service import (
    EmbeddingService,
    OpenAIEmbeddingService,
    OllamaEmbeddingService,
)
from application.infrastructure.vector_db.qdrant_client import QdrantClient
from application.infrastructure.file_parsers import (
    BaseFileParser,
    TextFileParser,
    MarkdownFileParser,
)

logger = logging.getLogger(__name__)


class DocumentIndexer:
    """
    Индексатор документов для загрузки в векторную базу данных.

    Для MVP реализует простую стратегию:
    1. Полная переиндексация всех файлов (без инкрементальности)
    2. Поддержка только .txt и .md файлов
    """

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        qdrant_client: Optional[QdrantClient] = None,
        parsers: Optional[List[BaseFileParser]] = None,
        progress_callback: Optional[callable] = None,
    ):
        if embedding_service is None:
            if settings.EMBEDDING_SERVICE == "ollama":
                self.embedding_service = OllamaEmbeddingService()
            else:
                self.embedding_service = OpenAIEmbeddingService()
        else:
            self.embedding_service = embedding_service

        self.qdrant_client = qdrant_client or QdrantClient()

        if parsers is None:
            self.parsers = [TextFileParser(), MarkdownFileParser()]
        else:
            self.parsers = parsers

        self.progress_callback = progress_callback
        self.executor = ThreadPoolExecutor(max_workers=4)

        logger.info("DocumentIndexer инициализирован")

    async def index_directory(
        self, directory_path: Path, collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Индексирует все поддерживаемые файлы в директории.

        Args:
            directory_path: Путь к директории для индексации
            collection_name: Имя коллекции Qdrant (опционально)

        Returns:
            Dict с результатами индексации:
            - total_files: общее количество найденных файлов
            - processed_files: количество обработанных файлов
            - indexed_chunks: количество проиндексированных чанков
            - errors: список ошибок
        """
        try:
            logger.info(f"Начинаем индексацию директории: {directory_path}")

            supported_files = self._find_supported_files(directory_path)
            logger.info(f"Найдено {len(supported_files)} поддерживаемых файлов")

            collection_name = collection_name or settings.QDRANT_COLLECTION_NAME
            await self._ensure_collection_exists(collection_name)
            total_processed = 0
            total_chunks = 0
            errors = []
            total_files = len(supported_files)

            for i, file_path in enumerate(supported_files):
                try:
                    logger.info(
                        f"Обрабатываем файл {i + 1}/{total_files}: {file_path.name}"
                    )

                    progress = 30 + int((i / total_files) * 65)  # 30-95%
                    if self.progress_callback:
                        self.progress_callback(progress, file_path.name)

                    chunks_count = await self._process_and_index_file(
                        file_path, collection_name
                    )
                    total_chunks += chunks_count
                    total_processed += 1

                except Exception as e:
                    error_msg = f"Ошибка обработки файла {file_path}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            logger.info(
                f"Индексация завершена: {total_processed}/{len(supported_files)} файлов, {total_chunks} чанков"
            )

            return {
                "total_files": len(supported_files),
                "processed_files": total_processed,
                "indexed_chunks": total_chunks,
                "errors": errors,
                "collection_name": collection_name,
            }

        except Exception as e:
            logger.error(f"Критическая ошибка при индексации: {e}")
            raise Exception(f"Не удалось проиндексировать директорию: {e}")

    def _find_supported_files(self, directory_path: Path) -> List[Path]:
        """
        Находит все поддерживаемые файлы в директории.

        Args:
            directory_path: Путь к директории

        Returns:
            Список путей к поддерживаемым файлам
        """
        supported_files = []

        supported_extensions = set()
        for parser in self.parsers:
            supported_extensions.update(parser.supported_extensions)

        for file_path in directory_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                if not any(part.startswith(".") for part in file_path.parts):
                    supported_files.append(file_path)

        return supported_files

    async def _ensure_collection_exists(self, collection_name: str) -> None:
        """
        Создает коллекцию в Qdrant если она не существует.

        Args:
            collection_name: Имя коллекции
        """
        try:
            collections = await self.qdrant_client.list_collections()
            result = collections.get("result", {})
            collection_list = result.get("collections", [])
            collection_names = [c["name"] for c in collection_list]

            if collection_name not in collection_names:
                logger.info(f"Создаем коллекцию {collection_name}")
                vector_size = self.embedding_service.get_vector_size()
                await self.qdrant_client.create_collection(
                    collection_name=collection_name, vector_size=vector_size
                )
                logger.info(f"Коллекция {collection_name} создана")
            else:
                logger.info(f"Коллекция {collection_name} уже существует")

        except Exception as e:
            logger.error(f"Ошибка при работе с коллекцией {collection_name}: {e}")
            raise

    async def _process_and_index_file(
        self, file_path: Path, collection_name: str
    ) -> int:
        """
        Обрабатывает файл и индексирует его чанки.

        Args:
            file_path: Путь к файлу
            collection_name: Имя коллекции Qdrant

        Returns:
            Количество проиндексированных чанков
        """
        parser = self._get_parser_for_file(file_path)
        if not parser:
            logger.warning(f"Не найден парсер для файла: {file_path}")
            return 0

        parsed_data = await parser.parse(file_path)

        chunks = parsed_data.get("chunks", [])
        if not chunks:
            logger.warning(f"Файл {file_path} не содержит чанков для индексации")
            return 0

        # Логируем статистику по чанкам
        chunk_sizes = [len(chunk.get("text", "")) for chunk in chunks]
        if chunk_sizes:
            avg_size = sum(chunk_sizes) / len(chunk_sizes)
            min_size = min(chunk_sizes)
            max_size = max(chunk_sizes)
            logger.info(f"Файл {file_path}: {len(chunks)} чанков, "
                       f"размер: avg={avg_size:.0f}, min={min_size}, max={max_size}")

        await self._index_chunks(chunks, collection_name)

        return len(chunks)

    def _get_parser_for_file(self, file_path: Path) -> Optional[BaseFileParser]:
        """
        Возвращает подходящий парсер для файла.

        Args:
            file_path: Путь к файлу

        Returns:
            Парсер или None
        """
        for parser in self.parsers:
            if parser.can_parse(file_path):
                return parser
        return None

    async def _index_chunks(
        self, chunks: List[Dict[str, Any]], collection_name: str
    ) -> None:
        """
        Индексирует чанки в векторную базу данных.

        Args:
            chunks: Список чанков для индексации
            collection_name: Имя коллекции
        """
        if not chunks:
            return

        texts = [chunk["text"] for chunk in chunks]

        logger.debug(f"Создаем эмбеддинги для {len(texts)} чанков")
        embeddings = await self.embedding_service.embed_batch(texts)

        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point = {
                "id": chunk["id"],
                "vector": embedding,
                "payload": {
                    "text": chunk["text"],
                    "file_name": chunk.get("file_name", ""),
                    "file_path": chunk.get("file_path", ""),
                    "chunk_type": chunk.get("chunk_type", "unknown"),
                    "position": chunk.get("position", i),
                    "metadata": chunk,
                },
            }
            points.append(point)

        logger.debug(f"Загружаем {len(points)} точек в Qdrant")
        await self.qdrant_client.upsert(points, collection_name)

    async def clear_collection(
        self, collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Очищает коллекцию (удаляет все точки).

        Args:
            collection_name: Имя коллекции (опционально)

        Returns:
            Результат операции
        """
        try:
            collection_name = collection_name or settings.QDRANT_COLLECTION_NAME

            scroll_result = await self.qdrant_client.scroll(
                collection_name=collection_name,
                limit=10000,
            )

            points = scroll_result.get("points", [])
            if not points:
                return {"cleared_points": 0, "message": "Коллекция уже пуста"}

            point_ids = [point["id"] for point in points]
            await self.qdrant_client.delete(point_ids, collection_name)

            logger.info(
                f"Удалено {len(point_ids)} точек из коллекции {collection_name}"
            )

            return {
                "cleared_points": len(point_ids),
                "collection_name": collection_name,
            }

        except Exception as e:
            logger.error(f"Ошибка при очистке коллекции: {e}")
            raise Exception(f"Не удалось очистить коллекцию: {e}")

    async def __aenter__(self):
        await self.embedding_service.__aenter__()
        await self.qdrant_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.embedding_service.__aexit__(exc_type, exc_val, exc_tb)
        await self.qdrant_client.__aexit__(exc_type, exc_val, exc_tb)
