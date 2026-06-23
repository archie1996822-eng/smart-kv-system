import { userPrefix } from './auth';

function safeGet(key, fallback = null) {
  try { const v = localStorage.getItem('smart_kv_' + userPrefix() + key); return v ? JSON.parse(v) : fallback; } catch { return fallback; }
}
function safeSet(key, value) {
  try { localStorage.setItem('smart_kv_' + userPrefix() + key, JSON.stringify(value)); } catch {}
}

export function loadTemplates() {
  return safeGet('templates', []);
}

export function saveTemplate(template) {
  const all = loadTemplates();
  const existing = all.findIndex(t => t.id === template.id);
  if (existing >= 0) {
    all[existing] = { ...all[existing], ...template, updatedAt: new Date().toISOString() };
  } else {
    template.id = 'tpl_' + Date.now();
    template.createdAt = new Date().toISOString();
    template.updatedAt = new Date().toISOString();
    all.push(template);
  }
  if (all.length > 50) all.length = 50;
  safeSet('templates', all);
  return template;
}

export function deleteTemplate(id) {
  const all = loadTemplates().filter(t => t.id !== id);
  safeSet('templates', all);
}

export function createTemplateFromWorkbench({ name, theme, subtitle, visionModel, genModel, selected }) {
  return saveTemplate({
    name: name || theme || '未命名模板',
    theme,
    subtitle,
    visionModel,
    genModel,
    selected,
  });
}
