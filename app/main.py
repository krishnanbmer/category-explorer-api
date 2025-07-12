from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List, Any
from pathlib import Path
import json
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

DATA_FILE = Path(os.getenv('DATA_FILE', 'data.json'))
PORT = int(os.getenv('PORT', '8000'))

app = FastAPI(title="Category Explorer API")

# Initialize Gemini client (API key from environment)
client = genai.Client()


def read_db() -> dict:
    with open(DATA_FILE, encoding='utf-8') as f:
        return json.load(f)


def write_db(data: dict) -> None:
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.get("/")
def root():
    return {"message": "Category Explorer API"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/categories")
def list_categories(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
    sort_by: Optional[str] = None,
    order: str = Query("asc", regex="^(asc|desc)$"),
    search: Optional[str] = None,
    filter_field: Optional[str] = None,
    filter_value: Optional[str] = None,
):
    db = read_db()
    categories = db.get("categories", [])

    # search in any field
    if search:
        categories = [c for c in categories if search.lower() in json.dumps(c, ensure_ascii=False).lower()]

    # simple filter by exact match on a field
    if filter_field and filter_value:
        categories = [c for c in categories if str(c.get(filter_field, "")).lower() == filter_value.lower()]

    # sorting
    if sort_by:
        categories.sort(key=lambda x: x.get(sort_by), reverse=(order.lower() == "desc"))

    total = len(categories)
    start = (page - 1) * size
    end = start + size
    items = categories[start:end]
    has_more = end < total
    remaining = total - end if end < total else 0

    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "has_more": has_more,
        "remaining": remaining,
    }


@app.get("/categories/{cat_id}")
def get_category(cat_id: int):
    db = read_db()
    categories = db.get("categories", [])
    if cat_id < 0 or cat_id >= len(categories):
        raise HTTPException(status_code=404, detail="Category not found")
    return categories[cat_id]


@app.put("/categories/{cat_id}")
def update_category(cat_id: int, payload: dict):
    db = read_db()
    categories = db.get("categories", [])
    if cat_id < 0 or cat_id >= len(categories):
        raise HTTPException(status_code=404, detail="Category not found")
    categories[cat_id].update(payload)
    write_db(db)
    return categories[cat_id]


@app.post("/categories/{cat_id}/regenerate")
def regenerate_category(cat_id: int):
    db = read_db()
    categories = db.get("categories", [])
    if cat_id < 0 or cat_id >= len(categories):
        raise HTTPException(status_code=404, detail="Category not found")
    category = categories[cat_id]

    prompt = f"""
    این یک دسته بندی از نرم افزارهای سایت https://www.capterra.com/categories است
این دسته بندی را بررسی بکن و در سطح اینترنت جستجو بکن و اطلاعات کامل از این دسته بندی نرم افزار و سیستم های دیجیتال 
به دست بیار و موارد زیر را پیدا کن
... (remaining Persian prompt from instructions) ...
"""
    prompt = prompt.replace("... (remaining Persian prompt from instructions) ...", json.dumps(category, ensure_ascii=False))

    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return json.loads(response.text)
