// Team collaboration + approval workflow
import { userPrefix, getCurrentUser, listAllUsers } from './auth';

function safeGet(key, fallback = null) {
  try { const v = localStorage.getItem('smart_kv_' + userPrefix() + key); return v ? JSON.parse(v) : fallback; } catch { return fallback; }
}
function safeSet(key, value) {
  try { localStorage.setItem('smart_kv_' + userPrefix() + key, JSON.stringify(value)); } catch {}
}

// Teams
export function loadTeams() {
  return safeGet('teams', []);
}

export function createTeam(name, members = []) {
  const teams = loadTeams();
  const team = { id: 'team_' + Date.now(), name, owner: getCurrentUser()?.username, members: [getCurrentUser()?.username, ...members], createdAt: new Date().toISOString() };
  teams.push(team);
  safeSet('teams', teams);
  return team;
}

// Approval workflow for generated items
export function loadApprovals() {
  return safeGet('approvals', []);
}

export function submitForApproval(generationId, projectName, imageUrl) {
  const approvals = loadApprovals();
  approvals.unshift({
    id: 'appr_' + Date.now(),
    generationId,
    projectName,
    imageUrl,
    submittedBy: getCurrentUser()?.displayName || getCurrentUser()?.username,
    status: 'pending',
    submittedAt: new Date().toISOString(),
  });
  safeSet('approvals', approvals);
  return approvals[0];
}

export function approveItem(id, reviewer) {
  const approvals = loadApprovals();
  const item = approvals.find(a => a.id === id);
  if (item) {
    item.status = 'approved';
    item.reviewedBy = reviewer;
    item.reviewedAt = new Date().toISOString();
  }
  safeSet('approvals', approvals);
  return item;
}

export function rejectItem(id, reviewer, reason = '') {
  const approvals = loadApprovals();
  const item = approvals.find(a => a.id === id);
  if (item) {
    item.status = 'rejected';
    item.reviewedBy = reviewer;
    item.reviewReason = reason;
    item.reviewedAt = new Date().toISOString();
  }
  safeSet('approvals', approvals);
  return item;
}

export function getPendingApprovals() {
  return loadApprovals().filter(a => a.status === 'pending');
}

// Activity log
export function logActivity(action, details = '') {
  const logs = safeGet('activity_log', []);
  logs.unshift({
    id: 'log_' + Date.now(),
    user: getCurrentUser()?.displayName || '系统',
    action,
    details,
    time: new Date().toISOString(),
  });
  if (logs.length > 200) logs.length = 200;
  safeSet('activity_log', logs);
}

export function loadActivityLog(limit = 50) {
  return safeGet('activity_log', []).slice(0, limit);
}
