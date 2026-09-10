from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole


class GigaVisionProcessor:
    def __init__(self, credentials: str):
        self.llm = GigaChat(
            credentials=credentials,
            verify_ssl_certs=False,
            scope="GIGACHAT_API_PERS",
            model="GigaChat-3-Pro"  # Pro лучше справляется с картинками
        )

    def analyze_image(self, image_path: str, prompt: str) -> str:
        try:
            # Загружаем картинку на сервер GigaChat
            with open(image_path, "rb") as image_file:
                uploaded_file = self.llm.upload_file(image_file, purpose="general")

            file_id = getattr(uploaded_file, 'id_', getattr(uploaded_file, 'id', None))
            if not file_id:
                return "Ошибка: Не удалось загрузить изображение."

            # Отправляем промпт с прикрепленной картинкой
            payload = Chat(
                messages=[
                    Messages(
                        role=MessagesRole.USER,
                        content=prompt,
                        attachments=[file_id]
                    )
                ],
                temperature=0.1
            )

            response = self.llm.chat(payload)
            return response.choices[0].message.content

        except Exception as e:
            return f"Ошибка при анализе изображения: {e}"