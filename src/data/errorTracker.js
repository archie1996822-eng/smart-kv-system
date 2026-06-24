// Client-side error tracker — lightweight Sentry alternative
const MAX_LOGS = 100;

function safeGet() {
  try { const v = localStorage.getItem('smart_kv_error_logs'); return v ? JSON.parse(v) : []; } catch { return []; }
}
function safeSet(logs) {
  try { localStorage.setItem('smart_kv_error_logs', JSON.stringify(logs.slice(-MAX_LOGS))); } catch {}
}

export function trackError(error, context = {}) {
  const logs = safeGet();
  logs.push({
    message: error?.message || String(error),
    stack: error?.stack?.substring(0, 500) || '',
    context,
    time: new Date().toISOString(),
    url: typeof window !== 'undefined' ? window.location?.href : '',
  });
  safeSet(logs);
  console.error('[Miketv Error]', error, context);
}

export function getErrorLogs() {
  return safeGet().reverse();
}

export function clearErrorLogs() {
  try { localStorage.removeItem('smart_kv_error_logs'); } catch {}
}

// Global error handler
export function initErrorTracking() {
  if (typeof window === 'undefined') return;
  window.addEventListener('error', (e) => {
    trackError(e.error || new Error(e.message), { type: 'unhandled', filename: e.filename, lineno: e.lineno });
  });
  window.addEventListener('unhandledrejection', (e) => {
    trackError(e.reason || new Error('Unhandled Promise'), { type: 'promise' });
  });
}
