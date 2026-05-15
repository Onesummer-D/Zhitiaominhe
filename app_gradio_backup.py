import gradio as gr
import os
import json
import requests

# =================== 配置 ===================
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/chat/completions"

# =================== 内联知识库 ===================
KB = {
    "国家法律": [
        {"编号": "《民法典》第1042条", "内容": "禁止包办、买卖婚姻和其他干涉婚姻自由的行为。禁止借婚姻索取财物。", "场景": ["彩礼", "退婚", "离婚", "赡养", "抚养", "继承"]},
        {"编号": "《人民调解法》第17条", "内容": "当事人可以向人民调解委员会申请调解；人民调解委员会也可以主动调解。", "场景": ["调解", "纠纷", "申请"]},
        {"编号": "《土地管理法》第14条", "内容": "土地所有权和使用权争议，由当事人协商解决；协商不成的，由人民政府处理。", "场景": ["宅基地", "土地", "山林"]},
        {"编号": "《民法典》第288条", "内容": "不动产的相邻权利人应当按照有利生产、方便生活、团结互助、公平合理的原则，正确处理相邻关系。", "场景": ["相邻关系", "排水", "通行", "用水"]},
        {"编号": "《民法典》第290条", "内容": "不动产权利人应当为相邻权利人用水、排水提供必要的便利。", "场景": ["排水", "用水", "相邻关系", "田水"]},
        {"编号": "《劳动合同法》第30条", "内容": "用人单位应当按照劳动合同约定和国家规定，向劳动者及时足额支付劳动报酬。", "场景": ["欠薪", "工资", "劳动报酬", "老板"]},
    ],
    "民族习惯法": [
        {"民族": "哈尼族", "地域": "云南红河州元阳县", "习俗名称": "寨老调解制", "内容": "村寨中发生纠纷时，由寨老主持调解，双方当事人各述其理，寨老依据传统习俗和村规民约作出调解决定。", "适用场景": ["邻里纠纷", "家庭矛盾", "债务争议"], "效力等级": "参考性", "冲突提示": "与《人民调解法》第23条'调解应自愿平等'可能存在程序差异，需注意当事人自愿参与"},
        {"民族": "彝族", "地域": "云南红河州", "习俗名称": "德古调解", "内容": "由德古依据习惯法进行调解，注重恢复社会关系而非单纯惩罚。", "适用场景": ["打架斗殴", "财产损害", "婚姻家庭"], "效力等级": "补充性", "冲突提示": "涉及人身伤害时，习惯法中的赔命价与《刑法》第234条故意伤害罪存在冲突，应优先适用国家法律"},
        {"民族": "苗族", "地域": "云南黔东南", "习俗名称": "理老调解", "内容": "由'理老'（通晓古理、善辩的长者）依据'榔规''理词'进行调解，注重说理与道德教化。", "适用场景": ["邻里纠纷", "家庭矛盾", "债务争议"], "效力等级": "参考性", "冲突提示": "与《人民调解法》第8条'人民调解委员会'组织形式不同，需注意程序合规"},
    ]
}

# =================== 规则引擎 ===================
DISPUTE_TYPES = {
    "婚姻家庭": {"核心词": ["彩礼", "退婚", "离婚", "赡养", "抚养", "继承"], "特征词": ["老婆", "老公", "婆婆", "娘家", "嫁妆", "聘礼", "退亲"]},
    "土地山林": {"核心词": ["宅基地", "土地", "山林", "地界", "征地", "承包"], "特征词": ["种树", "砍树", "开荒", "引水", "田埂", "边界", "淹", "占", "越界"]},
    "债务劳资": {"核心词": ["欠薪", "欠钱", "工资", "借款", "债务", "工钱"], "特征词": ["老板", "包工头", "借钱", "不还", "拖欠", "赖账", "讨薪"]},
    "邻里冲突": {"核心词": ["噪音", "漏水", "挡光", "过道", "围墙"], "特征词": ["邻居", "楼上", "楼下", "隔壁", "院子", "通道", "扰民"]},
}

def classify_dispute(text):
    text = text.lower()
    scores = {}
    hits = {}
    for dtype, words in DISPUTE_TYPES.items():
        score = 0
        hit_words = []
        for w in words["核心词"]:
            if w in text:
                score += 3
                hit_words.append(f"{w}(+3)")
        for w in words["特征词"]:
            if w in text:
                score += 1
                hit_words.append(f"{w}(+1)")
        scores[dtype] = score
        hits[dtype] = hit_words
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary, score = sorted_scores[0]
    return primary, score, hits[primary], scores

