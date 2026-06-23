import { useState } from 'react';
import { login, register } from '../data/auth';

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [regName, setRegName] = useState('');
  const [regUser, setRegUser] = useState('');
  const [regPwd, setRegPwd] = useState('');

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
    // Auto login after register
    const user = login(regUser.trim(), regPwd);
    if (user) onLogin(user);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#f0f4ff', gap: '16px', padding: '16px' }}>
      {mode === 'login' ? (
        <form onSubmit={handleSubmit} style={{ width: '360px', maxWidth: '100%', background: '#fff', borderRadius: '16px', padding: '40px 32px', boxShadow: '0 4px 24px rgba(0,0,0,0.06)' }}>
          <h1 style={{ textAlign: 'center', fontSize: '22px', fontWeight: 700, color: '#0b1c30', margin: '0 0 4px', fontFamily: 'Inter, sans-serif' }}>Miketv</h1>
          <p style={{ textAlign: 'center', fontSize: '13px', color: '#727687', margin: '0 0 28px' }}>AI 视觉工厂 · 智能物料延展</p>

          {error && <p style={{ background: '#fff0f0', color: '#c00', padding: '10px 14px', borderRadius: '8px', fontSize: '13px', textAlign: 'center', margin: '0 0 16px' }}>{error}</p>}

          <input value={username} onChange={e => setUsername(e.target.value)} placeholder="账号" autoFocus
            style={{ display: 'block', width: '100%', padding: '12px 14px', margin: '0 0 12px', border: '1px solid #dce0e8', borderRadius: '8px', fontSize: '14px', outline: 'none', boxSizing: 'border-box', background: '#f8f9ff' }} />

          <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="密码"
            style={{ display: 'block', width: '100%', padding: '12px 14px', margin: '0 0 20px', border: '1px solid #dce0e8', borderRadius: '8px', fontSize: '14px', outline: 'none', boxSizing: 'border-box', background: '#f8f9ff' }} />

          <button type="submit"
            style={{ display: 'block', width: '100%', padding: '13px', background: '#0066ff', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '15px', fontWeight: 600, cursor: 'pointer' }}>
            登 录
          </button>

          <p style={{ textAlign: 'center', marginTop: '16px', fontSize: '13px', color: '#727687' }}>
            没有账号？<button type="button" onClick={() => { setMode('register'); setError(''); }} style={{ background: 'none', border: 'none', color: '#0066ff', cursor: 'pointer', fontWeight: 600, fontSize: '13px', padding: 0 }}>注册新账号</button>
          </p>
        </form>
      ) : (
        <form onSubmit={handleRegister} style={{ width: '360px', maxWidth: '100%', background: '#fff', borderRadius: '16px', padding: '40px 32px', boxShadow: '0 4px 24px rgba(0,0,0,0.06)' }}>
          <h1 style={{ textAlign: 'center', fontSize: '22px', fontWeight: 700, color: '#0b1c30', margin: '0 0 4px', fontFamily: 'Inter, sans-serif' }}>注册新账号</h1>
          <p style={{ textAlign: 'center', fontSize: '13px', color: '#727687', margin: '0 0 28px' }}>加入 Miketv AI 视觉工厂</p>

          {error && <p style={{ background: '#fff0f0', color: '#c00', padding: '10px 14px', borderRadius: '8px', fontSize: '13px', textAlign: 'center', margin: '0 0 16px' }}>{error}</p>}

          <input value={regName} onChange={e => setRegName(e.target.value)} placeholder="昵称（选填）" autoFocus
            style={{ display: 'block', width: '100%', padding: '12px 14px', margin: '0 0 12px', border: '1px solid #dce0e8', borderRadius: '8px', fontSize: '14px', outline: 'none', boxSizing: 'border-box', background: '#f8f9ff' }} />

          <input value={regUser} onChange={e => setRegUser(e.target.value)} placeholder="账号（至少2位）"
            style={{ display: 'block', width: '100%', padding: '12px 14px', margin: '0 0 12px', border: '1px solid #dce0e8', borderRadius: '8px', fontSize: '14px', outline: 'none', boxSizing: 'border-box', background: '#f8f9ff' }} />

          <input type="password" value={regPwd} onChange={e => setRegPwd(e.target.value)} placeholder="密码（至少4位）"
            style={{ display: 'block', width: '100%', padding: '12px 14px', margin: '0 0 20px', border: '1px solid #dce0e8', borderRadius: '8px', fontSize: '14px', outline: 'none', boxSizing: 'border-box', background: '#f8f9ff' }} />

          <button type="submit"
            style={{ display: 'block', width: '100%', padding: '13px', background: '#0066ff', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '15px', fontWeight: 600, cursor: 'pointer' }}>
            注 册 并 登 录
          </button>

          <p style={{ textAlign: 'center', marginTop: '16px', fontSize: '13px', color: '#727687' }}>
            已有账号？<button type="button" onClick={() => { setMode('login'); setError(''); }} style={{ background: 'none', border: 'none', color: '#0066ff', cursor: 'pointer', fontWeight: 600, fontSize: '13px', padding: 0 }}>返回登录</button>
          </p>
        </form>
      )}
    </div>
  );
}
