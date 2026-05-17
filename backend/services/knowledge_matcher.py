import json
import os

# 加载知识库
KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'knowledge_base.json')

def load_knowledge_base():
    with open(KNOWLEDGE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def detect_custom_law_conflict(text, custom_law_flag=False):
    """
    检测文本中是否涉及习惯法，并返回冲突警示

    参数:
        text: 纠纷描述文本
        custom_law_flag: 用户是否勾选了"涉及民族习惯法"

    返回:
        {
            'conflict_alert': bool,
            'conflicts': [{
                'custom_law_name': str,
                'ethnicity': str,
                'conflict_with': [str],
                'conflict_note': str,
                'coordination_suggestion': str,
                'validity_level': str
            }],
            'matched_custom_laws': [{
                'id': str,
                'name': str,
                'ethnicity': str,
                'content': str,
                'validity_level': str
            }]
        }
    """
    kb = load_knowledge_base()
    custom_laws = kb.get('custom_laws', [])

    conflicts = []
    matched_laws = []

    # 遍历所有习惯法，检测文本中是否提及
    for law in custom_laws:
        # 检测关键词：习惯法名称、民族名、相关场景词
        match_keywords = [law['name'], law['ethnicity']]
        # 从适用场景中提取关键词
        match_keywords.extend(law.get('applicable_scenarios', []))

        is_matched = False
        for kw in match_keywords:
            if kw and kw in text:
                is_matched = True
                break

        # 如果用户勾选了涉及习惯法，也纳入匹配
        if custom_law_flag and not is_matched:
            # 尝试更宽泛的匹配（民族名+地区）
            if law['ethnicity'] in text or any(region in text for region in law.get('region', '').split('、')):
                is_matched = True

        if is_matched:
            matched_laws.append({
                'id': law['id'],
                'name': law['name'],
                'ethnicity': law['ethnicity'],
                'content': law['content'][:100] + '...' if len(law['content']) > 100 else law['content'],
                'validity_level': law.get('validity_level', '参考性')
            })

            # 检查是否有冲突
            if law.get('conflict_with') and len(law['conflict_with']) > 0:
                conflicts.append({
                    'custom_law_name': law['name'],
                    'ethnicity': law['ethnicity'],
                    'conflict_with': law['conflict_with'],
                    'conflict_note': law.get('conflict_note', ''),
                    'coordination_suggestion': law.get('coordination_suggestion', ''),
                    'validity_level': law.get('validity_level', '参考性')
                })

    return {
        'conflict_alert': len(conflicts) > 0,
        'conflicts': conflicts,
        'matched_custom_laws': matched_laws
    }

def get_related_laws(category):
    """根据分类获取相关法律依据"""
    kb = load_knowledge_base()
    national_laws = kb.get('national_laws', [])

    related = []
    for law in national_laws:
        if category in law.get('applicable_scenarios', []) or \
           any(category in scenario for scenario in law.get('applicable_scenarios', [])):
            related.append(law)

    return related

def get_similar_cases(text, category, top_n=3):
    """简单相似案例匹配（基于关键词重叠）"""
    kb = load_knowledge_base()
    # 从 typical_cases.json 加载
    typical_cases_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'typical_cases.json')
    try:
        with open(typical_cases_path, 'r', encoding='utf-8') as f:
            cases_data = json.load(f)
    except:
        return []

    # 兼容不同数据结构：可能是列表、字典（含cases字段）、或字符串
    cases = []
    if isinstance(cases_data, list):
        cases = cases_data
    elif isinstance(cases_data, dict):
        # 尝试常见字段名
        cases = cases_data.get('cases', cases_data.get('typical_cases', cases_data.get('data', [])))
    else:
        return []

    # 简单关键词匹配计算相似度
    text_words = set(text.lower().split())
    scored_cases = []

    for case in cases:
        # 跳过非字典项
        if not isinstance(case, dict):
            continue

        case_text = case.get('description', '') + case.get('title', '')
        case_words = set(case_text.lower().split())

        if not case_words:
            continue

        overlap = len(text_words & case_words)
        similarity = min(100, int((overlap / max(len(case_words), 1)) * 100))

        if similarity > 20:  # 阈值
            scored_cases.append({
                'title': case.get('title', '未命名案例'),
                'similarity': similarity,
                'result': case.get('result', '调解成功'),
                'description': case.get('description', '')[:80] + '...'
            })

    # 按相似度排序，取前N
    scored_cases.sort(key=lambda x: x['similarity'], reverse=True)
    return scored_cases[:top_n]

if __name__ == '__main__':
    test_text = "我是四川凉山彝族的，寨子里的人说找德古调解一下"
    res = detect_custom_law_conflict(test_text, custom_law_flag=True)
    print(json.dumps(res, ensure_ascii=False, indent=2))
