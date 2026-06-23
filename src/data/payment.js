// Payment system adapter — ready for Stripe / WeChat Pay / Alipay integration

const PLANS = {
  free: { id: 'free', name: '体验版', price: 0, priceCNY: 0, interval: 'month', features: ['每月10次生成', '基础视觉分析', '标准物料模板', '3天历史记录'] },
  pro: { id: 'pro', name: '专业版', price: 99, priceCNY: 99, interval: 'month', features: ['每月200次生成', 'Gemini 2.5 Pro', '全部物料', '30天历史', '品牌管理', '模板保存'] },
  enterprise: { id: 'enterprise', name: '企业版', price: 399, priceCNY: 399, interval: 'month', features: ['无限生成', '全部AI模型', '团队协作', 'API接口', '专属客服', '定制物料'] },
};

export function getPlans() { return PLANS; }
export function getPlan(id) { return PLANS[id] || PLANS.free; }

// Payment session (mock — replace with real Stripe/WeChat Pay integration)
export function createPaymentSession(planId, userId) {
  const plan = getPlan(planId);
  return {
    sessionId: 'pay_' + Date.now(),
    plan: plan.name,
    amount: plan.priceCNY,
    currency: 'CNY',
    userId,
    status: 'pending',
    createdAt: new Date().toISOString(),
    checkoutUrl: null, // Set when real payment gateway is integrated
  };
}

// Subscription management
export function getSubscription(userId) {
  try {
    const v = localStorage.getItem('smart_kv_subscription_' + userId);
    return v ? JSON.parse(v) : { plan: 'free', validUntil: null, autoRenew: false };
  } catch { return { plan: 'free', validUntil: null, autoRenew: false }; }
}

export function setSubscription(userId, planId, validUntil) {
  const sub = { plan: planId, validUntil, autoRenew: true, updatedAt: new Date().toISOString() };
  localStorage.setItem('smart_kv_subscription_' + userId, JSON.stringify(sub));
  localStorage.setItem('smart_kv_user_plan', planId);
  return sub;
}

// Invoice generation (mock)
export function generateInvoice(payment) {
  return {
    invoiceId: 'INV-' + Date.now(),
    payment,
    number: 'MKT-' + new Date().getFullYear() + '-' + String(Math.floor(Math.random() * 10000)).padStart(4, '0'),
    issuedAt: new Date().toISOString(),
  };
}

// Payment methods configuration
export const PAYMENT_METHODS = [
  { id: 'wechat', name: '微信支付', icon: 'chat', enabled: false }, // Set to true when configured
  { id: 'alipay', name: '支付宝', icon: 'account_balance_wallet', enabled: false },
  { id: 'stripe', name: 'Stripe', icon: 'credit_card', enabled: false },
];
