from fastapi import FastAPI, UploadFile, File
import json
import sys
import os

# Добавляем корневую директорию в пути поиска модулей, чтобы импорты из base работали
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base.pipeline import process_chat

app = FastAPI()


@app.post("/upload-chat")  # если кто-то отправит файл на /upload-chat, запусти функцию ниже
async def upload_chat(file: UploadFile = File(...)):
    contents = await file.read()  # открыть и прочитать файл
    data = json.loads(contents.decode("utf-8"))  # превращает данные в структуру: ключ → значение

    stats, clusters, amount, umap_b64, topics = process_chat(data)
    
    return {
        **stats,
        "clusters": clusters.to_dict(),
        "amount": amount.to_dict(),
        "umap_image": umap_b64,
        "topics": topics
    }