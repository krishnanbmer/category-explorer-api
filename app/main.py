import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os

# Load env vars
load_dotenv()
DB_PATH = Path(os.getenv("JSON_DB_PATH", "data/categories.json"))
PORT = int(os.getenv("PORT", 8000))

app = FastAPI(title="Category Explorer API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def read_db() -> Dict[str, Any]:
    with DB_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_db(data: Dict[str, Any]):
    with DB_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Category(BaseModel):
    case_studies: List[Dict[str, Any]]
    category_name: str
    category_persian_name: Optional[str] = None
    challenges: Dict[str, List[str]]
    emerging_startups: List[Dict[str, Any]]
    full_feature_list: List[str]
    kpis: List[str]
    market_cap_score: int
    market_leaders: Dict[str, List[Dict[str, str]]]
    one_line_description: str
    strengths_and_weaknesses: Dict[str, List[str]]
    top_5_customer_types: List[str]
    top_5_players: List[Dict[str, str]]


class CategoryUpdate(BaseModel):
    case_studies: Optional[List[Dict[str, Any]]] = None
    category_name: Optional[str] = None
    category_persian_name: Optional[str] = None
    challenges: Optional[Dict[str, List[str]]] = None
    emerging_startups: Optional[List[Dict[str, Any]]] = None
    full_feature_list: Optional[List[str]] = None
    kpis: Optional[List[str]] = None
    market_cap_score: Optional[int] = None
    market_leaders: Optional[Dict[str, List[Dict[str, str]]]] = None
    one_line_description: Optional[str] = None
    strengths_and_weaknesses: Optional[Dict[str, List[str]]] = None
    top_5_customer_types: Optional[List[str]] = None
    top_5_players: Optional[List[Dict[str, str]]] = None


@app.get("/categories")
def list_categories(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    search: Optional[str] = Query(None),
):
    data = read_db()
    categories = data.get("categories", [])

    if search:
        lower = search.lower()
        categories = [c for c in categories if lower in json.dumps(c, ensure_ascii=False).lower()]

    if sort_by:
        categories.sort(key=lambda x: x.get(sort_by), reverse=(sort_order == "desc"))

    total = len(categories)
    start = (page - 1) * limit
    end = start + limit
    items = categories[start:end]
    remaining = max(total - end, 0)

    return {
        "items": items,
        "page": page,
        "limit": limit,
        "remaining": remaining,
        "total": total,
    }


@app.get("/categories/{category_id}")
def get_category(category_id: int):
    data = read_db()
    categories = data.get("categories", [])
    if category_id < 0 or category_id >= len(categories):
        raise HTTPException(status_code=404, detail="Category not found")
    return categories[category_id]


@app.post("/categories", status_code=201)
def create_category(category: Category):
    data = read_db()
    categories = data.setdefault("categories", [])
    categories.append(category.dict())
    write_db(data)
    return {"id": len(categories) - 1, **category.dict()}


@app.put("/categories/{category_id}")
def update_category(category_id: int, payload: CategoryUpdate):
    data = read_db()
    categories = data.get("categories", [])
    if category_id < 0 or category_id >= len(categories):
        raise HTTPException(status_code=404, detail="Category not found")
    for key, value in payload.dict(exclude_unset=True).items():
        categories[category_id][key] = value
    write_db(data)
    return categories[category_id]


@app.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int):
    data = read_db()
    categories = data.get("categories", [])
    if category_id < 0 or category_id >= len(categories):
        raise HTTPException(status_code=404, detail="Category not found")
    categories.pop(category_id)
    write_db(data)
    return JSONResponse(status_code=204)


# Gemini regeneration endpoint
try:
    from google import genai
except Exception:
    genai = None


@app.post("/categories/{category_id}/regenerate")
def regenerate_category(category_id: int):
    if genai is None:
        raise HTTPException(status_code=500, detail="google-genai not installed")

    data = read_db()
    categories = data.get("categories", [])
    if category_id < 0 or category_id >= len(categories):
        raise HTTPException(status_code=404, detail="Category not found")

    category = categories[category_id]
    prompt_template = (
        "این یک دسته بندی از نرم افزارهای سایت https://www.capterra.com/categories است\n"
        "این دسته بندی را بررسی بکن و در سطح اینترنت جستجو بکن و اطلاعات کامل از این دسته بندی نرم افزار و سیستم های دیجیتال\n"
        "به دست بیار و موارد زیر را پیدا کن\n"
        "..."  # abbreviated in prompt for brevity
    )
    prompt = f"{prompt_template}\n{json.dumps({'categories':[category]}, ensure_ascii=False)}"

    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt
    )
    try:
        new_data = json.loads(response.text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse response from Gemini")

    return new_data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
