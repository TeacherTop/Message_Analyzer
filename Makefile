.PHONY: install run api

install:
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt

run:
	streamlit run base/streamlit_app.py

api:
	uvicorn base.main:app --reload --host 127.0.0.1 --port 8000
