const GRSAI_KEY = import.meta.env.VITE_GRSAI_API_KEY || '';
const CHAT_URL = 'https://grsai.dakka.com.cn/v1/chat/completions';
const NANO_DRAW_URL = 'https://api.grsai.com/v1/draw/nano-banana';
const NANO_RESULT_URL = 'https://api.grsai.com/v1/draw/result';
const GPT_GEN_URL = 'https://grsai.dakka.com.cn/v1/api/generate';

export const visionModels = [
  { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', price: '¥0.01/次', tier: 'fast', desc: '快速视觉分析，秒级响应' },
  { id: 'gemini-2.5-pro', name: 'Gemini 2.5 Pro', price: '¥0.03/次', tier: 'pro', desc: '最强分析，精准色板/字体/元素' },
];

export const generateModels = [
  { id: 'nano-banana-2', name: 'Nano Banana 2', price: '¥0.065/张', tier: 'pro', desc: 'Gemini 3.1 Flash Image, 1-4K', provider: 'nano' },
  { id: 'nano-banana-pro', name: 'Nano Banana Pro', price: '¥0.09/张', tier: 'pro', desc: 'Gemini 3 Pro Image, 1-4K', provider: 'nano' },
  { id: 'gpt-image-2', name: 'GPT-Image 2', price: '¥0.08/张', tier: 'pro', desc: 'OpenAI 生图，照片级写实', provider: 'gpt' },
  { id: 'gpt-image-2-vip', name: 'GPT-Image 2 VIP', price: '¥0.12/张', tier: 'pro', desc: 'GPT-Image 2 4K超清版', provider: 'gpt' },
  { id: 'nano-banana', name: 'Nano Banana', price: '¥0.022/张', tier: 'basic', desc: 'Gemini 2.5 Flash Image, 1-2K', provider: 'nano' },
  { id: 'nano-banana-fast', name: 'Nano Banana Fast', price: '¥0.015/张', tier: 'fast', desc: '低成本快速生图', provider: 'nano' },
];

const GPT_RATIOS = { '1:1': '1024x1024', '16:9': '1672x941', '9:16': '941x1672', '4:3': '1443x1090', '3:4': '1090x1443', '3:2': '1536x1024', '2:3': '1024x1536' };

// === Canvas 抠图工具 ===
export function cropElementFromImage(originalDataUrl, x, y, w, h) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const c = document.createElement('canvas');
      const iw = img.naturalWidth, ih = img.naturalHeight;
      c.width = Math.round(iw * w); c.height = Math.round(ih * h);
      const ctx = c.getContext('2d');
      ctx.drawImage(img, Math.round(iw * x), Math.round(ih * y), Math.round(iw * w), Math.round(ih * h), 0, 0, c.width, c.height);
      resolve(c.toDataURL('image/png'));
    };
    img.src = originalDataUrl;
  });
}

export async function cropAllElements(originalDataUrl, elements) {
  const results = [];
  for (const el of elements) {
    if (el.x !== undefined && el.w > 0.02 && el.h > 0.02) {
      try {
        const imgUrl = await cropElementFromImage(originalDataUrl, el.x, el.y, el.w, el.h);
        results.push({ name: el.name, imageUrl: imgUrl, x: el.x, y: el.y, w: el.w, h: el.h });
      } catch { results.push({ name: el.name, imageUrl: null }); }
    } else {
      results.push({ name: el.name, imageUrl: null });
    }
  }
  return results;
}

// === 本地提取（Gemini 失败时备用） ===
function extractColorsLocal(dataUrl) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const c = document.createElement('canvas'); c.width = c.height = 40;
      const ctx = c.getContext('2d'); ctx.drawImage(img, 0, 0, 40, 40);
      const p = ctx.getImageData(0, 0, 40, 40).data; const m = {};
      for (let i = 0; i < p.length; i += 4) {
        const k = `${Math.round(p[i]/32)*32},${Math.round(p[i+1]/32)*32},${Math.round(p[i+2]/32)*32}`;
        m[k] = (m[k] || 0) + 1;
      }
      const s = Object.entries(m).sort((a, b) => b[1] - a[1]).slice(0, 6);
      const cols = s.map(([k]) => {
        const [r, g, b] = k.split(',').map(Number);
        return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
      });
      const avg = cols.reduce((x, c) => x + parseInt(c.slice(1), 16), 0) / cols.length;
      resolve({
        colors: cols, fonts: ['汉仪旗黑', '思源黑体'], layout: '根据主视觉自适应', elements: '由本地算法提取',
        concreteObjects: [], style: avg < 0x888888 ? '深色系' : avg < 0xBBBBBB ? '中调' : '明亮系',
        themeHint: '', titleDesign: '', elementsWithPositions: []
      });
    };
    img.src = dataUrl;
  });
}

