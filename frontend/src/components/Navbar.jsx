import React from 'react';
import { NavLink } from 'react-router-dom';

const navItems = [
  { path: '/', label: '工作台' },
  { path: '/mediation', label: '智能调解' },
  { path: '/cases', label: '案件管理' },
  { path: '/knowledge', label: '知识库' },
  { path: '/training', label: '培训资讯' },
];

// 民族纹样SVG（简化版回纹，用于导航栏底部装饰）
const EthnicPattern = () => (
  <svg
    width="100%"
    height="6"
    viewBox="0 0 1200 6"
    preserveAspectRatio="none"
    style={{ display: 'block', opacity: 0.6 }}
  >
    <pattern id="ethnic-line" x="0" y="0" width="40" height="6" patternUnits="userSpaceOnUse">
      <rect x="0" y="2" width="8" height="2" fill="#A85A34" opacity="0.5"/>
      <rect x="12" y="1" width="4" height="4" fill="#2C7473" opacity="0.4"/>
      <rect x="20" y="2" width="8" height="2" fill="#A85A34" opacity="0.5"/>
      <rect x="32" y="1" width="4" height="4" fill="#2C7473" opacity="0.4"/>
    </pattern>
    <rect width="100%" height="6" fill="url(#ethnic-line)" />
  </svg>
);

function Navbar() {
  return (
    <header style={styles.header}>
      <div style={styles.container}>
        {/* Logo区 */}
        <div style={styles.logo}>
          <div>
            <h1 style={styles.logoTitle}>智调民和</h1>
            <p style={styles.logoSubtitle}>民族地区基层纠纷智能调解系统</p>
          </div>
        </div>

        {/* 导航链接 */}
        <nav style={styles.nav}>
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                ...styles.navLink,
                ...(isActive ? styles.navLinkActive : {}),
              })}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* 用户信息 */}
        <div style={styles.user}>
          <span style={styles.userBadge}>调解员</span>
          <span style={styles.userName}>李同志</span>
        </div>
      </div>
      {/* 民族纹样装饰线 */}
      <EthnicPattern />
    </header>
  );
}

const styles = {
  header: {
    backgroundColor: '#FFFFFF',
    borderBottom: '1px solid var(--border)',
    boxShadow: '0 2px 8px rgba(44, 116, 115, 0.06)',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  },
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '0 24px',
    height: '64px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  logoTitle: {
    fontSize: '20px',
    fontWeight: 700,
    color: 'var(--primary)',
    lineHeight: 1.2,
    letterSpacing: '1px',
  },
  logoSubtitle: {
    fontSize: '12px',
    color: 'var(--text-muted)',
    lineHeight: 1.2,
    marginTop: '2px',
  },
  nav: {
    display: 'flex',
    gap: '8px',
  },
  navLink: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '8px 16px',
    borderRadius: 'var(--radius-sm)',
    textDecoration: 'none',
    color: 'var(--text-secondary)',
    fontSize: '15px',
    fontWeight: 500,
    transition: 'all 0.2s',
  },
  navLinkActive: {
    backgroundColor: 'rgba(44, 116, 115, 0.08)',
    color: 'var(--primary)',
  },
  user: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  userBadge: {
    padding: '4px 10px',
    backgroundColor: 'rgba(44, 116, 115, 0.1)',
    color: 'var(--primary)',
    borderRadius: 'var(--radius-sm)',
    fontSize: '12px',
    fontWeight: 500,
  },
  userName: {
    fontSize: '14px',
    color: 'var(--text-primary)',
    fontWeight: 500,
  },
};

export default Navbar;
