import { userPrefix, listAllUsers } from './auth';

function storagePrefix(forUser) {
  return 'smart_kv_' + (forUser ? `u_${forUser}_` : userPrefix());
}

function sessGet(key, fallback = null, forUser) {
  try { const v = sessionStorage.getItem(storagePrefix(forUser) + key); return v ? JSON.parse(v) : fallback; } catch { return fallback; }
}
function sessSet(key, value, forUser) {
  try { sessionStorage.setItem(storagePrefix(forUser) + key, JSON.stringify(value)); } catch {}
}

function safeGet(key, fallback = null, forUser) {
  try { const v = localStorage.getItem(storagePrefix(forUser) + key); return v ? JSON.parse(v) : fallback; } catch { return fallback; }
}
function safeSet(key, value, forUser) {
  try { localStorage.setItem(storagePrefix(forUser) + key, JSON.stringify(value)); } catch {}
}

// === Material Config (12 items with appearance images) ===
const DEFAULT_MATERIALS = [
  { id: 'hand-sign', name: '手举牌', size: '450 × 320 mm', material: '3mm PVC板, 异形模切', category: '互动周边', icon: 'cut', appearanceImage: null },
  { id: 'flag', name: '道旗标准件', size: '3000 × 1200 mm', material: '经编布120g, 双面数码喷印', category: '场馆指引', icon: 'flag', appearanceImage: null },
  { id: 'badge', name: '人员工作证', size: '85 × 120 mm', material: 'PVC软胶, 丝印挂绳 2cm', category: '基础物料', icon: 'id_card', appearanceImage: null },
  { id: 'canvas-bag', name: '帆布袋', size: '350 × 400 × 100 mm', material: '12安纯棉帆布, 丝网印刷 4色', category: '基础物料', icon: 'shopping_bag', appearanceImage: null },
  { id: 'stand', name: '指引展架', size: '1200 × 2000 mm', material: 'KT板5mm, L型铁质展架', category: '场馆指引', icon: 'view_day', appearanceImage: null },
  { id: 'paper-bag', name: '手提纸袋', size: '320 × 270 × 100 mm', material: '250g白卡纸, 蓝色三股绳', category: '基础物料', icon: 'shopping_bag', appearanceImage: null },
  { id: 'host-card', name: '主持人手卡', size: '210 × 140 mm', material: '300g铜版纸, 双面覆哑膜', category: '基础物料', icon: 'description', appearanceImage: null },
  { id: 'signboard', name: '倒计时牌', size: '400 × 300 mm', material: 'KT板覆亚膜', category: '场馆指引', icon: 'calendar_clock', appearanceImage: null },
  { id: 'badge-sticker', name: '椅背贴', size: '300 × 150 mm', material: '车贴覆亚膜', category: '场馆指引', icon: 'sticky_note_2', appearanceImage: null },
  { id: 'manual', name: '会务手册', size: '210 × 285 mm', material: '封面300g铜版, 内页100g双胶', category: '基础物料', icon: 'book', appearanceImage: null },
  { id: 'ticket', name: '餐券/门票', size: '90 × 50 mm', material: '157g铜版纸, 打码', category: '基础物料', icon: 'confirmation_number', appearanceImage: null },
  { id: 'welcome-board', name: '接机接站牌', size: '600 × 400 mm', material: 'KT板覆亚膜', category: '场馆指引', icon: 'front_hand', appearanceImage: null },
];

export function loadMaterials() {
  const saved = safeGet('materials', []);
  if (saved.length === 0) return DEFAULT_MATERIALS;
  // Merge saved data with defaults (to add new items)
  return DEFAULT_MATERIALS.map(d => {
    const s = saved.find(x => x.id === d.id);
    return s ? { ...d, ...s } : d;
  });
}

export function saveMaterial(id, data) {
  const all = loadMaterials();
  const idx = all.findIndex(m => m.id === id);
  if (idx >= 0) { all[idx] = { ...all[idx], ...data }; safeSet('materials', all); }
}

// === Generation History ===
export function loadHistory() {
  return safeGet('history', []);
}

export function saveHistoryEntry(entry) {
  const history = loadHistory();
  // Keep max 20 entries, newest first
  history.unshift(entry);
  if (history.length > 20) history.length = 20;
  safeSet('history', history);
}

export function deleteHistoryEntry(index, forUser) {
  const history = forUser ? loadHistoryForUser(forUser) : loadHistory();
  history.splice(index, 1);
  safeSet('history', history, forUser);
}

function loadHistoryForUser(username) {
  return safeGet('history', [], username);
}

// === Custom Materials (user-added items) ===
export function loadCustomMaterials() {
  return safeGet('custom_materials', []);
}

export function saveCustomMaterial(item) {
  const all = loadCustomMaterials();
  const idx = all.findIndex(m => m.id === item.id);
  if (idx >= 0) { all[idx] = item; }
  else { all.push(item); }
  safeSet('custom_materials', all);
}

export function deleteCustomMaterial(id) {
  const all = loadCustomMaterials().filter(m => m.id !== id);
  safeSet('custom_materials', all);
}

// === Workbench State (for restore) ===
export function saveWorkbenchState(state) {
  safeSet('workbench_state', state);
}

export function loadWorkbenchState() {
  return safeGet('workbench_state', null);
}

