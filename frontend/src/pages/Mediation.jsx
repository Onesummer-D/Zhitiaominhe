import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useLocation, useNavigate } from 'react-router-dom';

const API_BASE = 'http://localhost:8000';

const adaptResult = (raw) => {
  if (!raw) return null;
  const similar_cases = raw.similar_cases || raw.similarCases || raw.cases || raw.case_list || raw.similarCase || [];
  const applicable_laws = raw.applicable_laws || raw.laws || raw.law_list || raw.national_laws || raw.applicableLaws || [];
  const applicable_customs = raw.applicable_customs || raw.customs || raw.custom_laws || raw.ethnic_customs || raw.applicableCustoms || [];
  const custom_law_notice = raw.custom_law_notice || raw.customLawNotice || raw.conflict_note || raw.conflict_alert || raw.custom_notice || raw.notice || '';
  return { ...raw, similar_cases, applicable_laws, applicable_customs, custom_law_notice };
};

// 从描述里提取民族名
const extractEthnicity = (text) => {
  const ethnicKeywords = ["藏族", "彝族", "苗族", "回族", "维吾尔族", "蒙古族", "壮族", "傣族", "土家族", "哈尼族", "哈萨克族", "侗族", "瑶族", "羌族", "纳西族", "门巴族", "珞巴族", "撒拉族"];
  for (const e of ethnicKeywords) if (text.includes(e)) return e;
  return '';
};

// 从描述里提取地名
const extractRegion = (text) => {
  const m = text.match(/(青海|四川|云南|贵州|广西|新疆|甘肃|湖北|湖南|内蒙古|西藏)[^\s，。]{1,6}(州|市|县|旗)/);
  return m ? m[0] : '';
};

// 格式化建议文本：确保有段落换行
const formatSuggestion = (text) => {
  if (!text) return '暂无具体建议';
  if (text.includes('\n')) return text;
  // 无换行时，按中文序号和关键词自动分段
  return text
    .replace(/([。；!])\s*(?=[一二三四五六七八九十1234567890]+[、.．]\s*)/g, '$1\n\n')
    .replace(/([。；])\s*(?=建议|注意|若|如|依据|涉及|根据|请|可)/g, '$1\n\n');
};

// ===== 新增：从纠纷描述自动抽取关键实体 =====
const extractEntities = (text) => {
  const entities = {
    amount: '________',
    date: '________',
    breach: '________',
    property: '________',
    injury: '________',
  };
  
  // 金额提取：匹配 "XX万/千/元/块"
  const amountMatch = text.match(/(\d+(?:\.\d+)?)\s*(万|千|元|块)/);
  if (amountMatch) {
    const num = parseFloat(amountMatch[1]);
    const unit = amountMatch[2];
    if (unit === '万') entities.amount = String(num * 10000);
    else if (unit === '千') entities.amount = String(num * 1000);
    else entities.amount = String(num);
  }
  
  // 日期提取
  const year = new Date().getFullYear();
  const dateMatch = text.match(/(\d{4})年(\d{1,2})月/);
  if (dateMatch) {
    entities.date = `${dateMatch[1]}年${dateMatch[2]}月`;
  } else if (text.includes('去年')) {
    entities.date = `${year - 1}年`;
  } else if (text.includes('今年')) {
    entities.date = `${year}年`;
  }
  
  // 违约行为/侵权事实提取
  if (text.includes('漏水') || text.includes('渗水')) entities.breach = '房屋漏水导致天花板受损';
  else if (text.includes('噪音') || text.includes('扰民')) entities.breach = '制造噪声干扰他人正常生活';
  else if (text.includes('采光') || text.includes('挡光')) entities.breach = '建造建筑物妨碍相邻建筑物采光';
  else if (text.includes('通行') || text.includes('不让过') || text.includes('堵住') || text.includes('挡路')) entities.breach = '妨碍相邻权利人正常通行';
  else if (text.includes('占用') || text.includes('堆放') || text.includes('杂物')) entities.breach = '占用共用通道堆放杂物';
  else if (text.includes('欠款') || text.includes('拖欠')) entities.breach = '未按约定支付款项';
  else if (text.includes('工资') || text.includes('欠薪') || text.includes('劳务费')) entities.breach = '拖欠劳动报酬';
  else if (text.includes('彩礼') || text.includes('聘礼')) entities.breach = '借婚姻索取财物';
  else if (text.includes('家暴') || text.includes('殴打') || text.includes('虐待')) entities.breach = '实施家庭暴力';
  
  // 损害结果
  if (text.includes('受伤') || text.includes('伤残') || text.includes('住院')) entities.injury = '人身损害';
  else if (text.includes('损失') || text.includes('损坏') || text.includes('泡坏') || text.includes('黄了')) entities.injury = '财产损失';
  
  return entities;
};

