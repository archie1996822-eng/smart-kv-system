// Video generation API layer
// Uses same GRSAI infrastructure as stitchApi.js

const GRSAI_KEY = import.meta.env.VITE_GRSAI_API_KEY || '';
const CHAT_URL = 'https://grsai.dakka.com.cn/v1/chat/completions';
const VIDEO_GEN_URL = 'https://grsai.dakka.com.cn/v1/video/generate';
const VIDEO_RESULT_URL = 'https://grsai.dakka.com.cn/v1/video/result';

export const videoModels = [
  { id: 'seedance-2.0', name: 'Seedance 2.0', price: '¥0.50/秒', tier: 'pro', desc: '高精度视频生成，支持复杂场景', duration: '5-15秒' },
  { id: 'veo-3.1', name: 'Veo 3.1', price: '¥0.35/秒', tier: 'pro', desc: '自然运动轨迹，适合人物场景', duration: '5-30秒' },
  { id: 'kling-v3', name: 'Kling V3', price: '¥0.25/秒', tier: 'basic', desc: '快速生成，适合短视频素材', duration: '3-10秒' },
  { id: 'sora-2', name: 'Sora 2', price: '¥0.80/秒', tier: 'pro', desc: '物理仿真，电影级画质', duration: '10-60秒' },
];

export const videoTemplates = [
  { id: 'product-showcase', name: '产品展示', icon: 'featured_video', desc: '产品360°展示+文字介绍', duration: '15秒' },
  { id: 'social-media', name: '社交媒体', icon: 'share', desc: '竖屏9:16，适合TikTok/Reels', duration: '10秒' },
  { id: 'ad-commercial', name: '广告片', icon: 'campaign', desc: '品牌广告，高品质输出', duration: '30秒' },
  { id: 'event-highlight', name: '活动集锦', icon: 'celebration', desc: '快节奏活动花絮', duration: '15秒' },
  { id: 'logo-animation', name: 'Logo动画', icon: 'animation', desc: '品牌Logo出场动画', duration: '5秒' },
  { id: 'text-reveal', name: '文字快闪', icon: 'text_fields', desc: '动态文字特效', duration: '8秒' },
];

export const aspectRatios = [
  { id: '16:9', label: '横屏 16:9', icon: 'videocam', w: 1920, h: 1080 },
  { id: '9:16', label: '竖屏 9:16', icon: 'smartphone', w: 1080, h: 1920 },
  { id: '1:1', label: '方形 1:1', icon: 'crop_square', w: 1080, h: 1080 },
  { id: '4:3', label: '标准 4:3', icon: 'crop_4_3', w: 1440, h: 1080 },
];

async function apiPost(url, body) {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${GRSAI_KEY}` },
    body: JSON.stringify(body),
  });
  if (!r.ok) { const t = await r.text(); throw new Error(t.substring(0, 200)); }
  return r.json();
}

// Generate AI video script from prompt
export async function generateScript(prompt, modelId = 'gemini-2.5-flash') {
  const systemPrompt = `你是专业视频导演。根据用户主题，输出视频脚本：
{
  "title": "视频标题",
  "duration": "预估时长(秒)",
  "scenes": [
    { "scene": 1, "duration": "3秒", "description": "场景描述", "visual": "画面内容", "text": "字幕文字", "transition": "转场效果" }
  ],
  "style": "整体风格",
  "bgm": "推荐背景音乐类型",
  "aspectRatio": "推荐比例"
}
只输出JSON，不要markdown。`;

  const res = await apiPost(CHAT_URL, {
    model: modelId,
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: prompt },
    ],
    max_tokens: 800,
    temperature: 0.7,
  });

  const t = res.choices?.[0]?.message?.content;
  if (!t) throw new Error('脚本生成失败');
  return JSON.parse(t.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim());
}

// Start video generation
export async function startVideoGen({ model, prompt, imageUrl, aspectRatio = '16:9', duration = 10, template }) {
  const ratio = aspectRatios.find(r => r.id === aspectRatio) || aspectRatios[0];
  const body = {
    model,
    prompt,
    image_url: imageUrl || undefined,
    width: ratio.w,
    height: ratio.h,
    duration,
    template,
  };

  const res = await apiPost(VIDEO_GEN_URL, body);
  if (res.code !== 0 && res.status === 'failed') throw new Error(res.error || '视频生成提交失败');
  return { id: res.data?.id || res.id, status: 'processing' };
}

// Poll for video result
export async function pollVideoResult(taskId, maxAttempts = 60) {
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise(r => setTimeout(r, 5000)); // 5 second intervals (video takes longer)
    const d = await apiPost(VIDEO_RESULT_URL, { id: taskId });
    if (d.code !== 0 && d.status === 'failed') throw new Error(d.error || '视频生成失败');
    if (d.data?.progress === 100 && d.data?.video_url) {
      return { videoUrl: d.data.video_url, thumbnailUrl: d.data.thumbnail_url, duration: d.data.duration };
    }
    if (d.data?.status === 'completed' && d.data?.results?.length > 0) {
      return { videoUrl: d.data.results[0].url, thumbnailUrl: d.data.results[0].thumbnail, duration: d.data.results[0].duration };
    }
  }
  throw new Error('视频生成超时（5分钟）');
}
