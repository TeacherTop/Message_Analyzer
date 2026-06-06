import pandas as pd

def build_df(data):

    messages = data.get("messages", [])

    rows = []

    for msg in messages:
        if msg.get("type") != "message":
            continue

        text = msg.get("text")

        if isinstance(text, list):
            text = "".join(
                part["text"] if isinstance(part, dict) else str(part)
                for part in text
            )

        rows.append({
            "id": msg.get("id"),
            "date": msg.get("date"),
            "sender": msg.get("from"),
            "text": text
        })

    df = pd.DataFrame(rows)

    df["date"] = pd.to_datetime(df["date"])

    return df