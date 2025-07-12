import json
import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai

load_dotenv()

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'categories.json')
PROMPT_FILE = os.path.join(os.path.dirname(__file__), 'gemini_prompt.txt')

app = FastAPI(title="Category Explorer API")


def load_data() -> Dict[str, Any]:
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_data(data: Dict[str, Any]) -> None:
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Category(BaseModel):
    case_studies: Optional[List[Dict[str, Any]]] = None
    category_name: Optional[str] = None
    category_persian_name: Optional[str] = None
    challenges: Optional[Dict[str, List[str]]] = None
    emerging_startups: Optional[List[Dict[str, str]]] = None
    full_feature_list: Optional[List[str]] = None
    kpis: Optional[List[str]] = None
    market_cap_score: Optional[int] = None
    market_leaders: Optional[Dict[str, List[Dict[str, str]]]] = None
    one_line_description: Optional[str] = None
    strengths_and_weaknesses: Optional[Dict[str, List[str]]] = None
    top_5_customer_types: Optional[List[str]] = None
    top_5_players: Optional[List[Dict[str, str]]] = None


@app.get("/categories")
async def list_categories(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    sort_by: Optional[str] = None,
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    search: Optional[str] = None,
):
    data = load_data()['categories']

    filters = {
        k: v for k, v in request.query_params.items()
        if k not in {"page", "page_size", "sort_by", "sort_order", "search"}
    }

    # Search
    if search:
        search_lower = search.lower()
        data = [item for item in data if search_lower in json.dumps(item, ensure_ascii=False).lower()]

    # Filtering
    for key, value in filters.items():
        data = [item for item in data if str(item.get(key)) == value]

    # Sorting
    if sort_by:
        data.sort(key=lambda x: x.get(sort_by), reverse=(sort_order == "desc"))

    total_items = len(data)
    start = (page - 1) * page_size
    end = start + page_size
    items = data[start:end]
    remaining = max(total_items - end, 0)
    has_next = end < total_items

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "remaining_items": remaining,
        "has_next": has_next,
    }


@app.get("/categories/{category_id}")
async def get_category(category_id: int):
    data = load_data()['categories']
    if not (0 <= category_id < len(data)):
        raise HTTPException(status_code=404, detail="Category not found")
    return data[category_id]


@app.post("/categories")
async def create_category(category: Category):
    data = load_data()
    data['categories'].append(category.model_dump(exclude_none=True))
    save_data(data)
    return {"message": "Category created", "id": len(data['categories']) - 1}


@app.put("/categories/{category_id}")
async def update_category(category_id: int, category: Category):
    data = load_data()
    if not (0 <= category_id < len(data['categories'])):
        raise HTTPException(status_code=404, detail="Category not found")
    existing = data['categories'][category_id]
    updated = category.model_dump(exclude_none=True)
    existing.update(updated)
    data['categories'][category_id] = existing
    save_data(data)
    return {"message": "Category updated"}


@app.delete("/categories/{category_id}")
async def delete_category(category_id: int):
    data = load_data()
    if not (0 <= category_id < len(data['categories'])):
        raise HTTPException(status_code=404, detail="Category not found")
    data['categories'].pop(category_id)
    save_data(data)
    return {"message": "Category deleted"}


@app.post("/categories/{category_id}/regenerate")
async def regenerate_category(category_id: int):
    data = load_data()['categories']
    if not (0 <= category_id < len(data)):
        raise HTTPException(status_code=404, detail="Category not found")

    category = data[category_id]
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        prompt = f.read()
    prompt = prompt.replace("\n{", f"\n{json.dumps(category, ensure_ascii=False, indent=2)}", 1)

    client = genai.Client()
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    try:
        new_data = json.loads(response.text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse Gemini response")
    return new_data


@app.get("/")
async def root():
    return {"message": "Category Explorer API"}