def match_laws(text, dispute_type):
    results = {"国家法律": [], "民族习惯法": []}
    for law in KB["国家法律"]:
        match_score = sum(1 for s in law["场景"] if s in text)
        if match_score > 0:
            results["国家法律"].append((match_score, law))
    for custom in KB["民族习惯法"]:
        match_score = sum(1 for s in custom["适用场景"] if s in text)
        if dispute_type in custom["适用场景"]:
            match_score += 2
        if match_score > 0:
            results["民族习惯法"].append((match_score, custom))
    for key in results:
        results[key].sort(key=lambda x: x[0], reverse=True)
        results[key] = [item for _, item in results[key][:2]]
    return results

# =================== DeepSeek API 客户端 ===================
def call_deepseek_api(text, rule_type, rule_score):
    if not API_KEY:
        return None, "API Key未配置"
    
    system_prompt = """你是中国民族地区基层纠纷调解领域的AI专家，精通国家法律与云南红河州哈尼族、彝族、苗族等民族习惯法。
    
任务：根据村民口语化描述的纠纷，输出结构化分析结果。
要求：
1. 准确识别纠纷类型（婚姻家庭/土地山林/债务劳资/邻里冲突）
2. 结合《民法典》《人民调解法》《土地管理法》等国家法律
3. 参考哈尼族"寨老调解制"、彝族"德古调解"、苗族"理老调解"等民族习惯法
4. 指出国家法律与习惯法的冲突点
5. 给出具体可操作的调解建议

输出必须严格为JSON格式，不要任何其他文字：
{
    "dispute_type": "纠纷类型",
    "confidence": "高/中/低",
    "legal_basis": ["《法律名称》第X条 简要内容"],
    "custom_law": {
        "ethnic": "民族名称",
        "custom_name": "习俗名称",
        "content": "习俗内容摘要",
        "conflict_warning": "与国家法律的冲突提示"
    },
    "mediation_advice": "具体调解建议，包含法律方案和习惯法融合方案",
    "keywords": ["命中关键词1", "命中关键词2"]
}"""

    user_prompt = f"""纠纷描述：{text}

规则引擎初步判断：类型={rule_type}，得分={rule_score}（满分越高越确定，低于3分表示规则引擎不确定）。

请基于上述描述，给出更准确的语义分析结果。注意：
- 村民可能使用方言或口语化表达（如"田水淹到地里"=相邻土地排水纠纷）
- 要考虑哈尼族村寨的实际情况
- 如果涉及习惯法与国家法律冲突，明确指出优先适用哪个"""

    try:
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.3,
                "max_tokens": 1500
            },
            timeout=15
        )
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        result = json.loads(content)
        return result, None
    except Exception as e:
        return None, str(e)

