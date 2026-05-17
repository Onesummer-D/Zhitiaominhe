import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Cases.css';

const API_BASE = 'http://localhost:8000';

const Cases = () => {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('');
  const [search, setSearch] = useState('');
  const [showDetail, setShowDetail] = useState(null);

  useEffect(() => {
    fetchCases();
  }, [filterStatus, search]);

  const fetchCases = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filterStatus) params.status = filterStatus;
      if (search.trim()) params.search = search.trim();
      const res = await axios.get(`${API_BASE}/api/cases`, { params });
      setCases(res.data);
    } catch (err) {
      console.error('获取案件失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('确定删除该案件？')) return;
    try {
      await axios.delete(`${API_BASE}/api/cases/${id}`);
      fetchCases();
    } catch (err) {
      alert('删除失败');
    }
  };

  const handleStatusChange = async (id, newStatus) => {
    try {
      await axios.put(`${API_BASE}/api/cases/${id}`, { status: newStatus });
      fetchCases();
    } catch (err) {
      alert('状态更新失败');
    }
  };

  const getStatusText = (status) => {
    const map = { pending: '待调解', mediating: '调解中', resolved: '已结案', failed: '调解失败', archived: '已归档' };
    return map[status] || status;
  };

  const getStatusClass = (status) => {
    const map = { pending: 'tag-pending', mediating: 'tag-mediating', resolved: 'tag-resolved', failed: 'tag-failed', archived: 'tag-archived' };
    return map[status] || 'tag-default';
  };

  return (
    <div className="cases-page">
      <div className="cases-container">
        <div className="cases-header">
          <h2>案件管理</h2>
          <button className="btn-new-case" onClick={() => window.location.href = '/mediation'}>
            + 新建案件
          </button>
        </div>

        <div className="cases-toolbar">
          <input
            type="text"
            className="search-input"
            placeholder="搜索当事人、案号..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="filter-select">
            <option value="">全部状态</option>
            <option value="pending">待调解</option>
            <option value="mediating">调解中</option>
            <option value="resolved">已结案</option>
            <option value="failed">调解失败</option>
            <option value="archived">已归档</option>
          </select>
          <span className="cases-count">共 {cases.length} 件案件</span>
        </div>

        {loading ? (
          <div className="loading">加载中...</div>
        ) : cases.length === 0 ? (
          <div className="empty">暂无案件</div>
        ) : (
          <div className="cases-table-wrapper">
            <table className="cases-table">
              <thead>
                <tr>
                  <th>案号</th>
                  <th>案件标题</th>
                  <th>类型</th>
                  <th>地区/民族</th>
                  <th>状态</th>
                  <th>更新时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {cases.map((c) => (
                  <tr key={c.id}>
                    <td className="cell-no">{c.case_no}</td>
                    <td className="cell-title">
                      {c.applicant} vs {c.respondent} - {c.dispute_type}纠纷
                    </td>
                    <td className="cell-type">{c.dispute_type}</td>
                    <td className="cell-region">{c.region || '-'}</td>
                    <td>
                      <span className={`status-tag ${getStatusClass(c.status)}`}>
                        {getStatusText(c.status)}
                      </span>
                    </td>
                    <td className="cell-time">{c.updated_at?.slice(0, 16).replace('T', ' ')}</td>
                    <td className="cell-actions">
                      <button className="action-link" onClick={() => setShowDetail(c)}>查看</button>
                      {c.status === 'pending' && (
                        <button className="action-link" onClick={() => handleStatusChange(c.id, 'mediating')}>开始调解</button>
                      )}
                      {c.status === 'mediating' && (
                        <>
                          <button className="action-link success" onClick={() => handleStatusChange(c.id, 'resolved')}>结案</button>
                          <button className="action-link danger" onClick={() => handleStatusChange(c.id, 'failed')}>失败</button>
                        </>
                      )}
                      <button className="action-link danger" onClick={() => handleDelete(c.id)}>删除</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* 详情弹窗 */}
        {showDetail && (
          <div className="modal-overlay" onClick={() => setShowDetail(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>案件详情 - {showDetail.case_no}</h3>
                <button className="close-btn" onClick={() => setShowDetail(null)}>×</button>
              </div>
              <div className="modal-body">
                <div className="detail-row"><label>申请人：</label><span>{showDetail.applicant}</span></div>
                <div className="detail-row"><label>被申请人：</label><span>{showDetail.respondent}</span></div>
                <div className="detail-row"><label>纠纷类型：</label><span>{showDetail.dispute_type}</span></div>
                <div className="detail-row"><label>涉及习惯法：</label><span>{showDetail.custom_law_involved ? '是' : '否'}</span></div>
                <div className="detail-row"><label>状态：</label>
                  <span className={`status-tag ${getStatusClass(showDetail.status)}`}>{getStatusText(showDetail.status)}</span>
                </div>
                <div className="detail-row"><label>所属地区：</label><span>{showDetail.region || '未填写'}</span></div>
                <div className="detail-row"><label>涉及民族：</label><span>{showDetail.ethnicity || '未填写'}</span></div>
                <div className="detail-row block">
                  <label>纠纷描述：</label>
                  <p className="detail-text">{showDetail.description}</p>
                </div>
                {showDetail.analysis_result && (
                  <div className="detail-row block">
                    <label>AI 分析结果：</label>
                    <div className="detail-box">
                      <p><strong>分类：</strong>{showDetail.analysis_result.category}</p>
                      <p><strong>置信度：</strong>{showDetail.analysis_result.confidence}分</p>
                      <p><strong>建议：</strong>{showDetail.analysis_result.suggestion}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Cases;
