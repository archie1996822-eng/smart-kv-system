import { useState } from 'react';
import { login, register } from '../data/auth';

function Icon({ name, filled = false, className = '' }) {
  return (<span className={`material-symbols-outlined ${className}`} style={filled ? { fontVariationSettings: '"FILL" 1, "wght" 400, "GRAD" 0, "opsz" 24' } : {}}>{name}</span>);
}

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [mode, setMode] = useState('login');
  const [regName, setRegName] = useState('');
  const [regUser, setRegUser] = useState('');
  const [regPwd, setRegPwd] = useState('');
  const [showPwd, setShowPwd] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');
    if (!username.trim() || !password.trim()) { setError('请输入账号和密码'); return; }
    const user = login(username.trim(), password);
    if (!user) { setError('账号或密码错误'); return; }
    onLogin(user);
  };

  const handleRegister = (e) => {
    e.preventDefault();
    setError('');
    const result = register(regUser.trim(), regPwd, regName.trim());
    if (result.error) { setError(result.error); return; }
    const user = login(regUser.trim(), regPwd);
    if (user) onLogin(user);
  };

  return (
    <div className="min-h-screen flex bg-background">
      {/* Left: Brand */}
      <div className="hidden lg:flex w-1/2 bg-surface-container-low relative overflow-hidden items-center justify-center">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-secondary/5" />
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 30% 50%, rgba(99,102,241,0.08) 0%, transparent 50%), radial-gradient(circle at 70% 30%, rgba(34,211,238,0.06) 0%, transparent 50%)',
        }} />
        <div className="relative text-center p-12 max-w-md">
          <h1 className="font-hanken text-5xl font-bold text-primary mb-4">Miketv</h1>
          <p className="text-xl text-on-surface font-semibold mb-2">AI 视觉工厂</p>
          <p className="text-on-surface-variant">视频与图像智能创作平台</p>
          <div className="mt-8 flex justify-center gap-4 text-sm text-on-surface-variant">
            <div className="text-center"><Icon name="auto_awesome" className="text-2xl text-primary mb-1 block mx-auto" /><span>AI 生图</span></div>
            <div className="text-center"><Icon name="videocam" className="text-2xl text-secondary mb-1 block mx-auto" /><span>视频创作</span></div>
            <div className="text-center"><Icon name="inventory_2" className="text-2xl text-tertiary mb-1 block mx-auto" /><span>批量物料</span></div>
            <div className="text-center"><Icon name="share" className="text-2xl text-primary mb-1 block mx-auto" /><span>一键导出</span></div>
          </div>
        </div>
      </div>

      {/* Right: Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        {mode === 'login' ? (
          <form onSubmit={handleSubmit} className="w-full max-w-sm">
            {/* Mobile brand */}
            <div className="lg:hidden text-center mb-8">
              <h1 className="font-hanken text-3xl font-bold text-primary">Miketv</h1>
              <p className="text-sm text-on-surface-variant mt-1">AI 视觉工厂</p>
            </div>

            <h2 className="text-2xl font-bold text-on-surface mb-1">欢迎回来</h2>
            <p className="text-sm text-on-surface-variant mb-8">登录你的 Miketv 账号</p>

            {error && (
              <div className="mb-4 p-3 bg-error/5 border border-error/20 rounded-xl text-sm text-error flex items-center gap-2">
                <Icon name="error" className="text-[18px]" />{error}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-on-surface mb-1.5">账号</label>
                <input
                  value={username} onChange={e => setUsername(e.target.value)} placeholder="输入账号"
                  autoFocus
                  className="w-full px-4 py-3 bg-surface-container-low border border-outline-variant rounded-xl text-sm outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-on-surface mb-1.5">密码</label>
                <div className="relative">
                  <input
                    type={showPwd ? 'text' : 'password'}
                    value={password} onChange={e => setPassword(e.target.value)} placeholder="输入密码"
                    className="w-full px-4 py-3 bg-surface-container-low border border-outline-variant rounded-xl text-sm outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all pr-10"
                  />
                  <button type="button" onClick={() => setShowPwd(!showPwd)} className="absolute right-3 top-1/2 -translate-y-1/2 text-outline hover:text-on-surface">
                    <Icon name={showPwd ? 'visibility_off' : 'visibility'} className="text-[18px]" />
                  </button>
                </div>
              </div>
            </div>

            <button type="submit" className="w-full mt-6 py-3 bg-primary text-on-primary rounded-xl font-semibold hover:shadow-[0_0_24px_rgba(99,102,241,0.35)] hover:scale-[1.02] active:scale-[0.97] transition-all">
              登 录
            </button>

            <p className="text-center text-sm text-on-surface-variant mt-6">
              没有账号？
              <button type="button" onClick={() => { setMode('register'); setError(''); }} className="text-primary font-semibold hover:underline ml-1">注册新账号</button>
            </p>

            <p className="text-center text-xs text-outline mt-8">
              演示账号: admin / 123456
            </p>
          </form>
        ) : (
          <form onSubmit={handleRegister} className="w-full max-w-sm">
            <div className="lg:hidden text-center mb-8">
              <h1 className="font-hanken text-3xl font-bold text-primary">Miketv</h1>
              <p className="text-sm text-on-surface-variant mt-1">AI 视觉工厂</p>
            </div>

            <h2 className="text-2xl font-bold text-on-surface mb-1">创建账号</h2>
            <p className="text-sm text-on-surface-variant mb-8">加入 Miketv，开启 AI 创作</p>

            {error && (
              <div className="mb-4 p-3 bg-error/5 border border-error/20 rounded-xl text-sm text-error flex items-center gap-2">
                <Icon name="error" className="text-[18px]" />{error}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-on-surface mb-1.5">昵称（选填）</label>
                <input value={regName} onChange={e => setRegName(e.target.value)} placeholder="你的名字" autoFocus
                  className="w-full px-4 py-3 bg-surface-container-low border border-outline-variant rounded-xl text-sm outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-on-surface mb-1.5">账号（至少2位）</label>
                <input value={regUser} onChange={e => setRegUser(e.target.value)} placeholder="输入账号"
                  className="w-full px-4 py-3 bg-surface-container-low border border-outline-variant rounded-xl text-sm outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-on-surface mb-1.5">密码（至少4位）</label>
                <div className="relative">
                  <input type={showPwd ? 'text' : 'password'} value={regPwd} onChange={e => setRegPwd(e.target.value)} placeholder="输入密码"
                    className="w-full px-4 py-3 bg-surface-container-low border border-outline-variant rounded-xl text-sm outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all pr-10" />
                  <button type="button" onClick={() => setShowPwd(!showPwd)} className="absolute right-3 top-1/2 -translate-y-1/2 text-outline hover:text-on-surface">
                    <Icon name={showPwd ? 'visibility_off' : 'visibility'} className="text-[18px]" />
                  </button>
                </div>
              </div>
            </div>

            <button type="submit" className="w-full mt-6 py-3 bg-primary text-on-primary rounded-xl font-semibold hover:shadow-[0_0_24px_rgba(99,102,241,0.35)] hover:scale-[1.02] active:scale-[0.97] transition-all">
              注 册 并 登 录
            </button>

            <p className="text-center text-sm text-on-surface-variant mt-6">
              已有账号？
              <button type="button" onClick={() => { setMode('login'); setError(''); }} className="text-primary font-semibold hover:underline ml-1">返回登录</button>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}
