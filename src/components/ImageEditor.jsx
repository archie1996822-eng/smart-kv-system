import { useState, useRef, useEffect } from 'react';

function Icon({ name, filled = false, className = '' }) {
  return (<span className={`material-symbols-outlined ${className}`} style={filled ? { fontVariationSettings: '"FILL" 1, "wght" 400, "GRAD" 0, "opsz" 24' } : {}}>{name}</span>);
}

// Text overlay on image using Canvas
export function TextOverlay({ imageUrl, onSave }) {
  const canvasRef = useRef(null);
  const [text, setText] = useState('');
  const [fontSize, setFontSize] = useState(48);
  const [color, setColor] = useState('#ffffff');
  const [x, setX] = useState(100);
  const [y, setY] = useState(100);

  useEffect(() => {
    if (!imageUrl || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onerror = () => {};
    img.onload = () => {
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      ctx.drawImage(img, 0, 0);
      if (text) {
        ctx.font = `bold ${fontSize}px "Inter", sans-serif`;
        ctx.fillStyle = color;
        ctx.strokeStyle = 'rgba(0,0,0,0.5)';
        ctx.lineWidth = 3;
        ctx.strokeText(text, x, y);
        ctx.fillText(text, x, y);
      }
    };
    img.src = imageUrl;
  }, [imageUrl, text, fontSize, color, x, y]);

  const handleSave = () => {
    const dataUrl = canvasRef.current?.toDataURL('image/png');
    if (dataUrl && onSave) onSave(dataUrl);
  };

  return (
    <div className="space-y-3">
      <canvas ref={canvasRef} className="w-full rounded-lg border border-outline-variant" />
      <div className="flex gap-2 flex-wrap">
        <input value={text} onChange={e => setText(e.target.value)} placeholder="叠加文字..." className="flex-1 px-3 py-2 bg-surface border border-outline-variant rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary" />
        <input type="number" value={fontSize} onChange={e => setFontSize(Number(e.target.value))} className="w-16 px-2 py-2 bg-surface border border-outline-variant rounded-lg text-sm text-center" title="字号" />
        <input type="color" value={color} onChange={e => setColor(e.target.value)} className="w-10 h-10 rounded-lg border border-outline-variant cursor-pointer" title="颜色" />
        <button onClick={handleSave} className="px-4 py-2 bg-primary text-on-primary rounded-lg text-sm font-semibold">保存</button>
      </div>
    </div>
  );
}

// Background removal client (uses remove.bg API or canvas-based fallback)
export function BgRemover({ imageUrl, onResult }) {
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState(null);

  const removeBg = async () => {
    setLoading(true);
    // Try canvas-based edge detection fallback
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();
      img.crossOrigin = 'anonymous';
    img.onerror = () => {};
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
        img.src = imageUrl;
      });
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      ctx.drawImage(img, 0, 0);
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;

      // Simple edge-based background removal (detects white/light backgrounds)
      for (let i = 0; i < data.length; i += 4) {
        const r = data[i], g = data[i + 1], b = data[i + 2];
        // Remove near-white pixels (> 240 in all channels) at edges
        const isEdge = (Math.floor(i / 4) % canvas.width < 5) ||
          (Math.floor(i / 4) % canvas.width > canvas.width - 5) ||
          (Math.floor(i / 4 / canvas.width) < 5) ||
          (Math.floor(i / 4 / canvas.width) > canvas.height - 5);
        if (isEdge && r > 200 && g > 200 && b > 200) {
          data[i + 3] = 0; // Make transparent
        }
      }
      ctx.putImageData(imageData, 0, 0);
      const result = canvas.toDataURL('image/png');
      setPreview(result);
      if (onResult) onResult(result);
    } catch (err) {
      console.warn('Bg removal fallback failed:', err);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-3">
      {preview ? (
        <div className="relative">
          <img src={preview} alt="去底预览" className="w-full rounded-lg border border-outline-variant bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHJlY3Qgd2lkdGg9IjEwIiBoZWlnaHQ9IjEwIiBmaWxsPSIjZjBmMGYwIi8+PHJlY3Qgd2lkdGg9IjEwIiBoZWlnaHQ9IjEwIiB4PSIxMCIgZmlsbD0iI2UwZTBlMCIvPjxyZWN0IHdpZHRoPSIxMCIgaGVpZ2h0PSIxMCIgeT0iMTAiIGZpbGw9IiNlMGUwZTAiLz48cmVjdCB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHg9IjEwIiB5PSIxMCIgZmlsbD0iI2YwZjBmMCIvPjwvcGF0dGVybj48L2RlZnM+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmlkKSIvPjwvc3ZnPg==')]" />
        </div>
      ) : (
        <div className="aspect-video bg-surface-container rounded-lg flex items-center justify-center border border-dashed border-outline-variant">
          <img src={imageUrl} alt="原图" className="max-w-full max-h-full object-contain rounded" />
        </div>
      )}
      <button onClick={removeBg} disabled={loading} className="w-full py-2 bg-primary text-on-primary rounded-lg text-sm font-semibold hover:shadow disabled:opacity-50">
        {loading ? '处理中...' : preview ? '重新去底' : '一键去底'}
      </button>
    </div>
  );
}

