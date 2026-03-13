from typing import Optional

from application.api.deps import get_db, get_rag_engine, verify_api_key_dependency
from application.services.rag.engine import RAGEngine
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["chat"])


class ChatRequestModel(BaseModel):
    question: str
    top_k: Optional[int] = None
    score_threshold: Optional[float] = None
    history_context: Optional[str] = None


class ChatResponseModel(BaseModel):
    answer: str
    sources: list = []
    has_rag_context: bool = False


@router.post("/chat", response_model=ChatResponseModel)
async def chat(
    request: ChatRequestModel,
    _: None = Depends(verify_api_key_dependency),
    rag_engine: RAGEngine = Depends(get_rag_engine),
    db: AsyncSession = Depends(get_db),
):
    """Основная эндпоинт для чата с RAG системой."""
    try:
        enhanced_question = request.question
        if request.history_context:
            enhanced_question = f"""История предыдущего разговора:
{request.history_context}

Текущий вопрос: {request.question}"""

        result = await rag_engine.query(
            question=enhanced_question,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
        )

        return ChatResponseModel(
            answer=result.get("answer", "Не удалось получить ответ"),
            sources=result.get("sources", []),
            has_rag_context=result.get("has_rag_context", False),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка обработки запроса: {str(e)}"
        )


@router.get("/chat/history")
async def chat_history(db: AsyncSession = Depends(get_db)):
    """Получение истории чата для API ключа."""
    return {"message": "История чата пока не реализована"}


@router.delete("/chat/history")
async def delete_chat_history(db: AsyncSession = Depends(get_db)):
    """Очистка истории чата для API ключа."""
    return {"message": "Очистка истории пока не реализована"}
