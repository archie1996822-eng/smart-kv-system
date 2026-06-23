import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { navItems } from '../data/mockData';

function Icon({ name, className = '' }) {
  return (<span className={`material-symbols-outlined ${className}`}>{name}</span>);
}

const COMMANDS = [
  { id: 'generate', label: '生成物料', icon: 'auto_awesome', action: 'navigate', path: '/workbench', keywords: ['生成', 'generate', '生图'] },
  { id: 'video', label: '视频创作', icon: 'videocam', action: 'navigate', path: '/video-studio', keywords: ['视频', 'video'] },
  { id: 'dashboard', label: '工作总览', icon: 'dashboard', action: 'navigate', path: '/app', keywords: ['首页', 'home', 'dashboard'] },
  { id: 'history', label: '历史记录', icon: 'history', action: 'navigate', path: '/history', keywords: ['历史', 'history'] },
  { id: 'brand', label: '品牌管理', icon: 'palette', action: 'navigate', path: '/brand-kit', keywords: ['品牌', 'brand'] },
  { id: 'materials', label: '物料库', icon: 'folder_copy', action: 'navigate', path: '/material-lib', keywords: ['物料', 'material'] },
  { id: 'admin', label: '管理控制台', icon: 'admin_panel_settings', action: 'navigate', path: '/admin', keywords: ['管理', 'admin', '设置'] },
  { id: 'darkmode', label: '切换暗色/浅色模式', icon: 'dark_mode', action: 'theme', keywords: ['暗色', '浅色', '主题', 'theme', 'dark'] },
  { id: 'logout', label: '退出登录', icon: 'logout', action: 'logout', keywords: ['退出', '登出', 'logout'] },
];

export default function CommandPalette({ open, onClose, onToggleTheme, onLogout }) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();

  // Focus input on open
  useEffect(() => {
    if (open) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  // Filter commands
  const filtered = query.trim()
    ? COMMANDS.filter(c =>
        c.label.toLowerCase().includes(query.toLowerCase()) ||
        c.keywords.some(k => k.includes(query.toLowerCase()))
      )
    : COMMANDS;

  // Keyboard navigation
  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(i => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(i => Math.max(i - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered[selectedIndex]) executeCommand(filtered[selectedIndex]);
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  const executeCommand = (cmd) => {
    onClose();
    if (cmd.action === 'navigate') {
      navigate(cmd.path);
    } else if (cmd.action === 'theme') {
      onToggleTheme?.();
    } else if (cmd.action === 'logout') {
      onLogout?.();
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[300] bg-black/60 backdrop-blur-sm flex items-start justify-center pt-[15vh] p-4" onClick={onClose}>
      <div className="bg-surface-container-high border border-outline-variant rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden" onClick={e => e.stopPropagation()}>
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-outline-variant">
          <Icon name="search" className="text-outline text-xl" />
          <input
            ref={inputRef}
            value={query}
            onChange={e => { setQuery(e.target.value); setSelectedIndex(0); }}
            onKeyDown={handleKeyDown}
            placeholder="输入命令... (Ctrl+K)"
            className="flex-1 bg-transparent border-none outline-none text-on-surface text-sm placeholder:text-outline"
          />
          <span className="text-[10px] text-outline font-mono">ESC 关闭</span>
        </div>

        {/* Command list */}
        <div className="max-h-72 overflow-y-auto py-2">
          {filtered.length === 0 ? (
            <p className="text-center text-sm text-on-surface-variant py-8">未找到匹配命令</p>
          ) : (
            filtered.map((cmd, i) => (
              <button
                key={cmd.id}
                onClick={() => executeCommand(cmd)}
                className={`w-full text-left px-4 py-2.5 flex items-center gap-3 transition-colors ${i === selectedIndex ? 'bg-primary/10 text-primary' : 'text-on-surface-variant hover:bg-surface-container'}`}
              >
                <Icon name={cmd.icon} className={`text-lg ${i === selectedIndex ? 'text-primary' : 'text-outline'}`} />
                <span className="text-sm font-medium">{cmd.label}</span>
              </button>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-outline-variant flex gap-4 text-[10px] text-outline font-mono">
          <span>↑↓ 导航</span>
          <span>↵ 选择</span>
          <span>Esc 关闭</span>
        </div>
      </div>
    </div>
  );
}
