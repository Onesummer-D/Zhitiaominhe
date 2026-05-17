import React from 'react';
import './Training.css';

const Training = () => {
  const articles = [
    {
      id: 1,
      tag: '政策速递',
      tagClass: 'tag-policy',
      date: '2025-10-26',
      title: '《政务领域人工智能大模型部署应用指引》正式发布',
      summary: '国家网信办发布政务AI应用指引，明确大模型在政务服务、社会治理等领域的应用规范...',
      icon: 'policy'
    },
    {
      id: 2,
      tag: '典型案例',
      tagClass: 'tag-case',
      date: '2025-05-10',
      title: '云南元阳"共享法庭"：哈尼族梯田纠纷调解经验',
      summary: '元阳县人民法院在哈尼梯田核心区设立"共享法庭"，结合哈尼族摩调解传统，成功化解多起土地边界纠纷...',
      icon: 'case'
    },
    {
      id: 3,
      tag: '调解技巧',
      tagClass: 'tag-skill',
      date: '2025-04-28',
      title: '如何用习惯法调解彩礼纠纷：凉山彝族实践',
      summary: '介绍彝族德古在彩礼纠纷中的调解技巧，如何平衡习惯法"聘礼"传统与国家法律对借婚姻索取财物的禁止性规定...',
      icon: 'skill'
    },
    {
      id: 4,
      tag: '民族地区动态',
      tagClass: 'tag-news',
      date: '2025-04-15',
      title: '内蒙古呼伦贝尔：草场承包纠纷多元化解机制',
      summary: '呼伦贝尔市建立"嘎查干部+司法所+法庭"联动机制，结合蒙古族传统调解方式，有效化解草场承包纠纷...',
      icon: 'news'
    }
  ];

  return (
    <div className="training-page">
      <div className="training-container">
        <h2 className="training-title">培训资讯</h2>
        <div className="articles-list">
          {articles.map(article => (
            <div key={article.id} className="article-card">
              <div className={`article-icon icon-${article.icon}`}></div>
              <div className="article-content">
                <div className="article-meta">
                  <span className={`article-tag ${article.tagClass}`}>{article.tag}</span>
                  <span className="article-date">{article.date}</span>
                </div>
                <h3 className="article-title">{article.title}</h3>
                <p className="article-summary">{article.summary}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Training;
