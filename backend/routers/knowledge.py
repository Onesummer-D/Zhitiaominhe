from fastapi import APIRouter, Query
from typing import Optional
import json
import os

router = APIRouter(prefix="/api", tags=["knowledge"])

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/knowledge_base.json")

def load_knowledge():
    if not os.path.exists(DATA_PATH):
        return {"national_laws": [], "custom_laws": []}
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

@router.get("/knowledge")
async def list_knowledge(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """获取知识库列表，返回 { national_laws, custom_laws }"""
    data = load_knowledge()
    
    national_laws = data.get("national_laws", [])
    custom_laws = data.get("custom_laws", [])

    # 分类过滤（国家法律）
    if category:
        national_laws = [l for l in national_laws if category in l.get("category", "")]
    
    # 搜索过滤（国家法律）
    if search:
        search_lower = search.lower()
        national_laws = [
            l for l in national_laws 
            if search_lower in l.get("name", "").lower() 
            or search_lower in l.get("content", "").lower()
        ]
        custom_laws = [
            l for l in custom_laws 
            if search_lower in l.get("name", "").lower() 
            or search_lower in l.get("content", "").lower()
        ]

    return {
        "national_laws": national_laws,
        "custom_laws": custom_laws
    }