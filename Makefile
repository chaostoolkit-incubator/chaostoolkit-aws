# run this first in order not to mess up with your local python dependencies
start-venv:
	pipenv shell

# needs to be ran before tests can be run
setup:
	python3 setup.py develop

pip-install:
	pip3 install -r requirements.txt

pip-install-dev: pip-install
	pip3 install -r requirements-dev.txt

pip-clean:
	pipenv clean

pip-clean-install: pip-clean pip-install

pip-install-all: pip-install pip-install-dev

# be sure to run setup target first
test:
	pytest