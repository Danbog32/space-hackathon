.PHONY: dev reqs install lint typecheck clean

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

reqs:
	pip freeze > requirements.txt

install:
	pip install -r requirements.txt

lint:
	ruff check app/

typecheck:
	mypy app/ --ignore-missing-imports

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf *.index *.faiss metadata.json

