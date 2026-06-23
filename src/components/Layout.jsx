import { useState, useCallback, useEffect, useRef } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { navItems } from '../data/mockData';
import { useUser, isAdmin } from '../data/auth';
import { useTheme } from '../data/theme.jsx';
import ErrorBoundary from './ErrorBoundary';
import CommandPalette from './CommandPalette';
import { useShortcuts } from '../data/shortcuts';

// Global toast queue
let toastId = 0;
const toastListeners = new Set();
function emitToast(toast) { toastListeners.forEach(fn => fn(toast)); }

export function showToast(message, type = 'success') {
  const id = ++toastId;
  emitToast({ id, message, type });
  setTimeout(() => emitToast({ id, remove: true }), 3500);
}

function Icon({ name, filled = false, className = '' }) {
  return (<span className={`material-symbols-outlined ${className}`} style={filled ? { fontVariationSettings: '"FILL" 1, "wght" 400, "GRAD" 0, "opsz" 24' } : {}}>{name}</span>);
}

// Dynamic notification store
let notifId = 0;
const notifListeners = new Set();
export function pushNotification(title, desc, icon = 'info', color = 'text-primary') {
  const n = { id: ++notifId, icon, title, desc, time: new Date().toLocaleTimeString('zh-CN'), color };
  notifListeners.forEach(fn => fn(n));
}
const MOCK_NOTIFICATIONS = [
  { id: -1, icon: 'update', title: '系统就绪', desc: 'Smart KV Extension 已启动，选择模型开始生图', time: '刚刚', color: 'text-primary' },
];

function ToastContainer() {
  const [toasts, setToasts] = useState([]);
  useEffect(() => {
    const handler = (t) => {
      if (t.remove) { setToasts(prev => prev.filter(x => x.id !== t.id)); }
      else { setToasts(prev => [...prev.slice(-4), t]); }
    };
    toastListeners.add(handler);
    return () => { toastListeners.delete(handler); };
  }, []);
  if (toasts.length === 0) return null;
  return (<div className="fixed top-20 right-4 md:right-8 z-[200] flex flex-col gap-2">{toasts.map(t => (<div key={t.id} className="animate-slide-in px-4 py-3 bg-surface border border-outline-variant rounded-xl shadow-lg text-sm font-semibold text-on-surface flex items-center gap-2" style={{animation:'slideIn 0.3s ease-out'}}><span className={`w-2 h-2 rounded-full ${t.type==='error'?'bg-error':'bg-green-500'}`}></span>{t.message}</div>))}
    <style>{`@keyframes slideIn{from{transform:translateX(100px);opacity:0}to{transform:translateX(0);opacity:1}}`}</style>
  </div>);
}

