"""Получение текстовых векторов через локальный Ollama."""

import os
import logging
import time

DEFAULT_EMBEDDING_MODEL = "qwen3-embedding:0.6b"
EMBEDDING_BATCH_SIZE = 32
logger = logging.getLogger(__name__)


def embed_texts(texts: list[str], model: str | None = None) -> list[list[float]]:
    """Преобразовать список текстов в векторы локальной embedding-моделью."""
    if not texts:
        return []
    if any(not isinstance(text, str) or not text.strip() for text in texts):
        raise ValueError("Для эмбеддингов нужны непустые строки")

    model = model or os.getenv("TOPIC_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
    try:
        import ollama
    except ImportError as exc:
        raise RuntimeError("Не установлен Python-клиент Ollama. Выполните make install.") from exc

    vectors = []
    batch_count = (len(texts) + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE
    logger.info("Building embeddings: texts=%d batches=%d model=%s", len(texts), batch_count, model)
    for batch_number, start in enumerate(range(0, len(texts), EMBEDDING_BATCH_SIZE), start=1):
        batch = texts[start:start + EMBEDDING_BATCH_SIZE]
        batch_started = time.perf_counter()
        try:
            response = ollama.embed(model=model, input=batch, truncate=True)
        except ollama.ResponseError as exc:
            if exc.status_code == 404:
                raise RuntimeError(
                    f"В Ollama нет модели {model!r}. Скачайте её командой: ollama pull {model}"
                ) from exc
            raise RuntimeError(f"Ollama не смог построить эмбеддинги: {exc.error}") from exc
        except Exception as exc:
            raise RuntimeError(
                "Не удалось подключиться к Ollama. Запустите приложение Ollama "
                "и проверьте, что локальный сервис доступен на http://127.0.0.1:11434."
            ) from exc

        batch_vectors = response.embeddings
        if len(batch_vectors) != len(batch):
            raise RuntimeError(
                f"Ollama вернул {len(batch_vectors)} векторов для {len(batch)} текстов"
            )
        vectors.extend([list(vector) for vector in batch_vectors])
        if batch_number == 1 or batch_number == batch_count or batch_number % 10 == 0:
            logger.info(
                "Embedding batch %d/%d finished in %.2fs",
                batch_number,
                batch_count,
                time.perf_counter() - batch_started,
            )

    if vectors and any(len(vector) != len(vectors[0]) for vector in vectors):
        raise RuntimeError("Ollama вернул эмбеддинги разной размерности")
    return vectors
