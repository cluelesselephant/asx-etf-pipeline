# Project notes for Claude Code

## Project
ELT pipeline: ASX ETF prices (yfinance API) and fund metadata (SFTP CSV) into Snowflake,
modelled with dbt into a star schema, reported in Power BI.

## Environment
- Windows, PowerShell, conda environment `etf` (Python 3.12)
- Run `conda activate etf` before any Python, pytest or dbt command

## Conventions
- Format and lint with ruff; type hints on all functions
- Never read, print or commit secrets: .env, *.p8 and *.pub stay local
- Config comes from environment variables via python-dotenv
- All loads must be idempotent (MERGE, or delete-insert in one transaction)
- Every new validation check needs a pytest case in tests/
- dbt: staging models are views, marts are tables; every key column gets unique and not_null tests

## Working style
- I'm learning: explain what each command does before running it
- Ask before installing packages or changing more than one file