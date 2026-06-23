// Usage quota system
import { userPrefix } from './auth';

const QUOTA_KEY = 'quota';

const PLANS = {
  free: { name: '体验版', monthlyGenerations: 10, models: ['nano-banana-fast', 'gemini-2.5-flash'], videoGenerations: 3, storageMB: 50 },
  pro: { name: '专业版', monthlyGenerations: 200, models: ['nano-banana-2', 'nano-banana-pro', 'gemini-2.5-flash', 'gemini-2.5-pro'], videoGenerations: 30, storageMB: 500 },
  enterprise: { name: '企业版', monthlyGenerations: 999999, models: 'all', videoGenerations: 999999, storageMB: 5000 },
};

function safeGet(key, fallback) {
  try { const v = localStorage.getItem('smart_kv_' + userPrefix() + key); return v ? JSON.parse(v) : fallback; } catch { return fallback; }
}
function safeSet(key, value) {
  try { localStorage.setItem('smart_kv_' + userPrefix() + key, JSON.stringify(value)); } catch {}
}

export function getUserPlan() {
  try { return localStorage.getItem('smart_kv_user_plan') || 'free'; } catch { return 'free'; }
}

export function setUserPlan(plan) {
  localStorage.setItem('smart_kv_user_plan', plan);
}

export function getPlanLimits(planId) {
  return PLANS[planId] || PLANS.free;
}

export function loadQuota() {
  const now = Date.now();
  const thisMonth = new Date().getMonth();
  const saved = safeGet(QUOTA_KEY, { month: thisMonth, generations: 0, videoGenerations: 0, history: [] });
  if (saved.month !== thisMonth) {
    return { month: thisMonth, generations: 0, videoGenerations: 0, history: [] };
  }
  return saved;
}

function saveQuota(q) {
  safeSet(QUOTA_KEY, q);
}

export function canGenerate(type = 'image') {
  const plan = getPlanLimits(getUserPlan());
  const quota = loadQuota();
  if (type === 'video') return quota.videoGenerations < plan.videoGenerations;
  return quota.generations < plan.monthlyGenerations;
}

export function recordGeneration(type = 'image', count = 1) {
  const quota = loadQuota();
  if (type === 'video') quota.videoGenerations += count;
  else quota.generations += count;
  quota.history.unshift({ type, count, time: Date.now() });
  if (quota.history.length > 100) quota.history.length = 100;
  saveQuota(quota);
  return quota;
}

export function getQuotaInfo() {
  const plan = getPlanLimits(getUserPlan());
  const quota = loadQuota();
  return {
    plan: plan.name,
    imageUsed: quota.generations,
    imageLimit: plan.monthlyGenerations,
    imagePct: plan.monthlyGenerations > 999 ? 0 : Math.round((quota.generations / plan.monthlyGenerations) * 100),
    videoUsed: quota.videoGenerations,
    videoLimit: plan.videoGenerations,
    videoPct: plan.videoGenerations > 999 ? 0 : Math.round((quota.videoGenerations / plan.videoGenerations) * 100),
    isUnlimited: plan.monthlyGenerations > 999,
  };
}
