.PHONY: install config install-dev lint format quality clean pip-clean nuke-venv run build release default

#----- setup -----
install:
	pip install -e .

config:
	teledm config

install-dev:
	pip install -e .[dev]

#----- Code quality -----
# Linting and Imports
lint:
	ruff check --fix .

# formatting
format:
	black .

# Run all quality checks
quality: lint format

#----- Build & Release -----
build: clean
	python -m build

release: build
	twine upload dist/*

#----- Misc -----
clean:
	rm -rf build dist *.egg-info __pycache__ .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -exec rm -f {} +
	find . -type f -name "*.pyo" -exec rm -f {} +
	find . -type f -name "*~" -exec rm -f {} +
	find . -type f -name ".DS_Store" -exec rm -f {} +

pip-clean:
	pip uninstall -y TeleDM
	pip cache purge

nuke-venv:
	@echo "WARNING: This will attempt to uninstall ALL packages in your vEnv."
	@echo "Press Ctrl+C to abort in the next 5 seconds..."
	@sleep 5
	pip freeze | grep -v "@" | cut -d= -f1 | xargs pip uninstall -y
	pip freeze | cut -d' ' -f1 | xargs pip uninstall -y

run:
	teledm

default: # Listing the make commands
	@echo "Makefile commands:"
	@echo "  install        - Install the package"
	@echo "  install-dev    - Install the package with development dependencies"
	@echo "  lint           - Run code linting and fix issues"
	@echo "  format         - Format code using black"
	@echo "  quality        - Run all code quality checks (lint and format)"
	@echo "  build          - Build the package for distribution"
	@echo "  release        - Build and upload the package to PyPI"
	@echo "  clean          - Clean build artifacts and caches"
	@echo "  pip-clean      - Uninstall the package and clear pip cache"
	@echo "  nuke-venv      - Uninstall all packages in the current virtual environment"
	@echo "  run            - Run the TeleDM application"
