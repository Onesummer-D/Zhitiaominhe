from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import requests

# ========== 配置 ==========
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/chat/completions"

# ========== 知识库 ==========
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

输出必须严格为JSON格式：
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
规则引擎初步判断：类型={rule_type}，得分={rule_score}（低于3分表示不确定）。
请给出更准确的语义分析结果。注意村民可能使用方言或口语化表达。"""

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

def analyze(text):
    if not text or len(text.strip()) < 5:
        return {"error": "请输入至少5个字的纠纷描述"}
    
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
    
    engine_tag = "DeepSeek语义分析" if api_result else "规则引擎"
    
    law_list = []
    if api_result and api_result.get("legal_basis"):
        law_list = [{"编号": l, "内容": ""} for l in api_result["legal_basis"]]
    elif laws["国家法律"]:
        law_list = laws["国家法律"]
    
    custom_list = []
    if api_result and api_result.get("custom_law"):
        c = api_result["custom_law"]
        custom_list = [{
            "民族": c["ethnic"], "习俗名称": c["custom_name"], "地域": "",
            "内容": c["content"], "效力等级": "", "冲突提示": c["conflict_warning"]
        }]
    elif laws["民族习惯法"]:
        custom_list = laws["民族习惯法"]
    
    if api_result and api_result.get("mediation_advice"):
        advice = api_result["mediation_advice"]
    else:
        first_law = law_list[0]["编号"] if law_list else "相关法律"
        first_ethnic = custom_list[0]["民族"] if custom_list else "当地"
        advice = f"依据《{first_law}》进行依法调解；可邀请{first_ethnic}德高望重的长者参与，兼顾民俗情感；注意习惯法与国家法律的冲突点，涉及人身/财产重大权益时优先适用法律。"
    
    return {
        "dispute_type": dispute_type,
        "score": score,
        "hits": hits,
        "engine": engine_tag,
        "laws": law_list,
        "customs": custom_list,
        "advice": advice,
        "api_error": api_error
    }

# ========== FastAPI ==========
app = FastAPI(title="智调民和API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class DisputeRequest(BaseModel):
    text: str

@app.post("/api/analyze")
async def api_analyze(req: DisputeRequest):
    return analyze(req.text)

@app.get("/")
async def root():
    return {"message": "智调民和API运行中", "docs": "http://localhost:8000/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)