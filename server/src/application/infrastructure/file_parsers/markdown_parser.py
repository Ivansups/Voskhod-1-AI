import re
from pathlib import Path
from typing import Any, Dict, List

import aiofiles

from .base_parser import BaseFileParser


class MarkdownFileParser(BaseFileParser):
    """Парсер для Markdown файлов (.md)."""

    @property
    def supported_extensions(self) -> list[str]:
        return [".md", ".markdown"]

    async def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Парсит Markdown файл.

        Args:
            file_path: Путь к .md файлу

        Returns:
            Dict с содержимым и метаданными файла
        """
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()

            metadata = self._get_file_metadata(file_path)

            title = self._extract_title(content)
            metadata["title"] = title

            chunks = self._create_chunks(content, file_path)

            return {"content": content, "metadata": metadata, "chunks": chunks}

        except UnicodeDecodeError:
            raise ValueError(
                f"Не удалось прочитать файл {file_path} - неподдерживаемая кодировка"
            )

    def _extract_title(self, content: str) -> str:
        """
        Извлекает заголовок документа из первой строки с #.

        Args:
            content: Содержимое файла

        Returns:
            Заголовок документа или имя файла
        """
        lines = content.split("\n")
        for line in lines[:10]:  # Проверяем первые 10 строк
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
        return ""

    def _create_chunks(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """
        Создает чанки из Markdown содержимого с учетом структуры документа.

        Стратегия:
        1. Разделение по заголовкам (# ## ###)
        2. Каждый раздел становится отдельным чанком
        3. Сохранение иерархии заголовков

        Args:
            content: Содержимое Markdown файла
            file_path: Путь к файлу

        Returns:
            Список словарей с чанками
        """
        chunks = []

        sections = self._split_by_headers(content)

        for i, section in enumerate(sections):
            content = section["content"].strip()
            if not content or len(content) < self.MIN_CHUNK_SIZE:
                continue

            header_level = self._get_header_level(section["header"])

            # Разделяем слишком большие секции
            sub_chunks = self._split_large_chunk(content, self.MAX_CHUNK_SIZE)

            for j, sub_chunk in enumerate(sub_chunks):
                chunk_id = abs(hash(f"{file_path}_{i}_{j}")) % 1000000

                chunks.append(
                    {
                        "id": chunk_id,
                        "text": sub_chunk,
                        "header": section["header"].strip(),
                        "header_level": header_level,
                        "position": i,
                        "sub_position": j,
                        "file_name": file_path.name,
                        "file_path": str(file_path),
                        "chunk_type": "markdown_section",
                        "chunk_size": len(sub_chunk),
                    }
                )

        return chunks

    def _split_by_headers(self, content: str) -> List[Dict[str, str]]:
        """
        Разделяет Markdown контент по заголовкам.

        Args:
            content: Markdown контент

        Returns:
            Список секций с заголовками и содержимым
        """
        sections = []

        header_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

        parts = header_pattern.split(content)

        if parts[0].strip():
            sections.append({"header": "Введение", "content": parts[0]})

        for i in range(1, len(parts), 3):
            if i + 2 < len(parts):
                header_marker = parts[i]
                header_text = parts[i + 1]
                section_content = parts[i + 2]

                sections.append(
                    {
                        "header": f"{header_marker} {header_text}",
                        "content": section_content,
                    }
                )

        return sections

    def _get_header_level(self, header: str) -> int:
        """
        Определяет уровень заголовка (1-6).

        Args:
            header: Строка заголовка (например, "## Section")

        Returns:
            Уровень заголовка (1-6)
        """
        if not header:
            return 0

        match = re.match(r"^(#+)", header.strip())
        if match:
            return len(match.group(1))
        return 0
