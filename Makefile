# Variables
ENV_NAME = alrawdha_match
PYTHON_VER = 3.10
REQ_FILE = requirements.txt

# Default target
.DEFAULT_GOAL := help

## Create conda environment and install dependencies
env:
	conda create -y -n $(ENV_NAME) python=$(PYTHON_VER)
	conda run -n $(ENV_NAME) pip install -r $(REQ_FILE)

## Update environment from requirements.txt
update:
	conda run -n $(ENV_NAME) pip install -r $(REQ_FILE)

## Create credentials .env and .json files
credentials:
	touch matching-service-account.json

	touch .env
	@echo "# Google Sheets / Form integration" > .env
	@echo "SERVICE_ACCOUNT_FILE = 'matching-service-account.json'" >> .env
	@echo "RAW_SHEET_NAME =           # Your Form response google sheets " >> .env
	@echo "PROC_SHEET_NAME =           # Initially blanc google sheet to store processed data" >> .env
	@echo "" >> testing.py
	@echo "# Gmail credentials for sending emails" >> .env
	@echo "GMAIL_USER = " >> .env
	@echo "GMAIL_APP_PASSWORD =           # Replace with your app password" >> .env
	@echo ".env file and matching-service-account.json created fill in your actual credentials. For more information, see README.md."

	touch .flake8


## Run your main Python script (change main.py to your entry file)
run:
	conda run -n $(ENV_NAME) python workflow.py

## Run your pdf formation python script
pdf:
	conda run -n $(ENV_NAME) python pdf_formation.py

## Run tests with pytest (assumes tests/ directory)
test:
	conda run -n $(ENV_NAME) pytest tests/

## Run linting with flake8
lint:
	conda run -n $(ENV_NAME) flake8 *.py || true

## Format code with black
format:
	conda run -n $(ENV_NAME) black *.py

## Remove caches and temp files
clean:
	rm -rf __pycache__ */__pycache__ .pytest_cache .mypy_cache .coverage

## Remove conda environment
clean-env:
	conda env remove -n $(ENV_NAME)

## Show help
help:
	@grep -E '^##' Makefile | sed 's/## //'
