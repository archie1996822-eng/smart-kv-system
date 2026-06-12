import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout, { Icon } from '../components/Layout';
import { loadHistory, deleteHistoryEntry, saveWorkbenchState, loadAllUsersHistory } from '../data/store';
import { generateModels, peripheralChecklist } from '../data/stitchApi';
import { isAdmin, useUser } from '../data/auth';

function ImageViewer({ src, title, onClose }) {
  const [cropMode, setCropMode] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [startPos, setStartPos] = useState(null);
  const [currentPos, setCurrentPos] = useState(null);
  const [confirmedCrop, setConfirmedCrop] = useState(null);
  const containerRef = useRef(null);
  const imgRef = useRef(null);

  const getXY = (e) => {
    const r = containerRef.current.getBoundingClientRect();
    return { x: Math.min(Math.max(e.clientX - r.left, 0), r.width), y: Math.min(Math.max(e.clientY - r.top, 0), r.height) };
  };

  const onMDown = (e) => {
    if (!cropMode || e.button !== 0) return;
    e.preventDefault(); e.stopPropagation();
    setDragging(true);
    setStartPos(getXY(e));
    setCurrentPos(null);
    setConfirmedCrop(null);
  };

  const onMMove = (e) => {
    if (!dragging) return;
    e.preventDefault(); e.stopPropagation();
    setCurrentPos(getXY(e));
  };

  const onMUp = () => {
    if (!dragging) return;
    setDragging(false);
    if (startPos && currentPos) {
      const area = {
        x: Math.min(startPos.x, currentPos.x),
        y: Math.min(startPos.y, currentPos.y),
        w: Math.abs(currentPos.x - startPos.x),
        h: Math.abs(currentPos.y - startPos.y),
      };
      if (area.w > 15 && area.h > 15) {
        setConfirmedCrop(area);
      }
    }
  };

  const cropArea = dragging && currentPos ? {
    x: Math.min(startPos.x, currentPos.x),
    y: Math.min(startPos.y, currentPos.y),
    w: Math.abs(currentPos.x - startPos.x),
    h: Math.abs(currentPos.y - startPos.y),
  } : confirmedCrop;

  const hasValidCrop = cropArea && cropArea.w > 15 && cropArea.h > 15;

  const doDownload = async () => {
    if (!hasValidCrop) return;
    try {
      // Use proxy to fetch image without CORS issues
      const proxyUrl = `/api/img-proxy?url=${encodeURIComponent(src)}`;
      const res = await fetch(proxyUrl);
      if (!res.ok) throw new Error('Proxy failed');
      const blob = await res.blob();
      const bitmap = await createImageBitmap(blob);
      const dr = containerRef.current.getBoundingClientRect();
      const sx = bitmap.width / dr.width;
      const sy = bitmap.height / dr.height;
      const cw = Math.round(cropArea.w * sx);
      const ch = Math.round(cropArea.h * sy);
      const cx = Math.round(cropArea.x * sx);
      const cy = Math.round(cropArea.y * sy);
      const cv = document.createElement('canvas');
      cv.width = cw; cv.height = ch;
      cv.getContext('2d').drawImage(bitmap, cx, cy, cw, ch, 0, 0, cw, ch);
      cv.toBlob(b => {
        const u = URL.createObjectURL(b);
        const a = document.createElement('a'); a.href = u; a.download = 'cropped.png'; document.body.appendChild(a); a.click(); document.body.removeChild(a);
        URL.revokeObjectURL(u);
      }, 'image/png');
    } catch(err) {
      console.error('Crop failed:', err);
      window.open(src, '_blank');
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex flex-col items-center justify-center p-4" style={{ backgroundColor: 'rgba(0,0,0,0.85)' }}>
      {/* Backdrop close only when NOT cropping */}
      {!cropMode && <div className="absolute inset-0" onClick={onClose} />}

      {/* Toolbar */}
      <div className="flex items-center gap-3 mb-3" style={{ zIndex: 101 }}>
        <button
          onClick={() => { setCropMode(!cropMode); setDragging(false); setStartPos(null); setCurrentPos(null); setConfirmedCrop(null); }}
          className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${cropMode ? 'bg-primary text-white ring-2 ring-primary/50' : 'bg-white/20 text-white hover:bg-white/30'}`}
        >
          <Icon name="crop" className="text-[16px] mr-1" />
          {cropMode ? (dragging ? '拖拽中...' : hasValidCrop ? '可重新框选' : '拖拽框选图片区域') : '裁剪图片'}
        </button>

        {hasValidCrop && (
          <button onClick={doDownload} className="px-5 py-2 bg-green-500 text-white rounded-lg text-sm font-semibold hover:bg-green-600 transition-all shadow-lg animate-pulse">
            <Icon name="download" className="text-[16px] mr-1" />下载裁剪结果 ({Math.round(cropArea.w)}×{Math.round(cropArea.h)}px)
          </button>
        )}

        <button onClick={onClose} className="px-3 py-2 bg-white/20 text-white rounded-lg text-sm hover:bg-white/30 transition-all">
          <Icon name="close" className="text-[16px] mr-1" />关闭
        </button>
      </div>

      {/* Image container */}
      <div
        ref={containerRef}
        className="relative inline-block select-none"
        style={{ cursor: cropMode ? 'crosshair' : 'default', zIndex: 101 }}
        onMouseDown={onMDown}
        onMouseMove={onMMove}
        onMouseUp={onMUp}
        onMouseLeave={onMUp}
      >
        <img ref={imgRef} src={src} alt={title} className="max-w-[85vw] max-h-[72vh] rounded-xl shadow-2xl bg-white" draggable={false} style={cropMode ? { pointerEvents: 'none' } : {}} />

        {/* Crop overlay */}
        {cropMode && cropArea && cropArea.w > 0 && cropArea.h > 0 && (
          <div className="absolute pointer-events-none border-2 border-primary/80 shadow-[0_0_0_9999px_rgba(0,0,0,0.4)]" style={{ left: cropArea.x, top: cropArea.y, width: cropArea.w, height: cropArea.height || cropArea.h }}>
            <div className="absolute -top-[5px] -left-[5px] w-[10px] h-[10px] bg-white border-2 border-primary rounded-sm" />
            <div className="absolute -top-[5px] -right-[5px] w-[10px] h-[10px] bg-white border-2 border-primary rounded-sm" />
            <div className="absolute -bottom-[5px] -left-[5px] w-[10px] h-[10px] bg-white border-2 border-primary rounded-sm" />
            <div className="absolute -bottom-[5px] -right-[5px] w-[10px] h-[10px] bg-white border-2 border-primary rounded-sm" />
            <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-primary text-white text-[10px] px-2 py-0.5 rounded whitespace-nowrap font-jetbrains">
              {Math.round(cropArea.w)}×{Math.round(cropArea.h)}px
            </div>
          </div>
        )}

        {/* Dim overlay when in crop mode */}
        {cropMode && !cropArea && (
          <div className="absolute inset-0 bg-black/20 pointer-events-none rounded-xl flex items-center justify-center">
            <span className="text-white text-sm font-semibold bg-black/50 px-4 py-2 rounded-lg">在此拖拽框选裁剪区域</span>
          </div>
        )}
      </div>

      {title && <p className="text-white text-center mt-3 text-sm opacity-70" style={{ zIndex: 101 }}>{title}</p>}
    </div>
  );
}

function HistoryCard({ entry, index, onDelete, onRestore }) {
  const [expanded, setExpanded] = useState(false);
  const [viewerImg, setViewerImg] = useState(null);
  const modelName = generateModels.find(m => m.id === entry.genModel)?.name || entry.genModel;

  const doneItems = [];
  if (entry.results) {
    peripheralChecklist.forEach(item => {
      const r = entry.results[item.id];
      if (r && r.status === 'done') {
        doneItems.push({ id: item.id, name: item.name, size: item.size, imageUrl: r.imageUrl });
      }
    });
  }

  const handleDownload = (e, url, filename) => {
    e.stopPropagation();
    e.preventDefault();
    const proxyUrl = `/api/img-proxy?url=${encodeURIComponent(url)}`;
    fetch(proxyUrl).then(r => r.blob()).then(blob => {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(a.href);
    }).catch(() => window.open(url, '_blank'));
  };

  return (<>
    <div className="bg-surface border border-outline-variant rounded-xl overflow-hidden hover:shadow-lg transition-all">
      <div className="aspect-[2/1] bg-surface-container-low relative overflow-hidden">
        {entry.kvThumbnail ? (<img src={entry.kvThumbnail} alt="KV" className="w-full h-full object-cover" />)
        : (<div className="w-full h-full flex items-center justify-center canvas-grid"><Icon name="image" className="text-on-surface-variant text-4xl opacity-30" /></div>)}
        <div className="absolute top-2 left-2 flex gap-1">
          <span className="px-2 py-0.5 bg-surface/90 backdrop-blur rounded text-[10px] font-jetbrains text-on-surface">{entry.createdAt}</span>
          {entry._username && <span className="px-2 py-0.5 bg-primary/10 backdrop-blur rounded text-[10px] font-jetbrains text-primary">{entry._displayName || entry._username}</span>}
        </div>
      </div>
      <div className="p-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-hanken text-base font-semibold text-on-surface">{entry.theme || '未命名项目'}</h4>
          <span className="text-[10px] font-jetbrains text-on-surface-variant">{modelName}</span>
        </div>
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs text-on-surface-variant">共 {doneItems.length} 个物料</span>
          {entry.analysis?.colors && (<div className="flex gap-1">{entry.analysis.colors.slice(0, 3).map((c, i) => (<div key={i} className="w-3 h-3 rounded-full border border-outline-variant" style={{ backgroundColor: c }} title={c}></div>))}</div>)}
        </div>
        <div className="flex gap-2 mb-3">
          <button onClick={() => onRestore(entry)} className="flex-1 py-1.5 bg-primary text-on-primary text-xs font-semibold rounded-lg hover:bg-primary-container transition-all active:scale-95 flex items-center justify-center gap-1"><Icon name="restart_alt" className="text-[14px]" />恢复到工作台</button>
          <button onClick={() => setExpanded(!expanded)} className="px-2 py-1.5 border border-outline-variant text-on-surface-variant rounded-lg hover:bg-surface-container transition-all text-xs"><Icon name={expanded ? 'expand_less' : 'expand_more'} className="text-[16px]" /></button>
          <button onClick={() => onDelete(index)} className="px-2 py-1.5 border border-outline-variant text-error rounded-lg hover:bg-error-container/20 transition-all text-xs"><Icon name="delete" className="text-[16px]" /></button>
        </div>

        {doneItems.length > 0 && (
          <div className="grid grid-cols-4 gap-1.5">
            {doneItems.map((di) => (
              <div key={di.id} className="relative group">
                <div className="aspect-square rounded-lg border border-outline-variant overflow-hidden bg-surface-container-low cursor-pointer relative z-10" onClick={() => setViewerImg({ url: di.imageUrl, title: `${di.name} - ${di.size}` })}>
                  <img src={di.imageUrl} alt={di.name} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300" />
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
                    <Icon name="zoom_in" className="text-white text-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                  </div>
                </div>
                <div className="flex items-center justify-between mt-0.5 relative z-20">
                  <span className="text-[9px] text-on-surface-variant truncate max-w-[65%]" title={di.name}>{di.name}</span>
                  <button onClick={(e) => handleDownload(e, di.imageUrl, `${entry.theme||'kv'}_${di.name}.png`)} className="relative z-30 text-[10px] text-primary hover:underline font-semibold px-1 py-0.5 rounded hover:bg-primary/10" title="下载">下载</button>
                </div>
              </div>
            ))}
          </div>
        )}

        {expanded && (<div className="mt-3 pt-3 border-t border-outline-variant space-y-2">
          {entry.analysis?.colors && (<div className="flex gap-1 flex-wrap">{entry.analysis.colors.map((c, i) => (<span key={i} className="font-jetbrains text-[10px] px-1.5 py-0.5 bg-surface-container rounded">{c}</span>))}</div>)}
          {entry.analysis?.style && <p className="text-[11px] text-on-surface-variant">风格：{entry.analysis.style}</p>}
          {entry.analysis?.fonts && <p className="text-[11px] text-on-surface-variant">字体：{entry.analysis.fonts.join('、')}</p>}
          {entry.analysis?.layout && <p className="text-[11px] text-on-surface-variant">布局：{entry.analysis.layout}</p>}
          {entry.analysis?.elements && <p className="text-[11px] text-on-surface-variant">元素：{entry.analysis.elements}</p>}
        </div>)}
      </div>
    </div>
    {viewerImg && <ImageViewer src={viewerImg.url} title={viewerImg.title} onClose={() => setViewerImg(null)} />}
  </>);
}

export default function HistoryPage() {
  const user = useUser();
  const admin = isAdmin();
  const [history, setHistory] = useState(() => admin ? loadAllUsersHistory() : loadHistory());
  const [showAllUsers, setShowAllUsers] = useState(admin);
  const navigate = useNavigate();

  const handleDelete = (index) => {
    const entry = history[index];
    deleteHistoryEntry(index, entry._username || null);
    setHistory(showAllUsers ? loadAllUsersHistory() : loadHistory());
  };

  const handleRestore = (entry) => {
    saveWorkbenchState({
      kvImage: entry.kvImageDataUrl ? { dataUrl: entry.kvImageDataUrl, name: '已恢复的KV', size: 0 } : null,
      analysis: entry.analysis,
      theme: entry.theme || '',
      visionModel: entry.visionModel,
      genModel: entry.genModel,
      results: entry.results || {},
    });
    navigate('/workbench');
  };

  return (<Layout>
    <div className="p-8 max-w-[1600px] mx-auto">
      <div className="flex items-end justify-between mb-6">
        <div><h2 className="font-hanken text-[24px] leading-8 font-semibold text-on-surface">生成历史</h2>
          <p className="text-on-surface-variant mt-1 text-sm">点击缩略图放大+裁剪，点击下载保存</p>
          {admin && (<div className="flex gap-2 mt-2">{[
            {label:'只看自己',value:false},{label:'查看全部用户',value:true}
          ].map(opt=>(<button key={opt.label} onClick={()=>{setShowAllUsers(opt.value);setHistory(opt.value?loadAllUsersHistory():loadHistory())}} className={`px-3 py-1 rounded-full text-xs font-semibold transition-all ${showAllUsers===opt.value?'bg-primary text-white':'bg-surface-container text-on-surface-variant hover:bg-surface-container-high'}`}>{opt.label}</button>))}
          </div>)}
        </div>
      </div>
      {history.length === 0 ? (<div className="text-center py-20"><Icon name="history" className="text-outline-variant text-6xl mb-4" /><p className="text-on-surface-variant">暂无历史记录</p><p className="text-xs text-outline mt-1">在工作台完成一次生成后会自动保存</p></div>)
      : (<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">{history.map((entry, i) => (<HistoryCard key={i} entry={entry} index={i} onDelete={handleDelete} onRestore={handleRestore} />))}</div>)}
    </div>
  </Layout>);
}
