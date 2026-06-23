import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[400px] flex items-center justify-center p-8">
          <div className="text-center max-w-md">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-error/10 flex items-center justify-center">
              <span className="material-symbols-outlined text-error text-3xl">error</span>
            </div>
            <h3 className="text-lg font-semibold text-on-surface mb-2">页面加载异常</h3>
            <p className="text-sm text-on-surface-variant mb-4">
              {this.state.error?.message || '发生了未知错误'}
            </p>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.reload();
              }}
              className="px-6 py-2 bg-primary text-on-primary rounded-lg font-semibold hover:shadow-lg active:scale-95 transition-all"
            >
              刷新页面
            </button>
            {this.props.onReset && (
              <button
                onClick={() => {
                  this.setState({ hasError: false, error: null });
                  this.props.onReset();
                }}
                className="ml-3 px-6 py-2 border border-outline-variant rounded-lg text-sm hover:bg-surface-container transition-all"
              >
                返回首页
              </button>
            )}
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// Friendly error messages for API errors
export function friendlyError(err) {
  const msg = err?.message || String(err);
  const map = {
    'Failed to fetch': '网络连接失败，请检查网络后重试',
    'NetworkError': '网络异常，请确认网络连接正常',
    'HTTP 401': 'API 密钥无效，请联系管理员',
    'HTTP 403': 'API 访问被拒绝，请检查权限',
    'HTTP 429': '请求过于频繁，请稍后再试',
    'HTTP 500': '服务器内部错误，请稍后重试',
    'HTTP 502': '服务器暂时不可用，请稍后重试',
    'timeout': '请求超时，请检查网络后重试',
    'abort': '请求已取消',
  };
  for (const [key, val] of Object.entries(map)) {
    if (msg.includes(key)) return val;
  }
  return msg.length > 100 ? msg.substring(0, 100) + '...' : msg;
}