function NotificationPopover({ onClose }) {
  const [items, setItems] = useState(MOCK_NOTIFICATIONS);
  useEffect(() => {
    const handler = (n) => setItems(prev => [n, ...prev].slice(0, 20));
    notifListeners.add(handler);
    return () => notifListeners.delete(handler);
  }, []);
  return (
    <div className="absolute top-full right-0 mt-2 w-80 bg-surface border border-outline-variant rounded-xl shadow-2xl z-50 overflow-hidden" onClick={e => e.stopPropagation()}>
      <div className="p-4 border-b border-outline-variant flex items-center justify-between">
        <h4 className="font-semibold text-sm">通知中心</h4>
        <button onClick={onClose} className="text-outline hover:text-on-surface"><Icon name="close" className="text-sm" /></button>
      </div>
      <div className="max-h-80 overflow-y-auto divide-y divide-outline-variant">
        {items.length === 0 ? <p className="p-4 text-sm text-on-surface-variant text-center">暂无通知</p> : items.map(n => (
          <div key={n.id} className="p-3 hover:bg-surface-container-low transition-colors flex gap-3">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${n.color?.replace('text-','bg-') || 'bg-surface-container'} bg-opacity-20`}>
              <Icon name={n.icon} className={`text-sm ${n.color || 'text-primary'}`} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-on-surface">{n.title}</p>
              <p className="text-[11px] text-on-surface-variant truncate">{n.desc}</p>
              <p className="text-[9px] text-outline mt-1">{n.time}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function HelpPopover({ onClose }) {
  const steps = [
    { icon: 'cloud_upload', title: '上传KV主视觉', desc: '拖放或点击上传活动的核心KV设计图' },
    { icon: 'psychology', title: 'AI视觉分析', desc: '选择分析模型，自动提取色板、字体、布局信息' },
    { icon: 'auto_awesome', title: '选择生图模型', desc: '根据需求选择合适的AI图像生成模型' },
    { icon: 'checklist', title: '勾选物料', desc: '在物料清单中选择要生成的周边物料类型' },
    { icon: 'play_circle', title: '一键生成', desc: '确认参数后启动批量生成，实时查看进度' },
    { icon: 'download', title: '查看/下载', desc: '在结果网格中查看大图或下载高清文件' },
    { icon: 'history', title: '历史恢复', desc: '所有生成记录自动保存，可随时恢复继续工作' },
  ];
  return (
    <div className="absolute top-full right-0 mt-2 w-96 bg-surface border border-outline-variant rounded-xl shadow-2xl z-50 overflow-hidden" onClick={e => e.stopPropagation()}>
      <div className="p-4 border-b border-outline-variant flex items-center justify-between">
        <h4 className="font-semibold text-sm">操作指引</h4>
        <button onClick={onClose} className="text-outline hover:text-on-surface"><Icon name="close" className="text-sm" /></button>
      </div>
      <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
        {steps.map((s, i) => (
          <div key={i} className="flex gap-3 p-2 rounded-lg hover:bg-surface-container-low transition-colors">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0"><Icon name={s.icon} className="text-primary text-lg" /></div>
            <div>
              <p className="text-xs font-semibold text-on-surface">{i+1}. {s.title}</p>
              <p className="text-[11px] text-on-surface-variant">{s.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Layout({ children }) {
  const user = useUser();
  const admin = isAdmin();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const searchRef = useRef(null);
  const location = useLocation();
  const [notifOpen, setNotifOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  // Ctrl+K command palette shortcut
  useShortcuts({
    'Ctrl+k': () => setCommandPaletteOpen(true),
    'Ctrl+K': () => setCommandPaletteOpen(true),
  });

  // Filter nav items by permission
  const visibleNavItems = navItems.filter(item => !item.adminOnly || admin);

  // Search functionality — searches pages, projects, history
  const handleSearch = (val) => {
    setSearchQuery(val);
    if (val.trim().length > 0) {
      const q = val.toLowerCase();
      const results = [];

      // Search nav pages
      navItems.forEach(item => {
        if (item.label.toLowerCase().includes(q) || item.id.toLowerCase().includes(q)) {
          results.push({ id: item.id, label: item.label, icon: item.icon, path: item.path, type: '页面' });
        }
      });

      // Search projects (from localStorage)
      try {
        const projects = JSON.parse(localStorage.getItem('smart_kv_' + (user?.username ? `u_${user.username}_` : '') + 'projects') || '[]');
        projects.forEach(p => {
          if (p.name?.toLowerCase().includes(q)) {
            results.push({ id: p.id, label: p.name, icon: 'folder', path: `/workbench?project=${p.id}`, type: '项目', desc: `${p.materialCount || 0} 个物料` });
          }
        });
      } catch {}

      // Search history
      try {
        const history = JSON.parse(localStorage.getItem('smart_kv_' + (user?.username ? `u_${user.username}_` : '') + 'history') || '[]');
        history.forEach((h, i) => {
          if (h.theme?.toLowerCase().includes(q)) {
            results.push({ id: 'hist_' + i, label: h.theme, icon: 'history', path: '/history', type: '历史', desc: h.createdAt });
          }
        });
      } catch {}

      setSearchResults(results.slice(0, 8));
      setShowSearchResults(true);
    } else {
      setSearchResults([]);
      setShowSearchResults(false);
    }
  };

  const handleSearchSelect = (path) => {
    navigate(path);
    setSearchQuery('');
    setShowSearchResults(false);
  };

  // Close search dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowSearchResults(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Close sidebar on route change (mobile)
  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  const getPageTitle = () => {
    const item = navItems.find(n => n.path === location.pathname);
    return item ? item.label : 'AI 视觉工厂';
  };

  const NavLinks = () => (
    <nav className="flex-1 space-y-1 px-3">
      {visibleNavItems.map((item) => (
        <NavLink key={item.id} to={item.path} onClick={() => setSidebarOpen(false)} className={({ isActive }) => `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors duration-200 ${isActive ? 'text-primary font-semibold border-r-2 border-primary bg-surface-container-low' : 'text-on-surface-variant hover:bg-surface-container-low'}`}>
          <Icon name={item.icon} filled={location.pathname === item.path} /><span>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );

  const SidebarContent = () => (
    <>
      <div className="px-6 mb-8">
        <button onClick={() => navigate('/')} className="text-left hover:opacity-80 transition-opacity bg-transparent border-none cursor-pointer p-0">
          <h1 className="font-hanken text-[20px] leading-7 font-semibold text-primary tracking-tight">Miketv</h1>
          <p className="text-on-surface-variant text-xs mt-1">AI 视觉工厂</p>
        </button>
      </div>
      <NavLinks />
      <div className="px-6 pt-6 mt-auto border-t border-outline-variant">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full bg-primary text-on-primary flex items-center justify-center text-sm font-bold">{user?.displayName?.[0] || 'U'}</div>
          <div className="flex flex-col flex-1 min-w-0">
            <span className="text-body-md font-semibold text-on-surface truncate">{user?.displayName || '用户'}</span>
            <span className="text-[10px] text-on-surface-variant uppercase tracking-wider">操作员</span>
          </div>
        </div>
        <a href="/login" onClick={(e)=>{e.preventDefault(); if(window.__kvLogout)window.__kvLogout();}} className="mt-3 flex items-center gap-1.5 text-[10px] text-outline hover:text-error transition-colors cursor-pointer">
          <Icon name="logout" className="text-[14px]" />退出登录
        </a>
      </div>
    </>
  );

  return (
    <div className="flex min-h-screen">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 bg-black/50 z-40" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar - desktop: fixed, mobile: overlay drawer */}
      <aside className={`bg-surface h-screen fixed left-0 top-0 border-r border-outline-variant flex flex-col py-6 z-50 transition-transform duration-300 w-64
        lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <SidebarContent />
      </aside>

      {/* Main */}
      <div className="flex-1 lg:ml-64">
        {/* Top Bar */}
        <header className="fixed top-0 right-0 w-full lg:w-[calc(100%-16rem)] h-16 bg-surface border-b border-outline-variant flex items-center justify-between px-4 md:px-8 z-40">
          <div className="flex items-center gap-3 flex-1 max-w-xl">
            {/* Hamburger for mobile */}
            <button onClick={() => setSidebarOpen(!sidebarOpen)} className="lg:hidden text-on-surface-variant hover:text-primary p-1">
              <Icon name="menu" className="text-2xl" />
            </button>
            <div className="relative w-full group" ref={searchRef}>
              <Icon name="search" className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant z-10" />
              <input className="w-full bg-surface-container-low border-none rounded-lg pl-10 pr-4 py-2 text-body-md focus:ring-2 focus:ring-primary focus:outline-none transition-all" placeholder={`搜索页面...`} value={searchQuery} onChange={(e) => handleSearch(e.target.value)} onFocus={() => searchQuery.trim() && setShowSearchResults(true)} />
              {showSearchResults && searchResults.length > 0 && (
                <div className="absolute top-full mt-1 left-0 right-0 bg-surface-container-high border border-outline-variant rounded-xl shadow-2xl z-50 overflow-hidden">
                  {searchResults.map(item => (
                    <button key={item.id} onClick={() => handleSearchSelect(item.path)} className="w-full text-left px-4 py-3 hover:bg-surface-container transition-colors flex items-center gap-3 text-sm">
                      <Icon name={item.icon} className="text-primary text-lg" />
                      <div className="flex-1 min-w-0">
                        <span className="font-semibold text-on-surface">{item.label}</span>
                        {item.desc && <span className="text-[10px] text-on-surface-variant ml-2">{item.desc}</span>}
                      </div>
                      <span className="text-[9px] px-2 py-0.5 rounded-full bg-primary/10 text-primary shrink-0">{item.type}</span>
                    </button>
                  ))}
                </div>
              )}
              {showSearchResults && searchQuery.trim() && searchResults.length === 0 && (
                <div className="absolute top-full mt-1 left-0 right-0 bg-surface-container-high border border-outline-variant rounded-xl shadow-2xl z-50 p-4 text-center text-sm text-on-surface-variant">
                  未找到匹配结果
                </div>
              )}
              {showSearchResults && searchQuery.trim() && searchResults.length === 0 && (
                <div className="absolute top-full mt-1 left-0 right-0 bg-surface border border-outline-variant rounded-xl shadow-2xl z-50 p-4 text-center text-sm text-on-surface-variant">
                  未找到匹配页面
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-2 md:space-x-4 relative">
            {/* Help button - hide text on small screens */}
            <button onClick={() => { setHelpOpen(!helpOpen); setNotifOpen(false); }} className={`flex items-center gap-1.5 px-2 md:px-3 py-2 rounded-lg transition-all ${helpOpen ? 'bg-primary text-white' : 'bg-primary/10 text-primary hover:bg-primary/20'}`}>
              <Icon name="help" className="text-[20px]" /><span className="hidden md:inline text-xs font-semibold">操作指引</span>
            </button>
            {helpOpen && <HelpPopover onClose={() => setHelpOpen(false)} />}

            {/* Theme toggle */}
            <button onClick={toggleTheme} className="text-on-surface-variant hover:text-primary transition-all p-1.5" title={theme === 'dark' ? '切换浅色模式' : '切换暗色模式'}>
              <Icon name={theme === 'dark' ? 'light_mode' : 'dark_mode'} className="text-[20px]" />
            </button>

            {/* Notification bell */}
            <button onClick={() => { setNotifOpen(!notifOpen); setHelpOpen(false); }} className="text-on-surface-variant hover:text-primary transition-all relative p-1.5">
              <Icon name="notifications" className="text-[22px]" />
              <span className="absolute top-0.5 right-0.5 w-2.5 h-2.5 bg-error rounded-full border-2 border-surface"></span>
            </button>
            {notifOpen && <NotificationPopover onClose={() => setNotifOpen(false)} />}

            <div className="hidden md:block h-8 w-px bg-outline-variant"></div>
            <button onClick={() => navigate('/workbench')} className="hidden md:flex bg-primary text-on-primary px-4 py-2 rounded-lg items-center space-x-2 active:scale-95 transition-all hover:shadow-lg cursor-pointer">
              <Icon name="add" className="text-sm" /><span className="font-semibold text-sm">新增任务</span>
            </button>
          </div>
        </header>

        <div className="pt-16 pb-16 lg:pb-0">
          <ErrorBoundary>{children}</ErrorBoundary>
        </div>
      </div>

      {/* Mobile Bottom Navigation */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 bg-surface border-t border-outline-variant z-50 flex justify-around items-center h-14 px-2">
        {visibleNavItems.slice(0, 5).map(item => (
          <NavLink key={item.id} to={item.path} className={({ isActive }) => `flex flex-col items-center gap-0.5 px-2 py-1 rounded-lg transition-colors ${isActive ? 'text-primary' : 'text-on-surface-variant'}`}>
            <Icon name={item.icon} className="text-[20px]" filled={location.pathname === item.path} />
            <span className="text-[9px] font-medium leading-none">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Toast notifications */}
      <ToastContainer />

      {/* Command Palette */}
      <CommandPalette
        open={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        onToggleTheme={toggleTheme}
        onLogout={() => { if (window.__kvLogout) window.__kvLogout(); }}
      />
    </div>
  );
}

export { Icon };
