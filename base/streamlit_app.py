import streamlit as st
import os
import sys
import json
import pandas as pd
import plotly.express as px
import base64

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base.pipeline import process_chat

# =========================================
# PAGE CONFIG
# =========================================

st.set_page_config(
    page_title="Аналитика чатов",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Кастомный CSS для "осовременивания" интерфейса
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    div[data-testid="stExpander"] {
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Аналитика чатов")


# =========================================
# FILE UPLOAD
# =========================================

uploaded_file = st.file_uploader(
    "Загрузите чат в JSON формате",
    type=["json"]
)

include_topics = st.sidebar.checkbox(
    "Искать темы через BERTopic",
    value=False,
    help="Медленная семантическая обработка. При первом запуске может загружать модель."
)

include_umap = st.sidebar.checkbox(
    "Строить UMAP-карту",
    value=True,
    help="Визуализация кластеров. Можно выключить для более быстрого расчета."
)


# =========================================
# HELPERS
# =========================================

def to_number(x):
    """убираем numpy float64 и приводим к норм типу"""
    return float(x)


# =========================================
# PROCESS FILE
# =========================================

if uploaded_file is not None:

    try:
        chat_data = json.loads(uploaded_file.getvalue().decode("utf-8"))

        with st.spinner("Обрабатываем переписку..."):
            stats, clusters, amount, umap_b64, topics = process_chat(
                chat_data,
                include_topics=include_topics,
                include_umap=include_umap
            )

        data = {
            **stats,
            "clusters": clusters.to_dict(),
            "amount": amount.to_dict(),
            "umap_image": umap_b64,
            "topics": topics
        }

        st.success("Файл успешно обработан")

        # ==================================================
        # OVERVIEW
        # ==================================================

        overview = data["overview"]

        st.subheader("📌 Overview")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Сообщений",
                overview["messages_total"]
            )

        with col2:
            st.metric(
                "Пользователей",
                overview["users_total"]
            )

        with col3:
            st.metric(
                "Диалогов",
                overview["sessions_total"]
            )

        # ==================================================
        # MESSAGES BLOCK
        # ==================================================

        st.subheader("💬 Аналитика по всем сообщениям")

        messages = data["messages"]

        col1, col2 = st.columns(2)

        with col1:
            st.write("📊 Сообщения по пользователям")

            df_users = pd.DataFrame({
                "Пользователь": list(messages["messages_per_user"].keys()),
                "Кол-во сообщений": list(messages["messages_per_user"].values())
            })

            st.dataframe(df_users)

        with col2:
            st.metric(
                "Среднее количество слов в сообщении",
                round(to_number(messages["avg_word_count"]), 2)
            )

            st.metric(
                "Среднее количество символов в сообщении",
                round(to_number(messages["avg_char_length"]), 2)
            )

        # ==================================================
        # ACTIVITY CHARTS
        # ==================================================

        st.subheader("⏱ Активность по всем сообщениям")

        activity = data["activity"]

        col1, col2 = st.columns(2)

        # -------- hour chart --------
        with col1:
            hour_df = pd.DataFrame({
                "Час": list(activity["activity_by_hour"].keys()),
                "Сообщения": list(activity["activity_by_hour"].values())
            })
            hour_df["Час"] = hour_df["Час"].astype(int)
            hour_df = hour_df.sort_values("Час")

            fig = px.bar(
                hour_df, 
                x="Час", 
                y="Сообщения",
                title="Активность по часам",
                color_discrete_sequence=['#636EFA']
            )
            fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

        # -------- weekday chart --------
        with col2:
            order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            weekday_data = activity["activity_by_weekday"]
            weekday_df = (
                pd.DataFrame(list(weekday_data.items()), columns=["День недели", "Сообщения"])
                .assign(weekday_cat=lambda x: pd.Categorical(x["День недели"], categories=order, ordered=True))
                .sort_values("weekday_cat")
            )

            fig = px.bar(
                weekday_df, 
                x="День недели", 
                y="Сообщения",
                title="Активность по дням недели",
                color_discrete_sequence=['#EF553B']
            )
            fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

        # ==================================================
        # SESSIONS BLOCK
        # ==================================================

        st.subheader("🧠 Аналитика по диалогам")

        sessions = data["sessions"]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Сред сообщений / сессию",
                round(to_number(sessions["avg_messages_per_session"]), 2)
            )

        with col2:
            st.metric(
                "Сред длительность (мин)",
                round(to_number(sessions["avg_session_duration_minutes"]), 2)
            )

        with col3:
            st.metric(
                "Темп сообщений",
                round(to_number(sessions["avg_message_rate"]), 3)
            )

        # session starters
        st.write("👥 Кто начинает диалоги")

        df_sess_start = pd.DataFrame({
            "Пользователь": list(sessions["session_starters"].keys()),
            "Кол-во начинаний диалогов": list(sessions["session_starters"].values())
        })

        st.dataframe(df_sess_start)

        # session start hours
        st.write("🕐 Начало диалогов по часам")

        session_start_hours_df = pd.DataFrame(
            list(sessions["session_start_hours"].items()),
            columns=["Час", "Количество диалогов"]
        )

        session_start_hours_df["Час"] = session_start_hours_df["Час"].astype(int)
        session_start_hours_df = session_start_hours_df.sort_values("Час")

        fig = px.line(
            session_start_hours_df, 
            x="Час", 
            y="Количество диалогов",
            title="Когда начинаются диалоги",
            markers=True,
            line_shape="spline",
            color_discrete_sequence=['#00CC96']
        )
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        # ==================================================
        # CLUSTERS + UMAP
        # ==================================================

        if "clusters" in data and "amount" in data:
            st.divider()
            st.subheader("🔎 Поведенческая кластеризация (без семантики) - Мета-данные (время, длина, скорость)")

            # render amount (counts per cluster)
            st.write("📊 Количество диалогов в кластерах")
            try:
                amount_series = pd.Series(data["amount"])
                amount_df = amount_series.reset_index()
                amount_df.columns = ["Кластер", "Количество диалогов"]
                st.dataframe(amount_df, hide_index=True)
                
            except Exception as e:
                st.error(f"Ошибка отрисовки кол-ва: {e}")

            # render clusters table
            st.write("📈 Средние характеристики кластеров")
            try:
                df_clusters = pd.DataFrame(data["clusters"])
                # Transpose if it's index-oriented (features as index)
                # Usually we want clusters as rows, features as columns
                st.dataframe(df_clusters)
            except Exception as e:
                st.error(f"Ошибка отрисовки таблицы: {e}")

        # UMAP
        if data.get("umap_image"):
            st.subheader("🗺 Визуализация кластеров (UMAP)")
            try:
                umap_bytes = base64.b64decode(data["umap_image"])
                st.image(umap_bytes, use_container_width=True)
            except Exception as e:
                st.error(f"Ошибка отрисовки UMAP: {e}")

        # Semantic Topics (BERTopic)
        if data.get("topics"):
            st.divider()
            st.subheader("📝 Семантическая кластеризация (BERTopic)")
            st.write("Модель нашла наиболее часто обсуждаемые темы в переписке (независимо от поведения):")
            
            for t_id, t_info in data["topics"].items():
                # t_info теперь словарь с keywords и count
                with st.expander(f"Тема №{t_id} ({t_info['count']} сообщений)"):
                    st.write(f"**Ключевые слова:** {t_info['keywords']}")


    except json.JSONDecodeError:
        st.error("Не удалось прочитать JSON. Проверьте, что загружен экспорт Telegram в JSON-формате.")
    except Exception as e:
        st.error(f"Ошибка обработки файла: {e}")
