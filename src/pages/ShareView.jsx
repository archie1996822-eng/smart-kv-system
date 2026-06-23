import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

function Icon({ name, filled = false, className = '' }) {
  return (<span className={`material-symbols-outlined ${className}`} style={filled ? { fontVariationSettings: '"FILL" 1, "wght" 400, "GRAD" 0, "opsz" 24' } : {}}>{name}</span>);
}

export default function ShareView() {
  const { shareKey } = useParams();
  const [data, setData] = useState(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem('smart_kv_' + shareKey);
      if (raw) setData(JSON.parse(raw));
    } catch {}
  }, [shareKey]);

  if (!data) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center p-8">
          <Icon name="link_off" className="text-6xl text-outline-variant mb-4" />
          <h2 className="text-2xl font-bold text-on-surface mb-2">分享链接已失效</h2>
          <p className="text-on-surface-variant">该分享内容可能已被删除或过期。</p>
        </div>
      </div>
    );
  }

  const results = Object.entries(data.results || {}).filter(([, r]) => r.status === 'done');

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-6xl mx-auto p-4 md:p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-on-surface mb-2">{data.theme || '物料生成结果'}</h1>
          {data.subtitle && <p className="text-on-surface-variant">{data.subtitle}</p>}
          <p className="text-xs text-outline mt-2">生成于 {data.createdAt ? new Date(data.createdAt).toLocaleString('zh-CN') : '未知时间'}</p>
        </div>

        {/* Results grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {results.map(([id, r]) => (
            <div key={id} className="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden">
              <div className="aspect-[1.6] bg-surface-container-low">
                {r.imageUrl ? (
                  <img src={r.imageUrl} alt={r.title} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center canvas-grid">
                    <Icon name="image" className="text-4xl text-outline-variant" />
                  </div>
                )}
              </div>
              <div className="p-4">
                <h4 className="font-semibold text-on-surface">{r.title}</h4>
                {r.quality && (
                  <span className={`inline-block mt-1 px-2 py-0.5 rounded text-[10px] font-bold ${r.quality==='A'?'bg-green-100 text-green-700':'bg-blue-100 text-blue-700'}`}>
                    质量: {r.quality}
                  </span>
                )}
                <button
                  onClick={() => {
                    if (r.imageUrl) {
                      const a = document.createElement('a');
                      a.href = r.imageUrl;
                      a.download = `${r.title || 'image'}.png`;
                      document.body.appendChild(a);
                      a.click();
                      document.body.removeChild(a);
                    }
                  }}
                  className="w-full mt-3 py-2 bg-primary text-on-primary rounded-lg text-sm font-semibold hover:shadow flex items-center justify-center gap-2"
                >
                  <Icon name="download" className="text-[16px]" />下载原图
                </button>
              </div>
            </div>
          ))}
        </div>

        {results.length === 0 && (
          <div className="text-center py-16">
            <Icon name="image_not_supported" className="text-5xl text-outline-variant mb-3" />
            <p className="text-on-surface-variant">暂无生成结果</p>
          </div>
        )}
      </div>
    </div>
  );
}
