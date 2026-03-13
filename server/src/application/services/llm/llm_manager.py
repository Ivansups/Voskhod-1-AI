import abc
from typing import Any, Dict, List, Optional


class LLMManager(abc.ABC):
    @abc.abstractmethod
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = api_key
        self.base_url = base_url
        self.messages: List[dict[str, str]] = []
        self.messages.append(
            {
                "role": "system",
                "content": "Ты помощник студента. Отвечай на вопросы пользователя на основе предоставленного контекста.",
            }
        )

    @abc.abstractmethod
    def generate_answer(self, context: str) -> str:
        pass

    @abc.abstractmethod
    def add_user_message(self, message: str) -> None:
        pass

    @abc.abstractmethod
    def add_assistant_message(self, message: str) -> None:
        pass

    @abc.abstractmethod
    def get_messages(self) -> list[str]:
        pass

    def generate_answer_with_rag(
        self, question: str, rag_context: str = "", return_json: bool = True
    ) -> Dict[str, Any]:
        """
        Генерирует ответ с использованием RAG контекста.
        Оптимизированный одноэтапный подход для экономии токенов.

        Args:
            question: Вопрос пользователя
            rag_context: Контекст из векторной БД для RAG (опционально)
            return_json: Если True, возвращает dict, иначе строку

        Returns:
            Dict с полями:
            - answer: Текстовый ответ модели
            - question: Исходный вопрос
            - has_rag_context: Флаг наличия RAG контекста
            - sources: Список источников (если доступны)
        """
        self.add_user_message(question)

        if rag_context:
            # Оптимизированный одноэтапный RAG промпт
            prompt = f"""Ты - помощник студента. Используй предоставленный контекст из учебных материалов.

КОНТЕКСТ ИЗ УЧЕБНЫХ МАТЕРИАЛОВ:
{rag_context}

ВОПРОС СТУДЕНТА: {question}

ИНСТРУКЦИИ:
- Проанализируй контекст и найди релевантную информацию для ответа
- Если в контексте есть нужная информация - используй её для точного ответа
- Если информации в контексте недостаточно - скажи об этом и дай общий ответ
- Будь полезен, точен и лаконичен
- Отвечай на русском языке

ОТВЕТ:"""

            try:
                answer = self.generate_answer(prompt)
            except Exception as e:
                answer = f"Ошибка генерации ответа: {str(e)}"

        else:
            # Без RAG контекста - обычный ответ
            prompt = f"""Ты - помощник студента. Отвечай на вопрос пользователя.

ВОПРОС: {question}

ОТВЕТ:"""

            try:
                answer = self.generate_answer(prompt)
            except Exception as e:
                answer = f"Ошибка генерации ответа: {str(e)}"

        if return_json:
            return {
                "answer": answer,
                "question": question,
                "has_rag_context": bool(rag_context),
                "sources": [],  # Можно расширить для возврата источников из RAG
            }
        else:
            return answer

    def get_messages_dict(self) -> List[Dict[str, str]]:
        """
        Возвращает полную историю сообщений в виде списка словарей.
        Удобно для экспорта и отладки.
        """
        return self.messages.copy()

    def clear_history(self) -> None:
        """Очищает историю сообщений, оставляя только system сообщение."""
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]


# Глобальная переменная для хранения единственного экземпляра LLM сервиса
_llm_service_instance: LLMManager = None


def get_llm_service() -> LLMManager:
    """
    Фабричная функция для создания/получения LLM сервиса.
    Возвращает синглтон экземпляр для сохранения истории диалога.
    Использует только OpenRouter, без fallback.

    Returns:
        Экземпляр LLMManager (только OpenRouter)

    Raises:
        ValueError: Если OpenRouter не настроен или не работает
    """
    global _llm_service_instance

    if _llm_service_instance is not None:
        return _llm_service_instance

    # Ollama как основной сервис (стабильный)
    try:
        from .ollama_service import OllamaService

        ollama_service = OllamaService()
        _llm_service_instance = ollama_service
        return _llm_service_instance
    except Exception as e:
        raise ValueError(f"Ollama недоступен: {e}")

    # OpenRouter отключен для стабильности


def reset_llm_service() -> None:
    """Сбрасывает глобальный экземпляр LLM сервиса (для тестирования или перезагрузки)."""
    global _llm_service_instance
    _llm_service_instance = None
