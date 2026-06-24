// Basic core functionality tests
import { describe, it, expect, beforeEach } from 'vitest';

// Mock localStorage
const store = {};
beforeEach(() => {
  Object.keys(store).forEach(k => delete store[k]);
  global.localStorage = {
    getItem: (k) => store[k] || null,
    setItem: (k, v) => { store[k] = v; },
    removeItem: (k) => { delete store[k]; },
    key: (i) => Object.keys(store)[i] || null,
    get length() { return Object.keys(store).length; },
    clear: () => { Object.keys(store).forEach(k => delete store[k]); },
  };
});

describe('Auth System', () => {
  it('should login with correct credentials', async () => {
    const { login } = await import('../data/auth.js');
    const user = login('admin', '123456');
    expect(user).toBeTruthy();
    expect(user.username).toBe('admin');
    expect(user.role).toBe('admin');
  });

  it('should reject wrong password', async () => {
    const { login } = await import('../data/auth.js');
    const user = login('admin', 'wrong');
    expect(user).toBeNull();
  });

  it('should register new user', async () => {
    const { register } = await import('../data/auth.js');
    const result = register('testuser', 'test1234', 'Test User');
    expect(result.success).toBe(true);
  });

  it('should reject short username', async () => {
    const { register } = await import('../data/auth.js');
    const result = register('a', '1234', 'Bad');
    expect(result.error).toBeTruthy();
  });
});

describe('Quota System', () => {
  it('should enforce free plan limits', async () => {
    localStorage.setItem('smart_kv_user_plan', 'free');
    const { canGenerate } = await import('../data/quota.js');
    // Reset quota
    const prefix = 'smart_kv_u_anon_';
    localStorage.removeItem(prefix + 'quota');
    expect(canGenerate('image')).toBe(true);
  });
});

describe('Recommendations', () => {
  it('should recommend materials based on analysis', async () => {
    const { getRecommendedMaterials } = await import('../data/recommendations.js');
    const analysis = { style: '科技', layout: '现代', elements: '几何', colors: ['#0066FF', '#FFFFFF'] };
    const materials = [
      { id: 'flag', name: '道旗' }, { id: 'badge', name: '工作证' },
      { id: 'stand', name: '展架' }, { id: 'hand-sign', name: '手举牌' },
    ];
    const recs = getRecommendedMaterials(analysis, materials);
    expect(recs.length).toBeGreaterThan(0);
    expect(recs[0].score).toBeGreaterThan(0);
  });
});

describe('Quota Limits', () => {
  it('should block over-limit generation', async () => {
    const { getQuotaInfo, recordGeneration, canGenerate } = await import('../data/quota.js');
    // Simulate maxed out quota
    const prefix = 'smart_kv_u_anon_';
    localStorage.setItem('smart_kv_user_plan', 'free');
    localStorage.setItem(prefix + 'quota', JSON.stringify({ month: new Date().getMonth(), generations: 10, videoGenerations: 0, history: [] }));
    expect(canGenerate('image')).toBe(false);
    const info = getQuotaInfo();
    expect(info.imageUsed).toBe(10);
    expect(info.imageLimit).toBe(10);
  });
});
