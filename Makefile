.PHONY: run install migrate-create migrate-up migrate-down seed test docker-up docker-down

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --reload --port 8000

migrate-create:
	alembic revision --autogenerate -m "$(msg)"

migrate-up:
	alembic upgrade head

migrate-down:
	alembic downgrade -1

seed:
	python -m app.seed

test:
	pytest -v

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down -v
