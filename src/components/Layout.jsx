import { useState, useCallback } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { navItems } from '../data/mockData';
import { useUser } from '../data/auth';

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
  useState(() => {
    const handler = (t) => {
      if (t.remove) { setToasts(prev => prev.filter(x => x.id !== t.id)); }
      else { setToasts(prev => [...prev.slice(-4), t]); }
    };
    toastListeners.add(handler);
    return () => toastListeners.delete(handler);
  }, []);
  if (toasts.length === 0) return null;
  return (<div className="fixed top-20 right-8 z-[200] flex flex-col gap-2">{toasts.map(t => (<div key={t.id} className="animate-slide-in px-4 py-3 bg-surface border border-outline-variant rounded-xl shadow-lg text-sm font-semibold text-on-surface flex items-center gap-2" style={{animation:'slideIn 0.3s ease-out'}}><span className={`w-2 h-2 rounded-full ${t.type==='error'?'bg-error':'bg-green-500'}`}></span>{t.message}</div>))}
    <style>{`@keyframes slideIn{from{transform:translateX(100px);opacity:0}to{transform:translateX(0);opacity:1}}`}</style>
  </div>);
}

function NotificationPopover({ onClose }) {
  const [items, setItems] = useState(MOCK_NOTIFICATIONS);
  useState(() => {
    const h = (n) => setItems(prev => [n, ...prev].slice(0, 20));
    notifListeners.add(h);
    return () => notifListeners.delete(h);
  }, []);
  return (<div className="absolute top-12 right-0 w-80 bg-surface border border-outline-variant rounded-xl shadow-2xl z-50 overflow-hidden" onClick={e => e.stopPropagation()}>
    <div className="p-4 border-b border-outline-variant flex items-center justify-between"><h4 className="font-hanken font-semibold text-sm">消息通知</h4><button onClick={onClose} className="text-xs text-outline hover:text-error">关闭</button></div>
    <div className="max-h-72 overflow-y-auto">{items.length===0?<p className="text-center text-xs text-on-surface-variant py-8">暂无通知</p>:items.map(n => (<div key={n.id} className="px-4 py-3 hover:bg-surface-container-low transition-colors border-b border-outline-variant/50 last:border-0"><div className="flex items-start gap-3"><Icon name={n.icon} className={`${n.color} text-[18px] mt-0.5`} /><div><p className="text-xs font-semibold text-on-surface">{n.title}</p><p className="text-[11px] text-on-surface-variant mt-0.5">{n.desc}</p><p className="text-[9px] text-outline mt-1 font-jetbrains">{n.time}</p></div></div></div>))}</div>
  </div>);
}

function HelpPopover({ onClose }) {
  return (<div className="absolute top-12 right-0 w-96 bg-surface border border-outline-variant rounded-xl shadow-2xl z-50 overflow-hidden" onClick={e => e.stopPropagation()}>
    <div className="p-4 border-b border-outline-variant flex items-center justify-between"><h4 className="font-hanken font-semibold text-sm">操作指引</h4><button onClick={onClose} className="text-xs text-outline hover:text-error">关闭</button></div>
    <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
      {[{s:'1',t:'上传主 KV 设计图',d:'拖放或点击上传 JPG/PNG 图片，自动压缩并发送给视觉模型分析。'},
        {s:'2',t:'等待 AI 分析',d:'Gemini 2.5 Flash 提取色板、字体、布局和风格。'},
        {s:'3',t:'填写主题名称',d:'可选，输入活动名如"2024品牌年会"。'},
        {s:'4',t:'选择生图模型',d:'6个模型可选，价格标注在卡片右上角。'},
        {s:'5',t:'勾选目标物料',d:'默认全选12个，可前往物料库自定义。'},
        {s:'6',t:'一键生成',d:'逐一生图，Nano Banana~30秒/张，GPT-Image 2 同步返回。'},
        {s:'7',t:'查看和保存',d:'缩略图放大查看+裁剪，结果自动保存到历史。'},
      ].map(item=>(<div key={item.s} className="flex gap-3"><div className="w-6 h-6 rounded-full bg-primary text-on-primary flex items-center justify-center shrink-0 font-semibold text-[11px]">{item.s}</div><div><p className="text-xs font-semibold text-on-surface">{item.t}</p><p className="text-[11px] text-on-surface-variant mt-0.5">{item.d}</p></div></div>))}
    </div>
  </div>);
}