# =================== 双引擎融合分析 ===================
def analyze_dispute(text):
    if not text or len(text.strip()) < 5:
        return "请输入至少5个字的纠纷描述", "", "", ""
    
    dispute_type, score, hits, all_scores = classify_dispute(text)
    laws = match_laws(text, dispute_type)
    
    need_api = (score < 3) or (all_scores.get("土地山林", 0) >= 2 and dispute_type != "土地山林")
    
    api_result = None
    api_error = None
    
    if need_api and API_KEY:
        api_result, api_error = call_deepseek_api(text, dispute_type, score)
        if api_result:
            dispute_type = api_result.get("dispute_type", dispute_type)
            hits = api_result.get("keywords", hits)
    
    engine_tag = "🤖 DeepSeek语义分析" if api_result else "⚡ 规则引擎"
    
    result_html = f"""
    <div class="result-box">
        <div class="box-header">📋 纠纷识别结果</div>
        <div class="engine-tag">{engine_tag}</div>
        <div class="info-row"><span class="label">纠纷类型：</span><span class="value highlight">{dispute_type}</span></div>
        <div class="info-row"><span class="label">置信度得分：</span><span class="value">{score} 分</span></div>
        <div class="info-row"><span class="label">命中关键词：</span><span class="value">{'、'.join(hits) if hits else '无'}</span></div>
        {f'<div class="error-msg">API错误：{api_error}</div>' if api_error else ''}
    </div>
    """
    
    law_html = ""
    custom_html = ""
    
    if api_result and api_result.get("legal_basis"):
        law_html += '<div class="section-title">⚖️ 国家法律依据（AI推荐）</div>'
        for law in api_result["legal_basis"]:
            law_html += f'<div class="law-card"><div class="card-icon">📜</div><div class="card-content"><b>{law}</b></div></div>'
    elif laws["国家法律"]:
        law_html += '<div class="section-title">⚖️ 国家法律依据</div>'
        for law in laws["国家法律"]:
            law_html += f'<div class="law-card"><div class="card-icon">📜</div><div class="card-content"><b>{law["编号"]}</b><br>{law["内容"][:100]}...</div></div>'
    else:
        law_html += '<div class="empty-tip">暂无直接匹配的国家法律条款</div>'
    
    if api_result and api_result.get("custom_law"):
        c = api_result["custom_law"]
        custom_html += f'<div class="section-title">🏔️ 民族习惯法参考（AI推荐）</div>'
        custom_html += f"""
        <div class="custom-card">
            <div class="card-icon">🎋</div>
            <div class="card-content">
                <b>{c['ethnic']} · {c['custom_name']}</b><br>
                {c['content'][:80]}...<<br>
                <span class="conflict-warning">⚠️ {c['conflict_warning'][:80]}...</span>
            </div>
        </div>
        """
    elif laws["民族习惯法"]:
        custom_html += '<div class="section-title">🏔️ 民族习惯法参考</div>'
        for c in laws["民族习惯法"]:
            custom_html += f"""
            <div class="custom-card">
                <div class="card-icon">🎋</div>
                <div class="card-content">
                    <b>{c["民族"]} · {c["习俗名称"]}</b>（{c["地域"]}）<<br>
                    效力等级：<span class="level-tag">{c["效力等级"]}</span><br>
                    {c["内容"][:80]}...<<br>
                    <span class="conflict-warning">⚠️ {c["冲突提示"][:80]}...</span>
                </div>
            </div>
            """
    else:
        custom_html += '<div class="empty-tip">暂无匹配的民族习惯法条目</div>'
    
    if api_result and api_result.get("mediation_advice"):
        advice_text = api_result["mediation_advice"]
    else:
        first_law = laws['国家法律'][0]['编号'] if laws['国家法律'] else '相关法律'
        first_ethnic = laws['民族习惯法'][0]['民族'] if laws['民族习惯法'] else '当地'
        advice_text = f"依据《{first_law}》进行依法调解；可邀请{first_ethnic}德高望重的长者参与，兼顾民俗情感；注意习惯法与国家法律的冲突点，涉及人身/财产重大权益时优先适用法律。"
    
    advice = f"""
    <div class="advice-box">
        <div class="box-header">💡 AI调解建议</div>
        <div class="advice-content">{advice_text}</div>
    </div>
    """
    
    return result_html, law_html, custom_html, advice

