import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler


def prepare_sessions_for_clustering(session_df: pd.DataFrame):
    """
    Подготавливает session_df для кластеризации.

    Что делает:
    -------------
    1. Удаляет datetime колонки
    2. Кодирует категориальные признаки (One-Hot Encoding)
    3. Преобразует циклическое время (hour -> sin/cos)
    4. Нормализует признаки через StandardScaler

    Возвращает:
    -------------
    X_scaled_df : pd.DataFrame
        Готовые для ML нормализованные признаки

    scaler : StandardScaler
        Обученный scaler

    processed_df : pd.DataFrame
        DataFrame ДО нормализации
    """

    # =====================================
    # COPY
    # =====================================

    df = session_df.copy()

    # =====================================
    # CYCLICAL HOUR ENCODING
    # =====================================

    if "start_hour" in df.columns:

        df["hour_sin"] = np.sin(
            2 * np.pi * df["start_hour"] / 24
        )

        df["hour_cos"] = np.cos(
            2 * np.pi * df["start_hour"] / 24
        )

        df = df.drop(columns=["start_hour"])

    # =====================================
    # DROP DATETIME
    # =====================================

    datetime_cols = df.select_dtypes(
        include=["datetime"]
    ).columns

    df = df.drop(columns=datetime_cols)

    # =====================================
    # ONE HOT ENCODING
    # =====================================

    categorical_cols = df.select_dtypes(
        include=["object", "string"]
    ).columns

    if len(categorical_cols) > 0:

        df = pd.get_dummies(
            df,
            columns=categorical_cols,
            drop_first=False
        )

    # =====================================
    # BOOL -> INT
    # =====================================

    bool_cols = df.select_dtypes(include="bool").columns

    if len(bool_cols) > 0:
        df[bool_cols] = df[bool_cols].astype(int)

    # =====================================
    # SCALE
    # =====================================

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(df)

    X_scaled_df = pd.DataFrame(
        X_scaled,
        columns=df.columns
    )

    return X_scaled_df, scaler, session_df