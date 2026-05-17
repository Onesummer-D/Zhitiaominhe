import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Dashboard.css';

const API_BASE = 'http://localhost:8000';

const Dashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({ pending: 0, today_new: 0, today_resolved: 0 });
  const [recentCases, setRecentCases] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, casesRes] = await Promise.all([
        axios.get(`${API_BASE}/api/stats`),
        axios.get(`${API_BASE}/api/cases?status=pending`)
      ]);
      setStats(statsRes.data);
      setRecentCases(casesRes.data.slice(0, 5));
    } catch (err) {
      console.error('获取数据失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    { label: '开始新调解', desc: '录入纠纷信息，获取AI分析建议', path: '/mediation', icon: 'plus' },
    { label: '查知识库', desc: '检索国家法与民族习惯法', path: '/knowledge', icon: 'book' },
    { label: '案件列表', desc: '查看所有案件及处理进度', path: '/cases', icon: 'list' },
    { label: '生成文书', desc: '一键生成调解协议等文书', path: '/mediation', icon: 'file' }
  ];

  const getStatusText = (status) => {
    const map = { pending: '待调解', mediating: '调解中', resolved: '已结案', failed: '调解失败', archived: '已归档' };
    return map[status] || status;
  };

  const getStatusClass = (status) => {
    const map = { pending: 'status-pending', mediating: 'status-mediating', resolved: 'status-resolved', failed: 'status-failed', archived: 'status-archived' };
    return map[status] || 'status-default';
  };

  return (
    <div className="dashboard-page" style={{ padding: '24px 32px' }}>
      {/* 欢迎区 */}
      <div className="welcome-section">
        <h1>上午好，李调解员</h1>
        <p>你今天有 <strong>{stats.pending}</strong> 个待办案件</p>
      </div>

      {/* 快捷操作 */}
      <div className="quick-actions-grid">
        {quickActions.map((action, idx) => (
          <div key={idx} className="quick-action-card" onClick={() => navigate(action.path)}>
            <div className={`action-icon icon-${action.icon}`}></div>
            <div className="action-info">
              <div className="action-title">{action.label}</div>
              <div className="action-desc">{action.desc}</div>
            </div>
          </div>
        ))}
      </div>

      {/* 统计 + 待办 */}
      <div className="dashboard-main">
        <div className="left-column">
          {/* 今日统计 */}
          <div className="stats-section">
            <h3>今日统计</h3>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-number" style={{ color: '#A85A34' }}>{stats.pending}</div>
                <div className="stat-label">待办案件</div>
              </div>
              <div className="stat-card">
                <div className="stat-number" style={{ color: '#2C7473' }}>{stats.today_new}</div>
                <div className="stat-label">今日新增</div>
              </div>
              <div className="stat-card">
                <div className="stat-number" style={{ color: '#04AF64' }}>{stats.today_resolved}</div>
                <div className="stat-label">调解成功</div>
              </div>
            </div>
          </div>

          {/* 最新动态 */}
          <div className="news-section">
            <h3>最新动态</h3>
            <div className="news-list">
              <div className="news-item">
                <span className="news-badge policy">政策速递</span>
                <span className="news-title">《政务领域人工智能大模型部署应用指引》发布</span>
              </div>
              <div className="news-item">
                <span className="news-badge case">典型案例</span>
                <span className="news-title">云南元阳"共享法庭"：哈尼族梯田纠纷调解经验</span>
              </div>
            </div>
          </div>
        </div>

        <div className="right-column">
          {/* 待办案件 */}
          <div className="pending-section">
            <h3>待办案件</h3>
            {loading ? (
              <div className="loading-text">加载中...</div>
            ) : recentCases.length === 0 ? (
              <div className="empty-text">暂无待办案件</div>
            ) : (
              <div className="pending-list">
                {recentCases.map((c) => (
                  <div key={c.id} className="pending-item" onClick={() => navigate(`/cases/${c.id}`)}>
                    <div className="pending-main">
                      <span className="pending-title">{c.applicant} vs {c.respondent} - {c.dispute_type}纠纷</span>
                      <span className={`pending-status ${getStatusClass(c.status)}`}>
                        {getStatusText(c.status)}
                      </span>
                    </div>
                    <div className="pending-meta">
                      <span className="pending-type">{c.dispute_type}</span>
                      <span className="pending-time">{c.updated_at?.slice(0, 10)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
