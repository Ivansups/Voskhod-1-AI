from .llm_manager import LLMManager
from typing import Optional
import httpx
from application.core.config import settings


class OllamaService(LLMManager):
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        base_url = base_url or settings.OLLAMA_BASE_URL
        model = model or settings.OLLAMA_MODEL
        temperature = (
            temperature if temperature is not None else settings.OLLAMA_TEMPERATURE
        )
        max_tokens = (
            max_tokens if max_tokens is not None else settings.OLLAMA_MAX_TOKENS
        )

        super().__init__(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            base_url=base_url,
        )
        self.base_url = base_url.rstrip("/")

    def generate_answer(self, context: str) -> str:
        """
        Генерирует ответ на основе контекста используя Ollama API.
        Автоматически добавляет ответ в историю диалога.
        """
        messages_for_api = self.messages.copy()

        if messages_for_api and messages_for_api[-1].get("role") == "user":
            messages_for_api[-1] = {"role": "user", "content": context}

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages_for_api,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()

                result = response.json()
                answer = result.get("message", {}).get("content", "")

                if not answer:
                    raise ValueError("Пустой ответ от Ollama API")

                self.add_assistant_message(answer)

                return answer

        except httpx.HTTPStatusError as e:
            raise ConnectionError(f"Ошибка подключения к Ollama API: {e}")
        except (KeyError, ValueError) as e:
            raise ValueError(f"Ошибка обработки ответа от Ollama API: {e}")

    def add_user_message(self, message: str) -> None:
        """Добавляет сообщение пользователя в историю диалога."""
        self.messages.append({"role": "user", "content": message})

    def add_assistant_message(self, message: str) -> None:
        """Добавляет сообщение ассистента в историю диалога."""
        self.messages.append({"role": "assistant", "content": message})

    def get_messages(self) -> list[str]:
        """Возвращает список всех сообщений (только содержимое)."""
        return [msg["content"] for msg in self.messages]
