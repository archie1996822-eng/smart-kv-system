import { userPrefix } from './auth';

function safeGet(key, fallback = null) {
  try { const v = localStorage.getItem('smart_kv_' + userPrefix() + key); return v ? JSON.parse(v) : fallback; } catch { return fallback; }
}
function safeSet(key, value) {
  try { localStorage.setItem('smart_kv_' + userPrefix() + key, JSON.stringify(value)); } catch {}
}

export function loadComments(materialId) {
  const all = safeGet('comments', {});
  return all[materialId] || [];
}

export function addComment(materialId, text, user) {
  const all = safeGet('comments', {});
  if (!all[materialId]) all[materialId] = [];
  all[materialId].push({
    id: 'cmt_' + Date.now(),
    text,
    user: user?.displayName || user?.username || '匿名',
    avatar: user?.avatar || 'U',
    createdAt: new Date().toISOString(),
  });
  safeSet('comments', all);
  return all[materialId];
}

export function deleteComment(materialId, commentId) {
  const all = safeGet('comments', {});
  if (all[materialId]) {
    all[materialId] = all[materialId].filter(c => c.id !== commentId);
    safeSet('comments', all);
  }
}

export function getCommentCount(materialId) {
  return loadComments(materialId).length;
}