export function clearWorkbenchState() {
  try { localStorage.removeItem(storagePrefix() + 'workbench_state'); } catch {}
}

// === Usage Statistics ===
export function loadStats() {
  const s = safeGet('usage_stats', { totalCalls: 0, totalCost: 0, history: [] });
  const thirtyDaysAgo = Date.now() - 30 * 24 * 60 * 60 * 1000;
  s.history = (s.history || []).filter(e => e.time > thirtyDaysAgo);
  return s;
}

export function trackUsage(model, type, success, cost) {
  const s = loadStats();
  const now = Date.now();
  s.totalCalls = (s.totalCalls || 0) + 1;
  s.totalCost = ((s.totalCost || 0) + (cost || 0));
  s.history.unshift({ time: now, model, type, success, cost: cost || 0 });
  if (s.history.length > 500) s.history.length = 500;
  safeSet('usage_stats', s);
}

export function getTodayStats() {
  const s = loadStats();
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const todayStart = today.getTime();
  const monthStart = new Date(today.getFullYear(), today.getMonth(), 1).getTime();
  const todayCalls = s.history.filter(e => e.time >= todayStart).length;
  const monthCalls = s.history.filter(e => e.time >= monthStart).length;
  const todayCost = s.history.filter(e => e.time >= todayStart).reduce((sum, e) => sum + (e.cost || 0), 0);
  const monthCost = s.history.filter(e => e.time >= monthStart).reduce((sum, e) => sum + (e.cost || 0), 0);
  return { todayCalls, monthCalls, todayCost, monthCost, totalCalls: s.totalCalls, totalCost: s.totalCost };
}

// === Spec Management Data ===
const DEFAULT_SPECS = [
  { id: 'AD-LB-01', name: '户外灯箱海报', icon: 'image', width: 1200, height: 1800, material: 'PET背喷灯箱片', crafts: ['高精度喷绘', '覆哑膜'], status: 'approved', category: '户外广告' },
  { id: 'AD-LB-02', name: '商场吊旗', icon: 'flag', width: 800, height: 2400, material: '双面丝光布', crafts: ['双面数码喷印', '锁边'], status: 'approved', category: '场馆指引' },
  { id: 'AD-LB-03', name: '易拉宝展架', icon: 'view_day', width: 800, height: 2000, material: 'PVC胶片覆亚膜', crafts: ['高精度写真', '覆哑膜'], status: 'reviewing', category: '场馆指引' },
  { id: 'AD-LB-04', name: '会议背景板', icon: 'dashboard', width: 4000, height: 2400, material: '经编布120g', crafts: ['UV宽幅喷绘', '打扣眼'], status: 'approved', category: '场馆指引' },
  { id: 'AD-LB-05', name: '宣传折页', icon: 'description', width: 210, height: 285, material: '157g铜版纸', crafts: ['四色印刷', '双面覆膜', '压痕折页'], status: 'draft', category: '基础物料' },
  { id: 'AD-LB-06', name: 'X展架画面', icon: 'photo_frame', width: 600, height: 1600, material: '户外防水PP纸', crafts: ['高精度写真', '覆亮膜'], status: 'approved', category: '场馆指引' },
];

export function loadAllSpecs() {
  return safeGet('specs', DEFAULT_SPECS);
}

export function saveSpec(data) {
  const all = loadAllSpecs();
  const idx = all.findIndex(s => s.id === data.id);
  if (idx >= 0) { all[idx] = { ...all[idx], ...data }; }
  else { all.push(data); }
  safeSet('specs', all);
}

export function deleteSpec(id) {
  const all = loadAllSpecs().filter(s => s.id !== id);
  safeSet('specs', all);
}

export function addSpec(data) {
  const all = loadAllSpecs();
  data.id = 'AD-LB-' + String(all.length + 1).padStart(2, '0');
  all.push(data);
  safeSet('specs', all);
  return data;
}

export function getSpecStats() {
  const all = loadAllSpecs();
  const approved = all.filter(s => s.status === 'approved').length;
  return {
    total: all.length,
    approved,
    templates: Math.floor(all.length * 0.25),
    exceptionRate: '0.4%',
  };
}

// === Session State ===
export function saveSession(state) { sessSet('workbench_session', state); }
export function loadSession() { return sessGet('workbench_session', null); }

// === Admin: cross-user data access ===
export function loadAllUsersHistory() {
  const users = listAllUsers();
  const allHistory = [];
  users.forEach(u => {
    const prefix = `smart_kv_u_${u.username}_`;
    // Scan localStorage for history keys for this user
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(prefix) && key.endsWith('history')) {
        try {
          const entries = JSON.parse(localStorage.getItem(key)) || [];
          entries.forEach(entry => {
            allHistory.push({ ...entry, _username: u.username, _displayName: u.displayName });
          });
        } catch {}
      }
    }
  });
  // Sort by date descending
  allHistory.sort((a, b) => (b.createdAt || '').localeCompare(a.createdAt || ''));
  return allHistory;
}

export function loadAllUsersMaterials() {
  const users = listAllUsers();
  const allMats = [];
  users.forEach(u => {
    const mat = safeGet('materials', [], u.username);
    const custom = safeGet('custom_materials', [], u.username);
    allMats.push({ username: u.username, displayName: u.displayName, materials: mat, custom: custom });
  });
  return allMats;
}
