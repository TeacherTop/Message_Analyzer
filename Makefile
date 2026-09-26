.PHONY: install frontend api app

install:
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt

frontend:
	npm --prefix frontend run dev -- --host 127.0.0.1

api:
	uvicorn base.main:app --reload --host 127.0.0.1 --port 8000

app: build
	uvicorn base.main:app --host 127.0.0.1 --port 8000

build:
	npm --prefix frontend run build
