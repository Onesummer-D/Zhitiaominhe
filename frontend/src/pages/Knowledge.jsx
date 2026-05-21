import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Knowledge.css';

const API_BASE = 'http://localhost:8000';

// 适配后端数据格式 → 前端显示格式
const adaptNationalLaw = (law) => ({
  id: law.id,
  name: law.name || '未命名法条',
  category: law.category || '',
  content: law.content || '',
});

const adaptCustomLaw = (law) => ({
  id: law.id,
  name: law.name || '未命名习惯法',
  ethnicity: law.ethnicity || '',
  region: law.region || '',
  validity: law.validity_level || '参考适用',
  content: law.content || '',
  conflict: law.conflict_note || '',
});

const VALIDITY_INFO = {
  '参考适用': '可作为调解参考，但需经司法确认方具强制执行力',
  '社会规范': '具有一定社区约束力，但无法律强制效力',
  '禁止适用': '与国家法律严重冲突，必须优先适用国家法律',
};

function Knowledge() {
  const [activeTab, setActiveTab] = useState('national');
  const [search, setSearch] = useState('');
  const [nationalLaws, setNationalLaws] = useState([]);
  const [customLaws, setCustomLaws] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchKnowledge();
  }, []);

  const fetchKnowledge = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/api/knowledge`);
      const adaptedNational = (res.data.national_laws || [])
        .filter(law => law.name && law.content && law.content.trim())
        .map(adaptNationalLaw);
      const adaptedCustom = (res.data.custom_laws || [])
        .filter(law => law.name && law.content && law.content.trim())
        .map(adaptCustomLaw);
      setNationalLaws(adaptedNational);
      setCustomLaws(adaptedCustom);
    } catch (err) {
      console.error('获取知识库失败:', err);
    } finally {
      setLoading(false);
    }
  };

  // 当前 Tab 数据源
  const data = activeTab === 'national' ? nationalLaws : customLaws;
  const filtered = data.filter(item => 
    item.name.includes(search) || 
    item.content.includes(search) || 
    (item.category && item.category.includes(search))
  );

  return (
    <div className="knowledge-page">
      <div className="knowledge-container">
        <h2 className="knowledge-title">知识库</h2>

        {/* Tab切换 */}
        <div style={{ display: 'flex', gap: '4px', marginBottom: '20px', borderBottom: '2px solid var(--border)' }}>
          <button
            onClick={() => { setActiveTab('national'); setSearch(''); }}
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
            onClick={() => { setActiveTab('custom'); setSearch(''); }}
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

        {/* 加载中 */}
        {loading && (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            加载中...
          </div>
        )}

        {/* 列表 */}
        {!loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {filtered.map(item => (
              <div key={item.id} className="card" style={{ padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                  <div>
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
        )}
      </div>
    </div>
  );
}

export default Knowledge;