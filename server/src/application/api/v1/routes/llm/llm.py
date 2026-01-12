from fastapi import APIRouter, Request

router = APIRouter(tags=["llm"])


@router.post("/llm/generate")
async def llm_chat(request: Request):
    pass


@router.get("/llm/history")
async def llm_history(request: Request):
    pass


@router.delete("/llm/history")
async def llm_history_delete(request: Request):
    pass
