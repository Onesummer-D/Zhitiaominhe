import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      const res = await axios.post('http://localhost:8000/api/analyze', { text });
      setResult(res.data);
    } catch (err) {
      alert('请求失败：请确认后端已启动（cd backend && py main.py）');
    }
    setLoading(false);
  };

  const handleClear = () => {
    setText('');
    setResult(null);
  };

  return (
    <div>
      <div className="app-container">
        <header className="app-header" style={{ gridColumn: '1 / -1' }}>
          <div>🌾 智调民和</div>
          <div className="app-subtitle">民族地区基层纠纷智能调解与法律适配系统</div>
        </header>

        {/* 左侧输入区 */}
        <div className="input-panel">
          <div className="panel-title">
            <span>📝</span> 纠纷描述录入
          </div>
          <textarea
            className="textarea-input"
            placeholder="例如：我是元阳县哈尼族的，邻居家的田水淹到我家地里了，寨老说各退一步，但我不服，想按国家法律来解决..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <div className="btn-group">
            <button
              className="btn-primary"
              onClick={handleAnalyze}
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="loading-spinner"></span>
                  分析中...
                </>
              ) : (
                '🔍 开始分析'
              )}
            </button>
            <button className="btn-secondary" onClick={handleClear}>
              🔄 清空
            </button>
          </div>
        </div>

        {/* 右侧结果区 */}
        <div className="result-area">
          {!result && (
            <div className="empty-state">
              <div className="empty-icon">🌾</div>
              <p>请在左侧输入纠纷描述，点击"开始分析"</p>
              <p style={{ fontSize: '12px', marginTop: '8px', color: '#bbb' }}>
                系统将自动识别纠纷类型并生成调解方案
              </p>
            </div>
          )}

          {result && result.error && (
            <div className="error-state">
              <div style={{ fontSize: '32px', marginBottom: '12px' }}>⚠️</div>
              <p>{result.error}</p>
            </div>
          )}

          {result && !result.error && (
            <>
              {/* 识别结果 */}
              <div className="result-card card-identify">
                <div className="card-header">
                  <span>📋</span> 纠纷识别结果
                </div>
                <div className="card-body">
                  <div className="engine-tag">🤖 {result.engine}</div>
                  <div className="info-row">
                    <span className="info-label">纠纷类型：</span>
                    <span className="info-value highlight">{result.dispute_type}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">置信度得分：</span>
                    <span className="info-value">{result.score} 分</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">命中关键词：</span>
                    <span className="info-value">
                      {result.hits?.join('、') || '无'}
                    </span>
                  </div>
                  {result.api_error && (
                    <div style={{ color: '#c0392b', fontSize: '12px', marginTop: '8px', background: '#fff5f5', padding: '8px', borderRadius: '6px', border: '1px solid #ffcdd2' }}>
                      API错误：{result.api_error}
                    </div>
                  )}
                </div>
              </div>

              {/* 国家法律 */}
              {result.laws && result.laws.length > 0 && (
                <div className="result-card card-law">
                  <div className="card-header">
                    <span>⚖️</span> 国家法律依据
                  </div>
                  <div className="card-body">
                    {result.laws.map((law, i) => (
                      <div className="law-item" key={i}>
                        <div className="law-title">{law.编号}</div>
                        {law.内容 && (
                          <div className="law-content">{law.内容.slice(0, 100)}...</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 民族习惯法 */}
              {result.customs && result.customs.length > 0 && (
                <div className="result-card card-custom">
                  <div className="card-header">
                    <span>🏔️</span> 民族习惯法参考
                  </div>
                  <div className="card-body">
                    {result.customs.map((c, i) => (
                      <div className="custom-item" key={i}>
                        <div className="custom-title">
                          <span>🎋</span>
                          {c.民族} · {c.习俗名称}
                          {c.地域 && (
                            <span className="custom-meta">（{c.地域}）</span>
                          )}
                        </div>
                        {c.效力等级 && (
                          <div className="level-tag">效力等级：{c.效力等级}</div>
                        )}
                        {c.内容 && (
                          <div className="custom-content">{c.内容.slice(0, 80)}...</div>
                        )}
                        {c.冲突提示 && (
                          <div className="conflict-warning">
                            <span>⚠️</span> {c.冲突提示}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 调解建议 */}
              <div className="result-card card-advice">
                <div className="card-header">
                  <span>💡</span> AI调解建议
                </div>
                <div className="advice-content">{result.advice}</div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;