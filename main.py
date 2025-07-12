import json
import os
from typing import List, Optional

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

load_dotenv()

app = FastAPI(
    title="FastAPI Categories API",
    description="A RESTful API for managing software categories.",
)

DB_FILE = "database.json"


def read_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)


def write_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)


class CaseStudy(BaseModel):
    description: str
    title: str
    type: str


class Challenges(BaseModel):
    economic: List[str]
    legal: List[str]
    security: List[str]
    technical: List[str]


class EmergingStartup(BaseModel):
    impact: str
    name: str


class MarketLeader(BaseModel):
    name: str
    url: str


class MarketLeaders(BaseModel):
    australia: List[MarketLeader]
    east_asia: List[MarketLeader]
    europe: List[MarketLeader]
    iran: List[MarketLeader]
    middle_east_excluding_iran: List[MarketLeader]
    usa: List[MarketLeader]


class StrengthsAndWeaknesses(BaseModel):
    strengths: List[str]
    weaknesses: List[str]


class TopPlayer(BaseModel):
    name: str
    website: str


class Category(BaseModel):
    case_studies: List[CaseStudy]
    category_name: str
    category_persian_name: str
    challenges: Challenges
    emerging_startups: List[EmergingStartup]
    full_feature_list: List[str]
    kpis: List[str]
    market_cap_score: int
    market_leaders: MarketLeaders
    one_line_description: str
    strengths_and_weaknesses: StrengthsAndWeaknesses
    top_5_customer_types: List[str]
    top_5_players: List[TopPlayer]


class PaginatedCategories(BaseModel):
    items: List[Category]
    total: int
    page: int
    size: int
    remaining: int


@app.get("/categories", response_model=PaginatedCategories)
def get_categories(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
    sort_by: Optional[str] = None,
    search: Optional[str] = None,
):
    db = read_db()
    categories = db["categories"]

    if search:
        categories = [
            c
            for c in categories
            if search.lower() in str(c).lower()
        ]

    if sort_by:
        categories = sorted(
            categories,
            key=lambda x: x.get(sort_by, ""),
            reverse=False,
        )

    total = len(categories)
    start = (page - 1) * size
    end = start + size
    paginated_categories = categories[start:end]

    return {
        "items": paginated_categories,
        "total": total,
        "page": page,
        "size": size,
        "remaining": total - end,
    }


@app.get("/categories/{category_id}", response_model=Category)
def get_category(category_id: int):
    db = read_db()
    categories = db["categories"]

    if category_id < 0 or category_id >= len(categories):
        raise HTTPException(status_code=404, detail="Category not found")

    return categories[category_id]


@app.put("/categories/{category_id}", response_model=Category)
def update_category(category_id: int, category: Category):
    db = read_db()
    categories = db["categories"]

    if category_id < 0 or category_id >= len(categories):
        raise HTTPException(status_code=404, detail="Category not found")

    categories[category_id] = category.dict()
    write_db(db)

    return category


@app.post("/categories/{category_id}/regenerate")
def regenerate_category(category_id: int):
    db = read_db()
    categories = db["categories"]

    if category_id < 0 or category_id >= len(categories):
        raise HTTPException(status_code=404, detail="Category not found")

    category = categories[category_id]

    try:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            f"""
            این یک دسته بندی از نرم افزارهای سایت https://www.capterra.com/categories است
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

            {json.dumps(category, indent=2, ensure_ascii=False)}

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
        )
        regenerated_data = json.loads(response.text)
        return regenerated_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