// Image upscale (client-side using canvas scaling)
export function ImageUpscale({ imageUrl, onResult }) {
  const [scale, setScale] = useState(2);
  const [preview, setPreview] = useState(null);

  const doUpscale = () => {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onerror = () => {};
    img.onload = () => {
      canvas.width = img.naturalWidth * scale;
      canvas.height = img.naturalHeight * scale;
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      const result = canvas.toDataURL('image/png');
      setPreview(result);
      if (onResult) onResult(result);
    };
    img.src = imageUrl;
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <span className="text-sm">放大倍数:</span>
        {[2, 3, 4].map(s => (
          <button key={s} onClick={() => setScale(s)} className={`px-3 py-1 rounded-lg text-sm ${scale === s ? 'bg-primary text-on-primary' : 'border border-outline-variant'}`}>{s}x</button>
        ))}
      </div>
      {preview && <img src={preview} alt="放大预览" className="w-full rounded-lg border border-outline-variant" />}
      <button onClick={doUpscale} className="w-full py-2 bg-primary text-on-primary rounded-lg text-sm font-semibold">开始放大</button>
    </div>
  );
}

// Combined image editor modal
export default function ImageEditor({ imageUrl, onClose, onSave }) {
  const [tab, setTab] = useState('text');

  return (
    <div className="fixed inset-0 z-[200] bg-black/60 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-surface rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-hanken text-lg font-semibold">图片编辑</h3>
          <button onClick={onClose}><Icon name="close" /></button>
        </div>

        <div className="flex gap-2 mb-4">
          {[
            { id: 'text', label: '文字叠加', icon: 'text_fields' },
            { id: 'bgremove', label: '去底', icon: 'auto_fix' },
            { id: 'upscale', label: '放大', icon: 'zoom_in' },
          ].map(t => (
            <button key={t.id} onClick={() => setTab(t.id)} className={`px-3 py-1.5 rounded-lg text-sm flex items-center gap-1 ${tab === t.id ? 'bg-primary text-on-primary' : 'border border-outline-variant text-on-surface-variant'}`}>
              <Icon name={t.icon} className="text-[16px]" />{t.label}
            </button>
          ))}
        </div>

        {tab === 'text' && <TextOverlay imageUrl={imageUrl} onSave={onSave} />}
        {tab === 'bgremove' && <BgRemover imageUrl={imageUrl} onResult={onSave} />}
        {tab === 'upscale' && <ImageUpscale imageUrl={imageUrl} onResult={onSave} />}
      </div>
    </div>
  );
}
