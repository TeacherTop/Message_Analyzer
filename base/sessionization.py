import pandas as pd

def make_sessions(df, gap_minutes=30):
    df = df.copy()
    df = df.sort_values("date")

    df["time_diff"] = df["date"].diff()

    df["new_session"] = df["time_diff"] > pd.Timedelta(minutes=gap_minutes)

    # базовая сессия
    df["session_id"] = df["new_session"].cumsum()

    return df