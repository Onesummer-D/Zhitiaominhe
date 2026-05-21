from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
import os
import json

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
                {"role": "system", "content": "你是一个民族地区基层纠纷智能调解助手。请分析以下纠纷描述，输出JSON格式：{category: '纠纷类型', confidence: 1-10的整数, suggestion: '具体可操作的调解建议，不少于50字，必须使用换行符进行适当分段', key_points: ['要点1', '要点2']}。注意：suggestion字段必须包含具体建议，不能为空，且必须包含换行符分段。"},
                {"role": "user", "content": f"纠纷描述：{text}\n已知分类提示：{category_hint or '无'}"}
            ],
            "response_format": {"type": "json_object"}
        }

        response = requests.post("https://api.deepseek.com/v1/chat/completions", 
                                  json=payload, headers=headers, timeout=30)
        result = response.json()
        content = json.loads(result['choices'][0]['message']['content'])

        suggestion = content.get('suggestion', '').strip()
        if not suggestion:
            suggestion = "建议优先通过当地人民调解委员会或村委会进行调解，必要时向司法所申请法律援助。"

        return {
            'category': content.get('category', category_hint or '未知'),
            'confidence': min(10, max(1, content.get('confidence', 5))),
            'suggestion': suggestion,
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

    # 优先使用二级分类作为展示分类
    display_category = rule_result.get('sub_category', rule_result['category']) if rule_result else request.type

    # Step 2: 习惯法冲突检测
    custom_law_result = detect_custom_law_conflict(text, request.custom_law, category_hint=display_category)

    # Step 3: 获取相关法律
    related_laws = get_related_laws(display_category)

    # Step 4: 相似案例匹配
    similar_cases = get_similar_cases(text, display_category)

    # Step 5: 文书模板推荐
    doc_suggestions = suggest_template(display_category, has_custom_law=request.custom_law)

    # Step 6: 决策逻辑
    if rule_result and rule_result['confidence_level'] == '高':
        final_category = display_category
        final_confidence = rule_result['score']
        final_suggestion = generate_suggestion(final_category, rule_result, custom_law_result, text)
        source = 'rule_engine'
    elif rule_result and rule_result['confidence_level'] == '中':
        ds_result = deepseek_fallback(text, display_category)
        if ds_result:
            final_category = ds_result['category']
            final_confidence = max(rule_result['score'], ds_result['confidence'])
            final_suggestion = ds_result['suggestion']
            source = 'hybrid'
        else:
            final_category = display_category
            final_confidence = rule_result['score']
            final_suggestion = generate_suggestion(final_category, rule_result, custom_law_result, text)
            source = 'rule_engine'
    else:
        ds_result = deepseek_fallback(text, display_category)
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

    # 构建冲突提示（修复格式）
    conflict_note = None
    if custom_law_result['conflict_alert'] and custom_law_result['conflicts']:
        conflict_parts = []
        for c in custom_law_result['conflicts']:
            # 修复：列表转自然语言，不再出现 ['']
            conflict_laws = '、'.join(c['conflict_with']) if isinstance(c['conflict_with'], list) else str(c['conflict_with'])
            suggestion = c['coordination_suggestion'] if c['coordination_suggestion'] else '建议优先适用国家法律，习惯法调解结果需经司法确认。'

            conflict_parts.append(
                f"【{c['custom_law_name']}】（{c['ethnicity']}）\n\n"
                f"与国家法{conflict_laws}存在冲突。\n\n"
                f"协调建议：{suggestion}"
            )
        conflict_note = "\n\n---\n\n".join(conflict_parts)
    elif custom_law_result['matched_custom_laws']:
        names = [c['name'] for c in custom_law_result['matched_custom_laws']]
        conflict_note = f"检测到涉及习惯法：{'、'.join(names)}。\n\n习惯法调解结果需经司法确认才具强制执行力，建议优先适用国家法律。"

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

def generate_suggestion(category, rule_result, custom_law_result, text=""):
    """生成精准调解建议，内置分段换行"""
    sub_category = category
    text_lower = text.lower()

    suggestions = {
        '彩礼纠纷': '建议先尝试村/社区调解，若无效可向法院起诉要求返还彩礼。\n\n根据《中华人民共和国民法典》及相关司法解释，未办理结婚登记且共同生活时间较短的，一般应当返还彩礼。注意收集支付凭证、证人证言等证据。',
        '婚约财产纠纷': '建议先尝试村/社区调解，若无效可向法院起诉要求返还彩礼。\n\n根据《中华人民共和国民法典》及相关司法解释，未办理结婚登记且共同生活时间较短的，一般应当返还彩礼。涉及习惯法"不退彩礼"约定的，需告知当事人国家法优先原则。',
        '离婚纠纷': '建议优先通过人民调解委员会调解。\n\n涉及财产分割和子女抚养的，依据《中华人民共和国民法典》第1079条、第1084条处理。如存在家庭暴力，应立即申请人身安全保护令。',
        '家暴纠纷': '建议立即报警并保留伤情证据，向妇联或公安机关申请人身安全保护令。\n\n依据《中华人民共和国反家庭暴力法》第23条，法院应当受理。必要时可申请人身安全保护令。',
        '土地承包': '建议先由乡镇人民政府或村委会进行土地权属确权。\n\n依据《中华人民共和国土地管理法》第14条处理。涉及习惯法调解的，协议需经司法确认方具强制力。',
        '宅基地': '建议向乡镇人民政府申请确权。\n\n依据《中华人民共和国土地管理法》第14条处理。宅基地使用权争议应先行政处理，对决定不服可30日内起诉。',
        '草场': '建议由苏木人民政府或草原主管部门调解。\n\n依据《中华人民共和国草原法》第13条、第14条处理。涉及苏鲁克制度的，可参照习惯法但须司法确认。',
        '欠薪': '建议先向劳动监察大队投诉或申请劳动仲裁。\n\n保留工资欠条、考勤记录等证据。依据《中华人民共和国劳动法》第50条，工资应按月支付不得拖欠。',
        '债务': '建议保留借条、转账记录等证据，可先人民调解，调解不成可起诉。\n\n依据《中华人民共和国民法典》第579条，金钱债务应当清偿。',
        '劳务受害': '建议固定医疗记录、现场证据并申请伤残鉴定。\n\n依据《中华人民共和国民法典》第1192条，根据双方过错划分责任。',
        # 邻里冲突子类别建议
        '相邻排水': '建议优先与邻居协商，协商不成可请求村委会或人民调解委员会调解。\n\n依据《中华人民共和国民法典》第290条，不动产权利人应当为相邻权利人用水、排水提供必要的便利。保留漏水照片、维修发票等证据。',
        '相邻通行': '建议优先协商，协商不成可请求村委会调解。\n\n依据《中华人民共和国民法典》第291条，不动产权利人对相邻权利人因通行等必须利用其土地的，应当提供必要的便利。',
        '噪音扰民': '建议先向物业或村委会反映，必要时报警处理。\n\n依据《中华人民共和国治安管理处罚法》第88条及《中华人民共和国民法典》第294条，制造噪声干扰他人正常生活的，处警告或罚款。保留录音、报警记录等证据。',
        '相邻漏水': '建议保留漏水照片、视频等证据，先与邻居协商维修及赔偿。\n\n依据《中华人民共和国民法典》第296条，使用相邻不动产应当尽量避免对相邻的不动产权利人造成损害。协商不成可起诉要求停止侵害、赔偿损失。',
        '采光妨碍': '建议保留现场照片，向村委会或乡镇司法所申请调解。\n\n依据《中华人民共和国民法典》第293条，建造建筑物不得妨碍相邻建筑物的通风、采光和日照。调解不成可提起民事诉讼。',
        '异味污染': '建议向村委会或环保部门反映，必要时起诉。\n\n依据《中华人民共和国民法典》第294条，不得排放大气污染物、水污染物等有害物质。保留照片、视频、证人证言等证据。',
        '动物损害': '建议保留证据，协商不成可起诉。\n\n依据《中华人民共和国民法典》第1245条，动物饲养人应承担无过错责任。可要求赔偿实际损失。',
        '树木越界': '建议协商修剪，协商不成可请求村委会调解。\n\n依据《中华人民共和国民法典》第288条，按照有利生产、方便生活、团结互助、公平合理的原则处理。',
        '侵占房屋': '建议立即要求返还，协商不成可起诉。\n\n依据《中华人民共和国民法典》第235条，无权占有不动产的，权利人可以请求返还原物。',
        '风俗侵权': '建议保留证据，必要时报警或起诉。\n\n涉及民族风俗的，习惯法调解结果需经司法确认才具强制执行力，建议优先适用国家法律。',
    }

    if sub_category in suggestions:
        base = suggestions[sub_category]
    else:
        primary_map = {
            '婚姻家庭': '建议优先通过人民调解委员会调解。\n\n涉及彩礼返还的参照《中华人民共和国民法典》第1042条。如存在家庭暴力，应立即申请人身安全保护令。',
            '土地山林': '建议先由乡镇人民政府或村委会进行土地权属确权。\n\n依据《中华人民共和国土地管理法》第14条处理。涉及习惯法调解的，协议需经司法确认方具强制力。',
            '债务劳资': '建议先向劳动监察大队投诉或申请劳动仲裁。\n\n保留工资欠条、考勤记录等证据。如涉及大额欠薪可向公安机关报案。',
            '邻里冲突': '建议优先通过村委会或社区调解组织调解。\n\n依据《中华人民共和国民法典》第288条处理相邻关系。调解不成可提起民事诉讼。涉及民族习惯法调解的，协议需经司法确认方具强制执行力。'
        }
        base = primary_map.get(sub_category, '建议咨询专业法律人士或向当地司法所寻求帮助。')

    # 文本关键词兜底匹配（增强邻里冲突识别）
    if '彩礼' in text or '聘礼' in text:
        base = suggestions.get('彩礼纠纷', base)
    elif '离婚' in text or '分居' in text:
        base = suggestions.get('离婚纠纷', base)
    elif '家暴' in text or '殴打' in text or '虐待' in text:
        base = suggestions.get('家暴纠纷', base)
    elif '工资' in text or '欠薪' in text or '劳务费' in text:
        base = suggestions.get('欠薪', base)
    elif '借款' in text or '欠款' in text or '债务' in text:
        base = suggestions.get('债务', base)
    elif '受伤' in text or '赔偿' in text or '医疗费' in text:
        base = suggestions.get('劳务受害', base)
    elif '漏水' in text or '渗水' in text or '排水' in text:
        base = suggestions.get('相邻漏水', base)
    elif '噪音' in text or '噪声' in text or '装修' in text or '扰民' in text:
        base = suggestions.get('噪音扰民', base)
    elif '通行' in text or '通道' in text or '过道' in text or '堵路' in text:
        base = suggestions.get('相邻通行', base)
    elif '采光' in text or '挡光' in text or '日照' in text or '遮阳' in text:
        base = suggestions.get('采光妨碍', base)
    elif '异味' in text or '臭味' in text or '油烟' in text or '鸡粪' in text:
        base = suggestions.get('异味污染', base)
    elif '狗' in text or '羊' in text or '牲畜' in text or '咬死' in text or '啃食' in text:
        base = suggestions.get('动物损害', base)
    elif '树枝' in text or '树根' in text or '越界' in text and '树' in text:
        base = suggestions.get('树木越界', base)
    elif '占用' in text or '侵占' in text or '堆放' in text and '房' in text:
        base = suggestions.get('侵占房屋', base)
    elif '风俗' in text or '诅咒' in text or '撒米饭' in text or '烧纸' in text:
        base = suggestions.get('风俗侵权', base)

    if custom_law_result.get('matched_custom_laws'):
        custom_names = [c['name'] for c in custom_law_result['matched_custom_laws']]
        base += f"\n\n【习惯法提示】检测到涉及习惯法：{'、'.join(custom_names)}。习惯法调解结果需经司法确认才具强制执行力，建议优先适用国家法律。"

    return base
