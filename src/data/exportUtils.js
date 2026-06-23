// Multi-format export utilities

export const EXPORT_FORMATS = [
  { id: 'png', label: 'PNG 原图', ext: 'png', mime: 'image/png', desc: '无损格式，推荐' },
  { id: 'jpeg', label: 'JPEG 高清', ext: 'jpg', mime: 'image/jpeg', desc: '高质量压缩', quality: 0.92 },
  { id: 'jpeg-web', label: 'JPEG 网页', ext: 'jpg', mime: 'image/jpeg', desc: '适合网页使用', quality: 0.75 },
  { id: 'webp', label: 'WebP 格式', ext: 'webp', mime: 'image/webp', desc: '新一代格式', quality: 0.85 },
];

// Convert image to specified format
export function convertImage(imageUrl, format, quality = 0.9) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0);
      const mime = format.mime || 'image/png';
      canvas.toBlob((blob) => {
        if (blob) {
          resolve({ blob, url: URL.createObjectURL(blob), width: canvas.width, height: canvas.height });
        } else {
          reject(new Error('格式转换失败'));
        }
      }, mime, format.quality || quality);
    };
    img.onerror = () => reject(new Error('图片加载失败'));
    img.src = imageUrl;
  });
}

// Download single image
export function downloadImage(imageUrl, filename, format = EXPORT_FORMATS[0]) {
  return convertImage(imageUrl, format).then(({ blob, url }) => {
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.${format.ext}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
}

// Batch download as individual files
export async function batchDownload(results, format = EXPORT_FORMATS[0]) {
  const items = Object.entries(results).filter(([, r]) => r.status === 'done' && r.imageUrl);
  for (const [id, r] of items) {
    try {
      await downloadImage(r.imageUrl, `${r.title || id}`, format);
      await new Promise(resolve => setTimeout(resolve, 500)); // Prevent browser blocking
    } catch (err) {
      console.warn('Download failed for', id, err);
    }
  }
}

// Generate spec sheet text for a material
export function generateSpecSheet(item, result) {
  return [
    `物料名称: ${item.name || '未命名'}`,
    `尺寸: ${item.size || 'N/A'}`,
    `材质: ${item.material || 'N/A'}`,
    `色彩模式: CMYK (建议)`,
    `分辨率: 300 dpi`,
    `出血: 3mm 四周`,
    `文件格式: PDF/AI/EPS`,
    `生成时间: ${new Date().toLocaleString('zh-CN')}`,
    `质量评分: ${result?.quality || '未评估'}`,
  ].join('\n');
}
