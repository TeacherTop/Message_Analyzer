from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import json
import sys
import os
from pathlib import Path

# Добавляем корневую директорию в пути поиска модулей, чтобы импорты из base работали
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base.pipeline import process_chat
from base.parser import build_df
from base.sessionization import make_sessions
from semantic_topics.sessions import build_session_documents
from semantic_topics.embeddings import embed_texts
from semantic_topics.clustering import extract_top_topics

app = FastAPI(title="Аналитика переписок API", version="1.0.0")
app.state.topics = []

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/upload-chat")
async def upload_chat(
    file: UploadFile = File(...),
    include_semantic: bool = True,
    include_behavior: bool = True,
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
        topics = []
        if include_semantic:
            session_messages = make_sessions(build_df(data), gap_minutes=30)
            session_documents = build_session_documents(session_messages)
            vectors = embed_texts([document["text"] for document in session_documents])
            if len(vectors) != len(session_documents):
                raise ValueError("Количество векторов не совпало с количеством сессий")
            vectorized_sessions = [
                {**document, "embedding": vector}
                for document, vector in zip(session_documents, vectors, strict=True)
            ]
            topics = extract_top_topics(vectorized_sessions)
        stats, clusters, amount, umap_b64, behavior_clusters = process_chat(
            data,
            include_umap=include_umap and include_behavior,
            include_behavior=include_behavior,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    # Replace the current in-memory corpus only after the new upload is processed.
    app.state.topics = topics
    
    return {
        **stats,
        "clusters": clusters.to_dict(),
        "amount": amount.to_dict(),
        "umap_image": umap_b64,
        "topics": topics,
        "behavior_clusters": behavior_clusters,
    }


if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def serve_frontend(path: str):
        requested_file = (FRONTEND_DIST / path).resolve()
        if path and requested_file.is_relative_to(FRONTEND_DIST) and requested_file.is_file():
            return FileResponse(requested_file)
        return FileResponse(FRONTEND_DIST / "index.html")
