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
│   ├── main.py                   # FastAPI backend
│   ├── parser.py                 # парсер Telegram JSON
│   ├── sessionization.py         # разбиение на сессии
│   ├── feature_engineering.py    # признаки сообщений и сессий
│   └── pipeline.py               # общий пайплайн обработки
├── frontend/                     # Vercel frontend
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

## Локальный запуск

Установите frontend-зависимости и запустите API и интерфейс в двух терминалах:

```bash
make install
npm --prefix frontend install
```

Терминал 1 — FastAPI:

```bash
make api
```

Терминал 2 — frontend:

```bash
make frontend
```

Для локальной работы задайте `VITE_API_URL=http://127.0.0.1:8000` в `frontend/.env.local`.

## Деплой

Проект рассчитан на два сервиса:

- Render запускает FastAPI из корневого `render.yaml`.
- Vercel собирает интерфейс из `frontend/` по корневому `vercel.json`.

После создания Render Web Service добавьте в настройках Vercel переменную окружения `VITE_API_URL` со значением публичного адреса Render-сервиса, например `https://chat-analytics-api.onrender.com`. Затем запустите redeploy Vercel, чтобы адрес попал в сборку frontend.

Проверить API можно по `/health`; интерактивная документация доступна по `/docs`.

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

Файлы реальных переписок не входят в репозиторий. Загруженный JSON передаётся на Render для анализа и не записывается приложением на диск.

## Быстрая проверка пайплайна

Если в папке `Переписки/` есть тестовый JSON, можно проверить базовую обработку без запуска UI:

```bash
python -c "import json; from base.pipeline import process_chat; data=json.load(open('Переписки/result_kotik.json')); stats, clusters, amount, umap, topics = process_chat(data, include_topics=False, include_umap=False); print(stats['overview']); print(amount.to_dict())"
```

Полный пайплайн может занять заметное время: UMAP строит двумерную проекцию кластеров, а BERTopic загружает sentence-transformer модель и обучает тематическую модель на сессиях.

## Текущие ограничения

- BERTopic может сильно замедлять обработку больших переписок, поэтому в интерфейсе он включается отдельно.
- Количество кластеров KMeans сейчас фиксировано: `4`.
- UMAP и KMeans используют фиксированные параметры, которые стоит адаптировать для маленьких чатов.
- Медиа, стикеры и сообщения без текста попадают в общую статистику как сообщения с пустым текстом.
