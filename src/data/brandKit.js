import { userPrefix } from './auth';

function safeGet(key, fallback = null) {
  try { const v = localStorage.getItem('smart_kv_' + userPrefix() + key); return v ? JSON.parse(v) : fallback; } catch { return fallback; }
}
function safeSet(key, value) {
  try { localStorage.setItem('smart_kv_' + userPrefix() + key, JSON.stringify(value)); } catch {}
}

const DEFAULT_KIT = {
  name: '默认品牌',
  colors: ['#0066FF', '#FFFFFF', '#1A1A2E', '#E94560', '#0F3460'],
  fonts: ['汉仪旗黑', '思源黑体'],
  logoUrl: null,
  themes: ['品牌年度盛典', '新品发布会', '行业峰会'],
  createdAt: null,
  updatedAt: null,
};

export function loadBrandKit() {
  const saved = safeGet('brand_kit', null);
  return saved || { ...DEFAULT_KIT, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() };
}

export function saveBrandKit(data) {
  data.updatedAt = new Date().toISOString();
  if (!data.createdAt) data.createdAt = new Date().toISOString();
  safeSet('brand_kit', data);
}

export function importFromAnalysis(analysis) {
  const kit = loadBrandKit();
  if (analysis.colors?.length > 0) {
    kit.colors = [...new Set([...analysis.colors, ...kit.colors])].slice(0, 8);
  }
  if (analysis.fonts?.length > 0) {
    kit.fonts = [...new Set([...analysis.fonts, ...kit.fonts])].slice(0, 6);
  }
  if (analysis.themeHint && !kit.themes.includes(analysis.themeHint)) {
    kit.themes.unshift(analysis.themeHint);
    if (kit.themes.length > 10) kit.themes.length = 10;
  }
  saveBrandKit(kit);
  return kit;
}
