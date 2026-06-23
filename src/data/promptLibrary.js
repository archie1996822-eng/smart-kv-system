import { userPrefix } from './auth';

function safeGet(key, fallback = null) {
  try { const v = localStorage.getItem('smart_kv_' + userPrefix() + key); return v ? JSON.parse(v) : fallback; } catch { return fallback; }
}
function safeSet(key, value) {
  try { localStorage.setItem('smart_kv_' + userPrefix() + key, JSON.stringify(value)); } catch {}
}

const MAX_PROMPTS = 200;

export function loadPrompts() {
  return safeGet('prompts', []);
}

export function savePrompt(text, meta = {}) {
  const all = loadPrompts();
  // Deduplicate by text
  const existing = all.find(p => p.text === text);
  if (existing) {
    existing.usedAt = new Date().toISOString();
    existing.useCount = (existing.useCount || 1) + 1;
    existing.meta = { ...existing.meta, ...meta };
  } else {
    all.unshift({
      id: 'pr_' + Date.now(),
      text,
      meta,
      createdAt: new Date().toISOString(),
      usedAt: new Date().toISOString(),
      useCount: 1,
    });
  }
  if (all.length > MAX_PROMPTS) all.length = MAX_PROMPTS;
  safeSet('prompts', all);
  return all;
}

export function deletePrompt(id) {
  const all = loadPrompts().filter(p => p.id !== id);
  safeSet('prompts', all);
}

export function searchPrompts(query) {
  const q = query.toLowerCase();
  return loadPrompts().filter(p =>
    p.text.toLowerCase().includes(q) ||
    (p.meta?.theme && p.meta.theme.toLowerCase().includes(q)) ||
    (p.meta?.model && p.meta.model.toLowerCase().includes(q))
  );
}

export function getTopPrompts(limit = 10) {
  return loadPrompts()
    .sort((a, b) => (b.useCount || 1) - (a.useCount || 1))
    .slice(0, limit);
}
