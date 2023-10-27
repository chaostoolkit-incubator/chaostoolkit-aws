.PHONY: install
install:
	pip install --upgrade pip setuptools wheel
	pip install -r requirements.txt

.PHONY: install-dev
install-dev: install
	pip install -r requirements-dev.txt
	python setup.py develop

.PHONY: lint
lint:
	ruff chaosaws/ tests/
	isort --check-only --profile black chaosaws/ tests/
	black --check --diff chaosaws/ tests/

.PHONY: format
format:
	isort --profile black chaosaws/ tests/
	black chaosaws/ tests/
	ruff --fix chaosaws/ tests/

.PHONY: tests
tests:
	pytest
