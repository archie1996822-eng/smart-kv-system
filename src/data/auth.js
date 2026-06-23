import { createContext, useContext } from 'react';

const AUTH_KEY = 'smart_kv_user';
const USERS_KEY = 'smart_kv_users';

const DEFAULT_USERS = [
  { username: 'admin', password: '123456', displayName: '管理员 Admin', role: 'admin', avatar: 'A' },
  { username: 'wanzi', password: '123456', displayName: 'Wanzi', role: 'tester', avatar: 'W' },
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
  const u = users.find(x => x.username === username && x.password === password);
  if (!u) return null;
  const session = { username: u.username, displayName: u.displayName, role: u.role, avatar: u.avatar, loginAt: Date.now() };
  localStorage.setItem(AUTH_KEY, JSON.stringify(session));
  return session;
}

export function register(username, password, displayName) {
  if (!username || !password || username.length < 2 || password.length < 4) return { error: '账号至少2位，密码至少4位' };
  const users = loadUsers();
  if (users.find(u => u.username === username)) return { error: '账号已存在' };
  const newUser = { username, password, displayName: displayName || username, role: 'tester', avatar: username[0].toUpperCase() };
  users.push(newUser);
  saveUsers(users);
  return { success: true, user: newUser };
}

export function logout() {
  localStorage.removeItem(AUTH_KEY);
  // Only clear session-scoped workbench data, preserve user's history/materials/templates
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
  return loadUsers().map(u => ({ username: u.username, displayName: u.displayName, role: u.role }));
}

// Namespace prefix for user-specific data
export function userPrefix(username) {
  const u = username || getCurrentUser()?.username;
  return u ? `u_${u}_` : 'u_anon_';
}
