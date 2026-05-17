import React, { useState } from 'react';

const KNOWLEDGE_DATA = {
  national: [
    { id: 'nl-001', name: '《民法典》第288条', category: '邻里冲突', content: '不动产的相邻权利人应当按照有利生产、方便生活、团结互助、公平合理的原则，正确处理相邻关系。' },
    { id: 'nl-002', name: '《民法典》第1042条', category: '婚姻家庭', content: '禁止包办、买卖婚姻和其他干涉婚姻自由的行为。禁止借婚姻索取财物。' },
    { id: 'nl-003', name: '《民法典》第1087条', category: '婚姻家庭', content: '离婚时，夫妻的共同财产由双方协议处理；协议不成的，由人民法院根据财产的具体情况判决。' },
    { id: 'nl-004', name: '《劳动法》第50条', category: '债务劳资', content: '工资应当以货币形式按月支付给劳动者本人。不得克扣或者无故拖欠劳动者的工资。' },
    { id: 'nl-005', name: '《土地管理法》第14条', category: '土地山林', content: '土地所有权和使用权争议，由当事人协商解决；协商不成的，由人民政府处理。' },
  ],
  custom: [
    { id: 'cl-001', name: '德古调解', ethnicity: '彝族', region: '四川凉山', validity: '参考适用', content: '由德高望重的"德古"主持，依据彝族习惯法进行调解，强调恢复社会关系和谐，注重家族声誉维护。', conflict: '调解结果需经司法确认方具强制执行力' },
    { id: 'cl-002', name: '寨老调解制', ethnicity: '苗族', region: '贵州黔东南', validity: '参考适用', content: '由村寨中德高望重的寨老主持调解，依据苗族古理词（习惯法）裁决，注重社区和谐与长老权威。', conflict: '部分裁决内容可能与国家法律存在效力冲突' },
    { id: 'cl-003', name: '摩调解', ethnicity: '哈尼族', region: '云南红河', validity: '参考适用', content: '哈尼族传统调解方式，由"摩批"（宗教祭司）或村寨长老主持，结合宗教仪式与习惯法进行调解。', conflict: '宗教仪式环节需与现行法律程序分离' },
    { id: 'cl-004', name: '赔命价', ethnicity: '藏族', region: '西藏/青海', validity: '禁止适用', content: '传统习惯法中由加害方向受害方支付财物以了结人命纠纷的做法。', conflict: '与《刑法》故意杀人罪/过失致人死亡罪严重冲突，必须优先适用国家法律' },
  ],
};

// 效力等级说明（悬停提示用）
const VALIDITY_INFO = {
  '参考适用': '可作为调解参考，但需经司法确认方具强制执行力',
  '社会规范': '具有一定社区约束力，但无法律强制效力',
  '禁止适用': '与国家法律严重冲突，必须优先适用国家法律',
};

function Knowledge() {
  const [activeTab, setActiveTab] = useState('national');
  const [search, setSearch] = useState('');

  const data = KNOWLEDGE_DATA[activeTab];
  const filtered = data.filter(item => 
    item.name.includes(search) || item.content.includes(search) || (item.category && item.category.includes(search))
  );

  return (
    <div className="page-container">
      <h2 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '20px' }}>知识库</h2>

      {/* Tab切换 */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: '20px', borderBottom: '2px solid var(--border)' }}>
        <button
          onClick={() => setActiveTab('national')}
          style={{
            padding: '10px 24px',
            fontSize: '15px',
            fontWeight: 600,
            border: 'none',
            background: 'none',
            cursor: 'pointer',
            borderBottom: activeTab === 'national' ? '2px solid var(--primary)' : '2px solid transparent',
            color: activeTab === 'national' ? 'var(--primary)' : 'var(--text-muted)',
            marginBottom: '-2px',
          }}
        >
          国家法律库
        </button>
        <button
          onClick={() => setActiveTab('custom')}
          style={{
            padding: '10px 24px',
            fontSize: '15px',
            fontWeight: 600,
            border: 'none',
            background: 'none',
            cursor: 'pointer',
            borderBottom: activeTab === 'custom' ? '2px solid var(--accent)' : '2px solid transparent',
            color: activeTab === 'custom' ? 'var(--accent)' : 'var(--text-muted)',
            marginBottom: '-2px',
          }}
        >
          民族习惯法库
        </button>
      </div>

      {/* 搜索 */}
      <div style={{ marginBottom: '20px' }}>
        <input
          type="text"
          placeholder={`搜索${activeTab === 'national' ? '法律条文' : '习惯法'}...`}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input"
          style={{ width: '360px' }}
        />
      </div>

      {/* 列表 */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {filtered.map(item => (
          <div key={item.id} className="card" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
              <div>
                {/* 习惯法标题：更深的棕褐色 */}
                <h4 style={{ 
                  fontSize: '17px', 
                  fontWeight: 700, 
                  color: activeTab === 'national' ? 'var(--primary)' : '#4A2508',
                  marginBottom: '8px' 
                }}>
                  {item.name}
                </h4>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
                  {item.category && <span className="tag tag-primary">{item.category}</span>}
                  {item.ethnicity && <span className="tag" style={{ background: 'rgba(168,90,52,0.1)', color: 'var(--accent)' }}>{item.ethnicity}</span>}
                  {/* 地区标签化 */}
                  {item.region && (
                    <span className="tag" style={{ background: 'rgba(102,102,102,0.08)', color: 'var(--text-secondary)', fontSize: '12px' }}>
                      {item.region}
                    </span>
                  )}
                  {item.validity && (
                    <span 
                      className="tag" 
                      style={{ 
                        background: item.validity === '禁止适用' ? 'rgba(214,63,62,0.1)' : 'rgba(4,175,100,0.1)', 
                        color: item.validity === '禁止适用' ? 'var(--danger)' : 'var(--success)' 
                      }}
                      title={VALIDITY_INFO[item.validity] || ''}
                    >
                      效力：{item.validity}
                    </span>
                  )}
                </div>
              </div>
            </div>
            <p style={{ fontSize: '15px', color: 'var(--text-secondary)', lineHeight: 1.7 }}>{item.content}</p>

            {/* 冲突提示：emoji + 深灰文字，去掉红色背景 */}
            {item.conflict && (
              <div style={{ 
                marginTop: '14px', 
                padding: '10px 14px', 
                background: 'var(--bg-hover)', 
                borderRadius: '6px', 
                borderLeft: '3px solid var(--text-muted)',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '8px'
              }}>
                <span style={{ fontSize: '16px', flexShrink: 0, marginTop: '1px' }}>⚠️</span>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
                  <strong style={{ color: 'var(--text-primary)' }}>冲突提示：</strong>{item.conflict}
                </p>
              </div>
            )}
          </div>
        ))}
        {filtered.length === 0 && (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            未找到匹配结果
          </div>
        )}
      </div>
    </div>
  );
}

export default Knowledge;