const Mediation = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  const [form, setForm] = useState({ applicant: '', respondent: '', type: '婚姻家庭', customLaw: false, description: '' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lawsOpen, setLawsOpen] = useState(false);
  const [customsOpen, setCustomsOpen] = useState(false);

  // 从案件管理跳转回来时自动填充
  useEffect(() => {
    if (location.state?.caseData) {
      const c = location.state.caseData;
      setForm({
        applicant: c.applicant || '',
        respondent: c.respondent || '',
        type: c.dispute_type || '婚姻家庭',
        customLaw: c.custom_law_involved || false,
        description: c.description || ''
      });
      if (c.analysis_result) {
        setResult(adaptResult(c.analysis_result));
        setLawsOpen(false);
        setCustomsOpen(false);
      }
      // 清空路由state，防止刷新重复填充
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

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
    setResult(null);
    setLawsOpen(false);
    setCustomsOpen(false);
    try {
      const res = await axios.post(`${API_BASE}/api/analyze`, {
        applicant: form.applicant || '未填写', respondent: form.respondent || '未填写',
        type: form.type, custom_law: form.customLaw, description: form.description
      });
      console.log('后端原始返回：', res.data);
      const adapted = adaptResult(res.data);
      console.log('适配后数据：', adapted);
      setResult(adapted);
    } catch (err) {
      console.error(err);
      alert('分析失败，请检查后端服务');
    }
    setLoading(false);
  };

  const getConfidenceStyle = (score) => {
    if (score >= 6) return { bg: '#04AF64', label: '高' };
    if (score >= 3) return { bg: '#F59E0B', label: '中' };
    return { bg: '#FC4E09', label: '低' };
  };

  // 生成文书并导出Word —— 接入队友真实模板
  const handleGenerateDoc = async (docType) => {
    if (!result || !form.description) { alert('请先完成智能分析'); return; }

    const nowStr = new Date().toLocaleDateString('zh-CN');
    const year = new Date().getFullYear();
    const ethnicity = extractEthnicity(form.description) || '________';
    const regionStr = extractRegion(form.description) || '';
    
    // ===== 新增：自动抽取实体 =====
    const entities = extractEntities(form.description);
    
    // 简易地址分解
    let province = '________', county = '________', township = '________', village = '________';
    if (regionStr) {
      const provMatch = regionStr.match(/^(青海|四川|云南|贵州|广西|新疆|甘肃|湖北|湖南|内蒙古|西藏)/);
      if (provMatch) province = provMatch[1] + '省';
      const countyMatch = regionStr.match(/([^省市区州盟]+?[县旗])/);
      if (countyMatch) county = countyMatch[1];
    }

    const context = {
      // 当事人信息
      '甲方姓名': form.applicant || '________',
      '乙方姓名': form.respondent || '________',
      '甲方姓名/单位名称': form.applicant || '________',
      '乙方姓名/单位名称': form.respondent || '________',
      '原告姓名': form.applicant || '________',
      '被告姓名': form.respondent || '________',
      '申请人姓名': form.applicant || '________',
      '被申请人姓名': form.respondent || '________',
      '其他当事人姓名': '________',
      
      // 基本信息
      '性别': '________',
      '民族': ethnicity,
      '身份证号': '________',
      '联系电话': '________',
      
      // 地址
      '省': province,
      '市': '________',
      '县': county,
      '乡': township,
      '村': village,
      '住址': regionStr || '________',
      '住所': '________',
      
      // 纠纷信息（自动填充）
      '纠纷简述': form.description,
      '纠纷原因': form.description,
      
      // 日期（自动填充）
      '调解日期': nowStr,
      '起诉日期': nowStr,
      '申请日期': nowStr,
      '结婚日期': entities.date,
      '离婚日期': '________',
      '分居起始日期': entities.date,
      '借款日期': entities.date,
      '合同签订日期': entities.date,
      '欠款起始日期': entities.date,
      '事故发生日期': entities.date,
      '首期支付日期': '________',
      '第二期支付日期': '________',
      '尾款支付日期': '________',
      '剩余款项支付日期': '________',
      
      // 金额（自动填充）
      '赔偿金额': entities.amount,
      '赔偿总额': entities.amount,
      '欠款金额': entities.amount,
      '欠款总额': entities.amount,
      '大写金额': entities.amount,
      '实际支付总额': entities.amount,
      '减免金额': entities.amount,
      '首期金额': entities.amount,
      '第二期金额': entities.amount,
      '尾款金额': entities.amount,
      '当庭支付金额': entities.amount,
      '剩余金额': entities.amount,
      '抚养费金额': '________',
      '医疗费金额': '________',
      '利率标准': '________',
      
      // 人员/机构
      '子女姓名': '________',
      '抚养方': '________',
      '工作单位': '________',
      '职业': '________',
      '文化程度': '________',
      '政治面貌': '________',
      '婚姻状况': '________',
      '籍贯': '________',
      '医院名称': '________',
      '诊断结果': '________',
      '鉴定机构名称': '________',
      '伤残等级': '________',
      '民间调解人': '________',
      '习惯法调解人员': '________',
      
      // 调解/司法机构
      '调解机构名称': '________人民调解委员会',
      '地区简称': '________',
      '年份': String(year),
      '编号': '001',
      '份数': '三',
      '调解方法': '________',
      '债务减免条款': '________',
      '村委会/乡镇司法所/人民调解委员会': '________',
      '有管辖权的人民法院': '________人民法院',
      '有管辖权的人民检察院': '________人民检察院',
      '作出生效法律文书的法院名称': '________人民法院',
      '生效法律文书文号': '________',
      
      // 合同/案件信息（自动填充）
      '合同名称': '________',
      '合同/协议名称': '________',
      '合同主要内容': entities.breach,
      '合同义务': '依约履行义务',
      '款项性质': '________',
      '工作场所': '________',
      '工作地点': '________',
      '工作内容': '________',
      '事故原因': '________',
      '受伤部位': '________',
      '受伤部位及伤情描述': entities.injury,
      '伤情描述': entities.injury,
      '医疗费': '________',
      
      // 具体请求/侵权（自动填充）
      '具体请求，如：拆除越界搭建的围墙/修复漏水管道/清理通道杂物/调整空调外机位置': entities.breach,
      '具体侵权行为，如：房屋漏水导致原告天花板受损/在共用通道堆放杂物妨碍通行/擅自将排水沟改道致使原告家积水': entities.breach,
      
      // 证据材料
      '借款合同': '________',
      '借条': '________',
      '工资单': '________',
      '送货单': '________',
      '对账单': '________',
      '催收记录': '________',
      '医疗费票据': '________',
      '住院病历': '________',
      '诊断证明': '________',
      '司法鉴定意见书': '________',
      '司法鉴定意见书（如有）': '________',
      '工资记录': '________',
      '考勤记录': '________',
      '证人证言': '________',
      '事故现场照片': '________',
      '事故现场视频': '________',
      '事故现场照片/视频': '________',
      '习惯法调解记录': '________',
      '综治中心调解记录': '________',
      '夫妻分居证明': '________',
      '证明借款系其他当事人单方行为的证据': '________',
      '证明借款未用于夫妻共同生活的证据': '________',
      '其他证明材料': '________',
      
      // 土地/财产相关
      '原告依法享有该地块的使用权（已取得林权证/承包合同/政府确权决定等）': '________',
      '被告实施了侵权行为，侵占原告土地': '________',
      '侵权现场照片/视频': '________',
      '土地界桩照片/卫星定位图': '________',
      '村委会/乡镇人民政府确权文件': '________',
      '土地承包经营权证/林权证': '________',
      '结婚证复印件': '________',
      '户口本复印件': '________',
      '家暴报警记录/医院诊断证明（如适用）': '________',
      '财产权属证明': '________',
      '财产清单': '________',
      
      // 调解结果与复合变量
      '调解结果第一条': '________',
      '调解结果第二条': '________',
      '履行方式': '________',
      '履行期限': '________',
      '原审判决情况': '________',
      '原审判决书/裁定书': '________',
      '借款合同/借条': '________',
      '合同/协议/欠条': '________',
      '工资单/送货单/对账单': '________',
    };

    try {
      const res = await axios.post(`${API_BASE}/api/documents/generate`, {
        category: result.category,
        doc_type: docType,
        field_values: context
      });
      if (res.data.error) { alert(res.data.error); return; }

      // 拆分标题与正文：第一行非空文字作为标题居中，其余留在pre里
      const rawContent = res.data.content || '';
      const lines = rawContent.split('\n');
      let titleLine = '';
      let bodyStartIdx = 0;
      for (let i = 0; i < lines.length; i++) {
        if (lines[i].trim()) {
          titleLine = lines[i].trim();
          bodyStartIdx = i + 1;
          break;
        }
      }
      const bodyContent = lines.slice(bodyStartIdx).join('\n');

      const html = `
        <html><head><meta charset="utf-8"><title>${res.data.title}</title>
        <style>
          @page { size: A4; margin: 3.7cm 2.6cm 3.5cm 2.8cm; }
          body{font-family:"FangSong_GB2312","仿宋_GB2312","SimFang","仿宋","SimSun","宋体",serif;max-width:720px;margin:40px auto;padding:0;line-height:28pt;color:#000;font-size:16pt}
          .doc-title{text-align:center;font-family:"SimHei","黑体","SimSun","宋体",sans-serif;font-size:22pt;font-weight:bold;color:#000;margin-bottom:30px}
          pre{white-space:pre-wrap;font-family:"FangSong_GB2312","仿宋_GB2312","仿宋","SimSun","宋体",serif;font-size:16pt;line-height:28pt;margin:0}
        </style></head><body>
        <h2 class="doc-title">${titleLine}</h2>
        <pre>${bodyContent.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>
        </body></html>
      `;
      const blob = new Blob(['\ufeff', html], { type: 'application/msword' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${res.data.title}.doc`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert('生成文书失败：' + (err.response?.data?.detail || err.message));
    }
  };

  // 清空所有内容
  const handleClear = () => {
    setForm({ applicant: '', respondent: '', type: '婚姻家庭', customLaw: false, description: '' });
    setResult(null);
    setLawsOpen(false);
    setCustomsOpen(false);
  };

  // 保存到案件管理 —— 字段对齐后端 CaseCreate
  const handleSaveCase = async () => {
    if (!result) { alert('请先完成智能分析'); return; }
    try {
      await axios.post(`${API_BASE}/api/cases`, {
        title: `${form.applicant || '未知'} vs ${form.respondent || '未知'} - ${result.category}`,
        applicant: form.applicant || '',
        respondent: form.respondent || '',
        dispute_type: form.type,
        custom_law_involved: form.customLaw,
        description: form.description,
        status: 'pending',
        analysis_result: result,
        region: extractRegion(form.description),
        ethnicity: extractEthnicity(form.description),
        created_at: new Date().toISOString()
      });
      alert('案件已保存到案件管理');
    } catch (err) {
      console.error(err);
      alert('保存失败：' + (err.response?.data?.detail || err.message));
    }
  };

  const PAD_LEFT = 24;

  return (
    <div style={{ padding: '24px 32px', background: '#FAFBFD', minHeight: 'calc(100vh - 64px)' }}>
      <div style={{ maxWidth: 1400, margin: '0 auto' }}>
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
            <button onClick={handleClear} style={{ width: '100%', padding: 14, marginTop: 12, background: '#2C7473', color: '#fff', border: 'none', borderRadius: 8, fontSize: 15, fontWeight: 600, cursor: 'pointer' }}>清空</button>
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
                    <p style={{ fontSize: 16, color: '#333', margin: 0, lineHeight: 1.6, whiteSpace: 'pre-line' }}>{formatSuggestion(result.suggestion)}</p>
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
                <div style={{ background: '#ffffff', border: '1.5px solid #A85A34', borderRadius: 8, padding: `16px ${PAD_LEFT}px`, boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
                  <div style={{ fontSize: 17, fontWeight: 700, color: '#A85A34', marginBottom: 8 }}>习惯法调解效力提示</div>
                  <div style={{ fontSize: 15, color: '#333333', lineHeight: 1.6, whiteSpace: 'pre-line' }}>
                    {result.custom_law_notice || '未检测到习惯法冲突。若调解过程中涉及民族习惯法，请注意习惯法调解结果需经司法确认方具强制执行力。'}
                  </div>
                </div>

                {/* 卡片3：国家法律依据 */}
                <div style={{ border: '1px solid #eee', borderRadius: 8, background: '#fff', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
                  <div onClick={() => setLawsOpen(!lawsOpen)} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: `16px ${PAD_LEFT}px`, cursor: 'pointer' }}>
                    <span style={{ fontSize: 11, color: '#666', display: 'inline-block', width: 14, textAlign: 'center' }}>{lawsOpen ? '▼' : '▶'}</span>
                    <span style={{ fontSize: 17, fontWeight: 600, color: '#333' }}>国家法律依据（{(result.applicable_laws || []).length}条）</span>
                  </div>
                  {lawsOpen && (
                    <div style={{ padding: `0 ${PAD_LEFT}px 16px ${PAD_LEFT + 22}px` }}>
                      {(result.applicable_laws || []).length > 0 ? (result.applicable_laws || []).map((law, idx) => (
                        <div key={idx} style={{ marginBottom: 16 }}>
                          <div style={{ fontSize: 16, fontWeight: 700, color: '#2C7473', marginBottom: 6 }}>{law.title || law.name || '未命名法条'}</div>
                          <div style={{ fontSize: 15, color: '#444', lineHeight: 1.7 }}>{law.content}</div>
                        </div>
                      )) : <div style={{ fontSize: 15, color: '#999', padding: '4px 0' }}>暂无匹配法条</div>}
                    </div>
                  )}
                </div>

                {/* 卡片4：民族习惯法依据 */}
                <div style={{ border: '1px solid #eee', borderRadius: 8, background: '#fff', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
                  <div onClick={() => setCustomsOpen(!customsOpen)} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: `16px ${PAD_LEFT}px`, cursor: 'pointer' }}>
                    <span style={{ fontSize: 11, color: '#666', display: 'inline-block', width: 14, textAlign: 'center' }}>{customsOpen ? '▼' : '▶'}</span>
                    <span style={{ fontSize: 17, fontWeight: 600, color: '#333' }}>民族习惯法依据（{(result.applicable_customs || []).length}条）</span>
                  </div>
                  {customsOpen && (
                    <div style={{ padding: `0 ${PAD_LEFT}px 16px ${PAD_LEFT + 22}px` }}>
                      {(result.applicable_customs || []).length > 0 ? (result.applicable_customs || []).map((c, idx) => (
                        <div key={idx} style={{ marginBottom: 16 }}>
                          <div style={{ fontSize: 16, fontWeight: 700, color: '#A85A34', marginBottom: 6 }}>{c.title || c.name || '未命名习惯法'}</div>
                          <div style={{ fontSize: 15, color: '#444', lineHeight: 1.7 }}>{c.content}</div>
                        </div>
                      )) : <div style={{ fontSize: 15, color: '#999', padding: '4px 0' }}>暂无匹配习惯法</div>}
                    </div>
                  )}
                </div>

                {/* 动态文书按钮：根据纠纷类型显示可用模板 */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  {(() => {
                    const cat = result.category || '';
                    const isDebt = cat.includes('债务') || cat.includes('欠薪') || cat.includes('劳资') || cat.includes('工资');
                    const isNeighbor = cat.includes('邻里') || cat.includes('相邻') || cat.includes('噪音') || cat.includes('漏水') || cat.includes('通行') || cat.includes('采光');
                    
                    const buttons = [];
                    
                    // 所有类型都有调解协议书
                    buttons.push(
                      <button key="mediation" onClick={() => handleGenerateDoc('mediation')} style={{ padding: 12, borderRadius: 8, border: 'none', background: '#2C7473', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>生成调解协议书</button>
                    );
                    
                    if (isNeighbor) {
                      buttons.push(
                        <button key="lawsuit" onClick={() => handleGenerateDoc('lawsuit')} style={{ padding: 12, borderRadius: 8, border: 'none', background: '#A85A34', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>生成民事起诉状</button>
                      );
                      buttons.push(
                        <button key="admin_lawsuit" onClick={() => handleGenerateDoc('admin_lawsuit')} style={{ padding: 12, borderRadius: 8, border: 'none', background: '#1E3A5F', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>生成行政起诉状</button>
                      );
                      buttons.push(
                        <button key="judicial_confirm" onClick={() => handleGenerateDoc('judicial_confirm')} style={{ padding: 12, borderRadius: 8, border: 'none', background: '#6B5B95', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>生成司法确认申请书</button>
                      );
                    } else if (isDebt) {
                      buttons.push(
                        <button key="lawsuit" onClick={() => handleGenerateDoc('lawsuit')} style={{ padding: 12, borderRadius: 8, border: 'none', background: '#A85A34', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>生成民事起诉状</button>
                      );
                      buttons.push(
                        <button key="supervision" onClick={() => handleGenerateDoc('supervision')} style={{ padding: 12, borderRadius: 8, border: 'none', background: '#1E3A5F', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>生成检察监督申请书</button>
                      );
                    } else {
                      buttons.push(
                        <button key="lawsuit" onClick={() => handleGenerateDoc('lawsuit')} style={{ padding: 12, borderRadius: 8, border: 'none', background: '#A85A34', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>生成起诉状草稿</button>
                      );
                    }
                    
                    // 保存按钮（始终在最后，跨两列）
                    buttons.push(
                      <button key="save" onClick={handleSaveCase} style={{ gridColumn: '1 / -1', padding: 12, borderRadius: 8, border: '1px solid #ddd', background: '#fff', color: '#555', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>保存到案件管理</button>
                    );
                    
                    return buttons;
                  })()}
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