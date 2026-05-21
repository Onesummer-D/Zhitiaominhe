import json
import os

# 加载关键词库
KEYWORDS_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'keywords.json')

# === 修复1 新增：大类场景词加分表（用于增强大类识别，解决"邻居+家门口"等口语词无法给邻里冲突加分的问题） ===
CATEGORY_SCENE_WORDS = {
    '邻里冲突': [
        '邻居', '楼上', '楼下', '隔壁', '家门口', '门前', '邻里', '物业', '小区',
        '楼道', '阳台', '天花板', '漏水', '噪音', '噪声', '装修', '扰民',
        '采光', '挡光', '通行', '过道', '通道', '堆放', '杂物', '狗叫',
        '鸡粪', '油烟', '臭味', '异味', '风俗', '诅咒', '撒米', '撒米饭',
        '不让过', '堵住', '挡住', '必经', '过路', '路过', '堵门', '拦路',
        '挡在', '挡道', '报复', '晦气', '犯忌讳', '不吉利'
    ],
    '婚姻家庭': [
        '结婚', '离婚', '彩礼', '聘礼', '定亲', '婚礼', '嫁妆', '家暴',
        '抚养', '赡养', '夫妻', '婆婆', '儿媳', '丈夫', '妻子', '出轨',
        '感情破裂', '分居', '同居', '重婚', '虐待', '遗弃', '抚养费',
        '赡养费', '抚养权', '监护权', '探视权', '未婚先孕', '非婚生'
    ],
    '土地山林': [
        '宅基地', '地基', '屋檐', '围墙', '越界', '草场', '草原', '牧场',
        '放牧', '转场', '围栏', '林地', '山林', '林木', '砍树', '采伐',
        '毁林', '开荒', '地界', '边界', '田埂', '界桩', '四至', '征地',
        '征收', '补偿', '安置', '青苗', '承包', '流转', '合同', '租金',
        '土地证', '林权证', '确权', '草场证', '牧区', '草山'
    ],
    '债务劳资': [
        '欠薪', '工资', '劳务费', '报酬', '欠款', '借款', '债务', '借贷',
        '赊购', '赊账', '赔偿', '工伤', '劳动合同', '工程款', '租金',
        '租赁', '机械', '材料款', '农民工', '讨薪', '拖欠', '分期',
        '还款', '借条', '欠条', '转账', '利息', '本金', '违约金'
    ],
}

# === 修复1 新增：邻里冲突强信号词（用于压制土地山林/债务劳资的误识别） ===
LLCT_STRONG_SIGNALS = [
    '邻居', '楼上', '楼下', '隔壁', '家门口', '门前', '邻里',
    '漏水', '噪音', '噪声', '装修', '扰民', '采光', '挡光',
    '通行', '不让过', '堵住', '挡住', '必经', '过路', '堵门',
    '风俗', '诅咒', '撒米', '撒米饭', '异味', '臭味',
    '鸡粪', '油烟', '狗叫', '羊群', '牲畜', '占用', '堆放',
    '杂物', '天花板', '墙皮', '渗水', '滴水', '阳台'
]

def load_keywords():
    with open(KEYWORDS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def keyword_match(text, category_hint=None):
    """
    双层级权重计分：核心定性词+3，特征词+1，排除词-2
    返回：最高一级分类、最高二级分类、分数、命中词详情
    """
    keywords_db = load_keywords()
    categories = keywords_db['categories']
    exclusion_words = keywords_db['exclusion_words']
    scoring = keywords_db['scoring_rules']

    text_lower = text.lower()

    best_category = None
    best_score = -999
    best_details = None
    best_subcategory = None   # 新增：最佳二级分类
    best_sub_score = -999     # 新增：最佳二级分类的独立分数

    # === 修复2 新增：记录每个大类的得分和 details（用于压制逻辑后恢复正确的大类信息） ===
    category_scores = {}
    category_details = {}

    # 遍历所有一级分类
    for primary_cat, subcategories in categories.items():
        total_score = 0
        core_words = []
        feature_words = []
        excluded_words = []
        matched_subcats = []
        cat_best_sub = None       # 修复2 新增：当前大类的最佳子类
        cat_best_sub_score = -999 # 修复2 新增

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

                # 追踪独立分数最高的二级分类（全局）
                if subcat_score > best_sub_score:
                    best_sub_score = subcat_score
                    best_subcategory = subcat_name

                # 修复2 新增：追踪当前大类的最佳子类
                if subcat_score > cat_best_sub_score:
                    cat_best_sub_score = subcat_score
                    cat_best_sub = subcat_name

        # 去重
        core_words = list(dict.fromkeys(core_words))
        feature_words = list(dict.fromkeys(feature_words))

        # === 修复2 新增：大类场景词加分（每个匹配词+1，封顶5分） ===
        scene_bonus = 0
        for word in CATEGORY_SCENE_WORDS.get(primary_cat, []):
            if word in text:
                scene_bonus += 1
        total_score += min(scene_bonus, 5)

        # 修复2 新增：保存当前大类的得分和详细信息
        category_scores[primary_cat] = total_score
        category_details[primary_cat] = {
            'core': core_words,
            'features': feature_words,
            'excluded': excluded_words,
            'subcategories': matched_subcats,
            'best_subcategory': cat_best_sub,
            'best_sub_score': cat_best_sub_score
        }

        # 更新最佳一级分类
        if total_score > best_score:
            best_score = total_score
            best_category = primary_cat
            best_details = {
                'core': core_words,
                'features': feature_words,
                'excluded': excluded_words,
                'subcategories': matched_subcats
            }

    # === 修复2 新增：邻里冲突强信号压制逻辑 ===
    # 当文本中出现≥2个邻里冲突强信号词（如"邻居"+"不让过"），
    # 但土地山林/债务劳资因"承包地""生意"等词虚高时，
    # 自动给邻里冲突+2分，给土地山林/债务劳资-3分
    llct_signal_count = sum(1 for s in LLCT_STRONG_SIGNALS if s in text)
    if llct_signal_count >= 2:
        llct_score = category_scores.get('邻里冲突', 0)
        for other_cat in ['土地山林', '债务劳资']:
            other_score = category_scores.get(other_cat, 0)
            if other_score > llct_score and (other_score - llct_score) < 4:
                category_scores[other_cat] -= 3
                category_scores['邻里冲突'] += 2

        # 重新确定最佳大类（如果邻里冲突因此反超）
        new_best_cat = max(category_scores, key=category_scores.get)
        if new_best_cat != best_category:
            best_category = new_best_cat
            best_score = category_scores[best_category]
            best_details = category_details[best_category]
            # 恢复被压制后的正确子类
            best_subcategory = category_details[best_category]['best_subcategory']
            best_sub_score = category_details[best_category]['best_sub_score']

    # 置信度等级
    if best_score >= scoring['high_confidence_threshold']:
        confidence_level = '高'
    elif best_score >= scoring['medium_confidence_threshold']:
        confidence_level = '中'
    else:
        confidence_level = '低'

    return {
        'category': best_category,
        'sub_category': best_subcategory or best_category,  # 优先返回二级分类
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