# =================== 民族风CSS ===================
CSS = """
/* ===== 全局底色（宣纸纹理感） ===== */
body { 
    background: #f7f3e8 !important; 
}

/* ===== 顶部Banner（藏蓝渐变+金色边框） ===== */
.main-title { 
    text-align: center; 
    font-size: 26px; 
    font-weight: bold; 
    padding: 20px; 
    margin-bottom: 20px;
    color: #f5f0e8;
    background: linear-gradient(135deg, #1e3a5f 0%, #2e5c8a 50%, #1e3a5f 100%);
    border-radius: 12px;
    border: 2px solid #c9a961;
    box-shadow: 0 4px 15px rgba(30, 58, 95, 0.3);
    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    letter-spacing: 2px;
}

/* ===== 左侧输入区装饰 ===== */
.input-panel {
    background: #fffdf5;
    border-radius: 12px;
    border: 1px solid #d4c4a8;
    padding: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

/* ===== 结果卡片通用样式（卷轴感） ===== */
.result-box, .advice-box {
    background: #fffdf5;
    border-radius: 10px;
    padding: 0;
    margin-top: 12px;
    border: 1px solid #d4c4a8;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    overflow: hidden;
}

.box-header {
    background: linear-gradient(90deg, #1e3a5f, #2e5c8a);
    color: #f5f0e8;
    padding: 10px 16px;
    font-size: 16px;
    font-weight: bold;
    border-bottom: 2px solid #c9a961;
}

.engine-tag {
    display: inline-block;
    background: #e8f4f8;
    color: #1e3a5f;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 12px;
    margin: 8px 16px;
    border: 1px solid #b8d4e3;
}

.info-row {
    padding: 6px 16px;
    font-size: 14px;
    color: #333;
}

.label {
    color: #666;
    font-weight: bold;
    display: inline-block;
    width: 90px;
}

.value {
    color: #1e3a5f;
}

.value.highlight {
    color: #c45c26;
    font-weight: bold;
    font-size: 16px;
}

.error-msg {
    color: #c0392b;
    padding: 6px 16px;
    font-size: 13px;
}

/* ===== 法条卡片（藏蓝边框） ===== */
.law-card {
    background: #fff;
    border-left: 4px solid #1e3a5f;
    margin: 10px 16px;
    padding: 12px;
    border-radius: 0 8px 8px 0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    display: flex;
    align-items: flex-start;
}

/* ===== 习惯法卡片（赭石边框） ===== */
.custom-card {
    background: #fffdf8;
    border-left: 4px solid #c45c26;
    margin: 10px 16px;
    padding: 12px;
    border-radius: 0 8px 8px 0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    display: flex;
    align-items: flex-start;
}

/* ===== 建议卡片（青绿边框） ===== */
.advice-box {
    border-left: 4px solid #2e7d32;
}

.advice-content {
    padding: 14px 16px;
    line-height: 1.8;
    color: #333;
    font-size: 14px;
}

/* ===== 卡片内图标 ===== */
.card-icon {
    font-size: 24px;
    margin-right: 12px;
    flex-shrink: 0;
}

.card-content {
    flex: 1;
    font-size: 14px;
    line-height: 1.6;
    color: #333;
}

/* ===== 冲突警告文字 ===== */
.conflict-warning {
    color: #c0392b;
    font-size: 13px;
    display: block;
    margin-top: 6px;
}

/* ===== 效力等级标签 ===== */
.level-tag {
    display: inline-block;
    background: #fff3e0;
    color: #c45c26;
    padding: 1px 8px;
    border-radius: 4px;
    font-size: 12px;
    border: 1px solid #ffcc80;
}

/* ===== 区块标题 ===== */
.section-title {
    font-size: 15px;
    font-weight: bold;
    color: #1e3a5f;
    margin: 14px 16px 6px 16px;
    padding-bottom: 4px;
    border-bottom: 1px dashed #d4c4a8;
}

/* ===== 空提示 ===== */
.empty-tip {
    color: #999;
    padding: 12px 16px;
    font-size: 14px;
    font-style: italic;
}

/* ===== 按钮美化 ===== */
button.primary {
    background: linear-gradient(135deg, #c45c26 0%, #a04010 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 8px rgba(196, 92, 38, 0.3) !important;
}
"""

# =================== Gradio 界面 ===================
with gr.Blocks() as demo:
    gr.HTML('<div class="main-title">🌾 智调民和 —— 民族地区基层纠纷智能调解与法律适配系统</div>')
    
    with gr.Row():
        # 左栏：输入
        with gr.Column(scale=1):
            gr.Markdown('<div class="input-panel">')
            gr.Markdown("### 📝 纠纷描述录入")
            input_text = gr.TextArea(
                label="",
                placeholder="例如：我是元阳县哈尼族的，邻居家的田水淹到我家地里了，寨老说各退一步，但我不服...",
                lines=10,
                show_label=False
            )
            gr.Markdown('</div>')
            with gr.Row():
                btn_analyze = gr.Button("🔍 开始分析", variant="primary", scale=2)
                btn_clear = gr.Button("🔄 清空", scale=1)
        
        # 右栏：结果
        with gr.Column(scale=2):
            gr.Markdown("### 📊 智能分析结果")
            out_result = gr.HTML()
            out_law = gr.HTML()
            out_custom = gr.HTML()
            out_advice = gr.HTML()
    
    btn_analyze.click(fn=analyze_dispute, inputs=input_text, outputs=[out_result, out_law, out_custom, out_advice])
    btn_clear.click(fn=lambda: ("", "", "", ""), inputs=None, outputs=[out_result, out_law, out_custom, out_advice])

if __name__ == "__main__":
    demo.launch(css=CSS)