PYTHON ?= python3
VENV := .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python
UVICORN := $(VENV)/bin/uvicorn

$(VENV)/bin/activate: requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt
	touch $(VENV)/bin/activate

install: $(VENV)/bin/activate

api: install
	$(UVICORN) app.main:app --reload --port 8000

demo: install
	$(PY) -m scripts.demo_negociacion

clean:
	rm -rf $(VENV) **/__pycache__

.PHONY: install api demo clean
