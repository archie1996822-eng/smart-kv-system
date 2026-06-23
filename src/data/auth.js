import { createContext, useContext } from 'react';

const AUTH_KEY = 'smart_kv_user';
const USERS_KEY = 'smart_kv_users';

// Simple hash function (SHA-256 would be better but requires async)
function hashPassword(pwd) {
  let hash = 0;
  const salt = 'miketv_salt_2024';
  const str = pwd + salt;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0;
  }
  return 'mktv_' + Math.abs(hash).toString(36);
}

const DEFAULT_USERS = [
  { username: 'admin', password: hashPassword('123456'), displayName: '管理员 Admin', role: 'admin', avatar: 'A', plan: 'enterprise' },
  { username: 'wanzi', password: hashPassword('123456'), displayName: 'Wanzi', role: 'tester', avatar: 'W', plan: 'pro' },
];

export const UserContext = createContext(null);
export const useUser = () => useContext(UserContext);

function loadUsers() {
  try {
    const v = localStorage.getItem(USERS_KEY);
    if (!v) { saveUsers(DEFAULT_USERS); return DEFAULT_USERS; }
    return JSON.parse(v);
  } catch { return DEFAULT_USERS; }
}

function saveUsers(users) {
  try { localStorage.setItem(USERS_KEY, JSON.stringify(users)); } catch {}
}

export function login(username, password) {
  const users = loadUsers();
  const hashedInput = hashPassword(password);
  const u = users.find(x => x.username === username && x.password === hashedInput);
  // Support old plaintext passwords for migration
  const uLegacy = !u ? users.find(x => x.username === username && x.password === password) : null;
  if (!u && !uLegacy) return null;

  const user = u || uLegacy;
  // Migrate legacy password to hash
  if (uLegacy) {
    user.password = hashedInput;
    const idx = users.findIndex(x => x.username === username);
    if (idx >= 0) { users[idx] = user; saveUsers(users); }
  }

  const session = {
    username: user.username,
    displayName: user.displayName,
    role: user.role,
    avatar: user.avatar,
    plan: user.plan || 'free',
    loginAt: Date.now(),
    token: 'tok_' + Math.random().toString(36).substring(2) + Date.now().toString(36),
  };
  localStorage.setItem(AUTH_KEY, JSON.stringify(session));
  localStorage.setItem('smart_kv_user_plan', user.plan || 'free');
  return session;
}

export function register(username, password, displayName) {
  if (!username || !password || username.length < 2 || password.length < 4) return { error: '账号至少2位，密码至少4位' };
  const users = loadUsers();
  if (users.find(u => u.username === username)) return { error: '账号已存在' };
  const newUser = {
    username,
    password: hashPassword(password),
    displayName: displayName || username,
    role: 'tester',
    avatar: username[0].toUpperCase(),
    plan: 'free',
  };
  users.push(newUser);
  saveUsers(users);
  return { success: true, user: newUser };
}

export function logout() {
  localStorage.removeItem(AUTH_KEY);
  try { sessionStorage.removeItem('smart_kv_' + userPrefix() + 'workbench_session'); } catch {}
}

export function getCurrentUser() {
  try { const v = localStorage.getItem(AUTH_KEY); return v ? JSON.parse(v) : null; } catch { return null; }
}

export function isAdmin() {
  const u = getCurrentUser();
  return u?.role === 'admin';
}

export function listAllUsers() {
  return loadUsers().map(u => ({ username: u.username, displayName: u.displayName, role: u.role, plan: u.plan || 'free' }));
}

export function userPrefix(username) {
  const u = username || getCurrentUser()?.username;
  return u ? `u_${u}_` : 'u_anon_';
}

// Session validation — checks if token is still valid
export function validateSession() {
  const u = getCurrentUser();
  if (!u) return false;
  // Token expires after 30 days
  if (Date.now() - u.loginAt > 30 * 24 * 60 * 60 * 1000) {
    logout();
    return false;
  }
  return true;
}

// Supabase Auth integration — import { loginWithSupabase } when credentials are ready
// Requires: VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in .env
