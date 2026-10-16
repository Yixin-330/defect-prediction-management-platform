"""
Agent Communication Schemas — Structured Output definitions for all Sub-Agents.
Each schema is a JSON Schema dict passed to Claude's structured output tool_use.
"""

# ── Trend Agent ──

TREND_AGENT_SCHEMA = {
    "name": "trend_analysis_result",
    "schema": {
        "type": "object",
        "properties": {
            "market_summary": {
                "type": "object",
                "properties": {
                    "country": {"type": "string"},
                    "analysis_date": {"type": "string"},
                    "hot_categories_count": {"type": "integer"},
                    "avg_order_daily_est": {"type": "integer"},
                    "avg_ticket_usd": {"type": "number"},
                },
                "required": ["country", "hot_categories_count"],
            },
            "category_rankings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "rank": {"type": "integer"},
                        "category": {"type": "string"},
                        "icon": {"type": "string"},
                        "search_heat": {"type": "integer"},
                        "growth_rate_30d": {"type": "number"},
                        "competition_level": {
                            "type": "string",
                            "enum": ["高", "中", "低"],
                        },
                        "avg_price_usd": {"type": "number"},
                        "main_countries": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "recommendation_score": {"type": "integer"},
                    },
                    "required": ["category", "search_heat", "growth_rate_30d", "competition_level"],
                },
            },
            "key_findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "insight": {"type": "string"},
                        "evidence": {"type": "string"},
                        "impact": {"type": "string", "enum": ["high", "medium", "low"]},
                    },
                    "required": ["insight", "evidence", "impact"],
                },
            },
        },
        "required": ["market_summary", "category_rankings", "key_findings"],
    },
}

# ── Competitor Agent ──

COMPETITOR_AGENT_SCHEMA = {
    "name": "competitor_analysis_result",
    "schema": {
        "type": "object",
        "properties": {
            "overview": {
                "type": "object",
                "properties": {
                    "total_monitored": {"type": "integer"},
                    "new_competitors": {"type": "integer"},
                    "price_changes": {"type": "integer"},
                    "avg_price_usd": {"type": "number"},
                },
                "required": ["total_monitored", "new_competitors"],
            },
            "competitors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "product_name": {"type": "string"},
                        "platform": {"type": "string", "enum": ["Shopee", "Lazada", "Tokopedia", "TikTok Shop"]},
                        "price_usd": {"type": "number"},
                        "monthly_sales_est": {"type": "integer"},
                        "rating": {"type": "number"},
                        "review_count": {"type": "integer"},
                        "price_competitiveness": {"type": "string", "enum": ["强", "中", "弱"]},
                        "key_features": {"type": "array", "items": {"type": "string"}},
                        "selling_strategy": {"type": "string"},
                        "strength_score": {"type": "integer"},
                    },
                    "required": ["product_name", "platform", "price_usd", "monthly_sales_est"],
                },
            },
            "niche_opportunities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "gap_description": {"type": "string"},
                        "market_potential": {"type": "string", "enum": ["high", "medium", "low"]},
                        "entry_difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
                        "suggested_approach": {"type": "string"},
                    },
                    "required": ["gap_description", "market_potential"],
                },
            },
        },
        "required": ["overview", "competitors", "niche_opportunities"],
    },
}

# ── Recommend Agent ──

RECOMMEND_AGENT_SCHEMA = {
    "name": "recommendation_result",
    "schema": {
        "type": "object",
        "properties": {
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "rank": {"type": "integer"},
                        "product_name": {"type": "string"},
                        "icon": {"type": "string"},
                        "target_market": {"type": "string"},
                        "reasoning": {"type": "string"},
                        "score": {"type": "integer"},
                        "roi_estimate": {"type": "string"},
                        "risk_level": {"type": "string", "enum": ["极低", "低", "中", "高"]},
                        "strategy_type": {
                            "type": "string",
                            "enum": ["蓝海品类", "爆品策略", "利润策略", "差异化策略"],
                        },
                        "estimated_cost_cny": {"type": "number"},
                        "estimated_profit_cny": {"type": "number"},
                        "confidence": {"type": "number"},
                    },
                    "required": ["product_name", "target_market", "reasoning", "score", "roi_estimate"],
                },
            },
            "strategy_advice": {
                "type": "object",
                "properties": {
                    "core_strategy": {"type": "string"},
                    "quick_wins": {"type": "array", "items": {"type": "string"}},
                    "risks_to_watch": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["core_strategy"],
            },
        },
        "required": ["recommendations", "strategy_advice"],
    },
}

