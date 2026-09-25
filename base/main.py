from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import sys
import os

# Добавляем корневую директорию в пути поиска модулей, чтобы импорты из base работали
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base.pipeline import process_chat

app = FastAPI(title="Аналитика переписок API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/upload-chat")  # если кто-то отправит файл на /upload-chat, запусти функцию ниже
async def upload_chat(
    file: UploadFile = File(...),
    include_topics: bool = False,
    include_umap: bool = True,
):
    contents = await file.read()  # открыть и прочитать файл
    try:
        data = json.loads(contents.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Файл должен быть корректным UTF-8 JSON") from exc

    if not isinstance(data, dict) or not isinstance(data.get("messages"), list):
        raise HTTPException(status_code=400, detail="Ожидается Telegram JSON export с массивом messages")

    try:
        stats, clusters, amount, umap_b64, topics = process_chat(
            data,
            include_topics=include_topics,
            include_umap=include_umap,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    
    return {
        **stats,
        "clusters": clusters.to_dict(),
        "amount": amount.to_dict(),
        "umap_image": umap_b64,
        "topics": topics
    }
