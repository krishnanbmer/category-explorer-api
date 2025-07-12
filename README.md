# Category Explorer API

This project provides a simple REST API built with FastAPI to explore and manage software categories stored in a JSON file. It also integrates with the Gemini API to regenerate category information.

## Features

- List categories with pagination, filtering, searching and sorting.
- Retrieve, create, update and delete categories.
- Regenerate category details through Gemini API.
- Swagger UI documentation at `/docs` when running the server.

## Installation

```bash
pip install -r requirements.txt
```

## Running

Create a `.env` file based on `.env.example` and set your `GEMINI_API_KEY` and optional `PORT`.

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Updating Dependencies

```
pip install -U -r requirements.txt
```