# ── Profit Agent ──

PROFIT_AGENT_SCHEMA = {
    "name": "profit_analysis_result",
    "schema": {
        "type": "object",
        "properties": {
            "cost_breakdown": {
                "type": "object",
                "properties": {
                    "purchase_cost_cny": {"type": "number"},
                    "logistics_cny": {"type": "number"},
                    "warehousing_cny": {"type": "number"},
                    "platform_commission_cny": {"type": "number"},
                    "payment_fee_cny": {"type": "number"},
                    "ad_cost_cny": {"type": "number"},
                    "return_loss_cny": {"type": "number"},
                    "total_cost_cny": {"type": "number"},
                },
                "required": ["purchase_cost_cny", "logistics_cny", "total_cost_cny"],
            },
            "revenue": {
                "type": "object",
                "properties": {
                    "selling_price_local": {"type": "number"},
                    "selling_price_cny_equiv": {"type": "number"},
                    "currency": {"type": "string"},
                },
                "required": ["selling_price_local", "selling_price_cny_equiv"],
            },
            "profit_summary": {
                "type": "object",
                "properties": {
                    "profit_per_unit_cny": {"type": "number"},
                    "profit_margin_pct": {"type": "number"},
                    "roi_pct": {"type": "number"},
                    "health_status": {"type": "string", "enum": ["健康", "一般", "偏低", "危险"]},
                },
                "required": ["profit_per_unit_cny", "profit_margin_pct"],
            },
            "scenarios": {
                "type": "object",
                "properties": {
                    "optimistic": {"type": "number"},
                    "realistic": {"type": "number"},
                    "pessimistic": {"type": "number"},
                },
                "required": ["optimistic", "realistic", "pessimistic"],
            },
        },
        "required": ["cost_breakdown", "revenue", "profit_summary", "scenarios"],
    },
}

# ── Report Agent ──

REPORT_AGENT_SCHEMA = {
    "name": "report_generation_result",
    "schema": {
        "type": "object",
        "properties": {
            "report_title": {"type": "string"},
            "report_type": {"type": "string"},
            "generated_at": {"type": "string"},
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "section_title": {"type": "string"},
                        "content_markdown": {"type": "string"},
                        "charts_needed": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "chart_type": {"type": "string", "enum": ["bar", "line", "pie", "radar"]},
                                    "data_source": {"type": "string"},
                                    "description": {"type": "string"},
                                },
                            },
                        },
                    },
                    "required": ["section_title", "content_markdown"],
                },
            },
            "conclusion": {"type": "string"},
            "action_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                        "action": {"type": "string"},
                        "timeline": {"type": "string"},
                    },
                },
            },
        },
        "required": ["report_title", "sections", "conclusion"],
    },
}

# ── Supervisor Agent output (merges all sub-agent results) ──

SUPERVISOR_FINAL_SCHEMA = {
    "name": "supervisor_merged_result",
    "schema": {
        "type": "object",
        "properties": {
            "query_understanding": {
                "type": "object",
                "properties": {
                    "target_country": {"type": "string"},
                    "budget_constraint": {"type": "string"},
                    "user_intent": {"type": "string"},
                    "priority_factors": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["target_country", "user_intent"],
            },
            "answer": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "top_recommendations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_name": {"type": "string"},
                                "market": {"type": "string"},
                                "score": {"type": "integer"},
                                "roi": {"type": "string"},
                                "reason": {"type": "string"},
                            },
                        },
                    },
                    "market_snapshot": {"type": "string"},
                    "risk_warnings": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["summary"],
            },
        },
        "required": ["query_understanding", "answer"],
    },
}
