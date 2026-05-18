from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
from services.document_generator import generate_document

router = APIRouter(prefix="/api/documents", tags=["documents"])

# category + doc_type → template_id 映射
DOC_TYPE_MAP = {
    '土地山林': {
        'mediation': 'tpl-tdsl-002',   # 人民调解协议书
        'lawsuit': 'tpl-tdsl-001',     # 起诉状
    },
    '婚姻家庭': {
        'mediation': 'tpl-hyjt-004',   # 调解协议书
        'lawsuit': 'tpl-hyjt-003',     # 民事起诉状
    },
    '债务劳资': {
        'mediation': 'tpl-zwlz-007',   # 调解协议书
        'lawsuit': 'tpl-zwlz-005',     # 民事起诉状
        'supervision': 'tpl-zwlz-009', # 检察监督申请书
    }
}

def _map_category(category):
    """把任意分类名归到大类"""
    c = category or ''
    if any(k in c for k in ['婚姻', '彩礼', '婚约', '离婚', '家暴', '赡养', '抚养', '嫁妆', '家庭']):
        return '婚姻家庭'
    if any(k in c for k in ['草场', '林地', '山林', '宅基地', '土地', '草原', '征地', '承包', '边界', '越界', '权属']):
        return '土地山林'
    if any(k in c for k in ['欠薪', '工资', '债务', '劳资', '劳务', '赔偿', '工伤', '借款', '欠款']):
        return '债务劳资'
    return c

class DocGenerateRequest(BaseModel):
    category: str
    doc_type: str  # mediation | lawsuit | supervision
    field_values: Optional[Dict[str, Any]] = {}

@router.post("/generate")
def generate_doc(req: DocGenerateRequest):
    primary = _map_category(req.category)
    tpl_id = DOC_TYPE_MAP.get(primary, {}).get(req.doc_type)
    
    if not tpl_id:
        return {"error": f"未找到「{primary}」类纠纷的「{req.doc_type}」模板"}
    
    result = generate_document(tpl_id, req.field_values or {})
    return result