export default function Layout({ children }) {
  const user = useUser();
  const [searchQuery, setSearchQuery] = useState('');
  const location = useLocation();
  const [notifOpen, setNotifOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);

  const getPageTitle = () => {
    const item = navItems.find(n => n.path === location.pathname);
    return item ? item.label : 'AI 视觉工厂';
  };

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="bg-surface h-screen w-64 fixed left-0 top-0 border-r border-outline-variant flex flex-col py-6 z-50">
        <div className="px-6 mb-8">
          <h1 className="font-hanken text-[20px] leading-7 font-semibold text-primary tracking-tight">AI 视觉工厂</h1>
          <p className="text-on-surface-variant text-xs mt-1">数字匠人工作空间</p>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {navItems.map((item) => (
            <NavLink key={item.id} to={item.path} className={({ isActive }) => `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors duration-200 ${isActive ? 'text-primary font-semibold border-r-2 border-primary bg-surface-container-low' : 'text-on-surface-variant hover:bg-surface-container-low'}`}>
              <Icon name={item.icon} filled={location.pathname === item.path} /><span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="px-6 pt-6 mt-auto border-t border-outline-variant">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-primary text-on-primary flex items-center justify-center text-sm font-bold">{user?.avatar || 'U'}</div>
            <div className="flex flex-col flex-1 min-w-0">
              <span className="text-body-md font-semibold text-on-surface truncate">{user?.displayName || '用户'}</span>
              <span className="text-[10px] text-on-surface-variant uppercase tracking-wider">操作员</span>
            </div>
          </div>
          <a href="/login" onClick={(e)=>{e.preventDefault(); if(window.__kvLogout)window.__kvLogout();}} className="mt-3 flex items-center gap-1.5 text-[10px] text-outline hover:text-error transition-colors cursor-pointer">
            <Icon name="logout" className="text-[14px]" />退出登录
          </a>
        </div>
      </aside>

      {/* Main */}
      <div className="ml-64 flex-1">
        {/* Top Bar */}
        <header className="fixed top-0 right-0 w-[calc(100%-16rem)] h-16 bg-surface border-b border-outline-variant flex items-center justify-between px-8 z-40">
          <div className="flex items-center flex-1 max-w-xl">
            <div className="relative w-full group">
              <Icon name="search" className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant" />
              <input className="w-full bg-surface-container-low border-none rounded-lg pl-10 pr-4 py-2 text-body-md focus:ring-2 focus:ring-primary focus:outline-none transition-all" placeholder={`搜索${getPageTitle()}...`} value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
            </div>
          </div>

          <div className="flex items-center space-x-4 relative">
            {/* Help button - prominent */}
            <button onClick={() => { setHelpOpen(!helpOpen); setNotifOpen(false); }} className={`flex items-center gap-1.5 px-3 py-2 rounded-lg transition-all ${helpOpen ? 'bg-primary text-white' : 'bg-primary/10 text-primary hover:bg-primary/20'}`}>
              <Icon name="help" className="text-[20px]" /><span className="text-xs font-semibold">操作指引</span>
            </button>
            {helpOpen && <HelpPopover onClose={() => setHelpOpen(false)} />}

            {/* Notification bell */}
            <button onClick={() => { setNotifOpen(!notifOpen); setHelpOpen(false); }} className="text-on-surface-variant hover:text-primary transition-all relative p-1.5">
              <Icon name="notifications" className="text-[22px]" />
              <span className="absolute top-0.5 right-0.5 w-2.5 h-2.5 bg-error rounded-full border-2 border-surface"></span>
            </button>
            {notifOpen && <NotificationPopover onClose={() => setNotifOpen(false)} />}

            <div className="h-8 w-px bg-outline-variant"></div>
            <button className="bg-primary text-on-primary px-4 py-2 rounded-lg flex items-center space-x-2 active:scale-95 transition-all hover:shadow-lg">
              <Icon name="add" className="text-sm" /><span className="font-semibold text-sm">新增任务</span>
            </button>
          </div>
        </header>

        <div className="pt-16">{children}</div>
      </div>

      {/* Toast notifications */}
      <ToastContainer />
    </div>
  );
}

export { Icon };
