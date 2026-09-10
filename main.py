from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time

from kb_manager import KnowledgeBaseManager
from giga_chat import SupportAgent

app = FastAPI(
    title="Molvest AI Support Agent",
    description="API для интеграции ИИ-агента с Bitrix24 и Redmine",
    version="1.0"
)

# В боевой среде токен берется из переменных окружения (os.environ)
# Для теста впиши сюда свой токен GigaChat
GIGACHAT_CREDENTIALS = "ВАШ ТОКЕН"

# Инициализируем ядро
try:
    kb = KnowledgeBaseManager()
    agent = SupportAgent(kb_manager=kb, credentials=GIGACHAT_CREDENTIALS)
except Exception as e:
    print(f"Ошибка инициализации нейросетей: {e}")


class UserQuery(BaseModel):
    user_id: str
    message: str


@app.post("/api/v1/bot/chat", summary="Режим Вопрос-Ответ (Чат-бот)")
async def chat_bot_endpoint(request: UserQuery):
    """Принимает сообщение от пользователя и возвращает готовый ответ или команду эскалации."""
    start_time = time.time()

    response = agent.process_query(request.message)
    process_time = time.time() - start_time

    # Требование ТЗ: время генерации менее 5 секунд
    if "ESCALATE" in response:
        return {
            "status": "escalated",
            "reply": "Перевожу диалог на оператора...",
            "generation_time_sec": round(process_time, 2)
        }

    return {
        "status": "success",
        "reply": response,
        "generation_time_sec": round(process_time, 2)
    }


@app.post("/api/v1/bot/sufler", summary="Режим Суфлер (Подсказки оператору)")
async def sufler_endpoint(request: UserQuery):
    """Слушает чат и генерирует черновик ответа для сотрудника техподдержки."""
    response = agent.process_query(request.message)
    if "ESCALATE" in response:
        return {"suggested_reply": None, "note": "Нет уверенного ответа в базе"}

    return {"suggested_reply": response}