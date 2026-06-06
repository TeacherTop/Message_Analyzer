# Аналитика переписок

Пет-проект для анализа экспортов Telegram в JSON-формате. Приложение считает базовую статистику по сообщениям, разбивает переписку на диалоговые сессии, строит поведенческие кластеры сессий и показывает семантические темы через BERTopic.

## Что умеет

- Парсит Telegram JSON export.
- Считает количество сообщений, пользователей и диалоговых сессий.
- Показывает активность по часам и дням недели.
- Делит переписку на сессии по паузе между сообщениями.
- Строит признаки сессий: длина, длительность, темп, автор начала диалога.
- Кластеризует сессии через KMeans.
- Визуализирует кластеры через UMAP.
- Извлекает темы переписки через BERTopic.

## Структура

```text
.
├── analytics/
│   └── analytics.py              # базовая статистика
├── base/
│   ├── main.py                   # FastAPI endpoint
│   ├── parser.py                 # парсер Telegram JSON
│   ├── sessionization.py         # разбиение на сессии
│   ├── feature_engineering.py    # признаки сообщений и сессий
│   ├── pipeline.py               # общий пайплайн обработки
│   └── streamlit_app.py          # Streamlit UI
├── ML/
│   ├── prepare_for_clustering.py # подготовка признаков
│   └── clustering.py             # KMeans и UMAP
├── DL/
│   └── BERTopic.py               # тематическое моделирование
└── Переписки/                    # локальные JSON-файлы переписок
```

## Установка

Проект рассчитан на Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Для BERTopic нужны русские стоп-слова NLTK. Если они не скачаны локально, выполните:

```bash
python -c "import nltk; nltk.download('stopwords')"
```

## Быстрый запуск

Основной сценарий запуска - один процесс Streamlit.

```bash
source .venv/bin/activate
make run
```

Если `make` недоступен, запустите напрямую:

```bash
source .venv/bin/activate
streamlit run base/streamlit_app.py
```

После этого откройте Streamlit-адрес из терминала и загрузите JSON-файл экспорта Telegram.

Семантические темы через BERTopic выключены по умолчанию, потому что это самая тяжелая часть обработки. Их можно включить в боковой панели приложения. UMAP-карту тоже можно выключить там же, если нужен более быстрый расчет.

## Дополнительный API-режим

FastAPI backend оставлен в проекте как дополнительный режим для будущего отдельного frontend или интеграций:

```bash
source .venv/bin/activate
make api
```

То же самое без `make`:

```bash
source .venv/bin/activate
uvicorn base.main:app --reload --host 127.0.0.1 --port 8000
```

## Формат входных данных

Ожидается JSON export из Telegram со структурой:

```json
{
  "messages": [
    {
      "id": 1,
      "type": "message",
      "date": "2026-01-01T12:00:00",
      "from": "User name",
      "text": "Message text"
    }
  ]
}
```

Поле `text` может быть строкой или списком Telegram text entities. Парсер приводит оба варианта к обычной строке.

## Приватность данных

Файлы реальных переписок не входят в репозиторий. Папка `Переписки/` добавлена в `.gitignore`, поэтому пользователь загружает свой Telegram JSON через интерфейс приложения.

## Быстрая проверка пайплайна

Если в папке `Переписки/` есть тестовый JSON, можно проверить базовую обработку без запуска UI:

```bash
python -c "import json; from base.pipeline import process_chat; data=json.load(open('Переписки/result_kotik.json')); stats, clusters, amount, umap, topics = process_chat(data, include_topics=False, include_umap=False); print(stats['overview']); print(amount.to_dict())"
```

Полный пайплайн может занять заметное время: UMAP строит двумерную проекцию кластеров, а BERTopic загружает sentence-transformer модель и обучает тематическую модель на сессиях.

## Текущие ограничения

- BERTopic может сильно замедлять обработку больших переписок, поэтому в Streamlit он включается отдельно.
- Количество кластеров KMeans сейчас фиксировано: `4`.
- UMAP и KMeans используют фиксированные параметры, которые стоит адаптировать для маленьких чатов.
- Медиа, стикеры и сообщения без текста попадают в общую статистику как сообщения с пустым текстом.
