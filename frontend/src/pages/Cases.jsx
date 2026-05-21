import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './Cases.css';

const API_BASE = 'http://localhost:8000';

const Cases = () => {
  const navigate = useNavigate();
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('');
  const [search, setSearch] = useState('');
  const [showDetail, setShowDetail] = useState(null);
  const [showResolveModal, setShowResolveModal] = useState(null);
  const [resolveNote, setResolveNote] = useState('');

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

  const handleStatusChange = async (id, newStatus, note = '') => {
    try {
      const c = cases.find(x => x.id === id);
      const updatedAnalysis = c?.analysis_result ? {
        ...c.analysis_result,
        ...(note ? { resolution_note: note, resolution_time: new Date().toISOString(), resolution_action: newStatus } : {})
      } : undefined;
      
      await axios.put(`${API_BASE}/api/cases/${id}`, { 
        status: newStatus,
        ...(updatedAnalysis ? { analysis_result: updatedAnalysis } : {})
      });
      fetchCases();
    } catch (err) {
      alert('状态更新失败');
    }
  };

  const confirmResolve = async () => {
    if (!resolveNote.trim()) { alert('请填写调解结果或失败原因'); return; }
    await handleStatusChange(showResolveModal.case.id, showResolveModal.action, resolveNote.trim());
    setShowResolveModal(null);
    setResolveNote('');
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
          <button className="btn-new-case" onClick={() => navigate('/mediation')}>
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
                      {(c.status === 'resolved' || c.status === 'failed') ? (
                        <button className="action-link" onClick={() => setShowDetail(c)}>回溯</button>
                      ) : (
                        <button className="action-link" onClick={() => navigate('/mediation', { state: { caseData: c } })}>查看</button>
                      )}
                      {c.status === 'pending' && (
                        <button className="action-link" onClick={() => handleStatusChange(c.id, 'mediating')}>开始调解</button>
                      )}
                      {c.status === 'mediating' && (
                        <>
                          <button className="action-link success" onClick={() => setShowResolveModal({ case: c, action: 'resolved' })}>结案</button>
                          <button className="action-link danger" onClick={() => setShowResolveModal({ case: c, action: 'failed' })}>失败</button>
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

        {/* 回溯详情弹窗 */}
        {showDetail && (
          <div className="modal-overlay" onClick={() => setShowDetail(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>案件回溯 - {showDetail.case_no}</h3>
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
                      {showDetail.analysis_result.resolution_note && (
                        <p><strong>调解备注：</strong>{showDetail.analysis_result.resolution_note}</p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 结案/失败弹窗 */}
        {showResolveModal && (
          <div className="modal-overlay" onClick={() => setShowResolveModal(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 480 }}>
              <div className="modal-header">
                <h3>{showResolveModal.action === 'resolved' ? '确认结案' : '确认调解失败'}</h3>
                <button className="close-btn" onClick={() => setShowResolveModal(null)}>×</button>
              </div>
              <div className="modal-body">
                <p style={{ marginBottom: 12, color: '#666' }}>
                  {showResolveModal.action === 'resolved' 
                    ? '请填写调解结果（如：双方达成和解、赔偿金额、履行方式等）：' 
                    : '请填写调解失败原因（如：一方拒绝调解、无法联系当事人等）：'}
                </p>
                <textarea
                  value={resolveNote}
                  onChange={(e) => setResolveNote(e.target.value)}
                  rows={4}
                  placeholder={showResolveModal.action === 'resolved' ? '例如：双方达成和解，被告同意退还彩礼8万元...' : '例如：被告拒绝出席调解会议，经三次联系无果...'}
                  style={{ width: '100%', padding: 10, border: '1px solid #ddd', borderRadius: 6, fontSize: 14, resize: 'vertical', minHeight: 80 }}
                />
                <div style={{ display: 'flex', gap: 12, marginTop: 16, justifyContent: 'flex-end' }}>
                  <button onClick={() => setShowResolveModal(null)} style={{ padding: '8px 16px', border: '1px solid #ddd', background: '#fff', borderRadius: 6, cursor: 'pointer' }}>取消</button>
                  <button 
                    onClick={confirmResolve} 
                    style={{ 
                      padding: '8px 16px', 
                      border: 'none', 
                      background: showResolveModal.action === 'resolved' ? '#04AF64' : '#FC4E09', 
                      color: '#fff', 
                      borderRadius: 6, 
                      cursor: 'pointer' 
                    }}
                  >
                    确认{showResolveModal.action === 'resolved' ? '结案' : '失败'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Cases;