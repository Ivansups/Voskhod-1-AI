from typing import Any, Dict, List

from pydantic import BaseModel


class ChatResponse(BaseModel):
    chat_id: str
    name: str  # First name + Last name of the user
    message: str
    answer: str
    sources: List[Dict[str, Any]]
    has_rag_context: bool
    has_tool_calls: bool = False
