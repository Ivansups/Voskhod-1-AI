"""Парсеры файлов для индексации документов."""

from .base_parser import BaseFileParser
from .markdown_parser import MarkdownFileParser
from .text_parser import TextFileParser

__all__ = ["BaseFileParser", "TextFileParser", "MarkdownFileParser"]
