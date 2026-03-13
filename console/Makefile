PYTHON=python3
VENV=.venv
REQ=requirements.txt

.PHONY: all run venv freeze clean

all: venv

venv:
	$(PYTHON) -m venv $(VENV)
	. $(VENV)/bin/activate && pip install --upgrade pip && pip install -r $(REQ)

run: venv
	. $(VENV)/bin/activate && python main.py

freeze:
	. $(VENV)/bin/activate && pip freeze > $(REQ)

clean:
	rm -rf $(VENV)

# Build executable with PyInstaller
exe: venv
	. $(VENV)/bin/activate && pip install pyinstaller && pyinstaller --onefile main.py --name shop_console