// === Gemini AI 分析 ===
export async function analyzeImage(imageBase64, modelId = 'gemini-2.5-flash', originalDataUrl = null) {
  const prompt = `你是资深品牌设计师。仔细分析这张KV主视觉图，完成以下任务：
1. 提取主色板（5个hex值）
2. 识别标题字体风格
3. 识别画面中所有可见的独立元素（Logo、人物、产品、建筑、图标、装饰图形、纹理等），每个元素给出名称和位置（用0-1之间的小数表示，x=左边缘位置，y=上边缘位置，w=宽度占比，h=高度占比，例如Logo在右下角则为：x:0.7,y:0.8,w:0.25,h:0.15）
4. 描述整体风格和布局
5. 精确读出图中最大的标题文字内容

只输出纯JSON，不要markdown格式：
{"colors":["#hex1","#hex2","#hex3","#hex4","#hex5"],"fonts":["字体1","字体2"],"layout":"布局描述","elements":"视觉元素概述","elementsWithPositions":[{"name":"元素名","x":0.1,"y":0.2,"w":0.3,"h":0.4},{"name":"元素名2",...}],"style":"品牌风格描述","themeHint":"图中主标题文字内容","titleDesign":"主标题的字体设计：字体名、粗细、颜色、特效"}`;

  for (let a = 0; a < 3; a++) {
    try {
      const res = await fetch(CHAT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${GRSAI_KEY}` },
        body: JSON.stringify({
          model: modelId,
          messages: [{ role: 'user', content: [{ type: 'image_url', image_url: { url: imageBase64, detail: 'low' } }, { type: 'text', text: prompt }] }],
          max_tokens: 500,
          temperature: 0.3,
        }),
      });
      if (!res.ok) throw new Error(`响应异常 ${res.status}`);
      const d = await res.json();
      const t = d.choices?.[0]?.message?.content;
      if (!t) throw new Error('返回为空');
      const parsed = JSON.parse(t.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim());

      // 如果提供了原图，裁剪元素
      if (originalDataUrl && parsed.elementsWithPositions?.length > 0) {
        const cropped = await cropAllElements(originalDataUrl, parsed.elementsWithPositions);
        parsed.croppedElements = cropped;
      }
      return parsed;
    } catch (e) {
      if (a < 2) await new Promise(r => setTimeout(r, 2000));
    }
  }
  // 失败回退到本地
  return extractColorsLocal(imageBase64);
}

// === 图片压缩 ===
export function compressImage(dataUrl, maxWidth = 512, quality = 0.5) {
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

// === 生成提示词 ===
function buildPrompt(a, item, theme, subtitle) {
  const cs = a.colors?.join('、') || '#0066FF、#FFFFFF';
  const p = a.colors?.[0] || '#0066FF';
  const s = a.style || '现代简约科技风';
  const el = a.elements || '几何线条、数据流装饰';
  const f = a.fonts?.join('、') || '汉仪旗黑、思源黑体';
  const objs = a.concreteObjects?.join('、') || (a.elementsWithPositions?.map(e => e.name).join('、') || '');
  const td = a.titleDesign || '';
  const tn = theme || '品牌活动';
  const sub = subtitle ? `副标题：${subtitle}` : '';
  const titleHint = td ? `主标题设计规范（必须严格遵循）：${td}。` : '';
  const objHint = objs ? `画面中必须包含以下KV元素：${objs}。将这些元素自然地融入${item.name}设计中。` : '';
  return `设计主题：${tn}。${sub}生成${item.name}，尺寸${item.size}，材质${item.material}。品牌主色${p}，配色${cs}。使用字体${f}。设计风格：${s}。视觉元素：${el}。${titleHint}${objHint}必须使用中文，禁止英文。高清品质。`;
}

// === API 调用 ===
function isGpt(m) { return m?.startsWith('gpt-'); }

async function apiPost(url, body) {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${GRSAI_KEY}` },
    body: JSON.stringify(body),
  });
  if (!r.ok) { const t = await r.text(); throw new Error(t.substring(0, 200)); }
  return r.json();
}

export async function startNanoDraw({ model, analysis, item, theme, subtitle, appearanceUrls = [] }) {
  const prompt = buildPrompt(analysis, item, theme, subtitle);
  const promptText = prompt;
  let ratio = '1:1';
  if (item.id === 'flag') ratio = '9:16';
  else if (['stand', 'welcome-board'].includes(item.id)) ratio = '3:4';
  else if (['badge', 'host-card'].includes(item.id)) ratio = '2:3';

  if (isGpt(model)) {
    const d = await apiPost(GPT_GEN_URL, { model, prompt, aspectRatio: GPT_RATIOS[ratio] || '1024x1024', images: appearanceUrls, replyType: 'json' });
    if (d.status === 'failed') throw new Error(d.error || 'GPT生成失败');
    if (d.status === 'succeeded' && d.results?.length > 0) return { _direct: true, results: d.results, promptText };
    throw new Error('GPT返回异常');
  }
  const d = await apiPost(NANO_DRAW_URL, { model, prompt, aspectRatio: ratio, urls: appearanceUrls, webHook: '-1' });
  if (d.code !== 0) throw new Error(d.msg || '提交失败');
  return { id: d.data.id, promptText };
}

export async function pollNanoResult(taskId, maxAttempts = 30) {
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise(r => setTimeout(r, 3000));
    const d = await apiPost(NANO_RESULT_URL, { id: taskId });
    if (d.code !== 0) continue;
    if (d.data?.progress === 100 && d.data?.results?.length > 0) return d.data.results;
    if (d.data?.status === 'failed') throw new Error(d.data.failure_reason || '生成失败');
  }
  throw new Error('生成超时');
}

const SK = 'smart_kv_results';
export function saveResults(rr) { try { const s = {}; for (const [id, r] of Object.entries(rr)) { if (r.status === 'done') s[id] = { status: 'done', savedAt: new Date().toISOString(), imageUrl: r.imageUrl || null }; } localStorage.setItem(SK, JSON.stringify(s)); } catch {} }
export function loadResults() { try { const r = localStorage.getItem(SK); return r ? JSON.parse(r) : {}; } catch { return {}; } }

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
