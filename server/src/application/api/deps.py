from application.infrastructure.postgreSQL.models.key import verify_api_key
from application.infrastructure.postgreSQL.session import AsyncSessionLocal
from application.infrastructure.vector_db.qdrant_client import QdrantClient
from application.services.llm.llm_manager import get_llm_service
from application.services.rag.embedding_service import get_embedding_service
from application.services.rag.engine import RAGEngine
from application.services.rag.retriever import RAGRetriever
from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_rag_engine() -> RAGEngine:
    """
    Dependency для получения RAG движка.

    Создает экземпляр RAGEngine с настроенными сервисами.
    """
    try:
        llm_manager = get_llm_service()
        qdrant_client = QdrantClient()
        embedding_service = get_embedding_service()

        retriever = RAGRetriever(
            qdrant_client=qdrant_client, embedding_service=embedding_service
        )

        rag_engine = RAGEngine(retriever=retriever, llm_service=llm_manager)

        return rag_engine

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to initialize RAG engine: {str(e)}"
        )


async def verify_api_key_dependency(
    request: Request, db: AsyncSession = Depends(get_db)
) -> None:
    """
    Dependency для проверки API ключа из заголовков запроса.
    """
    return

    api_key = request.headers.get("X-API-Key")
    user_tag = request.headers.get("X-User-Tag")

    if not api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header is required")

    if not user_tag:
        raise HTTPException(status_code=401, detail="X-User-Tag header is required")

    user_tag = user_tag.lstrip("@")
    is_valid = await verify_api_key(db, api_key, user_tag)

    if not is_valid:
        raise HTTPException(
            status_code=403, detail="Invalid API key or user not authorized"
        )
