import json
import os
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from dotenv import load_dotenv
from google import genai

load_dotenv()
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

app = FastAPI(title="Category Explorer API")

# Utility functions

def load_data() -> Dict[str, Any]:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data: Dict[str, Any]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class CategoryModel(BaseModel):
    class Config:
        extra = "allow"

class UpdateCategoryModel(BaseModel):
    class Config:
        extra = "allow"

PROMPT_TEMPLATE = """
\tاین یک دسته بندی از نرم افزارهای سایت https://www.capterra.com/categories است
این دسته بندی را بررسی بکن و در سطح اینترنت جستجو بکن و اطلاعات کامل از این دسته بندی نرم افزار و سیستم های دیجیتال 
به دست بیار و موارد زیر را پیدا کن

توضیح یک خطی با این مضمون که نرم افزارها و سیستم ها در این دسته بندی چطور سیستم هایی هستند و به چه کاری می آیند و برای چی هستند
5 تا از بهترین و معروفترین و بزرگترین بازیگران این دسته بندی به همراه لینک وبسایت
5 تا از بهترین انواع مشتریان این سیستم ها که وجود چنین سیستم هایی برای آنها ضروری است
یک امتیاز از 0 تا 20 به مارکت کپ و بزرگی بازار محصولات این دسته بندی
قویترین سیستم یا شرکت که در این دسته بندی محصول دارد یا خدمات ارائه میدهد و بیشترین سهم بازار این دسته بندی را دارد را بطور جداگانه در ایران  و آمریکا و اروپا و آسیای شرقی و استرالیا و خاورمیانه به جز ایران پیدا کن و نام ببر
نقاط قوت و نقاط ضعف
لیست تمام قابلیت ها بطور کامل به طوری که هیچ کدام از 
چند مثال عملی (مثلاً یک یا دو مورد) از کاربردهای واقعی موفق یا ناموفق این سیستم‌ها را در قالب کیس استادی بررسی کنید.
چالش‌های فنی، امنیتی، اقتصادی و قانونی احتمالی که این سیستم‌ها با آنها مواجه‌اند را بررسی کنید.
شاخص‌های کلیدی که برای سنجش عملکرد این سیستم‌ها در کسب‌وکار استفاده می‌شوند را ذکر کنید.
استارتاپ‌ها یا شرکت‌های نوظهور که اخیراً وارد این حوزه شده‌اند و تأثیرگذار هستند را شناسایی کنید.
تمام این موارد را درون یک قالب json قرار بده و به عنوان خروجی یک آبجکت json را بده
قالب json باید دقیقه دقیق بدون هیچ کم و کاستی شبیه این json باشد:
{...}
هیچ گونه اطلاعات پس و پیش اضافه تری نگو چون من می خواهم از این جیسان در کد استفاده کنم و هر اطلاعات دیگری کد من را خراب می کند
نکات زیر را توجه کن و دقیق رعایت کن:
Full_feature_list
باید کامل باید و همه قابلیت های نرم افزارهای این دسته بندی باشد چه قابلیت های کلیدی و چه غیر کلیدی به طوری که هیچ قابلیتی از قلم نیفته
تاکید می کنم همه قابلیت ها حتی اگر یک هزار قابلیت بود
خروجی باید فقط در قالب json ای که دادم باشد
اطلاعات باید دقیق و کامل باشد
اطلاعات توضیحی و مشروح باید به زبان فارسی روان باشد اما کلمات تخصصی و مخفف ها نباید به فارسی ترجمه شوند
هر جایی که نیاز به قراردادن لینک بود باید در دیتاهای json لینک آن را هم قرار بدی
تاکید میکنم تمام خروجی تو باید فقط و تنها یک json باشد 
"""

# Endpoints

@app.get("/categories")
def get_categories(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    filter_field: Optional[str] = None,
    filter_value: Optional[str] = None,
):
    data = load_data()
    categories = data.get("categories", [])

    if search:
        categories = [c for c in categories if search.lower() in json.dumps(c, ensure_ascii=False).lower()]

    if filter_field and filter_value is not None:
        categories = [c for c in categories if str(c.get(filter_field, "")).lower() == filter_value.lower()]

    if sort_by:
        categories.sort(key=lambda x: x.get(sort_by))
        if sort_order == "desc":
            categories.reverse()

    total_items = len(categories)
    total_pages = (total_items + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    items = categories[start:end]
    has_next = end < total_items

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": has_next,
    }

@app.get("/categories/{category_id}")
def get_category(category_id: int):
    data = load_data()
    try:
        return data["categories"][category_id]
    except IndexError:
        raise HTTPException(status_code=404, detail="Category not found")

@app.post("/categories", status_code=201)
def create_category(category: CategoryModel):
    data = load_data()
    data.setdefault("categories", []).append(category.dict())
    save_data(data)
    return {"id": len(data["categories"]) - 1, **category.dict()}

@app.put("/categories/{category_id}")
def update_category(category_id: int, update: UpdateCategoryModel):
    data = load_data()
    try:
        current = data["categories"][category_id]
    except IndexError:
        raise HTTPException(status_code=404, detail="Category not found")
    current.update(update.dict(exclude_unset=True))
    data["categories"][category_id] = current
    save_data(data)
    return current

@app.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int):
    data = load_data()
    try:
        data["categories"].pop(category_id)
    except IndexError:
        raise HTTPException(status_code=404, detail="Category not found")
    save_data(data)
    return

@app.post("/categories/{category_id}/regenerate")
def regenerate_category(category_id: int):
    data = load_data()
    try:
        category = data["categories"][category_id]
    except IndexError:
        raise HTTPException(status_code=404, detail="Category not found")

    prompt = PROMPT_TEMPLATE + "\n" + json.dumps(category, ensure_ascii=False)
    client = genai.Client()
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    try:
        regenerated = json.loads(response.text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid response from Gemini")
    return regenerated
