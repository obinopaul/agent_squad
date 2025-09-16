SHELL=/usr/bin/env bash

# Conda environment name and Python version
ENV_NAME = dra
PYTHON_VERSION = 3.11

# Default goal
.DEFAULT_GOAL := help

# 🛠️ Remove Conda environment
.PHONY: clean
clean:
	conda remove -y --name $(ENV_NAME) --all

# 🛠️ Install dependencies using Poetry
.PHONY: install
install:
	@echo "Installing dependencies"
	pip install poetry
	pip install 'markitdown[all]'
	pip install "browser-use[memory]"==0.1.48

	@echo install playwright
	pip install playwright
	playwright install chromium --with-deps --no-shell

	@echo install dependencies
	poetry install

	@echo install xlrd
	pip install xlrd==2.0.1

install-requirements:
	@echo "Installing dependencies"
	pip install poetry
	pip install 'markitdown[all]'
	pip install "browser-use[memory]"==0.1.48

	@echo install playwright
	pip install playwright
	playwright install chromium --with-deps --no-shell

	@echo install dependencies
	pip install -r requirements.txt

	@echo install xlrd
	pip install xlrd==2.0.1

# 🛠️ Update dependencies using Poetry
.PHONY: update
update:
	poetry update

# 🛠️ Show available Makefile commands
.PHONY: help
help:
	@echo "Makefile commands:"
	@echo "  make create      - Create Conda environment and install Poetry"
	@echo "  make activate    - Show activation command"
	@echo "  make clean       - Remove Conda environment"
	@echo "  make install     - Install dependencies using Poetry"
	@echo "  make update      - Update dependencies using Poetry"
