import React from 'react';
import Navbar from './Navbar';

function Layout({ children }) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />
      <main style={{ flex: 1, paddingTop: '8px' }}>
        {children}
      </main>
      <footer style={styles.footer}>
        <p style={styles.footerText}>
          智调民和 · 民族地区基层纠纷智能调解与法律适配系统
        </p>
      </footer>
    </div>
  );
}

const styles = {
  footer: {
    padding: '20px 24px',
    textAlign: 'center',
    borderTop: '1px solid var(--border)',
    backgroundColor: '#FFFFFF',
  },
  footerText: {
    fontSize: '13px',
    color: 'var(--text-muted)',
  },
};

export default Layout;
