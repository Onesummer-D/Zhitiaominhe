import json
import os
import re

TEMPLATES_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'document_templates.json')

def load_templates():
    with open(TEMPLATES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_document(template_id, field_values):
    """
    根据模板ID和字段值生成文书
    """
    templates_db = load_templates()
    templates = templates_db.get('templates', [])

    template = next((t for t in templates if t['id'] == template_id), None)
    if not template:
        return {'error': f'模板 {template_id} 不存在'}

    content = template['content']
    missing = []

    # 修复：自动从 content 中提取 {{变量}}，不再依赖 JSON 里的 fields 字段
    fields = template.get('fields', [])
    if not fields:
        fields = list(set(re.findall(r'\{\{([^}]+)\}\}', content)))

    # 替换所有 {{变量}} 占位符
    for field in fields:
        placeholder = f'{{{{{field}}}}}'
        if field in field_values and field_values[field] is not None and str(field_values[field]):
            content = content.replace(placeholder, str(field_values[field]))
        else:
            content = content.replace(placeholder, f'【{field}】')
            missing.append(field)

    return {
        'title': template['name'],
        'content': content,
        'missing_fields': missing,
        'category': template.get('category', '通用')
    }

def suggest_template(dispute_type, subcategory=None, has_custom_law=False):
    """
    根据纠纷类型推荐合适的文书模板
    返回: [(template_id, template_name, reason), ...]
    """
    templates_db = load_templates()
    templates = templates_db.get('templates', [])

    # 大类映射
    primary_map = {
        '婚姻家庭': '婚姻家庭',
        '土地山林': '土地山林',
        '债务劳资': '债务劳资',
        '邻里冲突': '通用'
    }
    primary = primary_map.get(dispute_type, dispute_type)

    suggestions = []
    for t in templates:
        cat = t.get('category', '')
        if primary in cat or cat == '通用':
            reason = f"适用于{primary}纠纷"
            if has_custom_law and '调解' in t['name']:
                reason += "（涉及习惯法，建议优先调解）"
            suggestions.append((t['id'], t['name'], reason))
    return suggestions

def get_template_list():
    """获取所有模板列表"""
    templates_db = load_templates()
    templates = templates_db.get('templates', [])
    return [{
        'id': t['id'],
        'name': t['name'],
        'category': t.get('category', '通用')
    } for t in templates]

if __name__ == '__main__':
    result = generate_document('tpl-hyjt-004', {
        '甲方姓名': '张三',
        '乙方姓名': '李四',
        '纠纷简述': '彩礼返还争议',
        '调解结果第一条': '乙方退还彩礼60%',
        '履行方式': '一次性转账',
        '履行期限': '2025年6月30日前',
        '调解日期': '2025-05-18'
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))