"""Evidence-based human-readable interpretations of behavioral clusters."""

import json
import logging
import os

DEFAULT_CHAT_MODEL = "llama3.1:8b"
logger = logging.getLogger(__name__)


def _cluster_payload(profiles, amounts):
    feature_names = {
        "messages_count": "сообщений за сессию в среднем",
        "total_words": "слов за сессию в среднем",
        "avg_words_per_message": "слов в сообщении в среднем",
        "max_words_per_message": "максимум слов в одном сообщении в среднем по сессиям",
        "avg_char_len": "символов в сообщении в среднем",
        "unique_users": "участников в сессии в среднем",
        "duration_minutes": "длительность сессии в минутах в среднем",
        "message_rate": "сообщений в минуту в среднем",
    }
    payload = []

    for cluster_id in sorted(int(value) for value in profiles.index):
        profile = profiles.loc[cluster_id]
        metrics = {}
        for key, description in feature_names.items():
            if key in profile.index:
                value = float(profile[key])
                if value == value and abs(value) != float("inf"):
                    metrics[description] = round(value, 2)

        payload.append({
            "cluster_id": cluster_id,
            "session_count": int(amounts.get(cluster_id, 0)),
            "metrics": metrics,
        })
    return payload


def describe_behavior_clusters(profiles, amounts, model: str | None = None) -> list[dict]:
    """Name behavior groups using only their aggregated numeric metadata."""
    payload = _cluster_payload(profiles, amounts)
    if not payload:
        return []

    model = model or os.getenv("BEHAVIOR_LABEL_MODEL", os.getenv("TOPIC_LABEL_MODEL", DEFAULT_CHAT_MODEL))
    system_prompt = (
        "Ты даёшь поведенческую интерпретацию кластеров на основе агрегированных числовых метаданных. "
        "Тебе переданы только число сессий и средние значения признаков; текста переписки и её тем у тебя нет. "
        "Дай каждой группе короткое название на русском (2–6 слов) и одно предложение-объяснение, "
        "описывающие только форму общения: короткие или длинные сессии, редкий или интенсивный обмен, "
        "короткие или развёрнутые сообщения, небольшой или большой объём текста. Сравнивай значения "
        "между группами из входных данных. Не делай выводов о тематике разговоров, характерах, "
        "эмоциях, намерениях или отношениях участников. Не приписывай группам свойства, которых нельзя "
        "обосновать метриками. Используй конкретные формулировки вроде «Короткие редкие обмены» или "
        "«Долгие многословные разговоры», а не общие «Группа 1». "
        "Верни только JSON: {\"clusters\":[{\"cluster_id\":0,\"label\":\"...\","
        "\"interpretation\":\"...\"}]}; включи каждый cluster_id ровно один раз."
    )

    try:
        import ollama
    except ImportError as exc:
        raise RuntimeError("Не установлен Python-клиент Ollama. Выполните make install.") from exc

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            format="json",
            options={"temperature": 0.1, "num_predict": 512, "num_ctx": 4096},
        )
        result = json.loads(response.message.content)
        if not isinstance(result, dict) or not isinstance(result.get("clusters"), list):
            raise ValueError("ожидался JSON-объект со списком clusters")
    except ollama.ResponseError as exc:
        if exc.status_code == 404:
            raise RuntimeError(
                f"В Ollama не найдена LLM {model!r}. Загрузите её командой: ollama pull {model}"
            ) from exc
        raise RuntimeError(f"Ollama не смогла интерпретировать поведенческие группы: {exc.error}") from exc
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("Локальная LLM вернула некорректный формат интерпретаций кластеров") from exc
    except Exception as exc:
        raise RuntimeError(
            "Не удалось подключиться к Ollama. Запустите Ollama и проверьте локальный сервис."
        ) from exc

    descriptions = {}
    for item in result.get("clusters", []):
        try:
            cluster_id = int(item["cluster_id"])
            label = str(item["label"]).strip()
            interpretation = str(item["interpretation"]).strip()
        except (KeyError, TypeError, ValueError):
            continue
        if label and interpretation:
            descriptions[cluster_id] = {"label": label, "interpretation": interpretation}

    expected_ids = {cluster["cluster_id"] for cluster in payload}
    if expected_ids - descriptions.keys():
        raise RuntimeError("Локальная LLM не вернула интерпретации для всех поведенческих кластеров")

    return [
        {
            "cluster_id": cluster["cluster_id"],
            "session_count": cluster["session_count"],
            **descriptions[cluster["cluster_id"]],
        }
        for cluster in payload
    ]
