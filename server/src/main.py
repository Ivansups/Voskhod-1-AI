from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from application.api.v1.routes.health.health import router as health_router
from application.api.v1.routes.chat.chat import router as chat_router
from application.api.v1.routes.admin.admin import router as admin_router
from application.api.v1.routes.llm.llm import router as llm_router
from application.api.v1.routes.key.key import router as key_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health роутер доступен без префикса для обратной совместимости
app.include_router(health_router)
app.include_router(health_router, prefix="/v1")

# Остальные роутеры с префиксом v1
app.include_router(chat_router, prefix="/v1")
app.include_router(admin_router, prefix="/v1")
app.include_router(llm_router, prefix="/v1")
app.include_router(key_router, prefix="/v1")
