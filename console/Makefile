PYTHON = python3
VENV = .venv

.PHONY: all venv run freeze clean build

all: run

venv:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt

run:
	$(VENV)/bin/python main.py

clean:
	rm -rf $(VENV)

build: venv
	$(VENV)/bin/pyinstaller --onefile main.py --name console