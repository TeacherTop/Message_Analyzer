import pandas as pd


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["hour"] = df["date"].dt.hour
    df["weekday"] = df["date"].dt.day_name()
    df["day_of_week"] = df["date"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"] >= 5

    return df


def add_text_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # длина сообщения в символах
    df["char_len"] = df["text"].fillna("").astype(str).str.len()

    # количество слов
    df["word_count"] = (
        df["text"]
        .fillna("")
        .astype(str)
        .str.split()
        .str.len()
    )

    return df

def build_session_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    1 строка = 1 диалоговая сессия
    """

    df = df.copy()

    # группировка по диалогам
    g = df.groupby("session_id")

    session_df = pd.DataFrame({

        # количество сообщений в диалоге
        "messages_count": g.size(),

        # суммарное количество слов
        "total_words": g["word_count"].sum(),

        # средняя длина сообщения
        "avg_words_per_message": g["word_count"].mean(),

        # максимальная длина сообщения
        "max_words_per_message": g["word_count"].max(),

        # средняя длина сообщения в символах
        "avg_char_len": g["char_len"].mean(),

        # ----------------------------
        # USERS
        # ----------------------------

        # сколько уникальных участников
        "unique_users": g["sender"].nunique(),

        # ----------------------------
        # TIME
        # ----------------------------

        # начало диалога
        "start_time": g["date"].min(),

        # конец диалога
        "end_time": g["date"].max(),

        # стартовый час
        "start_hour": g["hour"].first(),
    })

    # ----------------------------
    # SESSION DURATION
    # ----------------------------

    session_df["duration_minutes"] = (
        session_df["end_time"] - session_df["start_time"]
    ).dt.total_seconds() / 60

    # ----------------------------
    # MESSAGE RATE
    # ----------------------------

    # защита от деления на 0
    session_df["message_rate"] = (
        session_df["messages_count"] /
        (session_df["duration_minutes"] + 1)
    )

    #Кто начал диалог
    session_starters = g.first()["sender"]

    session_df["started_by"] = session_starters

    return session_df






def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Главная функция feature engineering пайплайна
    """

    df = add_time_features(df)
    df = add_text_features(df)

    session_df = build_session_features(df)

    return df, session_df