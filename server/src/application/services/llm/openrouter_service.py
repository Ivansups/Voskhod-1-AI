import openai
from .llm_manager import LLMManager
from typing import Optional
from application.core.config import settings


class OpenRouterService(LLMManager):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        api_key = api_key or settings.OPENROUTER_API_KEY
        model = model or settings.OPENROUTER_MODEL
        temperature = (
            temperature if temperature is not None else settings.OPENROUTER_TEMPERATURE
        )
        max_tokens = (
            max_tokens if max_tokens is not None else settings.OPENROUTER_MAX_TOKENS
        )

        super().__init__(
            model=model, temperature=temperature, max_tokens=max_tokens, api_key=api_key
        )
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )

    def generate_answer(self, context: str) -> str:
        import logging
        logger = logging.getLogger(__name__)

        # Создаем временные сообщения с контекстом для этого запроса
        messages_for_request = self.messages.copy()

        # Если контекст отличается от последнего сообщения пользователя, добавляем его
        if context and (not messages_for_request or messages_for_request[-1]["content"] != context):
            messages_for_request.append({"role": "user", "content": context})

        # Логируем запрос для отладки
        logger.info(f"OpenRouter request - Model: {self.model}, Messages count: {len(messages_for_request)}")
        for i, msg in enumerate(messages_for_request):
            logger.info(f"Message {i}: {msg['role']} - {msg['content'][:100]}...")

        try:
            response = (
                self.client.chat.completions.create(
                    model=self.model,
                    messages=messages_for_request,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                .choices[0]
                .message.content
            )

            # Добавляем в историю: пользовательское сообщение (если его там нет) и ответ ассистента
            if context and (not self.messages or self.messages[-1]["content"] != context):
                self.messages.append({"role": "user", "content": context})
            self.messages.append({"role": "assistant", "content": response})

            return response
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            raise

    def add_user_message(self, message: str) -> None:
        self.messages.append({"role": "user", "content": message})

    def add_assistant_message(self, message: str) -> None:
        self.messages.append({"role": "assistant", "content": message})

    def get_messages(self) -> list[str]:
        return [msg["content"] for msg in self.messages]
