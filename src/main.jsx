import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { HashRouter } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import { ThemeProvider } from './data/theme.jsx'
import { initErrorTracking } from './data/errorTracker.js'

initErrorTracking();

// Global error display for debugging
window.addEventListener('error', (e) => {
  const root = document.getElementById('root');
  if (root && !root.innerHTML.includes('miketv-error-banner')) {
    const banner = document.createElement('div');
    banner.className = 'miketv-error-banner';
    banner.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:99999;background:#dc2626;color:#fff;padding:12px 16px;font-family:monospace;font-size:12px;';
    banner.innerHTML = '<b>⚠ 系统错误:</b> ' + (e.error?.message || e.message || 'Unknown') + '<br><span style=\"opacity:0.7;font-size:10px\">打开控制台(F12)查看详情</span>';
    root.prepend(banner);
  }
});

window.addEventListener('unhandledrejection', (e) => {
  const root = document.getElementById('root');
  if (root && !root.innerHTML.includes('miketv-error-banner')) {
    const banner = document.createElement('div');
    banner.className = 'miketv-error-banner';
    banner.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:99999;background:#dc2626;color:#fff;padding:12px 16px;font-family:monospace;font-size:12px;';
    banner.innerHTML = '<b>⚠ 异步错误:</b> ' + (e.reason?.message || String(e.reason) || 'Unknown') + '<br><span style=\"opacity:0.7;font-size:10px\">打开控制台(F12)查看详情</span>';
    root.prepend(banner);
  }
});

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      <HashRouter>
        <App />
      </HashRouter>
    </ThemeProvider>
  </StrictMode>,
)
