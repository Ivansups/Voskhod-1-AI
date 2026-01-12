from pydantic import BaseModel


class ChatRequest(BaseModel):
    chat_id: str
    name: str  # First name + Last name of the user
    question: str  # Message to the AI
    temperature: float
    max_tokens: int
