import abc
from pathlib import Path
from typing import Any, Dict


class BaseFileParser(abc.ABC):
    """Абстрактный базовый класс для парсеров файлов."""

    # Константы для разделения на чанки
    MAX_CHUNK_SIZE = 1500  # Максимальный размер чанка в символах
    MIN_CHUNK_SIZE = 50  # Минимальный размер чанка в символах
    OVERLAP_SIZE = 100  # Размер перекрытия между чанками
    """Абстрактный базовый класс для парсеров файлов."""

    @property
    @abc.abstractmethod
    def supported_extensions(self) -> list[str]:
        """
        Возвращает список поддерживаемых расширений файлов.

        Returns:
            Список строк с расширениями (например, ['.txt', '.md'])
        """
        pass

    @abc.abstractmethod
    async def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Парсит файл и возвращает структурированные данные.

        Args:
            file_path: Путь к файлу для парсинга

        Returns:
            Dict с полями:
            - content: Текстовое содержимое файла
            - metadata: Метаданные файла (название, размер, дата модификации и т.д.)
            - chunks: Список чанков для индексации (опционально)
        """
        pass

    def can_parse(self, file_path: Path) -> bool:
        """
        Проверяет, может ли парсер обработать данный файл.

        Args:
            file_path: Путь к файлу

        Returns:
            True если файл поддерживается, False иначе
        """
        return file_path.suffix.lower() in self.supported_extensions

    def _get_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Получает базовые метаданные файла.

        Args:
            file_path: Путь к файлу

        Returns:
            Dict с метаданными файла
        """
        stat = file_path.stat()
        return {
            "file_name": file_path.name,
            "file_path": str(file_path),
            "file_size": stat.st_size,
            "modified_time": stat.st_mtime,
            "extension": file_path.suffix.lower(),
        }

    def _split_large_chunk(self, text: str, max_size: int) -> list[str]:
        """
        Разделяет большой текст на меньшие чанки с перекрытием.

        Args:
            text: Текст для разделения
            max_size: Максимальный размер чанка

        Returns:
            Список чанков
        """
        if len(text) <= max_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + max_size

            # Если конец находится в середине слова, ищем границу слова
            if end < len(text):
                # Ищем ближайший пробел или перенос строки
                while end > start + self.MIN_CHUNK_SIZE and text[end] not in [
                    " ",
                    "\n",
                    ".",
                    "!",
                    "?",
                ]:
                    end -= 1

                # Если не нашли хорошую границу, просто режем по размеру
                if end <= start + self.MIN_CHUNK_SIZE:
                    end = start + max_size

            chunk = text[start:end].strip()
            if len(chunk) >= self.MIN_CHUNK_SIZE:
                chunks.append(chunk)

            # Переходим к следующему чанку с перекрытием
            start = max(start + 1, end - self.OVERLAP_SIZE)

        return chunks
