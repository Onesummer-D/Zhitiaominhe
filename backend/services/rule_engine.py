import json
import os

# 加载关键词库
KEYWORDS_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'keywords.json')

def load_keywords():
    with open(KEYWORDS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def keyword_match(text, category_hint=None):
    """
    双层级权重计分：核心定性词+3，特征词+1，排除词-2
    返回：最高分类、分数、命中词详情
    """
    keywords_db = load_keywords()
    categories = keywords_db['categories']
    exclusion_words = keywords_db['exclusion_words']
    scoring = keywords_db['scoring_rules']

    text_lower = text.lower()

    best_category = None
    best_score = -999
    best_details = None

    # 遍历所有一级分类
    for primary_cat, subcategories in categories.items():
        total_score = 0
        core_words = []
        feature_words = []
        excluded_words = []
        matched_subcats = []

        # 检查排除词（全局）
        for ew in exclusion_words:
            if ew in text or ew in text_lower:
                total_score += scoring['exclusion_word_penalty']
                excluded_words.append(ew)

        # 遍历二级分类
        for subcat_name, subcat_data in subcategories.items():
            subcat_score = 0
            subcat_core = []
            subcat_features = []

            # 核心定性词
            for kw in subcat_data['core_keywords']:
                if kw in text or kw in text_lower:
                    subcat_score += scoring['core_keyword_score']
                    subcat_core.append(kw)
                # 同义词
                for syn_list in subcat_data.get('synonyms', {}).values():
                    for syn in syn_list:
                        if syn in text or syn in text_lower:
                            subcat_score += scoring['core_keyword_score']
                            subcat_core.append(syn)

            # 特征词
            for kw in subcat_data['feature_keywords']:
                if kw in text or kw in text_lower:
                    subcat_score += scoring['feature_keyword_score']
                    subcat_features.append(kw)

            if subcat_score > 0:
                matched_subcats.append(subcat_name)
                total_score += subcat_score
                core_words.extend(subcat_core)
                feature_words.extend(subcat_features)

        # 去重
        core_words = list(dict.fromkeys(core_words))
        feature_words = list(dict.fromkeys(feature_words))

        # 更新最佳分类
        if total_score > best_score:
            best_score = total_score
            best_category = primary_cat
            best_details = {
                'core': core_words,
                'features': feature_words,
                'excluded': excluded_words,
                'subcategories': matched_subcats
            }

    # 置信度等级
    if best_score >= scoring['high_confidence_threshold']:
        confidence_level = '高'
    elif best_score >= scoring['medium_confidence_threshold']:
        confidence_level = '中'
    else:
        confidence_level = '低'

    return {
        'category': best_category,
        'score': best_score,
        'confidence_level': confidence_level,
        'keywords': best_details
    }

def analyze_text(text, category_hint=None):
    """主入口：返回完整规则引擎分析结果"""
    result = keyword_match(text, category_hint)

    # 如果分数过低且无核心词匹配，返回None触发API兜底
    if result['score'] < 1 and not result['keywords']['core']:
        return None

    return result

if __name__ == '__main__':
    import json
    test_text = "我是贵州黔东南苗族的，跟着包工头在广西工地干了三个月活，到现在一分钱没拿到"
    res = analyze_text(test_text)
    print(json.dumps(res, ensure_ascii=False, indent=2))
