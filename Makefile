.PHONY: install
install:
	pip install -r requirements.txt

.PHONY: install-dev
install-dev: install
	pip install -r requirements-dev.txt
	python setup.py develop

.PHONY: lint
lint:
	flake8 chaosaws/ tests/
	isort --check-only --profile black chaosaws/ tests/
	black --check --diff chaosaws/ tests/

.PHONY: format
format:
	isort --profile black chaosaws/ tests/
	black chaosaws/ tests/

.PHONY: tests
tests:
	pytest
