import json
import os

# 加载知识库
KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'knowledge_base.json')

# 二级分类 → 一级分类 映射表（补全队友所有可能的分类名）
CATEGORY_MAP = {
    # 婚姻家庭
    "彩礼纠纷": "婚姻家庭", "婚约财产纠纷": "婚姻家庭", "离婚纠纷": "婚姻家庭",
    "家暴纠纷": "婚姻家庭", "包办早婚": "婚姻家庭", "赡养扶养": "婚姻家庭",
    "婚姻": "婚姻家庭", "家庭": "婚姻家庭", "婚约": "婚姻家庭",
    # 土地山林（补全队友用词）
    "宅基地": "土地山林", "草场": "土地山林", "林地": "土地山林",
    "山林": "土地山林", "土地": "土地山林", "草原": "土地山林",
    "边界争议": "土地山林", "征地补偿": "土地山林", "承包合同": "土地山林",
    "越界": "土地山林", "权属": "土地山林", "征地": "土地山林",
    # 债务劳资（补全队友用词）
    "欠薪": "债务劳资", "债务": "债务劳资", "劳务合同": "债务劳资",
    "民间借贷": "债务劳资", "租赁合同": "债务劳资", "夫妻共同债务": "债务劳资",
    "个人劳务受害": "债务劳资", "合同违约": "债务劳资", "习惯法调解": "债务劳资",
    "工程款欠薪": "债务劳资", "劳务合同欠薪": "债务劳资", "工资": "债务劳资",
    "劳资纠纷": "债务劳资", "债务纠纷": "债务劳资", "债务/劳资": "债务劳资",
    # 邻里冲突
    "邻里冲突": "邻里冲突", "相邻纠纷": "邻里冲突", "排水": "邻里冲突",
    "通行": "邻里冲突", "采光": "邻里冲突", "噪音": "邻里冲突",
}

# 分类 → 相关场景关键词 映射
CATEGORY_SCENE_KEYWORDS = {
    "婚姻家庭": ["婚姻", "彩礼", "聘礼", "婚礼", "嫁娶", "婚约", "离婚", "感情", "分居", "抚养", "家暴", "暴力", "赡养", "继承", "家庭", "调解"],
    "土地山林": ["宅基地", "地基", "房屋", "建房", "草场", "草原", "牧场", "放牧", "林地", "山林", "林木", "砍树", "地界", "边界", "田埂", "征地", "征收", "承包", "流转", "越界", "权属"],
    "债务劳资": ["工资", "欠薪", "劳务", "报酬", "农民工", "工程款", "借款", "欠款", "债务", "借贷", "赊购", "还钱", "受伤", "赔偿", "医疗费", "伤残", "工伤"],
    "邻里冲突": ["排水", "通风", "采光", "噪音", "通行", "相邻", "宅基地", "围墙", "过道", "邻里", "物业", "小区", "漏水", "扰民", "装修", "异味", "动物", "风俗", "诅咒", "撒米"],
    "彩礼纠纷": ["婚姻", "彩礼", "聘礼", "婚礼", "嫁娶", "婚约", "家庭", "调解"],
    "离婚纠纷": ["婚姻", "离婚", "感情", "分居", "抚养", "财产分割", "家庭"],
    "家暴纠纷": ["家暴", "暴力", "殴打", "虐待", "伤害", "人身安全"],
    "宅基地": ["宅基地", "地基", "房屋", "建房", "屋檐", "宅基"],
    "草场": ["草场", "草原", "牧场", "放牧", "围栏", "越界", "苏鲁克"],
    "林地": ["林地", "山林", "林木", "砍树", "采伐", "神山", "风水林"],
    "边界争议": ["地界", "边界", "田埂", "界桩", "四至", "越界"],
    "征地补偿": ["征地", "征收", "补偿", "拆迁", "安置"],
    "承包合同": ["承包", "流转", "租赁", "合同", "租金"],
    "欠薪": ["工资", "欠薪", "劳务", "报酬", "农民工", "工程款"],
    "债务": ["借款", "欠款", "债务", "借贷", "赊购", "还钱"],
    "劳务受害": ["受伤", "赔偿", "医疗费", "伤残", "工伤", "劳务"],
    # 邻里冲突子类场景词
    "相邻排水": ["排水", "漏水", "渗水", "用水", "水渠", "沟渠", "水利", "灌溉", "积水", "污水", "邻里", "相邻"],
    "相邻通行": ["通行", "道路", "通道", "走路", "过路", "运输", "必经", "邻里", "相邻"],
    "噪音扰民": ["噪音", "噪声", "扰民", "装修", "音响", "狗叫", "喧哗", "邻里", "相邻"],
    "相邻漏水": ["漏水", "渗水", "天花板", "墙壁", "管道", "防水", "邻里", "相邻", "物业"],
    "采光妨碍": ["采光", "日照", "阳光", "挡光", "遮阳", "建筑", "邻里", "相邻"],
    "异味污染": ["异味", "臭味", "油烟", "鸡粪", "臭气", "养殖", "排放", "邻里", "相邻"],
    "动物损害": ["动物", "宠物", "狗", "羊", "牲畜", "咬死", "啃食", "邻里", "相邻"],
    "树木越界": ["树木", "树枝", "树根", "竹子", "越界", "修剪", "邻里", "相邻"],
    "侵占房屋": ["侵占", "占用", "堆放", "杂物", "房屋", "空房", "邻里", "相邻"],
    "风俗侵权": ["风俗", "民俗", "习惯", "诅咒", "撒米", "精神损害", "邻里", "相邻"],
}

