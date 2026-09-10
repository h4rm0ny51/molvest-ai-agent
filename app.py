import streamlit as st
import os
import pandas as pd

from kb_manager import KnowledgeBaseManager
from giga_chat import SupportAgent
from vision_giga import GigaVisionProcessor

st.set_page_config(page_title="AI-Агент Молвест", page_icon="🤖", layout="wide")
st.title("🤖 Интеллектуальная поддержка 1С")

# --- ИНИЦИАЛИЗАЦИЯ ДАННЫХ АНАЛИТИКИ В ПАМЯТИ ---
if "analytics" not in st.session_state:
    st.session_state.analytics = {
        "auto_percent": "38%",
        "auto_delta": "+5% за неделю",
        "time_sec": "2.1",
        "time_delta": "-0.3 сек",
        "escalations": "62%",
        "esc_delta": "-5% за неделю",
        "chart_data": pd.DataFrame(
            {"Обращения": [45, 20, 15, 10, 10]},
            index=["Ошибки входа/Пароли", "Закрытие месяца", "Справочники и документы", "Печатные формы", "Прочее"]
        ),
        "is_empty": False
    }

with st.sidebar:
    st.header("⚙️ Доступ")
    api_token = st.text_input("Токен GigaChat API:", type="password")


@st.cache_resource
def load_system(token):
    kb = KnowledgeBaseManager()
    agent = SupportAgent(kb_manager=kb, credentials=token)
    vision = GigaVisionProcessor(credentials=token)
    return kb, agent, vision


if api_token:
    kb, agent, vision = load_system(api_token)

    # Создаем логические вкладки
    tab_chat, tab_kb, tab_metrics = st.tabs(["💬 Чат-бот", "📚 Управление Базой", "📊 Аналитика"])

    # --- ВКЛАДКА 1: ЧАТ ---
    with tab_chat:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        chat_image = st.file_uploader("Прикрепить скриншот", type=['png', 'jpg', 'jpeg'])

        if prompt := st.chat_input("Опишите проблему..."):
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                with st.spinner("Анализ..."):
                    final_prompt = prompt
                    if chat_image:
                        img_path = chat_image.name
                        with open(img_path, "wb") as f:
                            f.write(chat_image.getbuffer())
                        vision_text = vision.analyze_image(img_path, prompt="Выпиши текст ошибки с экрана.")
                        final_prompt = f"Вопрос: {prompt}\n\nСкриншот: {vision_text}"
                        os.remove(img_path)

                    response = agent.process_query(final_prompt)

                    if "ESCALATE" in response:
                        ui_res = "⚠️ **Ответ не найден (уверенность < 80%).**\n\n*Эскалация на оператора.*"
                        st.error(ui_res)
                        st.session_state.messages.append({"role": "assistant", "content": ui_res})
                    else:
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})

    # --- ВКЛАДКА 2: БАЗА ЗНАНИЙ ---
    with tab_kb:
        st.subheader("Управление памятью агента")

        # Кнопка для автоочистки базы, истории чата и аналитики
        if st.button("🗑️ Очистить базу знаний и сбросить данные"):
            kb.clear_database()

            # Очищаем историю сообщений
            st.session_state.messages = []

            # Обнуляем метрики в дашборде
            st.session_state.analytics = {
                "auto_percent": "0%",
                "auto_delta": "0%",
                "time_sec": "0.0",
                "time_delta": "0 сек",
                "escalations": "0%",
                "esc_delta": "0%",
                "chart_data": pd.DataFrame({"Обращения": []}),
                "is_empty": True
            }

            # Принудительно перезагружаем страницу, чтобы обновить интерфейс
            st.rerun()

        st.markdown("---")
        uploaded_file = st.file_uploader("Загрузить новую инструкцию (PDF, DOCX, MD, HTML)",
                                         type=['docx', 'pdf', 'md', 'html'])

        if uploaded_file is not None:
            temp_path = uploaded_file.name
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with st.spinner("Векторизация документа..."):
                kb.load_document(temp_path)
            st.success(f"Материалы из '{temp_path}' добавлены в память нейросети!")
            os.remove(temp_path)

    # --- ВКЛАДКА 3: МЕТРИКИ ---
    with tab_metrics:
        st.subheader("Показатели эффективности AI-агента")
        col1, col2, col3 = st.columns(3)

        # Берем актуальные данные из состояния сессии
        data = st.session_state.analytics

        col1.metric(label="Автоматизировано обращений", value=data["auto_percent"], delta=data["auto_delta"])
        col2.metric(
            label="Среднее время ответа (с)",
            value=data["time_sec"],
            delta=data["time_delta"],
            delta_color="off" if data["is_empty"] else "inverse"
        )
        col3.metric(
            label="Эскалаций на оператора",
            value=data["escalations"],
            delta=data["esc_delta"],
            delta_color="off" if data["is_empty"] else "inverse"
        )

        st.divider()
        st.markdown("**Распределение тематик обращений**")

        # Если данные очищены, показываем заглушку, иначе — рисуем график
        if data["is_empty"]:
            st.info("📊 Нет данных для отображения. База знаний была очищена.")
        else:
            st.bar_chart(data["chart_data"])

else:
    st.info("👈 Введите токен GigaChat для запуска системы.")