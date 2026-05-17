import json
import os

TEMPLATES_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'document_templates.json')

def load_templates():
    with open(TEMPLATES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_document(template_id, field_values):
    """
    根据模板ID和字段值生成文书

    参数:
        template_id: 模板ID，如 'tpl-001'
        field_values: 字段值字典，如 {'原告姓名': '张三', '性别': '男'}

    返回:
        {
            'title': str,
            'content': str,
            'missing_fields': [str]  # 缺失的必填字段
        }
    """
    templates_db = load_templates()
    templates = templates_db.get('templates', [])

    template = next((t for t in templates if t['id'] == template_id), None)
    if not template:
        return {'error': f'模板 {template_id} 不存在'}

    content = template['content']
    missing = []

    # 替换所有 {{变量}} 占位符
    for field in template.get('fields', []):
        placeholder = f'{{{{{field}}}}}'
        if field in field_values and field_values[field]:
            content = content.replace(placeholder, str(field_values[field]))
        else:
            content = content.replace(placeholder, f'【{field}】')
            missing.append(field)

    return {
        'title': template['name'],
        'content': content,
        'missing_fields': missing,
        'type': template['type'],
        'category': template['category']
    }

def suggest_template(dispute_type, subcategory=None, has_custom_law=False):
    """
    根据纠纷类型推荐合适的文书模板

    返回: [(template_id, template_name, reason), ...]
    """
    templates_db = load_templates()
    templates = templates_db.get('templates', [])

    suggestions = []

    for t in templates:
        # 匹配适用场景
        scenarios = t.get('applicable_scenarios', [])

        # 简单匹配逻辑
        if dispute_type in t['category'] or t['category'] == '通用':
            reason = f"适用于{dispute_type}纠纷"
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
        'type': t['type'],
        'category': t['category']
    } for t in templates]

if __name__ == '__main__':
    # 测试
    result = generate_document('tpl-003', {
        '甲方姓名': '张三',
        '乙方姓名': '李四',
        '纠纷简述': '土地边界争议',
        '调解结果第一条': '乙方退还多占土地0.5亩',
        '履行方式': '一次性退还',
        '履行期限': '2025年6月30日前',
        '调解日期': '2025-05-18'
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))
