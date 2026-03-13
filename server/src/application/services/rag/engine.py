from typing import Any, Dict, Optional

from ..llm.llm_manager import LLMManager
from .retriever import RAGRetriever


class RAGEngine:
    """RAG движок, объединяющий поиск в векторной БД и генерацию ответов через LLM."""

    def __init__(
        self,
        retriever: RAGRetriever,
        llm_service: LLMManager,
    ):
        self.retriever = retriever
        self.llm_service = llm_service

    async def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        return_json: bool = True,
        filter: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        print(f"🔍 RAG QUERY: {question}, top_k={top_k}")  # DEBUG
        """
        Основной метод для выполнения RAG запроса.

        Args:
            question: Вопрос пользователя
            top_k: Количество релевантных чанков для поиска
            score_threshold: Минимальный порог схожести
            return_json: Если True, возвращает структурированный JSON
            filter: Фильтр по метаданным для поиска

        Returns:
            Dict с полями:
            - answer: Текстовый ответ модели
            - question: Исходный вопрос
            - sources: Список источников с метаданными
            - has_rag_context: Флаг наличия RAG контекста
        """
        retrieved_chunks = await self.retriever.retrieve(
            query=question, top_k=top_k, score_threshold=score_threshold, filter=filter
        )

        if retrieved_chunks:
            rag_context = await self.retriever.retrieve_with_context(
                query=question,
                top_k=top_k,
                score_threshold=score_threshold,
                filter=filter,
            )

            # Ограничиваем длину контекста для избежания проблем с LLM
            max_context_length = 4000  # Ограничиваем до 4000 символов
            if len(rag_context) > max_context_length:
                rag_context = (
                    rag_context[:max_context_length]
                    + "\n\n[Контекст сокращен для экономии токенов]"
                )

            sources = []
            for chunk in retrieved_chunks:
                metadata = chunk.get("metadata", {})
                sources.append(
                    {
                        "content": chunk.get("content", ""),
                        "score": chunk.get("score", 0.0),
                        "source": metadata.get("source", ""),
                        "file_path": metadata.get("file_path", ""),
                        "chunk_index": metadata.get("chunk_index", 0),
                    }
                )

            # Логируем контекст для отладки
            import logging

            logger = logging.getLogger(__name__)
            logger.info(f"RAG DEBUG: Question: {question}")
            logger.info(f"RAG DEBUG: Found {len(retrieved_chunks)} chunks")
            logger.info(f"RAG DEBUG: Context length: {len(rag_context)} chars")
            logger.info(f"RAG DEBUG: Context preview: {rag_context[:300]}...")
            logger.info(
                f"RAG DEBUG: Sources in chunks: {[chunk.get('metadata', {}).get('file_path', '') for chunk in retrieved_chunks[:3]]}"
            )
            logger.info(f"RAG DEBUG: Sources list length: {len(sources)}")
            logger.info(f"RAG DEBUG: Has RAG context: {bool(rag_context)}")

            result = self.llm_service.generate_answer_with_rag(
                question=question, rag_context=rag_context, return_json=True
            )

            result["sources"] = sources

            if not return_json:
                return result["answer"]

            return result
        else:
            result = self.llm_service.generate_answer_with_rag(
                question=question, rag_context="", return_json=True
            )

            if not return_json:
                return result["answer"]

            return result

    async def query_stream(
        self,
        question: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        filter: Optional[Dict[str, Any]] = None,
    ):
        """
        Выполняет RAG запрос с потоковой генерацией ответа.

        Args:
            question: Вопрос пользователя
            top_k: Количество релевантных чанков
            score_threshold: Минимальный порог схожести
            filter: Фильтр по метаданным

        Yields:
            Части сгенерированного ответа
        """
        retrieved_chunks = await self.retriever.retrieve(
            query=question, top_k=top_k, score_threshold=score_threshold, filter=filter
        )

        if retrieved_chunks:
            rag_context = await self.retriever.retrieve_with_context(
                query=question,
                top_k=top_k,
                score_threshold=score_threshold,
                filter=filter,
            )
        else:
            rag_context = ""

        self.llm_service.add_user_message(question)

        if rag_context:
            prompt = f"""Используй следующий контекст для ответа на вопрос. Если в контексте нет информации для ответа, скажи об этом.

Контекст:
{rag_context}

Вопрос: {question}

Ответ:"""
        else:
            prompt = question

        answer = self.llm_service.generate_answer(prompt)

        yield answer

    def get_retriever(self) -> RAGRetriever:
        """Возвращает экземпляр retriever."""
        return self.retriever

    def get_llm_service(self) -> LLMManager:
        """Возвращает экземпляр LLM сервиса."""
        return self.llm_service
