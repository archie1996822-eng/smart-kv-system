import { useEffect } from 'react';

// Global keyboard shortcut handler
export function useShortcuts(handlers = {}) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      const tag = e.target.tagName;
      // Don't intercept when typing in inputs
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || e.target.isContentEditable) {
        if (e.key === 'Escape' && handlers['Escape']) {
          handlers['Escape'](e);
        }
        return;
      }

      const key = [
        e.ctrlKey && 'Ctrl',
        e.metaKey && 'Meta',
        e.shiftKey && 'Shift',
        e.altKey && 'Alt',
        e.key,
      ].filter(Boolean).join('+');

      if (handlers[key]) {
        e.preventDefault();
        handlers[key](e);
      } else if (e.key === 'Escape' && handlers['Escape']) {
        handlers['Escape'](e);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handlers]);
}

// Default shortcuts
export const DEFAULT_SHORTCUTS = [
  { key: 'Ctrl+Enter', desc: '确认生成' },
  { key: 'Ctrl+S', desc: '保存模板' },
  { key: 'Escape', desc: '关闭弹窗' },
  { key: '/', desc: '聚焦搜索框' },
  { key: 'Ctrl+K', desc: '全局命令面板' },
];
