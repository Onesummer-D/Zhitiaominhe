import json
import requests
import pandas as pd
from datetime import datetime
import os
import re

API_BASE = "http://localhost:8000"
TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'test_data.json')
REPORT_PATH = os.path.join(os.path.dirname(__file__), 'data', 'test_report.xlsx')

# 民族关键词库
ETHNIC_KEYWORDS = ["藏族", "彝族", "苗族", "回族", "维吾尔族", "蒙古族", "壮族", "傣族", 
                   "土家族", "哈尼族", "哈萨克族", "侗族", "瑶族", "羌族", "纳西族", "门巴族", 
                   "珞巴族", "撒拉族", "布依族", "白族", "黎族", "鄂伦春族", "鄂温克族", "土家族"]

def load_test_data():
    with open(TEST_DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_ethnicity(text):
    for e in ETHNIC_KEYWORDS:
        if e in text:
            return e
    return ''

def get_primary_category(cat):
    """把各种category写法映射到四大类"""
    c = cat or ''
    if any(k in c for k in ['婚姻', '彩礼', '婚约', '离婚', '家暴', '赡养', '抚养', '嫁妆', '家庭']):
        return '婚姻家庭'
    if any(k in c for k in ['草场', '林地', '山林', '宅基地', '土地', '草原', '征地', '承包', '边界', '越界', '权属']):
        return '土地山林'
    if any(k in c for k in ['欠薪', '工资', '债务', '劳资', '劳务', '赔偿', '工伤', '借款', '欠款', '民间借贷']):
        return '债务劳资'
    if any(k in c for k in ['邻里', '相邻', '噪音', '漏水', '采光', '通行', '动物', '侵占', '风俗', '异味', '树木', '排水']):
        return '邻里冲突'
    return c

def run_single_test(case):
    """调用后端 analyze 接口"""
    payload = {
        "applicant": "测试申请人",
        "respondent": "测试被申请人",
        "type": get_primary_category(case.get("category", "婚姻家庭")),
        "custom_law": case.get("custom_law", False),
        "description": case["description"]
    }
    try:
        resp = requests.post(f"{API_BASE}/api/analyze", json=payload, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"  [{case['id']}] HTTP {resp.status_code}")
            return None
    except Exception as e:
        print(f"  [{case['id']}] 请求失败: {e}")
        return None

def evaluate():
    cases = load_test_data()
    total = len(cases)
    
    correct_primary = 0
    correct_custom_law = 0
    correct_ethnicity = 0
    has_laws = 0
    has_customs = 0
    has_similar_cases = 0
    confidence_sum = 0
    deepseek_fallback_count = 0
    
    results = []
    
    print(f"开始批量测试，共 {total} 条数据...\n")
    
    for case in cases:
        print(f"测试 {case['id']} —— {case.get('sub_category', '')}")
        raw = run_single_test(case)
        
        if raw is None:
            results.append({
                "ID": case["id"],
                "子类别": case.get("sub_category", ""),
                "描述前30字": case["description"][:30],
                "预期大类": get_primary_category(case.get("category", "")),
                "实际大类": "ERROR",
                "分类正确": False,
                "预期习惯法": case.get("custom_law", False),
                "实际习惯法冲突": False,
                "习惯法检测正确": False,
                "预期民族": extract_ethnicity(case["description"]),
                "实际民族": "",
                "民族正确": False,
                "返回法条数": 0,
                "返回习惯法数": 0,
                "相似案例数": 0,
                "置信度": 0,
                "来源": "ERROR"
            })
            continue
        
        # 解析实际结果
        actual_category = raw.get("category", "未知")
        actual_confidence = raw.get("confidence", 0)
        actual_custom_alert = raw.get("conflict_alert", False)
        actual_customs = raw.get("customs", [])
        actual_laws = raw.get("laws", [])
        actual_similar = raw.get("similar_cases", [])
        
        # 预期值
        expected_primary = get_primary_category(case.get("category", ""))
        actual_primary = get_primary_category(actual_category)
        expected_custom_law = case.get("custom_law", False)
        expected_ethnicity = extract_ethnicity(case["description"])
        detected_ethnicity = extract_ethnicity(case["description"])
        
        # 判断指标
        cat_correct = (expected_primary == actual_primary)
        if cat_correct:
            correct_primary += 1
            
        custom_correct = (expected_custom_law == actual_custom_alert)
        if custom_correct:
            correct_custom_law += 1
            
        ethnic_correct = (expected_ethnicity == detected_ethnicity)
        if ethnic_correct:
            correct_ethnicity += 1
            
        if len(actual_laws) > 0:
            has_laws += 1
        if len(actual_customs) > 0:
            has_customs += 1
        if len(actual_similar) > 0:
            has_similar_cases += 1
            
        confidence_sum += actual_confidence
        
        source = "rule_engine" if actual_confidence >= 6 else ("hybrid" if actual_confidence >= 3 else "deepseek")
        if actual_confidence < 3:
            deepseek_fallback_count += 1
        
        results.append({
            "ID": case["id"],
            "子类别": case.get("sub_category", ""),
            "描述前30字": case["description"][:30],
            "预期大类": expected_primary,
            "实际大类": actual_primary,
            "分类正确": cat_correct,
            "预期习惯法": expected_custom_law,
            "实际习惯法冲突": actual_custom_alert,
            "习惯法检测正确": custom_correct,
            "预期民族": expected_ethnicity,
            "实际民族": detected_ethnicity,
            "民族正确": ethnic_correct,
            "返回法条数": len(actual_laws),
            "返回习惯法数": len(actual_customs),
            "相似案例数": len(actual_similar),
            "置信度": actual_confidence,
            "置信度等级": raw.get("confidence_level", ""),
            "来源": source
        })
        
        print(f"  → 大类:{actual_primary} | 置信度:{actual_confidence} | 法条:{len(actual_laws)} | 习惯法:{len(actual_customs)} | 案例:{len(actual_similar)} | 冲突:{actual_custom_alert}")
    
    # 汇总统计
    print("\n" + "="*60)
    print("【智调民和 — 批量测试报告】")
    print(f"测试总数: {total}")
    print(f"大类分类准确率: {correct_primary}/{total} = {correct_primary/total*100:.1f}%")
    print(f"习惯法检测准确率: {correct_custom_law}/{total} = {correct_custom_law/total*100:.1f}%")
    print(f"民族识别准确率: {correct_ethnicity}/{total} = {correct_ethnicity/total*100:.1f}%")
    print(f"法条召回率: {has_laws}/{total} = {has_laws/total*100:.1f}%")
    print(f"习惯法召回率: {has_customs}/{total} = {has_customs/total*100:.1f}%")
    print(f"相似案例匹配率: {has_similar_cases}/{total} = {has_similar_cases/total*100:.1f}%")
    print(f"平均置信度: {confidence_sum/total:.1f}")
    print(f"DeepSeek兜底/混合次数: {deepseek_fallback_count}/{total}")
    print("="*60)
    
    # 生成Excel报告
    df = pd.DataFrame(results)
    
    summary = pd.DataFrame([
        {"指标": "测试总数", "数值": total},
        {"指标": "大类分类准确率", "数值": f"{correct_primary/total*100:.1f}%"},
        {"指标": "习惯法检测准确率", "数值": f"{correct_custom_law/total*100:.1f}%"},
        {"指标": "民族识别准确率", "数值": f"{correct_ethnicity/total*100:.1f}%"},
        {"指标": "法条召回率", "数值": f"{has_laws/total*100:.1f}%"},
        {"指标": "习惯法召回率", "数值": f"{has_customs/total*100:.1f}%"},
        {"指标": "相似案例匹配率", "数值": f"{has_similar_cases/total*100:.1f}%"},
        {"指标": "平均置信度", "数值": f"{confidence_sum/total:.1f}"},
        {"指标": "DeepSeek兜底次数", "数值": deepseek_fallback_count},
        {"指标": "测试时间", "数值": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    ])
    
    with pd.ExcelWriter(REPORT_PATH, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='详细结果', index=False)
        summary.to_excel(writer, sheet_name='汇总统计', index=False)
    
    print(f"\n报告已保存: {REPORT_PATH}")

if __name__ == '__main__':
    evaluate()