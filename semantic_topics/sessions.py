"""Подготовка диалоговых сессий для тематической группировки."""

import pandas as pd


def build_session_documents(messages: pd.DataFrame) -> list[dict]:
    """Вернуть по одному текстовому документу на каждую сессию.

    Ожидает сообщения с колонками id, date, sender, text и session_id.
    Границы сессий должны быть предварительно выставлены make_sessions.
    """
    required_columns = {"id", "date", "sender", "text", "session_id"}
    missing_columns = required_columns.difference(messages.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Не хватает колонок для документов сессий: {missing}")

    documents = []
    for session_id, session in messages.groupby("session_id", sort=True):
        session = session.sort_values("date")
        text_lines = []
        for row in session.itertuples(index=False):
            text = " ".join(str(row.text or "").split())
            if text:
                sender = str(row.sender or "Неизвестный участник")
                text_lines.append(f"{sender}: {text}")

        combined_text = "\n".join(text_lines)
        if not combined_text:
            continue

        start_date = session["date"].min()
        end_date = session["date"].max()
        documents.append({
            "text": combined_text,
            "session_id": int(session_id),
            "date_start": start_date.isoformat() if pd.notna(start_date) else None,
            "date_end": end_date.isoformat() if pd.notna(end_date) else None,
            "participants": sorted({
                str(sender) for sender in session["sender"].dropna() if str(sender).strip()
            }),
            "message_ids": [
                message_id.item() if hasattr(message_id, "item") else message_id
                for message_id in session["id"].dropna().tolist()
            ],
        })

    return documents
