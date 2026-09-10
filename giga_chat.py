from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

class SupportAgent:
    def __init__(self, kb_manager, credentials: str):
        self.kb = kb_manager
        self.llm = GigaChat(
            credentials=credentials,
            verify_ssl_certs=False,
            scope="GIGACHAT_API_PERS",
            model="GigaChat-3-Pro" # Оставляем Pro для максимальной адекватности ответов
        )

    def process_query(self, user_query: str) -> str:
        found_docs = self.kb.search_similar(user_query, top_k=3)
        if not found_docs:
            return "ESCALATE"

        # ПРОГРАММНАЯ ФИЛЬТРАЦИЯ ДУБЛИКАТОВ: оставляем только уникальные тексты
        unique_chunks = []
        for doc in found_docs:
            if doc.page_content not in unique_chunks:
                unique_chunks.append(doc.page_content)

        context = "\n\n".join(unique_chunks)

        # Жесткий промпт для предотвращения повторений
        system_prompt = f"""Ты — AI-агент техподдержки 1С (АО "Молвест").
Опирайся ТОЛЬКО на этот контекст:
{context}

ПРАВИЛА:
1. Сформулируй ОДИН емкий, понятный и вежливый ответ. Никогда не дублируй абзацы.
2. Если в контексте нет ответа — верни ровно одно слово: ESCALATE. Не придумывай решения от себя."""

        payload = Chat(
            messages=[
                Messages(role=MessagesRole.SYSTEM, content=system_prompt),
                Messages(role=MessagesRole.USER, content=user_query)
            ],
            temperature=0.1,
            max_tokens=700
        )

        try:
            response = self.llm.chat(payload)
            answer = response.choices[0].message.content
            if "ESCALATE" in answer.upper():
                return "ESCALATE"
            return answer
        except Exception as e:
            return f"ESCALATE (Системная ошибка: {e})"