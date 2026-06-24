import { useState } from 'react';
import Layout, { Icon, showToast } from '../components/Layout';
import { useUser, logout, login } from '../data/auth';

export default function Profile() {
  const user = useUser();
  const [displayName, setDisplayName] = useState(user?.displayName || '');
  const [currentPwd, setCurrentPwd] = useState('');
  const [newPwd, setNewPwd] = useState('');
  const [confirmPwd, setConfirmPwd] = useState('');
  const [avatar, setAvatar] = useState(user?.avatar || '');

  const handleUpdateProfile = () => {
    if (!displayName.trim()) { showToast('昵称不能为空', 'error'); return; }
    // Update user in localStorage
    const users = JSON.parse(localStorage.getItem('smart_kv_users') || '[]');
    const idx = users.findIndex(u => u.username === user.username);
    if (idx >= 0) {
      users[idx].displayName = displayName.trim();
      users[idx].avatar = avatar || displayName.trim()[0].toUpperCase();
      localStorage.setItem('smart_kv_users', JSON.stringify(users));
      // Update session
      const session = JSON.parse(localStorage.getItem('smart_kv_user') || '{}');
      session.displayName = displayName.trim();
      session.avatar = avatar || displayName.trim()[0].toUpperCase();
      localStorage.setItem('smart_kv_user', JSON.stringify(session));
      showToast('资料已更新', 'success');
    }
  };

  const handleChangePassword = () => {
    if (!currentPwd || !newPwd) { showToast('请填写新旧密码', 'error'); return; }
    if (newPwd !== confirmPwd) { showToast('两次密码不一致', 'error'); return; }
    if (newPwd.length < 4) { showToast('新密码至少4位', 'error'); return; }
    // Verify current password
    const check = login(user.username, currentPwd);
    if (!check) { showToast('当前密码错误', 'error'); return; }
    // Update password
    const users = JSON.parse(localStorage.getItem('smart_kv_users') || '[]');
    const idx = users.findIndex(u => u.username === user.username);
    if (idx >= 0) {
      // Use same hash as auth.js
      function hashPassword(pwd) {
        let hash = 0;
        const str = pwd + 'miketv_salt_2024';
        for (let i = 0; i < str.length; i++) {
          hash = ((hash << 5) - hash) + str.charCodeAt(i);
          hash |= 0;
        }
        return 'mktv_' + Math.abs(hash).toString(36);
      }
      users[idx].password = hashPassword(newPwd);
      localStorage.setItem('smart_kv_users', JSON.stringify(users));
      setCurrentPwd(''); setNewPwd(''); setConfirmPwd('');
      showToast('密码已修改', 'success');
    }
  };

  const handleLogout = () => {
    logout();
    window.location.href = '/';
  };

  return (
    <Layout>
      <div className="p-4 md:p-8 max-w-2xl mx-auto">
        <h2 className="font-hanken text-[24px] leading-8 font-semibold text-on-surface mb-6">个人中心</h2>

        {/* Avatar + Name */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6 mb-6">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-16 h-16 rounded-full bg-primary text-on-primary flex items-center justify-center text-2xl font-bold">
              {avatar || user?.displayName?.[0] || 'U'}
            </div>
            <div>
              <h3 className="font-semibold text-lg text-on-surface">{user?.displayName}</h3>
              <p className="text-sm text-on-surface-variant">@{user?.username} · {user?.role}</p>
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-on-surface mb-1.5">显示名称</label>
            <input value={displayName} onChange={e => setDisplayName(e.target.value)} className="w-full px-4 py-2.5 bg-surface border border-outline-variant rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary" />
          </div>
          <button onClick={handleUpdateProfile} className="mt-4 px-6 py-2 bg-primary text-on-primary rounded-lg font-semibold hover:shadow active:scale-95 transition-all">保存修改</button>
        </div>

        {/* Change Password */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6 mb-6">
          <h3 className="font-semibold text-lg text-on-surface mb-4">修改密码</h3>
          <div className="space-y-3">
            <input type="password" value={currentPwd} onChange={e => setCurrentPwd(e.target.value)} placeholder="当前密码" className="w-full px-4 py-2.5 bg-surface border border-outline-variant rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary" />
            <input type="password" value={newPwd} onChange={e => setNewPwd(e.target.value)} placeholder="新密码（至少4位）" className="w-full px-4 py-2.5 bg-surface border border-outline-variant rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary" />
            <input type="password" value={confirmPwd} onChange={e => setConfirmPwd(e.target.value)} placeholder="确认新密码" className="w-full px-4 py-2.5 bg-surface border border-outline-variant rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary" />
          </div>
          <button onClick={handleChangePassword} className="mt-4 px-6 py-2 bg-primary text-on-primary rounded-lg font-semibold hover:shadow active:scale-95 transition-all">修改密码</button>
        </div>

        {/* Logout */}
        <button onClick={handleLogout} className="w-full py-3 border border-error/50 text-error rounded-xl font-semibold hover:bg-error/5 transition-all">退出登录</button>
      </div>
    </Layout>
  );
}
