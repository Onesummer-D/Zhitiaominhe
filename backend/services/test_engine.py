import json
import os
from datetime import datetime

# 导入服务
from services.rule_engine import analyze_text as rule_analyze
from services.knowledge_matcher import detect_custom_law_conflict, get_related_laws

def load_test_data():
    """加载测试数据集"""
    test_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'test_data_full.json')
    with open(test_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_batch_test():
    """批量测试规则引擎准确率"""
    test_cases = load_test_data()

    results = {
        'total': len(test_cases),
        'correct_category': 0,
        'correct_custom_law_detected': 0,
        'high_confidence': 0,
        'medium_confidence': 0,
        'low_confidence': 0,
        'details': [],
        'timestamp': datetime.now().isoformat()
    }

    for case in test_cases:
        text = case['description']
        expected_category = case['category']
        expected_custom = case.get('custom_law', '无') != '无'

        # 规则引擎分析
        rule_result = rule_analyze(text)

        # 习惯法检测
        custom_result = detect_custom_law_conflict(text, custom_law_flag=expected_custom)

        # 评估分类准确率
        predicted_category = rule_result['category'] if rule_result else None
        category_correct = predicted_category == expected_category

        # 评估习惯法检测准确率
        custom_detected = len(custom_result['matched_custom_laws']) > 0
        custom_correct = (expected_custom and custom_detected) or (not expected_custom and not custom_detected)

        # 统计置信度分布
        if rule_result:
            if rule_result['confidence_level'] == '高':
                results['high_confidence'] += 1
            elif rule_result['confidence_level'] == '中':
                results['medium_confidence'] += 1
            else:
                results['low_confidence'] += 1
        else:
            results['low_confidence'] += 1

        if category_correct:
            results['correct_category'] += 1
        if custom_correct:
            results['correct_custom_law_detected'] += 1

        # 记录详情
        results['details'].append({
            'id': case['id'],
            'expected_category': expected_category,
            'predicted_category': predicted_category,
            'category_correct': category_correct,
            'score': rule_result['score'] if rule_result else 0,
            'confidence_level': rule_result['confidence_level'] if rule_result else '无',
            'keywords': rule_result['keywords'] if rule_result else None,
            'custom_law_expected': expected_custom,
            'custom_law_detected': custom_detected,
            'custom_laws_matched': [l['name'] for l in custom_result['matched_custom_laws']],
            'conflicts': [c['custom_law_name'] for c in custom_result['conflicts']]
        })

    # 计算准确率
    results['category_accuracy'] = round(results['correct_category'] / results['total'] * 100, 2)
    results['custom_law_accuracy'] = round(results['correct_custom_law_detected'] / results['total'] * 100, 2)

    return results

def print_report(results):
    """打印测试报告"""
    print("=" * 60)
    print(f"智调民和 —— 规则引擎批量测试报告")
    print(f"测试时间：{results['timestamp']}")
    print("=" * 60)
    print(f"\n总体统计：")
    print(f"  测试样本总数：{results['total']} 条")
    print(f"  分类准确率：{results['category_accuracy']}% ({results['correct_category']}/{results['total']})")
    print(f"  习惯法检测准确率：{results['custom_law_accuracy']}% ({results['correct_custom_law_detected']}/{results['total']})")
    print(f"\n置信度分布：")
    print(f"  高置信度：{results['high_confidence']} 条")
    print(f"  中置信度：{results['medium_confidence']} 条")
    print(f"  低置信度：{results['low_confidence']} 条")

    print(f"\n详细结果：")
    print("-" * 60)
    for detail in results['details']:
        status = "✅" if detail['category_correct'] else "❌"
        print(f"\n{status} {detail['id']}: {detail['expected_category']}")
        print(f"   预测：{detail['predicted_category']} | 分数：{detail['score']} | 置信度：{detail['confidence_level']}")
        if not detail['category_correct']:
            print(f"   ⚠️ 分类错误！预期：{detail['expected_category']}，实际：{detail['predicted_category']}")
        if detail['keywords']:
            print(f"   核心词：{detail['keywords'].get('core', [])}")
            print(f"   特征词：{detail['keywords'].get('features', [])}")
        if detail['custom_laws_matched']:
            print(f"   匹配习惯法：{detail['custom_laws_matched']}")
        if detail['conflicts']:
            print(f"   ⚠️ 冲突警示：{detail['conflicts']}")

    print("\n" + "=" * 60)

def export_report(results, filepath='test_report.json'):
    """导出测试报告到文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n报告已导出：{filepath}")

if __name__ == '__main__':
    results = run_batch_test()
    print_report(results)
    export_report(results, 'test_report.json')
