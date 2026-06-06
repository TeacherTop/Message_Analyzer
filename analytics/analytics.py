def basic_stats(df, session_df):
    """
    Общая аналитика по сообщениям и диалоговым сессиям
    """

    df = df.copy()
    session_df = session_df.copy()

    return {

        # ==================================================
        # OVERVIEW
        # ==================================================

        "overview": {

            # общее количество сообщений
            "messages_total": len(df),

            # количество уникальных пользователей
            "users_total": df["sender"].nunique(),

            # общее количество диалоговых сессий
            "sessions_total": len(session_df),
        },

        # ==================================================
        # MESSAGE-LEVEL STATS
        # ==================================================

        "messages": {

            # сколько сообщений написал каждый пользователь
            "messages_per_user": (
                df["sender"]
                .value_counts()
                .to_dict()
            ),

            # среднее количество слов в сообщении
            "avg_word_count": round(
                df["word_count"].mean(), 2
            ),

            # средняя длина сообщения в символах
            "avg_char_length": round(
                df["char_len"].mean(), 2
            ),
        },

        # ==================================================
        # ACTIVITY
        # ==================================================

        "activity": {

            # активность по часам
            "activity_by_hour": (
                df.groupby("hour")
                .size()
                .to_dict()
            ),

            # активность по дням недели
            "activity_by_weekday": (
                df.groupby("weekday")
                .size()
                .to_dict()
            ),
        },

        # ==================================================
        # SESSION-LEVEL STATS
        # ==================================================

        "sessions": {

            # среднее количество сообщений в диалоге
            "avg_messages_per_session": round(
                session_df["messages_count"].mean(), 2
            ),

            # максимальное количество сообщений в диалоге
            "max_messages_in_session": int(
                session_df["messages_count"].max()
            ),

            # средняя длительность диалога
            "avg_session_duration_minutes": round(
                session_df["duration_minutes"].mean(), 2
            ),

            # максимальная длительность диалога
            "max_session_duration_minutes": round(
                session_df["duration_minutes"].max(), 2
            ),

            # кто чаще начинает диалог
            "session_starters": (
                session_df["started_by"]
                .value_counts()
                .to_dict()
            ),

            # средний темп сообщений
            "avg_message_rate": round(
                session_df["message_rate"].mean(), 4
            ),

            # распределение стартов диалогов по часам
            "session_start_hours": (
                session_df["start_hour"]
                .value_counts()
                .sort_index()
                .to_dict()
            ),
        },

        # ==================================================
        # USER BEHAVIOR INSIGHTS
        # ==================================================

        "users": {

            # среднее количество диалогов на пользователя
            "avg_sessions_per_user": round(
                len(session_df) / df["sender"].nunique(), 2
            ),

            # пользователь с максимальным количеством сообщений
            "most_active_user": (
                df["sender"]
                .value_counts()
                .idxmax()
            ),
        }
    }

