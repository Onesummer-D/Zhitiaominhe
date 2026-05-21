from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
from services.document_generator import generate_document

router = APIRouter(prefix="/api/documents", tags=["documents"])

DOC_TYPE_MAP = {
    '土地山林': {
        'mediation': 'tpl-tdsl-002',
        'lawsuit': 'tpl-tdsl-001',
    },
    '婚姻家庭': {
        'mediation': 'tpl-hyjt-004',
        'lawsuit': 'tpl-hyjt-003',
    },
    '债务劳资': {
        'mediation': 'tpl-zwlz-007',
        'lawsuit': 'tpl-zwlz-005',
        'lawsuit_injury': 'tpl-zwlz-006',    # 人身损害赔偿起诉状（新增）
        'mediation_injury': 'tpl-zwlz-008',  # 人身损害赔偿调解书（新增）
        'supervision': 'tpl-zwlz-009',
    },
    '邻里冲突': {
        'mediation': 'tpl-llct-004',
        'lawsuit': 'tpl-llct-001',
        'admin_lawsuit': 'tpl-llct-002',
        'judicial_confirm': 'tpl-llct-003',
    }
}

def _map_category(category):
    c = category or ''
    if any(k in c for k in ['婚姻', '彩礼', '婚约', '离婚', '家暴', '赡养', '抚养', '嫁妆', '家庭']):
        return '婚姻家庭'
    if any(k in c for k in ['草场', '林地', '山林', '宅基地', '土地', '草原', '征地', '承包', '边界', '越界', '权属']):
        return '土地山林'
    if any(k in c for k in ['欠薪', '工资', '债务', '劳资', '劳务', '赔偿', '工伤', '借款', '欠款', '民间借贷']):
        return '债务劳资'
    if any(k in c for k in ['邻里', '相邻', '噪音', '漏水', '采光', '通行', '动物', '侵占', '风俗', '异味', '树木', '排水']):
        return '邻里冲突'
    return c

class DocGenerateRequest(BaseModel):
    category: str
    doc_type: str
    field_values: Optional[Dict[str, Any]] = {}

@router.post("/generate")
def generate_doc(req: DocGenerateRequest):
    primary = _map_category(req.category)
    tpl_id = DOC_TYPE_MAP.get(primary, {}).get(req.doc_type)
    if not tpl_id:
        return {"error": f"未找到「{primary}」类纠纷的「{req.doc_type}」模板"}
    result = generate_document(tpl_id, req.field_values or {})
    return result