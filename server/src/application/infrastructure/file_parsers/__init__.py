"""Парсеры файлов для индексации документов."""

from .base_parser import BaseFileParser
from .text_parser import TextFileParser
from .markdown_parser import MarkdownFileParser

__all__ = ["BaseFileParser", "TextFileParser", "MarkdownFileParser"]
