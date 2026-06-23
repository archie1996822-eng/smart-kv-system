// AI-powered material recommendations based on KV analysis

// Style-to-material mapping: which materials work best for each style
const STYLE_MATERIAL_MAP = {
  '科技': ['flag', 'badge', 'stand', 'welcome-board', 'signboard', 'manual'],
  '简约': ['badge', 'host-card', 'paper-bag', 'manual', 'ticket', 'canvas-bag'],
  '现代': ['flag', 'stand', 'badge', 'welcome-board', 'hand-sign', 'canvas-bag'],
  '商务': ['badge', 'host-card', 'manual', 'paper-bag', 'ticket', 'stand'],
  '时尚': ['hand-sign', 'canvas-bag', 'badge', 'flag', 'badge-sticker', 'paper-bag'],
  '活泼': ['hand-sign', 'badge-sticker', 'ticket', 'canvas-bag', 'flag', 'signboard'],
  '奢华': ['host-card', 'paper-bag', 'badge', 'manual', 'ticket', 'stand'],
  '自然': ['canvas-bag', 'paper-bag', 'flag', 'manual', 'badge-sticker', 'hand-sign'],
  '工业': ['stand', 'flag', 'signboard', 'badge', 'welcome-board', 'manual'],
  '学术': ['manual', 'badge', 'host-card', 'signboard', 'stand', 'ticket'],
  '医疗': ['badge', 'manual', 'welcome-board', 'signboard', 'host-card', 'stand'],
  '教育': ['manual', 'badge', 'flag', 'hand-sign', 'stand', 'canvas-bag'],
  '餐饮': ['ticket', 'paper-bag', 'hand-sign', 'canvas-bag', 'badge-sticker', 'signboard'],
  '运动': ['flag', 'hand-sign', 'canvas-bag', 'ticket', 'badge-sticker', 'badge'],
  '音乐': ['hand-sign', 'flag', 'badge-sticker', 'canvas-bag', 'ticket', 'badge'],
};

// Color-to-material scoring
function colorMatchScore(kvColors, materialId) {
  if (!kvColors?.length) return 0;
  // Materials that work well with bright colors
  const brightMaterials = ['hand-sign', 'flag', 'badge-sticker', 'canvas-bag'];
  // Materials that work well with dark/subtle colors
  const subtleMaterials = ['badge', 'host-card', 'manual', 'paper-bag', 'ticket'];

  const avgBrightness = kvColors.reduce((sum, c) => {
    const r = parseInt(c.slice(1,3), 16);
    const g = parseInt(c.slice(3,5), 16);
    const b = parseInt(c.slice(5,7), 16);
    return sum + (r + g + b) / 3;
  }, 0) / kvColors.length;

  if (avgBrightness > 160 && brightMaterials.includes(materialId)) return 3;
  if (avgBrightness < 100 && subtleMaterials.includes(materialId)) return 3;
  return 1;
}

// Detect style keywords from analysis
function detectStyle(analysis) {
  const text = [
    analysis?.style || '',
    analysis?.layout || '',
    analysis?.elements || '',
    analysis?.titleDesign || '',
  ].join(' ').toLowerCase();

  const keywords = Object.keys(STYLE_MATERIAL_MAP);
  const scores = keywords.map(kw => ({
    style: kw,
    score: text.includes(kw) ? 3 : text.includes(kw.slice(0, 1)) ? 1 : 0,
  }));

  return scores.sort((a, b) => b.score - a.score);
}

// Main recommendation function
export function getRecommendedMaterials(analysis, allMaterials) {
  if (!analysis) return [];

  const styleScores = detectStyle(analysis);
  const topStyle = styleScores[0]?.style || '科技';

  // Base recommendations from style match
  const styleRecs = STYLE_MATERIAL_MAP[topStyle] || STYLE_MATERIAL_MAP['科技'];

  // Score all materials
  const scored = allMaterials.map(material => {
    let score = 0;

    // Style match bonus
    if (styleRecs.includes(material.id)) score += 5;

    // Color match
    score += colorMatchScore(analysis.colors, material.id);

    // Secondary style bonus
    if (styleScores[1] && STYLE_MATERIAL_MAP[styleScores[1].style]?.includes(material.id)) score += 2;

    return { id: material.id, score, reason: score >= 7 ? '强烈推荐' : score >= 4 ? '推荐' : '' };
  });

  return scored
    .filter(s => s.score >= 4)
    .sort((a, b) => b.score - a.score)
    .slice(0, 8);
}

// Generate recommendation summary text
export function getRecommendationSummary(analysis) {
  if (!analysis) return '';
  const styleScores = detectStyle(analysis);
  const top = styleScores[0];
  const colors = analysis.colors?.slice(0, 3).join('、') || '';

  return `AI 分析：风格偏向"${top?.style || '科技'}"，主色调 ${colors}。建议优先选择下方推荐的物料组合。`;
}
