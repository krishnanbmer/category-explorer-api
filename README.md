# Category Explorer API

This project provides a small REST API to explore software categories stored in a JSON file.

## Features
- CRUD operations on categories
- Infinite scroll style listing with search and sorting
- Update categories in place
- Regenerate category content using Google Gemini API
- Swagger documentation via FastAPI

## Installation
1. Clone the repository and install dependencies:
   ```bash
   pip install fastapi uvicorn python-dotenv google-genai
   ```
2. Copy `.env.example` to `.env` and set `GEMINI_API_KEY` and other values if needed.

## Running
```
uvicorn app.main:app --reload --port $PORT
```
The API docs will be available at `http://localhost:$PORT/docs`.

## Upgrade
Update dependencies with:
```
pip install --upgrade fastapi uvicorn google-genai
```
