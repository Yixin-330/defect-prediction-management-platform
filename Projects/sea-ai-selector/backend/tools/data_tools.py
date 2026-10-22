"""
Tools — function-based tools callable by Sub-Agents.
In production, these would call real APIs / databases.
"""
import random
from datetime import datetime, timedelta

# ── Shopee / E-commerce Data Tools ──

def get_hot_search_categories(country: str = "id", limit: int = 20) -> list[dict]:
    """Fetch hot search categories from Shopee."""
    pool = {
        "id": [
            {"category": "手机配件", "icon": "📱", "heat": 98, "growth": 15.2},
            {"category": "穆斯林服饰", "icon": "👗", "heat": 95, "growth": 22.8},
            {"category": "美妆工具", "icon": "💄", "heat": 91, "growth": 8.5},
            {"category": "家居收纳", "icon": "🏠", "heat": 88, "growth": 18.3},
            {"category": "小型家电", "icon": "🔌", "heat": 86, "growth": 10.1},
            {"category": "母婴用品", "icon": "🍼", "heat": 84, "growth": 6.7},
            {"category": "运动户外", "icon": "⚽", "heat": 81, "growth": 14.0},
            {"category": "宠物用品", "icon": "🐾", "heat": 79, "growth": 25.3},
            {"category": "食品饮料", "icon": "🍜", "heat": 76, "growth": 5.4},
            {"category": "汽配摩托", "icon": "🏍️", "heat": 74, "growth": 12.8},
        ],
        "th": [
            {"category": "美妆护肤", "icon": "💄", "heat": 96, "growth": 11.0},
            {"category": "手机配件", "icon": "📱", "heat": 93, "growth": 9.2},
            {"category": "家居收纳", "icon": "🏠", "heat": 90, "growth": 16.5},
            {"category": "宠物用品", "icon": "🐾", "heat": 87, "growth": 28.0},
            {"category": "运动户外", "icon": "⚽", "heat": 85, "growth": 18.7},
        ],
        "vn": [
            {"category": "健康食品", "icon": "🥗", "heat": 94, "growth": 20.1},
            {"category": "小型家电", "icon": "🔌", "heat": 91, "growth": 13.4},
            {"category": "母婴用品", "icon": "🍼", "heat": 88, "growth": 9.8},
            {"category": "手机配件", "icon": "📱", "heat": 86, "growth": 7.5},
            {"category": "美妆工具", "icon": "💄", "heat": 83, "growth": 12.3},
        ],
        "ph": [
            {"category": "手机配件", "icon": "📱", "heat": 95, "growth": 14.0},
            {"category": "家居收纳", "icon": "🏠", "heat": 89, "growth": 20.5},
            {"category": "美妆工具", "icon": "💄", "heat": 86, "growth": 11.2},
            {"category": "食品零食", "icon": "🍪", "heat": 82, "growth": 8.3},
            {"category": "宠物用品", "icon": "🐾", "heat": 78, "growth": 22.0},
        ],
        "my": [
            {"category": "穆斯林服饰", "icon": "👗", "heat": 97, "growth": 18.5},
            {"category": "手机配件", "icon": "📱", "heat": 92, "growth": 10.0},
            {"category": "母婴用品", "icon": "🍼", "heat": 88, "growth": 12.8},
            {"category": "家居收纳", "icon": "🏠", "heat": 85, "growth": 15.2},
            {"category": "美妆护肤", "icon": "💄", "heat": 82, "growth": 9.5},
        ],
        "sg": [
            {"category": "高端美妆", "icon": "💄", "heat": 93, "growth": 11.5},
            {"category": "进口食品", "icon": "🍫", "heat": 90, "growth": 8.0},
            {"category": "母婴高端", "icon": "🍼", "heat": 87, "growth": 14.2},
            {"category": "家居收纳", "icon": "🏠", "heat": 84, "growth": 16.8},
            {"category": "宠物用品", "icon": "🐾", "heat": 80, "growth": 20.0},
        ],
    }
    rows = pool.get(country, pool["id"])
    for r in rows:
        r.update({
            "competition": random.choice(["高", "中", "低"]),
            "avg_price_usd": round(random.uniform(2.5, 35), 2),
            "score": min(99, r["heat"] - random.randint(0, 5) + (r["growth"] // 5)),
        })
    return rows[:limit]


def get_competitor_products(category: str = None, platform: str = None, limit: int = 15) -> list[dict]:
    """Search competitor products across platforms."""
    base = [
        {"product": "Type-C快充数据线 2米", "platform": "Shopee", "price": 3.99, "sales": 23500, "rating": 4.8, "reviews": 12400, "features": ["快充", "耐用编织线", "2米长度"], "strategy": "捆绑销售·买二送一"},
        {"product": "Silk Hijab Premium", "platform": "Shopee", "price": 8.50, "sales": 18200, "rating": 4.9, "reviews": 15800, "features": ["丝绸质感", "30色可选", "防滑设计"], "strategy": "INS网红推广"},
        {"product": "LED化妆镜 带补光", "platform": "Lazada", "price": 12.99, "sales": 15600, "rating": 4.6, "reviews": 8900, "features": ["USB充电", "三档调光", "折叠便携"], "strategy": "功能差异化定价"},
        {"product": "折叠收纳箱 66L", "platform": "Shopee", "price": 5.99, "sales": 14200, "rating": 4.7, "reviews": 11200, "features": ["免安装", "可叠放", "带盖防尘"], "strategy": "多件优惠装"},
        {"product": "迷你小风扇 USB充电", "platform": "Tokopedia", "price": 2.99, "sales": 12800, "rating": 4.5, "reviews": 9800, "features": ["超静音", "三档风速", "桌面夹式"], "strategy": "超低价引流+配件盈利"},
        {"product": "穆斯林长袍 Abaya", "platform": "Lazada", "price": 22.00, "sales": 11500, "rating": 4.9, "reviews": 7500, "features": ["高端面料", "定制尺码", "刺绣工艺"], "strategy": "高端品牌定位"},
        {"product": "不锈钢保温杯 500ml", "platform": "Shopee", "price": 6.50, "sales": 10800, "rating": 4.7, "reviews": 8200, "features": ["12小时保温", "304不锈钢", "多色可选"], "strategy": "IP联名限量款"},
        {"product": "瑜伽垫 加厚防滑", "platform": "Lazada", "price": 15.00, "sales": 9500, "rating": 4.8, "reviews": 6300, "features": ["环保TPE材质", "6mm加厚", "含背带"], "strategy": "直播教学+带货"},
        {"product": "便携式挂烫机", "platform": "Shopee", "price": 11.50, "sales": 8800, "rating": 4.6, "reviews": 5200, "features": ["手持便携", "快速预热", "干湿两用"], "strategy": "差异化颜色+赠品"},
        {"product": "儿童硅胶餐盘", "platform": "Shopee", "price": 7.99, "sales": 7600, "rating": 4.8, "reviews": 4800, "features": ["食品级硅胶", "分区设计", "吸盘防翻"], "strategy": "母婴KOL种草"},
    ]
    if category:
        base = [c for c in base if any(kw in c["product"] for kw in category.split(" "))]
    if platform:
        base = [c for c in base if c["platform"].lower() == platform.lower()]
    for c in base:
        c["competitiveness"] = "强" if c["sales"] > 15000 else "中" if c["sales"] > 8000 else "弱"
    return base[:limit]


def get_price_trend(product: str, days: int = 30) -> list[float]:
    """Simulate price trend data."""
    base = random.uniform(5, 25)
    return [round(base + random.uniform(-1.5, 1.0), 2) for _ in range(days)]


def search_1688_suppliers(product_keyword: str) -> list[dict]:
    """Search 1688.com for wholesale prices."""
    supplier_pool = [
        {"supplier": "义乌市XX日用品厂", "price_cny": 28.5, "moq": 100, "rating": 4.8},
        {"supplier": "广州XX贸易有限公司", "price_cny": 35.0, "moq": 50, "rating": 4.6},
        {"supplier": "深圳市XX科技有限公司", "price_cny": 42.0, "moq": 200, "rating": 4.7},
        {"supplier": "汕头XX塑胶制品厂", "price_cny": 22.0, "moq": 500, "rating": 4.5},
        {"supplier": "浙江XX家居用品有限公司", "price_cny": 31.0, "moq": 80, "rating": 4.9},
    ]
    return supplier_pool


def get_logistics_cost(country: str, weight_kg: float = 0.3) -> dict:
    """Estimate logistics cost (CNY) by country."""
    rates = {
        "id": {"first_kg": 22, "additional_kg": 12, "days": "7-12"},
        "th": {"first_kg": 18, "additional_kg": 10, "days": "5-8"},
        "vn": {"first_kg": 16, "additional_kg": 9, "days": "5-8"},
        "ph": {"first_kg": 20, "additional_kg": 11, "days": "7-10"},
        "my": {"first_kg": 15, "additional_kg": 8, "days": "4-7"},
        "sg": {"first_kg": 14, "additional_kg": 7, "days": "3-5"},
    }
    r = rates.get(country, rates["id"])
    cost = r["first_kg"] + max(0, weight_kg - 1) * r["additional_kg"]
    return {"cost_cny": round(cost, 2), "estimated_days": r["days"]}


def get_platform_fees(platform: str, price_cny: float) -> dict:
    """Calculate platform commission and fees."""
    fees_table = {
        "shopee": {"commission": 0.05, "payment_fee": 0.02, "service_fee": 0.03},
        "lazada": {"commission": 0.06, "payment_fee": 0.02, "service_fee": 0.02},
        "tokopedia": {"commission": 0.055, "payment_fee": 0.015, "service_fee": 0.025},
        "tiktok": {"commission": 0.05, "payment_fee": 0.02, "service_fee": 0.025},
    }
    f = fees_table.get(platform, fees_table["shopee"])
    return {
        "commission_cny": round(price_cny * f["commission"], 2),
        "payment_fee_cny": round(price_cny * f["payment_fee"], 2),
        "service_fee_cny": round(price_cny * f["service_fee"], 2),
        "total_fees_cny": round(price_cny * (f["commission"] + f["payment_fee"] + f["service_fee"]), 2),
    }


# ── Market Data Tools ──

def get_gmv_by_country() -> dict:
    """Total GMV share across SEA countries."""
    return {
        "countries": ["印度尼西亚", "泰国", "越南", "菲律宾", "马来西亚", "新加坡"],
        "shares": [38, 22, 16, 12, 8, 4],
        "total_gmv_est_billion_usd": 58.6,
        "month": "2026-05",
    }


def get_market_summary(country: str) -> dict:
    """Overall market health summary for a country."""
    summaries = {
        "id": {"active_sellers": 520000, "daily_orders": 1800000, "avg_ticket": 8.5, "growth_yoy": 0.18},
        "th": {"active_sellers": 280000, "daily_orders": 950000, "avg_ticket": 12.0, "growth_yoy": 0.22},
        "vn": {"active_sellers": 180000, "daily_orders": 720000, "avg_ticket": 7.5, "growth_yoy": 0.25},
        "ph": {"active_sellers": 120000, "daily_orders": 580000, "avg_ticket": 6.8, "growth_yoy": 0.16},
        "my": {"active_sellers": 95000, "daily_orders": 350000, "avg_ticket": 14.5, "growth_yoy": 0.12},
        "sg": {"active_sellers": 45000, "daily_orders": 180000, "avg_ticket": 22.0, "growth_yoy": 0.10},
    }
    return summaries.get(country, summaries["id"])


def get_currency_rate(country: str) -> dict:
    """Simulate live FX rate (1 CNY = X local currency)."""
    rates = {
        "id": {"code": "IDR", "rate": 2200, "symbol": "Rp"},
        "th": {"code": "THB", "rate": 4.95, "symbol": "฿"},
        "vn": {"code": "VND", "rate": 3500, "symbol": "₫"},
        "ph": {"code": "PHP", "rate": 7.85, "symbol": "₱"},
        "my": {"code": "MYR", "rate": 0.65, "symbol": "RM"},
        "sg": {"code": "SGD", "rate": 0.19, "symbol": "S$"},
    }
    return rates.get(country, rates["id"])


__all__ = [
    "get_hot_search_categories",
    "get_competitor_products",
    "get_price_trend",
    "search_1688_suppliers",
    "get_logistics_cost",
    "get_platform_fees",
    "get_gmv_by_country",
    "get_market_summary",
    "get_currency_rate",
]
