import { userPrefix } from './auth';

function safeGet(key, fallback = null) {
  try { const v = localStorage.getItem('smart_kv_' + userPrefix() + key); return v ? JSON.parse(v) : fallback; } catch { return fallback; }
}
function safeSet(key, value) {
  try { localStorage.setItem('smart_kv_' + userPrefix() + key, JSON.stringify(value)); } catch {}
}

export function loadFavorites() {
  return safeGet('favorites', []);
}

export function addFavorite(item) {
  const all = loadFavorites();
  if (!all.find(f => f.imageUrl === item.imageUrl)) {
    all.unshift({ ...item, favoritedAt: new Date().toISOString() });
    if (all.length > 100) all.length = 100;
    safeSet('favorites', all);
  }
  return all;
}

export function removeFavorite(imageUrl) {
  const all = loadFavorites().filter(f => f.imageUrl !== imageUrl);
  safeSet('favorites', all);
  return all;
}

export function isFavorited(imageUrl) {
  return loadFavorites().some(f => f.imageUrl === imageUrl);
}
