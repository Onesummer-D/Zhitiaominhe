from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
import os
import json

# 导入服务模块
from services.rule_engine import analyze_text as rule_analyze
from services.knowledge_matcher import detect_custom_law_conflict, get_related_laws, get_similar_cases
from services.document_generator import suggest_template

router = APIRouter(prefix="/api", tags=["analyze"])

class AnalyzeRequest(BaseModel):
    applicant: str = "未填写"
    respondent: str = "未填写"
    type: str = "婚姻家庭"
    custom_law: bool = False
    description: str

class AnalyzeResponse(BaseModel):
    category: str
    confidence: int
    confidence_level: str
    suggestion: str
    keywords: Optional[dict] = None
    conflict_alert: bool = False
    conflict_note: Optional[str] = None
    laws: List[dict] = []
    customs: List[dict] = []
    similar_cases: List[dict] = []
    document_suggestions: List[dict] = []

# DeepSeek API 兜底（可选）
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

def deepseek_fallback(text, category_hint=None):
    """DeepSeek API 兜底分析"""
    try:
        import requests
        if not DEEPSEEK_API_KEY:
            return None

        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个民族地区基层纠纷智能调解助手。请分析以下纠纷描述，输出JSON格式：{category: '纠纷类型', confidence: 1-10的整数, suggestion: '调解建议', key_points: ['要点1', '要点2']}"},
                {"role": "user", "content": text}
            ],
            "response_format": {"type": "json_object"}
        }

        response = requests.post("https://api.deepseek.com/v1/chat/completions", 
                                  json=payload, headers=headers, timeout=30)
        result = response.json()
        content = json.loads(result['choices'][0]['message']['content'])

        return {
            'category': content.get('category', '未知'),
            'confidence': min(10, max(1, content.get('confidence', 5))),
            'suggestion': content.get('suggestion', '建议咨询专业法律人士'),
            'source': 'deepseek'
        }
    except Exception as e:
        print(f"DeepSeek API 调用失败: {e}")
        return None

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_dispute(request: AnalyzeRequest):
    text = request.description

    # Step 1: 规则引擎分析
    rule_result = rule_analyze(text, category_hint=request.type)

    # Step 2: 习惯法冲突检测
    custom_law_result = detect_custom_law_conflict(text, request.custom_law)

    # Step 3: 获取相关法律
    category = rule_result['category'] if rule_result else request.type
    related_laws = get_related_laws(category)

    # Step 4: 相似案例匹配
    similar_cases = get_similar_cases(text, category)

    # Step 5: 文书模板推荐
    doc_suggestions = suggest_template(category, has_custom_law=request.custom_law)

    # Step 6: 决策逻辑
    if rule_result and rule_result['confidence_level'] == '高':
        # 高分直接返回规则引擎结果
        final_category = rule_result['category']
        final_confidence = rule_result['score']
        final_suggestion = generate_suggestion(final_category, rule_result, custom_law_result)
        source = 'rule_engine'
    elif rule_result and rule_result['confidence_level'] == '中':
        # 中分：规则引擎 + DeepSeek 二次确认
        ds_result = deepseek_fallback(text, request.type)
        if ds_result:
            final_category = ds_result['category']
            final_confidence = max(rule_result['score'], ds_result['confidence'])
            final_suggestion = ds_result['suggestion']
            source = 'hybrid'
        else:
            final_category = rule_result['category']
            final_confidence = rule_result['score']
            final_suggestion = generate_suggestion(final_category, rule_result, custom_law_result)
            source = 'rule_engine'
    else:
        # 低分/无匹配：完全交给 DeepSeek
        ds_result = deepseek_fallback(text, request.type)
        if ds_result:
            final_category = ds_result['category']
            final_confidence = ds_result['confidence']
            final_suggestion = ds_result['suggestion']
            source = 'deepseek'
        else:
            final_category = request.type
            final_confidence = 1
            final_suggestion = "系统无法准确识别纠纷类型，建议人工介入分析。"
            source = 'fallback'

    # 构建冲突提示
    conflict_note = None
    if custom_law_result['conflict_alert']:
        conflicts = custom_law_result['conflicts']
        conflict_parts = []
        for c in conflicts:
            conflict_parts.append(
                f"【{c['custom_law_name']}】({c['ethnicity']}) "
                f"与{c['conflict_with']}存在冲突。"
                f"建议：{c['coordination_suggestion'][:60]}..."
            )
        conflict_note = "\\n".join(conflict_parts)

    return AnalyzeResponse(
        category=final_category,
        confidence=final_confidence,
        confidence_level='高' if final_confidence >= 6 else ('中' if final_confidence >= 3 else '低'),
        suggestion=final_suggestion,
        keywords=rule_result['keywords'] if rule_result else None,
        conflict_alert=custom_law_result['conflict_alert'],
        conflict_note=conflict_note,
        laws=related_laws[:5],
        customs=custom_law_result['matched_custom_laws'][:3],
        similar_cases=similar_cases,
        document_suggestions=[{"id": d[0], "name": d[1], "reason": d[2]} for d in doc_suggestions]
    )

def generate_suggestion(category, rule_result, custom_law_result):
    """根据分类和检测结果生成调解建议"""
    suggestions = {
        '婚姻家庭': '建议优先通过人民调解委员会调解，涉及彩礼返还的参照《民法典》第1042条。如存在家庭暴力，应立即申请人身安全保护令。',
        '土地山林': '建议先由乡镇人民政府或村委会进行土地权属确权，依据《土地管理法》第14条处理。涉及习惯法调解的，协议需经司法确认方具强制力。',
        '债务劳资': '建议先向劳动监察大队投诉或申请劳动仲裁。保留工资欠条、考勤记录等证据。如涉及大额欠薪可向公安机关报案。',
        '邻里冲突': '建议优先通过村委会或社区调解组织调解，依据《民法典》第288条处理相邻关系。调解不成可提起民事诉讼。'
    }

    base = suggestions.get(category, '建议咨询专业法律人士或向当地司法所寻求帮助。')

    # 追加习惯法相关建议
    if custom_law_result['matched_custom_laws']:
        custom_names = [c['name'] for c in custom_law_result['matched_custom_laws']]
        base += f"\\n\\n检测到涉及习惯法：{'、'.join(custom_names)}。习惯法调解结果需经司法确认才具强制执行力，建议优先适用国家法律。"

    return base

@router.get("/knowledge")
def get_knowledge(category: Optional[str] = None, search: Optional[str] = None):
    """获取知识库列表"""
    kb_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'knowledge_base.json')
    with open(kb_path, 'r', encoding='utf-8') as f:
        kb = json.load(f)

    result = {'national_laws': kb.get('national_laws', []), 'custom_laws': kb.get('custom_laws', [])}

    if category:
        result['national_laws'] = [l for l in result['national_laws'] if category in l.get('category', '')]
        result['custom_laws'] = [l for l in result['custom_laws'] if category in l.get('applicable_scenarios', [])]

    if search:
        search_lower = search.lower()
        result['national_laws'] = [l for l in result['national_laws'] if search_lower in l.get('name', '').lower() or search_lower in l.get('content', '').lower()]
        result['custom_laws'] = [l for l in result['custom_laws'] if search_lower in l.get('name', '').lower() or search_lower in l.get('content', '').lower()]

    return result
