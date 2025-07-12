# Category Explorer API

A FastAPI service that provides access to software category data stored in `data.json`.

## Features
- Infinite scroll listing of categories with sorting, searching and filtering.
- Retrieve, create, update and delete categories.
- Regenerate a category using Google Gemini API.
- Swagger documentation available at `/docs` when the server is running.

## Installation
1. Clone the repository.
2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and set `GEMINI_API_KEY` and `PORT`.

## Running
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Upgrade dependencies
```bash
pip install -U -r requirements.txt
```
