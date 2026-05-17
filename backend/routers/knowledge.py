from fastapi import APIRouter, Query
from typing import Optional, List
from models.schemas import KnowledgeItem
import json
import os

router = APIRouter()

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/knowledge_base.json")

def load_knowledge():
    if not os.path.exists(DATA_PATH):
        return {"national_laws": [], "custom_laws": []}
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

@router.get("/knowledge")
async def list_knowledge(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    type: Optional[str] = Query(None)  # 'national' | 'custom'
):
    """获取知识库列表"""
    data = load_knowledge()
    results = []

    # 国家法律
    if type in (None, 'national'):
        for item in data.get("national_laws", []):
            if category and item.get("category") != category:
                continue
            if search and search not in item.get("name", "") and search not in item.get("content", ""):
                continue
            results.append({**item, "type": "national"})

    # 习惯法
    if type in (None, 'custom'):
        for item in data.get("custom_laws", []):
            if search and search not in item.get("name", "") and search not in item.get("content", ""):
                continue
            results.append({**item, "type": "custom"})

    return results
