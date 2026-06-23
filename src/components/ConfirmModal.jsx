import { useState, useRef, useEffect } from 'react';
import { useShortcuts } from '../data/shortcuts';

function Icon({ name, filled = false, className = '' }) {
  return (<span className={`material-symbols-outlined ${className}`} style={filled ? { fontVariationSettings: '"FILL" 1, "wght" 400, "GRAD" 0, "opsz" 24' } : {}}>{name}</span>);
}

export default function ConfirmModal({ open, onClose, onConfirm, title, message, confirmText = '确认', cancelText = '取消', variant = 'primary', children, icon }) {
  useShortcuts({
    'Escape': () => { if (open) onClose(); },
  });

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[200] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in" onClick={onClose}>
      <div className="bg-surface-container-high border border-outline-variant rounded-2xl shadow-2xl max-w-md w-full p-6" onClick={e => e.stopPropagation()} style={{ animation: 'slideUp 0.2s ease-out' }}>
        {icon && (
          <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-primary/10 flex items-center justify-center">
            <Icon name={icon} className={`text-2xl ${variant === 'danger' ? 'text-error' : 'text-primary'}`} />
          </div>
        )}
        {title && <h3 className="font-hanken text-lg font-semibold text-on-surface mb-2 text-center">{title}</h3>}
        {message && <p className="text-sm text-on-surface-variant mb-4 text-center">{message}</p>}
        {children && <div className="mb-4">{children}</div>}
        <div className="flex gap-3">
          <button onClick={onClose} className="flex-1 py-2.5 border border-outline-variant rounded-xl text-sm font-semibold text-on-surface-variant hover:bg-surface-container transition-all active:scale-95">
            {cancelText}
          </button>
          <button onClick={onConfirm} className={`flex-1 py-2.5 rounded-xl text-sm font-semibold transition-all active:scale-95 btn-primary-glow ${
            variant === 'danger' ? 'bg-error text-on-error hover:shadow-[0_0_20px_rgba(239,68,68,0.3)]' : 'bg-primary text-on-primary'
          }`}>
            {confirmText}
          </button>
        </div>
      </div>
      <style>{`@keyframes slideUp{from{transform:translateY(20px);opacity:0}to{transform:translateY(0);opacity:1}}`}</style>
    </div>
  );
}

// Simple prompt modal (replaces window.prompt)
export function PromptModal({ open, onClose, onSubmit, title, placeholder = '', defaultValue = '' }) {
  const [value, setValue] = useState(defaultValue);
  const inputRef = useRef(null);

  useEffect(() => {
    if (open) {
      setValue(defaultValue);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [open, defaultValue]);

  useShortcuts({
    'Escape': () => { if (open) onClose(); },
    'Enter': () => { if (open && value.trim()) { onSubmit(value.trim()); onClose(); } },
  });

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[200] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-surface-container-high border border-outline-variant rounded-2xl shadow-2xl max-w-md w-full p-6" onClick={e => e.stopPropagation()} style={{ animation: 'slideUp 0.2s ease-out' }}>
        {title && <h3 className="font-hanken text-lg font-semibold text-on-surface mb-4">{title}</h3>}
        <input
          ref={inputRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          placeholder={placeholder}
          className="w-full px-4 py-3 bg-surface border border-outline-variant rounded-xl text-sm outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all"
          onKeyDown={e => { if (e.key === 'Enter' && value.trim()) { onSubmit(value.trim()); onClose(); } }}
        />
        <div className="flex gap-3 mt-4">
          <button onClick={onClose} className="flex-1 py-2.5 border border-outline-variant rounded-xl text-sm font-semibold text-on-surface-variant hover:bg-surface-container transition-all active:scale-95">取消</button>
          <button onClick={() => { if (value.trim()) { onSubmit(value.trim()); onClose(); } }} className="flex-1 py-2.5 bg-primary text-on-primary rounded-xl text-sm font-semibold btn-primary-glow">确认</button>
        </div>
      </div>
    </div>
  );
}
