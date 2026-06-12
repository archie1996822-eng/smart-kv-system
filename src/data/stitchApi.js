const GRSAI_KEY = import.meta.env.VITE_GRSAI_API_KEY || '';
const WORKER_URL = import.meta.env.VITE_WORKER_URL || '';

// Use Worker proxy in production (hides API key), direct in dev
const NANO_DRAW_URL = WORKER_URL ? `${WORKER_URL}/api/nano-draw` : 'https://api.grsai.com/v1/draw/nano-banana';
const NANO_RESULT_URL = WORKER_URL ? `${WORKER_URL}/api/nano-result` : 'https://api.grsai.com/v1/draw/result';
const GPT_GEN_URL = WORKER_URL ? `${WORKER_URL}/api/gpt-draw` : 'https://grsai.dakka.com.cn/v1/api/generate';

// === Models ===
export const visionModels = [
  { id: 'canvas', name: 'Canvas 智能提取', price: '免费', tier: 'fast', desc: '本地像素采样，精准色板提取' },
];

export const generateModels = [
  { id: 'nano-banana-2', name: 'Nano Banana 2', price: '¥0.065/张', tier: 'pro', desc: 'Gemini 3.1 Flash Image, 1-4K', provider: 'nano' },
  { id: 'nano-banana-pro', name: 'Nano Banana Pro', price: '¥0.09/张', tier: 'pro', desc: 'Gemini 3 Pro Image, 1-4K', provider: 'nano' },
  { id: 'gpt-image-2', name: 'GPT-Image 2', price: '¥0.08/张', tier: 'pro', desc: 'OpenAI 最新生图，照片级写实', provider: 'gpt' },
  { id: 'gpt-image-2-vip', name: 'GPT-Image 2 VIP', price: '¥0.12/张', tier: 'pro', desc: 'GPT-Image 2 4K超清版', provider: 'gpt' },
  { id: 'nano-banana', name: 'Nano Banana', price: '¥0.022/张', tier: 'basic', desc: 'Gemini 2.5 Flash Image, 1-2K', provider: 'nano' },
  { id: 'nano-banana-fast', name: 'Nano Banana Fast', price: '¥0.015/张', tier: 'fast', desc: '低成本快速生图', provider: 'nano' },
];

const GPT_RATIOS = { '1:1': '1024x1024', '16:9': '1672x941', '9:16': '941x1672', '4:3': '1443x1090', '3:4': '1090x1443', '3:2': '1536x1024', '2:3': '1024x1536' };

// === Client-side Color Extraction ===
export function extractColors(dataUrl) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const size = 50;
      canvas.width = size; canvas.height = size;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, size, size);
      const pixels = ctx.getImageData(0, 0, size, size).data;
      const colorMap = {};
      for (let i = 0; i < pixels.length; i += 4) {
        const r = pixels[i], g = pixels[i + 1], b = pixels[i + 2];
        const qr = Math.round(r / 32) * 32, qg = Math.round(g / 32) * 32, qb = Math.round(b / 32) * 32;
        const key = `${qr},${qg},${qb}`;
        colorMap[key] = (colorMap[key] || 0) + 1;
      }
      const sorted = Object.entries(colorMap).sort((a, b) => b[1] - a[1]).slice(0, 5);
      const colors = sorted.map(([key]) => {
        const [r, g, b] = key.split(',').map(Number);
        return { hex: `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`, r, g, b };
      });
      const avgBrightness = colors.reduce((s, c) => s + (c.r * 0.299 + c.g * 0.587 + c.b * 0.114), 0) / colors.length;
      const styleHint = avgBrightness < 100 ? '深色系高端商务风' : avgBrightness < 160 ? '中调现代简约风' : '明亮清新科技风';
      resolve({
        colors: colors.map(c => c.hex),
        fonts: ['汉仪旗黑', '思源黑体'],
        layout: '根据KV主视觉布局自适应',
        elements: '几何线条、渐变层次、品牌标识',
        style: styleHint,
        primaryColor: colors[0]?.hex || '#0066FF',
        isDark: avgBrightness < 128,
      });
    };
    img.src = dataUrl;
  });
}

// === Legacy analyzeImage (for backward compatibility) ===
export async function analyzeImage(imageBase64) {
  return extractColors(imageBase64);
}

// === Image Compression ===
export function compressImage(dataUrl, maxWidth = 768, quality = 0.7) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const c = document.createElement('canvas');
      let w = img.width, h = img.height;
      if (w > maxWidth) { h = (h * maxWidth) / w; w = maxWidth; }
      c.width = Math.round(w); c.height = Math.round(h);
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
      resolve({ dataUrl: c.toDataURL('image/jpeg', quality), width: c.width, height: c.height });
    };
    img.src = dataUrl;
  });
}

// === Prompt Builder ===
function buildNanoPrompt(analysis, item, theme, subtitle) {
  const colors = analysis.colors?.join('、') || '#0066FF、#FFFFFF';
  const primary = analysis.colors?.[0] || '#0066FF';
  const style = analysis.style || '现代简约科技风，干净几何构图，专业B2B品质';
  const elements = analysis.elements || '几何线条、数据流装饰、点阵背景';
  const fonts = analysis.fonts?.join('、') || '汉仪旗黑、思源黑体';
  const themeName = theme || '品牌活动';
  const sub = subtitle ? `\n副标题：${subtitle}` : '';
  return `主题：${themeName}。${sub}${item.name}设计，尺寸${item.size}，材质${item.material}。主色${primary}，配色${colors}。字体${fonts}。设计风格：${style}。视觉元素：${elements}。严格要求：所有文字必须是中文，画面中不能出现任何英文字母或英文单词。高清商业级品质，干净布光，锐利细节。延展设计必须与主KV品牌视觉保持一致。`;
}

