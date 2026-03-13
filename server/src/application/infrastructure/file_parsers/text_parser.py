from pathlib import Path
from typing import Any, Dict

import aiofiles

from .base_parser import BaseFileParser


class TextFileParser(BaseFileParser):
    """Парсер для текстовых файлов (.txt)."""

    @property
    def supported_extensions(self) -> list[str]:
        return [".txt"]

    async def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Парсит текстовый файл.

        Args:
            file_path: Путь к .txt файлу

        Returns:
            Dict с содержимым и метаданными файла
        """
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()

            metadata = self._get_file_metadata(file_path)

            chunks = self._create_chunks(content, file_path)

            return {"content": content, "metadata": metadata, "chunks": chunks}

        except UnicodeDecodeError:
            try:
                async with aiofiles.open(file_path, "r", encoding="cp1251") as f:
                    content = await f.read()
            except UnicodeDecodeError:
                raise ValueError(
                    f"Не удалось прочитать файл {file_path} - неподдерживаемая кодировка"
                )

            metadata = self._get_file_metadata(file_path)
            chunks = self._create_chunks(content, file_path)

            return {"content": content, "metadata": metadata, "chunks": chunks}

    def _create_chunks(self, content: str, file_path: Path) -> list[Dict[str, Any]]:
        """
        Создает чанки из текстового содержимого.

        Стратегия:
        1. Разделение по двойным переносам строк (абзацам)
        2. Ограничение размера чанков
        3. Каждый чанк содержит текст, позицию и метаданные.

        Args:
            content: Текстовое содержимое файла
            file_path: Путь к файлу

        Returns:
            Список словарей с чанками
        """
        chunks = []

        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        for i, paragraph in enumerate(paragraphs):
            if len(paragraph) < self.MIN_CHUNK_SIZE:
                continue

            # Разделяем слишком большие абзацы
            sub_chunks = self._split_large_chunk(paragraph, self.MAX_CHUNK_SIZE)

            for j, sub_chunk in enumerate(sub_chunks):
                chunk_id = abs(hash(f"{file_path}_{i}_{j}")) % 1000000

                chunks.append(
                    {
                        "id": chunk_id,
                        "text": sub_chunk,
                        "position": i,
                        "sub_position": j,
                        "file_name": file_path.name,
                        "file_path": str(file_path),
                        "chunk_type": "paragraph",
                        "chunk_size": len(sub_chunk),
                    }
                )

        return chunks
