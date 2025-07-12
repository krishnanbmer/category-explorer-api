# Category Explorer API

This project provides a simple REST API using **FastAPI** to explore and manage software categories stored in a JSON file.

## Features

- List categories with pagination (infinite scroll style), sorting, searching and filtering
- Retrieve a category by its index
- Update a category in place
- Regenerate category details using **Gemini** API
- Health check endpoint
- Interactive API docs via Swagger

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your `GEMINI_API_KEY` and preferred `PORT`.

## Running

```bash
uvicorn app.main:app --reload --port $PORT
```

API documentation will be available at `http://localhost:$PORT/docs`.

## Upgrade

To upgrade dependencies:

```bash
pip install -U -r requirements.txt
```
