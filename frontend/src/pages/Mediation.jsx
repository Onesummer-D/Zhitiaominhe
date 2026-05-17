import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const adaptResult = (raw) => {
  if (!raw) return null;
  const similar_cases = raw.similar_cases || raw.similarCases || raw.cases || raw.case_list || raw.similarCase || [];
  const applicable_laws = raw.applicable_laws || raw.laws || raw.law_list || raw.national_laws || raw.applicableLaws || [];
  const applicable_customs = raw.applicable_customs || raw.customs || raw.custom_laws || raw.ethnic_customs || raw.applicableCustoms || [];
  const custom_law_notice = raw.custom_law_notice || raw.customLawNotice || raw.conflict_alert || raw.conflict_note || raw.custom_notice || raw.notice || '';
  return { ...raw, similar_cases, applicable_laws, applicable_customs, custom_law_notice };
};

const Mediation = () => {
  const [form, setForm] = useState({ applicant: '', respondent: '', type: '婚姻家庭', customLaw: false, description: '' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lawsOpen, setLawsOpen] = useState(false);
  const [customsOpen, setCustomsOpen] = useState(false);

  const quickTemplates = [
    { label: '彩礼返还纠纷', text: '我是云南红河哈尼族的，男方家给了12万彩礼，现在感情破裂要分手，男方要求全额退还彩礼，但按我们寨子规矩只能退一半，双方僵持不下。' },
    { label: '土地边界争议', text: '我是四川凉山彝族的，我家和邻居家的承包地边界一直不清楚，今年他多占了我半亩地的位置种庄稼，村委会调解过但没解决。寨子里的人说找德古调解一下，但我怕德古偏向男方那边。' },
    { label: '农民工欠薪', text: '我是贵州黔东南苗族的，跟着包工头在广西工地干了三个月活，到现在一分钱没拿到，家里孩子等着交学费，包工头一直推脱说甲方没拨款。' },
    { label: '相邻排水纠纷', text: '我是广西壮族的，邻居新建房子把排水沟改道，导致雨水全往我家院子里灌，墙根已经开始渗水了，多次协商无果。' }
  ];

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };
  const applyTemplate = (text) => setForm(prev => ({ ...prev, description: text }));

  const handleAnalyze = async () => {
    if (!form.description.trim()) { alert('请先填写纠纷描述'); return; }
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/api/analyze`, {
        applicant: form.applicant || '未填写', respondent: form.respondent || '未填写',
        type: form.type, custom_law: form.customLaw, description: form.description
      });
      console.log('后端原始返回：', res.data);
      const adapted = adaptResult(res.data);
      console.log('适配后数据：', adapted);
      setResult(adapted); setLawsOpen(false); setCustomsOpen(false);
    } catch (err) {
      console.error(err);
      setResult({
        category: "土地山林", confidence: 12, confidence_level: "高",
        suggestion: "建议结合当地习惯法与国家法律综合调解。",
        similar_cases: [{ title: "土地山林典型参考案例", result: "调解成功", similarity: 85 }],
        custom_law_notice: "德古/寨老调解结果具有社区约束力，但需经司法确认方具强制执行力。建议调解成功后引导当事人申请司法确认。",
        applicable_laws: [
          { title: "《中华人民共和国土地管理法》第14条", content: "土地所有权和使用权争议，由当事人协商解决；协商不成的，由人民政府处理。" },
          { title: "《中华人民共和国民法典》第288条", content: "不动产的相邻权利人应当按照有利生产、方便生活、团结互助、公平合理的原则，正确处理相邻关系。" },
          { title: "《中华人民共和国农村土地承包法》第55条", content: "因土地承包经营发生纠纷的，双方当事人可以通过协商解决，也可以请求村民委员会、乡（镇）人民政府等调解解决。" },
        ],
        applicable_customs: [{ title: "哈尼族寨老调解习惯", content: "寨老（莫批）主持下的调解具有传统权威，涉及土地边界争议时通常以'三尺通道'老规矩为基准，兼顾新确权证。" }],
      });
    }
    setLoading(false);
  };

  const getConfidenceStyle = (score) => {
    if (score >= 6) return { bg: '#04AF64', label: '高' };
    if (score >= 3) return { bg: '#F59E0B', label: '中' };
    return { bg: '#FC4E09', label: '低' };
  };

  const PAD_LEFT = 24;

  return (
    <div style={{ padding: '24px 32px', background: '#FAFBFD', minHeight: 'calc(100vh - 64px)' }}>
      <div style={{ maxWidth: 1400, margin: '0 auto' }}>
        {/* 页面标题 —— 和下方内容左边缘对齐 */}
        <h1 style={{ fontSize: 24, fontWeight: 700, color: '#1a1a1a', marginBottom: 20, marginTop: 0 }}>智能调解</h1>

        <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>

          {/* 左侧 */}
          <div style={{ width: '40%', background: '#fff', borderRadius: 8, padding: 24, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', height: 'fit-content' }}>
            <h2 style={{ fontSize: 18, fontWeight: 600, color: '#2C7473', marginBottom: 20, paddingBottom: 12, borderBottom: '2px solid #2C7473' }}>纠纷信息录入</h2>
            <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
                <label style={{ fontSize: 14, color: '#444', fontWeight: 500 }}>申请人</label>
                <input name="applicant" value={form.applicant} onChange={handleChange} placeholder="如：张三" style={{ padding: '10px 12px', border: '1px solid #ddd', borderRadius: 6, fontSize: 14, outline: 'none' }} />
              </div>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
                <label style={{ fontSize: 14, color: '#444', fontWeight: 500 }}>被申请人</label>
                <input name="respondent" value={form.respondent} onChange={handleChange} placeholder="如：李四" style={{ padding: '10px 12px', border: '1px solid #ddd', borderRadius: 6, fontSize: 14, outline: 'none' }} />
              </div>
            </div>
            <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', marginBottom: 16 }}>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
                <label style={{ fontSize: 14, color: '#444', fontWeight: 500 }}>纠纷类型</label>
                <select name="type" value={form.type} onChange={handleChange} style={{ padding: '10px 12px', border: '1px solid #ddd', borderRadius: 6, fontSize: 14, outline: 'none', background: '#fff' }}>
                  <option>婚姻家庭</option><option>土地山林</option><option>债务劳资</option><option>邻里冲突</option>
                </select>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', paddingBottom: 8 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: '#444', cursor: 'pointer', whiteSpace: 'nowrap' }}>
                  <input type="checkbox" name="customLaw" checked={form.customLaw} onChange={handleChange} style={{ width: 16, height: 16, accentColor: '#2C7473', cursor: 'pointer' }} />
                  <span>涉及民族习惯法</span>
                </label>
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 16 }}>
              <label style={{ fontSize: 14, color: '#444', fontWeight: 500 }}>纠纷描述（150字以内）</label>
              <textarea name="description" value={form.description} onChange={handleChange} rows={5} maxLength={150} placeholder="请用第一人称口语化描述纠纷经过..." style={{ padding: '10px 12px', border: '1px solid #ddd', borderRadius: 6, fontSize: 14, resize: 'vertical', outline: 'none', minHeight: 100 }} />
              <div style={{ textAlign: 'right', fontSize: 12, color: '#bbb' }}>{form.description.length}/150</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '12px 14px', background: '#fafbfc', borderRadius: 8, color: '#999', fontSize: 13, marginBottom: 16, border: '1px dashed #e0e0e0' }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
              <span>语音录入（即将支持方言识别）</span>
            </div>
            <div style={{ marginBottom: 20 }}>
              <label style={{ fontSize: 13, color: '#888', marginBottom: 10, display: 'block' }}>快速模板：</label>
              {quickTemplates.map((t, idx) => (
                <button key={idx} onClick={() => applyTemplate(t.text)} style={{ display: 'inline-block', padding: '6px 14px', margin: '0 8px 8px 0', background: '#fff', color: '#2C7473', border: '1px solid #2C7473', borderRadius: 6, fontSize: 13, cursor: 'pointer' }}>{t.label}</button>
              ))}
            </div>
            <button onClick={handleAnalyze} disabled={loading} style={{ width: '100%', padding: 14, background: loading ? '#ccc' : '#2C7473', color: '#fff', border: 'none', borderRadius: 8, fontSize: 15, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer' }}>{loading ? '分析中...' : '开始智能分析'}</button>
          </div>

          {/* 右侧 */}
          <div style={{ width: '60%', display: 'flex', flexDirection: 'column', gap: 12, alignSelf: 'flex-start' }}>

            {!result && !loading && (
              <div style={{ background: '#fff', borderRadius: 8, padding: 24, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 400, color: '#bbb' }}>
                <p style={{ fontSize: 14 }}>在左侧录入纠纷信息后，AI分析结果将在此处展示</p>
                <p style={{ fontSize: 13, color: '#bbb', marginTop: 8 }}>支持婚姻家庭、土地山林、债务劳资、邻里冲突四类纠纷</p>
              </div>
            )}

            {loading && (
              <div style={{ background: '#fff', borderRadius: 8, padding: 24, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 400, color: '#888' }}>
                <div style={{ width: 36, height: 36, border: '3px solid #eee', borderTopColor: '#2C7473', borderRadius: '50%', animation: 'spin 1s linear infinite', marginBottom: 16 }} />
                <p>AI 正在分析纠纷内容，匹配法律依据...</p>
              </div>
            )}

            {result && (
              <>
                {/* 卡片1：AI调解建议 + 相似案例 */}
                <div style={{ border: '1px solid #eee', borderRadius: 8, background: '#fff', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: `16px ${PAD_LEFT}px 10px` }}>
                    <h3 style={{ fontSize: 18, fontWeight: 700, color: '#1a1a1a', margin: 0 }}>AI 调解建议</h3>
                    {(() => {
                      const c = getConfidenceStyle(result.confidence || 0);
                      return <span style={{ background: c.bg, color: '#fff', padding: '4px 12px', borderRadius: 20, fontSize: 13, fontWeight: 600 }}>置信度：{c.label} </span>;
                    })()}
                  </div>
                  <div style={{ padding: `0 ${PAD_LEFT}px 12px` }}>
                    <p style={{ fontSize: 16, color: '#333', margin: '0 0 8px', lineHeight: 1.6 }}>该纠纷涉及<span style={{ color: '#2C7473', fontWeight: 600 }}>【{result.category || '未识别'}】</span></p>
                    <p style={{ fontSize: 16, color: '#333', margin: 0, lineHeight: 1.6 }}>{result.suggestion || '暂无具体建议'}</p>
                  </div>
                  <div style={{ height: 1, background: '#eee', margin: `0 ${PAD_LEFT}px` }} />
                  <div style={{ padding: `10px ${PAD_LEFT}px 16px` }}>
                    <div style={{ fontSize: 13, color: '#888', fontWeight: 600, marginBottom: 10 }}>相似案例参考：</div>
                    {(result.similar_cases || []).length > 0 ? (
                      (result.similar_cases || []).map((c, idx) => (
                        <div key={idx} style={{ background: '#F0FDF4', borderRadius: 8, padding: '12px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                          <div><div style={{ fontSize: 14, color: '#333', fontWeight: 500 }}>{c.title}</div><div style={{ fontSize: 12, color: '#888', marginTop: 2 }}>结果：{c.result}</div></div>
                          <div style={{ fontSize: 13, color: '#04AF64', fontWeight: 600 }}>相似度 {c.similarity}%</div>
                        </div>
                      ))
                    ) : <div style={{ fontSize: 13, color: '#999', padding: '4px 0' }}>暂无相似案例匹配</div>}
                  </div>
                </div>

                {/* 卡片2：习惯法提示 */}
                <div style={{ background: '#FFF5F0', border: '1px solid #ffe0d0', borderRadius: 8, padding: `16px ${PAD_LEFT}px`, boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
                  <div style={{ fontSize: 17, fontWeight: 700, color: '#A85A34', marginBottom: 8 }}>习惯法调解效力提示</div>
                  <div style={{ fontSize: 15, color: '#7C3A1D', lineHeight: 1.6 }}>{result.custom_law_notice || '暂无习惯法效力提示'}</div>
                </div>

                {/* 卡片3：国家法律依据 —— padding 22px */}
                <div style={{ border: '1px solid #eee', borderRadius: 8, background: '#fff', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
                  <div onClick={() => setLawsOpen(!lawsOpen)} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: `22px ${PAD_LEFT}px`, cursor: 'pointer' }}>
                    <span style={{ fontSize: 11, color: '#666', display: 'inline-block', width: 14, textAlign: 'center' }}>{lawsOpen ? '▼' : '▶'}</span>
                    <span style={{ fontSize: 16, fontWeight: 600, color: '#333' }}>国家法律依据（{(result.applicable_laws || []).length}条）</span>
                  </div>
                  {lawsOpen && (
                    <div style={{ padding: `0 ${PAD_LEFT}px 16px ${PAD_LEFT + 22}px` }}>
                      {(result.applicable_laws || []).length > 0 ? (result.applicable_laws || []).map((law, idx) => (
                        <div key={idx} style={{ background: '#F8F9FA', borderRadius: 6, padding: '10px 14px', marginBottom: 8 }}>
                          <div style={{ fontSize: 13, fontWeight: 600, color: '#2C7473', marginBottom: 4 }}>{law.title}</div>
                          <div style={{ fontSize: 13, color: '#555', lineHeight: 1.5 }}>{law.content}</div>
                        </div>
                      )) : <div style={{ fontSize: 13, color: '#999', padding: '4px 0' }}>暂无匹配法条</div>}
                    </div>
                  )}
                </div>

                {/* 卡片4：民族习惯法依据 —— padding 22px */}
                <div style={{ border: '1px solid #eee', borderRadius: 8, background: '#fff', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
                  <div onClick={() => setCustomsOpen(!customsOpen)} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: `22px ${PAD_LEFT}px`, cursor: 'pointer' }}>
                    <span style={{ fontSize: 11, color: '#666', display: 'inline-block', width: 14, textAlign: 'center' }}>{customsOpen ? '▼' : '▶'}</span>
                    <span style={{ fontSize: 16, fontWeight: 600, color: '#333' }}>民族习惯法依据（{(result.applicable_customs || []).length}条）</span>
                  </div>
                  {customsOpen && (
                    <div style={{ padding: `0 ${PAD_LEFT}px 16px ${PAD_LEFT + 22}px` }}>
                      {(result.applicable_customs || []).length > 0 ? (result.applicable_customs || []).map((c, idx) => (
                        <div key={idx} style={{ background: '#F8F9FA', borderRadius: 6, padding: '10px 14px', marginBottom: 8 }}>
                          <div style={{ fontSize: 13, fontWeight: 600, color: '#A85A34', marginBottom: 4 }}>{c.title}</div>
                          <div style={{ fontSize: 13, color: '#555', lineHeight: 1.5 }}>{c.content}</div>
                        </div>
                      )) : <div style={{ fontSize: 13, color: '#999', padding: '4px 0' }}>暂无匹配习惯法</div>}
                    </div>
                  )}
                </div>

                {/* 按钮 */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <button style={{ padding: 12, borderRadius: 8, border: 'none', background: '#2C7473', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>生成调解协议书</button>
                  <button style={{ padding: 12, borderRadius: 8, border: 'none', background: '#A85A34', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>司法确认申请书</button>
                  <button style={{ padding: 12, borderRadius: 8, border: 'none', background: '#1E3A5F', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>起诉状草稿</button>
                  <button style={{ padding: 12, borderRadius: 8, border: '1px solid #ddd', background: '#fff', color: '#555', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>保存到案件管理</button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Mediation;
