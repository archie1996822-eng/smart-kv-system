import { userPrefix } from './auth';

function safeGet(key, fallback = null) {
  try { const v = localStorage.getItem('smart_kv_' + userPrefix() + key); return v ? JSON.parse(v) : fallback; } catch { return fallback; }
}
function safeSet(key, value) {
  try { localStorage.setItem('smart_kv_' + userPrefix() + key, JSON.stringify(value)); } catch {}
}

export function loadProjects() {
  return safeGet('projects', []);
}

export function createProject(data) {
  const all = loadProjects();
  const project = {
    id: 'proj_' + Date.now(),
    name: data.name || '未命名项目',
    description: data.description || '',
    kvImageUrl: data.kvImageUrl || null,
    thumbnailUrl: data.thumbnailUrl || data.kvImageUrl || null,
    status: 'active',
    materialCount: data.materialCount || 0,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
  all.unshift(project);
  if (all.length > 100) all.length = 100;
  safeSet('projects', all);
  return project;
}

export function updateProject(id, data) {
  const all = loadProjects();
  const idx = all.findIndex(p => p.id === id);
  if (idx >= 0) {
    all[idx] = { ...all[idx], ...data, updatedAt: new Date().toISOString() };
    safeSet('projects', all);
  }
  return all[idx] || null;
}

export function deleteProject(id) {
  const all = loadProjects().filter(p => p.id !== id);
  safeSet('projects', all);
}

export function getProject(id) {
  return loadProjects().find(p => p.id === id) || null;
}

export function getProjectStats() {
  const projects = loadProjects();
  const active = projects.filter(p => p.status === 'active').length;
  const totalMaterials = projects.reduce((sum, p) => sum + (p.materialCount || 0), 0);
  return { total: projects.length, active, totalMaterials };
}
