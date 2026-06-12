// Cloudflare Worker — 安全代理 grsai API，隐藏 API Key
// 部署: npx wrangler deploy worker.js
// 免费额度: 100,000 请求/天

const API_KEY = 'sk-4eccd16364e542a19473d0891d85f1b3';

// 允许的前端域名（部署后改为你的 GitHub Pages 域名）
const ALLOWED_ORIGINS = [
  'http://localhost:5173',
  'http://localhost:4173',
  'https://你的用户名.github.io',
];

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const origin = request.headers.get('Origin') || '';

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    // Route to grsai endpoints
    let targetUrl;
    if (url.pathname.startsWith('/api/nano-draw')) {
      targetUrl = 'https://api.grsai.com/v1/draw/nano-banana';
    } else if (url.pathname.startsWith('/api/nano-result')) {
      targetUrl = 'https://api.grsai.com/v1/draw/result';
    } else if (url.pathname.startsWith('/api/gpt-draw')) {
      targetUrl = 'https://grsai.dakka.com.cn/v1/api/generate';
    } else if (url.pathname.startsWith('/api/vision')) {
      // Vision removed — using client-side Canvas extraction now
      return new Response(JSON.stringify({ error: 'Vision endpoint removed, use client-side extraction' }), {
        status: 410, headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' }
      });
    } else {
      return new Response(JSON.stringify({ error: 'Not found' }), {
        status: 404, headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' }
      });
    }

    // Forward request to grsai with API key
    try {
      const body = await request.text();
      const grsaiRes = await fetch(targetUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${API_KEY}`,
        },
        body: body,
      });

      const data = await grsaiRes.text();
      return new Response(data, {
        status: grsaiRes.status,
        headers: {
          ...CORS_HEADERS,
          'Content-Type': 'application/json',
        },
      });
    } catch (err) {
      return new Response(JSON.stringify({ error: err.message }), {
        status: 502,
        headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
      });
    }
  },
};
