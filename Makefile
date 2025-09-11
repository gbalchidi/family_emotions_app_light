.PHONY: help install run test lint format clean docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install      Install dependencies"
	@echo "  make run         Run the bot locally"
	@echo "  make test        Run tests"
	@echo "  make lint        Run linters"
	@echo "  make format      Format code"
	@echo "  make clean       Clean cache files"
	@echo "  make docker-up   Start bot with Docker"
	@echo "  make docker-down Stop Docker containers"

install:
	pip install poetry
	poetry install

run:
	poetry run python -m src.main

test:
	poetry run pytest tests/ -v --cov=src

lint:
	poetry run flake8 src tests
	poetry run mypy src

format:
	poetry run black src tests
	poetry run isort src tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f bot