function isGptModel(model) { return model && model.startsWith('gpt-'); }

async function apiPost(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${GRSAI_KEY}` },
    body: JSON.stringify(body),
  });
  if (!res.ok) { const t = await res.text(); throw new Error(`HTTP ${res.status}: ${t.substring(0, 200)}`); }
  return res.json();
}

export async function startNanoDraw({ model, analysis, item, theme, subtitle, appearanceUrls = [] }) {
  const prompt = buildNanoPrompt(analysis, item, theme, subtitle);
  let aspectRatio = '1:1';
  if (item.id === 'flag') aspectRatio = '9:16';
  else if (['stand', 'welcome-board'].includes(item.id)) aspectRatio = '3:4';
  else if (['badge', 'host-card'].includes(item.id)) aspectRatio = '2:3';

  if (isGptModel(model)) {
    const gptRatio = GPT_RATIOS[aspectRatio] || '1024x1024';
    const data = await apiPost(GPT_GEN_URL, { model, prompt, aspectRatio: gptRatio, images: appearanceUrls, replyType: 'json' });
    if (data.status === 'failed') throw new Error(data.error || 'GPT生成失败');
    if (data.status === 'succeeded' && data.results?.length > 0) {
      return { _direct: true, results: data.results };
    }
    throw new Error('GPT返回格式异常');
  }

  const data = await apiPost(NANO_DRAW_URL, { model, prompt, aspectRatio, urls: appearanceUrls, webHook: '-1' });
  if (data.code !== 0) throw new Error(data.msg || '提交失败');
  return data.data.id;
}

export async function pollNanoResult(taskId, maxAttempts = 30) {
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise(r => setTimeout(r, 3000));
    const data = await apiPost(NANO_RESULT_URL, { id: taskId });
    if (data.code !== 0) continue;
    if (data.data?.progress === 100 && data.data?.results?.length > 0) { return data.data.results; }
    if (data.data?.status === 'failed') { throw new Error(data.data.failure_reason || '生成失败'); }
  }
  throw new Error('生成超时，请重试');
}

// === Persistence ===
const STORAGE_KEY = 'smart_kv_results';
export function saveResults(results) {
  try {
    const toSave = {};
    for (const [id, r] of Object.entries(results)) {
      if (r.status === 'done') { toSave[id] = { status: 'done', savedAt: new Date().toISOString(), imageUrl: r.imageUrl || null, title: r.title || '' }; }
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
  } catch {}
}
export function loadResults() {
  try { const r = localStorage.getItem(STORAGE_KEY); return r ? JSON.parse(r) : {}; } catch { return {}; }
}

export const peripheralChecklist = [
  { id: 'hand-sign', name: '手举牌', icon: 'cut', size: '450 × 320 mm', material: '3mm PVC板, 异形模切', category: '互动周边' },
  { id: 'flag', name: '道旗标准件', icon: 'flag', size: '3000 × 1200 mm', material: '经编布120g, 双面数码喷印', category: '场馆指引' },
  { id: 'badge', name: '人员工作证', icon: 'id_card', size: '85 × 120 mm', material: 'PVC软胶, 丝印挂绳 2cm', category: '基础物料' },
  { id: 'canvas-bag', name: '帆布袋', icon: 'shopping_bag', size: '350 × 400 × 100 mm', material: '12安纯棉帆布, 丝网印刷 4色', category: '基础物料' },
  { id: 'stand', name: '指引展架', icon: 'view_day', size: '1200 × 2000 mm', material: 'KT板5mm, L型铁质展架', category: '场馆指引' },
  { id: 'paper-bag', name: '手提纸袋', icon: 'shopping_bag', size: '320 × 270 × 100 mm', material: '250g白卡纸, 蓝色三股绳', category: '基础物料' },
  { id: 'host-card', name: '主持人手卡', icon: 'description', size: '210 × 140 mm', material: '300g铜版纸, 双面覆哑膜', category: '基础物料' },
  { id: 'signboard', name: '倒计时牌', icon: 'calendar_clock', size: '400 × 300 mm', material: 'KT板覆亚膜', category: '场馆指引' },
  { id: 'badge-sticker', name: '椅背贴', icon: 'sticky_note_2', size: '300 × 150 mm', material: '车贴覆亚膜', category: '场馆指引' },
  { id: 'manual', name: '会务手册', icon: 'book', size: '210 × 285 mm', material: '封面300g铜版, 内页100g双胶', category: '基础物料' },
  { id: 'ticket', name: '餐券/门票', icon: 'confirmation_number', size: '90 × 50 mm', material: '157g铜版纸, 打码', category: '基础物料' },
  { id: 'welcome-board', name: '接机接站牌', icon: 'front_hand', size: '600 × 400 mm', material: 'KT板覆亚膜', category: '场馆指引' },
];
