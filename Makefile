.PHONY: setup run test lint format typecheck dashboard web clean all

PYTHON ?= python
PIP ?= $(PYTHON) -m pip
LINT_PATHS = main.py src/ ai/ tests/ dashboard/ scripts/ flows/

setup:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Setup complete"

run:
	$(PYTHON) -m src.pipeline
	@echo "Pipeline finished - exports in data/exports/"

test:
	$(PYTHON) -m pytest tests/ -q

lint:
	ruff check $(LINT_PATHS)
	ruff format --check $(LINT_PATHS)

format:
	ruff check --fix $(LINT_PATHS)
	ruff format $(LINT_PATHS)

typecheck:
	mypy main.py src/ ai/

dashboard:
	streamlit run dashboard/app.py --server.headless true

web:
	$(PYTHON) -m uvicorn main:app --reload

clean:
	$(PYTHON) scripts/clean.py

all: setup run test