def get_primary_category(sub_category):
    """二级分类转一级分类，支持模糊匹配和关键词兜底"""
    if not sub_category:
        return ""
    if sub_category in CATEGORY_MAP:
        return CATEGORY_MAP[sub_category]
    for k, v in CATEGORY_MAP.items():
        if k in sub_category or sub_category in k:
            return v
    sc = sub_category
    if any(x in sc for x in ["婚姻", "彩礼", "婚约", "离婚", "家暴", "赡养", "抚养", "嫁妆", "抚养费"]):
        return "婚姻家庭"
    if any(x in sc for x in ["草场", "林地", "山林", "宅基地", "土地", "草原", "征地", "承包", "边界", "越界", "权属"]):
        return "土地山林"
    if any(x in sc for x in ["欠薪", "工资", "债务", "劳资", "劳务", "赔偿", "工伤", "借款", "欠款"]):
        return "债务劳资"
    if any(x in sc for x in ["邻里", "相邻", "排水", "通行", "采光", "噪音", "漏水", "异味", "动物", "侵占", "风俗", "树木"]):
        return "邻里冲突"
    return sub_category

def get_scene_keywords(category):
    return CATEGORY_SCENE_KEYWORDS.get(category, [category])

def load_knowledge_base():
    with open(KNOWLEDGE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def detect_custom_law_conflict(text, custom_law_flag=False, category_hint=""):
    kb = load_knowledge_base()
    custom_laws = kb.get('custom_laws', [])

    conflicts = []
    matched_laws = []

    def _extract_ethnicity_from_text(t):
        ethnic_keywords = ["藏族", "彝族", "苗族", "回族", "维吾尔族", "蒙古族", "壮族", "傣族", "土家族", "哈尼族", "哈萨克族", "侗族", "瑶族", "羌族", "纳西族", "门巴族", "珞巴族", "撒拉族"]
        for e in ethnic_keywords:
            if e in t:
                return e
        return None

    scene_keywords = get_scene_keywords(category_hint)
    primary = get_primary_category(category_hint)

    for law in custom_laws:
        match_keywords = set()
        # === 修复：民族名不再加入初始 match_keywords，避免"壮族"匹配所有壮族习惯法 ===
        # 原代码：match_keywords.add(law.get('ethnicity', ''))
        # 现改为：民族名只在 custom_law_flag=True 且前面未匹配时作为兜底

        name = law.get('name', '')
        # 改进 name 拆分，支持 / + 、 等分隔符
        name_clean = name.replace('制', ' ').replace('法', ' ').replace('（', ' ').replace('）', ' ').replace('/', ' ').replace('+', ' ').replace('、', ' ')
        for part in name_clean.split():
            if len(part) >= 2 and part not in ['调解', '制度', '规则', '法律', '习惯', '方法', '工作']:
                match_keywords.add(part)

        for scene in law.get('applicable_scenarios', []):
            for part in scene.replace('，', ',').replace('、', ',').split(','):
                if len(part.strip()) >= 2:
                    match_keywords.add(part.strip())

        is_matched = False
        for kw in match_keywords:
            if kw and kw in text:
                is_matched = True
                break

        # 特殊民族习惯法词汇直接匹配（解决"款首""咪谷""梯玛"等无法通过 name 拆分匹配的问题）
        if not is_matched:
            special_terms = {
                '款约': ['款首', '款约', '侗款'],
                '咪谷': ['咪谷', '最巴', '赶沟人', '欧嘎阿波'],
                '梯玛': ['梯玛'],
                '德古': ['德古'],
                '部落长老': ['部落长老', '长老'],
                '嘎查达': ['嘎查达'],
                '都老': ['都老', '寨老'],
                '阿訇': ['阿訇'],
                '石牌': ['石牌', '石牌头人'],
                '贝侬': ['贝侬'],
                '石榴籽': ['石榴籽'],
                '刻木分水': ['刻木分水', '刻木', '分水'],
                '乡所共治': ['乡所共治'],
                '团场': ['团场'],
                '草原诚信': ['草原诚信'],
                '部门联动': ['中心吹哨', '部门报到'],
                '苏鲁克': ['苏鲁克'],
                '烙印': ['烙印', '约孙'],
                '神山': ['神山', '圣水'],
                '贾理': ['贾理', '理老'],
                '榔规': ['榔规', '议榔'],
                '侗款': ['侗款', '款会', '埋岩'],
                '赔命价': ['赔命价', '赔血价'],
                '神判': ['神判'],
                '共妻': ['共妻', '一妻多夫'],
                '休妻': ['休妻'],
                '转房': ['转房', '收继婚', '填房婚', '安明格尔'],
                '不落夫家': ['不落夫家'],
                '姑舅表': ['姑舅表', '阿舅则美该'],
                '包办': ['包办', '红爷', '说亲', '定亲'],
                '早婚': ['早婚'],
                '塔拉克': ['塔拉克'],
                '拴线': ['拴线', '泼水', '休书'],
                '尼卡亥': ['尼卡亥'],
                '你姜': ['你姜', '陪礼钱', '破竹断婚'],
            }
            for key, aliases in special_terms.items():
                if key in name:
                    for alias in aliases:
                        if alias in text:
                            is_matched = True
                            break
                    if is_matched:
                        break

        # === 修复：民族名匹配改为兜底逻辑，仅在 custom_law_flag=True 且前面未匹配时触发 ===
        # 且要求该习惯法的 applicable_scenarios 与当前 category_hint 的大类相关
        if custom_law_flag and not is_matched:
            ethnicity = law.get('ethnicity', '')
            if ethnicity and ethnicity in text:
                # 增加约束：民族名单独匹配时，必须 applicable_scenarios 包含当前大类关键词
                law_scenes = law.get('applicable_scenarios', [])
                scene_relevant = False
                for scene in law_scenes:
                    if primary in scene or any(kw in scene for kw in scene_keywords):
                        scene_relevant = True
                        break
                # 邻里冲突额外放宽：允许"邻里""相邻""家庭""纠纷"等场景
                if not scene_relevant and primary == "邻里冲突":
                    for scene in law_scenes:
                        if any(x in scene for x in ["邻里", "相邻", "家庭", "纠纷", "矛盾", "用水", "通行", "土地", "边界"]):
                            scene_relevant = True
                            break
                if scene_relevant:
                    is_matched = True

        if is_matched and category_hint:
            law_scenes = law.get('applicable_scenarios', [])
            scene_match = False

            for scene in law_scenes:
                scene_lower = scene.lower()
                if primary in scene_lower:
                    scene_match = True
                    break
                for kw in scene_keywords:
                    if kw in scene_lower:
                        scene_match = True
                        break
                if scene_match:
                    break

            # 邻里冲突大类放宽 scene_match
            if not scene_match and primary == "邻里冲突":
                for scene in law_scenes:
                    if any(x in scene for x in ["邻里", "相邻", "家庭", "纠纷", "矛盾", "用水", "通行", "土地", "边界"]):
                        scene_match = True
                        break

            if scene_match and primary == "婚姻家庭":
                exclude_scenes = ["森林", "林木", "草场", "放牧", "债务", "欠款", "借款", "欠薪", "工伤", "赔偿", "杀人", "伤害", "环保", "矿产", "水源"]
                for scene in law_scenes:
                    if any(ex in scene for ex in exclude_scenes):
                        scene_match = False
                        break

            if not scene_match:
                is_matched = False

        if is_matched:
            content = law.get('content', '')
            matched_laws.append({
                'id': law.get('id', ''),
                'name': law.get('name', ''),
                'ethnicity': law.get('ethnicity', ''),
                'content': content[:120] + '...' if len(content) > 120 else content,
                'validity_level': law.get('validity_level', '参考性')
            })

            conflict_with = law.get('conflict_with', [])
            if conflict_with and len(conflict_with) > 0 and any(c for c in conflict_with if c):
                conflicts.append({
                    'custom_law_name': law.get('name', ''),
                    'ethnicity': law.get('ethnicity', ''),
                    'conflict_with': [c for c in conflict_with if c],
                    'conflict_note': '',
                    'coordination_suggestion': law.get('coordination_suggestion', ''),
                    'validity_level': law.get('validity_level', '参考性')
                })
                
    detected_ethnicity = _extract_ethnicity_from_text(text)
    if detected_ethnicity:
        # 如果文本明确提到了民族（如"哈尼族"），只保留该民族的习惯法
        matched_laws = [law for law in matched_laws if law.get('ethnicity') == detected_ethnicity]
        conflicts = [c for c in conflicts if c.get('ethnicity') == detected_ethnicity]

    return {
        'conflict_alert': len(conflicts) > 0,
        'conflicts': conflicts,
        'matched_custom_laws': matched_laws
    }

def get_related_laws(category):
    kb = load_knowledge_base()
    national_laws = kb.get('national_laws', [])

    primary = get_primary_category(category)
    related = []

    for law in national_laws:
        law_category = law.get('category', '')
        scenarios = law.get('applicable_scenarios', [])

        law_copy = dict(law)
        law_copy['title'] = law.get('name', '未命名法条')

        if law_category == primary:
            related.append(law_copy)
            continue

        if any(category in scenario for scenario in scenarios):
            related.append(law_copy)
            continue

        if any(scenario in category or category in scenario for scenario in scenarios):
            related.append(law_copy)

    return related

def extract_chinese_phrases(text, min_len=2, max_len=4):
    """提取文本中所有长度在 min_len~max_len 的连续子串（中文相似度核心）"""
    phrases = set()
    clean = ''.join(c for c in text if ('\u4e00' <= c <= '\u9fff') or c.isalnum())
    L = len(clean)
    for length in range(min_len, max_len + 1):
        for i in range(L - length + 1):
            phrases.add(clean[i:i+length])
    return phrases

def get_similar_cases(text, category, top_n=3):
    """相似案例匹配（修复：中文子串提取 + 标题高权重 + 民族 bonus）"""
    typical_cases_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'typical_cases.json')
    try:
        with open(typical_cases_path, 'r', encoding='utf-8') as f:
            cases_data = json.load(f)
    except Exception as e:
        print(f"[get_similar_cases] 读取失败: {e}")
        return []

    cases = []
    if isinstance(cases_data, list):
        cases = cases_data
    elif isinstance(cases_data, dict):
        cases = cases_data.get('cases', cases_data.get('typical_cases', cases_data.get('data', [])))
    else:
        return []

    if not cases:
        print("[get_similar_cases] 案例数量为 0")
        return []

    primary = get_primary_category(category)
    text_lower = text.lower()
    text_phrases = extract_chinese_phrases(text_lower)
    scored_cases = []

    same_category_count = 0

    for case in cases:
        if not isinstance(case, dict):
            continue

        case_category = case.get('category', '')
        case_primary = get_primary_category(case_category)

        if case_category and case_primary != primary:
            continue

        same_category_count += 1

        case_text = (case.get('description', '') + ' ' + case.get('title', '')).lower()
        case_phrases = extract_chinese_phrases(case_text)

        if not case_phrases:
            continue

        # 1. 基础分：子串重叠（每个重叠 +2 分，封顶 40）
        overlap = len(text_phrases & case_phrases)
        base_score = min(40, overlap * 2)

        # 2. 标题关键词 bonus（标题匹配权重更高，每个命中 +5 分）
        title_bonus = 0
        case_title = case.get('title', '').lower()
        title_phrases = extract_chinese_phrases(case_title)
        for tp in title_phrases:
            if tp in text_lower:
                title_bonus += 5

        # 3. 民族 bonus（同民族 +15 分）
        ethnic_bonus = 0
        ethnic_keywords = ["藏族", "彝族", "苗族", "回族", "维吾尔族", "蒙古族", "壮族", "傣族", "土家族", "哈尼族", "哈萨克族", "侗族", "瑶族", "羌族", "纳西族", "门巴族", "珞巴族", "撒拉族"]
        for ethnic in ethnic_keywords:
            if ethnic in text and ethnic in case_text:
                ethnic_bonus += 15

        final_similarity = min(100, base_score + title_bonus + ethnic_bonus)

        if final_similarity >= 1:
            scored_cases.append({
                'title': case.get('title', '未命名案例'),
                'similarity': final_similarity,
                'result': case.get('result', '调解成功'),
                'description': case.get('description', '')[:80] + '...'
            })

    scored_cases.sort(key=lambda x: x['similarity'], reverse=True)

    if scored_cases:
        print(f"[get_similar_cases] 匹配到 {len(scored_cases)} 条案例，最高相似度: {scored_cases[0]['similarity']}%，目标分类: {primary}")
    else:
        print(f"[get_similar_cases] 未匹配到案例。目标分类: {primary}，同分类案例数: {same_category_count}")

    return scored_cases[:top_n]

if __name__ == '__main__':
    test_text = "我是四川凉山彝族的，寨子里的人说找德古调解一下"
    res = detect_custom_law_conflict(test_text, custom_law_flag=True, category_hint="彩礼纠纷")
    print(json.dumps(res, ensure_ascii=False, indent=2))
