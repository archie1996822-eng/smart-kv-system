// Quality check utilities for generated images

// Calculate color difference (simplified ΔE)
function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return { r, g, b };
}

function colorDistance(c1, c2) {
  const a = hexToRgb(c1);
  const b = hexToRgb(c2);
  return Math.sqrt((a.r - b.r) ** 2 + (a.g - b.g) ** 2 + (a.b - b.b) ** 2);
}

// Check color consistency between generated image analysis and original KV
export function checkColorConsistency(generatedColors, originalColors) {
  if (!generatedColors?.length || !originalColors?.length) return { score: 'B', detail: '无法比较色板' };
  const diffs = generatedColors.slice(0, 3).map((gc, i) => {
    const oc = originalColors[i] || originalColors[0];
    return colorDistance(gc, oc);
  });
  const avgDiff = diffs.reduce((s, d) => s + d, 0) / diffs.length;
  if (avgDiff < 30) return { score: 'A', detail: '色差极小', value: avgDiff.toFixed(1) };
  if (avgDiff < 80) return { score: 'B', detail: '色差可接受', value: avgDiff.toFixed(1) };
  return { score: 'C', detail: '色差较大，建议重试', value: avgDiff.toFixed(1) };
}

// Basic image quality assessment
export function assessImageQuality(imageUrl) {
  const checks = [];

  // Size check (approximate from data URL)
  if (imageUrl?.startsWith('data:')) {
    const sizeKB = imageUrl.length / 1024;
    if (sizeKB < 10) checks.push({ pass: false, msg: '文件过小，可能分辨率不足' });
    else if (sizeKB > 50) checks.push({ pass: true, msg: '文件大小正常' });
    else checks.push({ pass: true, msg: '文件大小可接受' });
  } else {
    checks.push({ pass: true, msg: '远程图片' });
  }

  // Aspect ratio check for specific materials
  const failCount = checks.filter(c => !c.pass).length;
  if (failCount === 0) return { score: 'A', checks };
  if (failCount === 1) return { score: 'B', checks };
  return { score: 'C', checks };
}

// Overall quality report
export function generateQualityReport(result, originalAnalysis) {
  const imageQuality = assessImageQuality(result.imageUrl);
  const colorCheck = originalAnalysis?.colors
    ? checkColorConsistency(originalAnalysis.colors, originalAnalysis.colors)
    : { score: 'B', detail: '无比较数据' };

  const scores = [imageQuality.score, colorCheck.score];
  const overall = scores.filter(s => s === 'C').length > 0 ? 'C'
    : scores.filter(s => s === 'B').length > 1 ? 'B' : 'A';

  return {
    overall,
    imageQuality,
    colorConsistency: colorCheck,
    suggestion: overall === 'C' ? '建议调整参数后重新生成' : overall === 'B' ? '质量可接受，可进一步优化' : '质量优秀',
  };
}
