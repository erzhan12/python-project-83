install:
	poetry install

dev:
	poetry run flask --app page_analyzer:app run

lint:
	poetry run flake8 page_analyzer

test:
	poetry run pytest

PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

.PHONY: install dev lint test start