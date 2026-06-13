import { useState, useRef, useCallback, useEffect } from 'react';
import Layout, { Icon, showToast, pushNotification } from '../components/Layout';
import { peripheralChecklist, compressImage, analyzeImage, startNanoDraw, pollNanoResult, visionModels, generateModels } from '../data/stitchApi';
import { loadMaterials, loadCustomMaterials, saveHistoryEntry, saveWorkbenchState, loadWorkbenchState, clearWorkbenchState, saveSession, loadSession } from '../data/store';

function KVUpload({ image, onImageSet, processing }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);
  const handleFile = useCallback((file) => {
    if (!file || !file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = (e) => onImageSet({ dataUrl: e.target.result, name: file.name, size: file.size });
    reader.readAsDataURL(file);
  }, [onImageSet]);
  return (<section onDragOver={(e)=>{e.preventDefault();setDragging(true)}} onDragLeave={(e)=>{e.preventDefault();setDragging(false)}} onDrop={(e)=>{e.preventDefault();setDragging(false);handleFile(e.dataTransfer.files[0])}} onClick={()=>!image&&inputRef.current?.click()} className={`col-span-12 border-2 rounded-xl p-8 flex flex-col items-center justify-center min-h-[260px] transition-all ${dragging?'border-primary bg-surface-container-high':image?'border-primary border-solid bg-surface-container-low':'border-dashed border-outline-variant hover:border-primary hover:bg-surface-container-low cursor-pointer'}`}>
    {image ? (<div className="text-center w-full"><div className="relative group mx-auto max-w-md"><img src={image.dataUrl} alt="KV" className="max-h-[150px] rounded-xl shadow-lg mx-auto object-contain" /><button onClick={(e)=>{e.stopPropagation();onImageSet(null)}} className="absolute top-2 right-2 bg-white/90 hover:bg-white p-1.5 rounded-full shadow opacity-0 group-hover:opacity-100 transition-opacity"><Icon name="close" className="text-sm text-error" /></button></div><p className="text-on-surface font-semibold mt-2">{image.name}</p><p className="text-xs text-on-surface-variant">{(image.size/1024).toFixed(1)}KB{processing?' · 分析中...':' · 点击替换'}</p></div>) : (<><div className="w-14 h-14 rounded-full bg-primary-fixed flex items-center justify-center mb-6"><Icon name="cloud_upload" className="text-primary text-[32px]" filled /></div><h3 className="font-hanken text-[20px] leading-7 font-semibold mb-2 text-on-surface">拖放 / 点击上传主 KV 视觉设计图</h3><p className="text-on-surface-variant mb-4 text-center max-w-sm">视觉模型分析 → 选择生图模型 → 批量生成</p><div className="px-6 py-2.5 bg-primary text-on-primary rounded-lg font-semibold hover:shadow-lg transition-all">选择本地文件</div></>)}
    <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={(e)=>{if(e.target.files[0]){handleFile(e.target.files[0]);e.target.value=''}}} />
  </section>);
}

function ModelSelector({ label, icon, models, selected, onSelect }) {
  return (<div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-5">
    <h3 className="font-hanken text-base font-semibold flex items-center gap-2 mb-3"><Icon name={icon} className="text-primary text-[20px]" />{label}</h3>
    <div className="grid grid-cols-2 gap-2">{models.map((m)=>(<button key={m.id} onClick={()=>onSelect(m.id)} className={`text-left px-3 py-2.5 rounded-lg border transition-all ${selected===m.id?'border-primary bg-primary-fixed/20 shadow-sm':'border-outline-variant hover:border-primary/50'}`}><div className="flex items-center justify-between"><span className="font-semibold text-sm text-on-surface">{m.name}</span><span className={`font-jetbrains text-[11px] px-1.5 py-0.5 rounded-full ${m.tier==='pro'?'bg-primary-container/20 text-primary':m.tier==='fast'?'bg-green-100 text-green-700':'bg-surface-container text-on-surface-variant'}`}>{m.price}</span></div><p className="text-[10px] text-on-surface-variant mt-1 leading-tight">{m.desc}</p></button>))}</div>
  </div>);
}

function AnalysisCard({ analysis, kvImage }) {
  if (!analysis) return null;
  if (analysis.rawAnalysis) return (<section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-5 col-span-12"><h3 className="font-hanken text-base font-semibold flex items-center gap-2 mb-2"><Icon name="psychology" className="text-secondary" />分析结果</h3><p className="text-sm text-on-surface-variant whitespace-pre-wrap">{analysis.rawAnalysis.substring(0, 500)}</p></section>);

  const cs = analysis.colors || [];
  const objs = analysis.concreteObjects || [];
  const cropped = analysis.croppedElements || [];
  const positioned = analysis.elementsWithPositions || [];
  return (<section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-5 col-span-12">
    <h3 className="font-hanken text-base font-semibold flex items-center gap-2 mb-4"><Icon name="psychology" className="text-secondary" />KV 分析结果 {cs.length===0&&<span className="text-[11px] font-normal text-amber-600">（本地提取，可重新上传）</span>}</h3>
    <div className="flex flex-col lg:flex-row gap-5">
      {kvImage && (<div className="shrink-0"><p className="text-[10px] text-outline uppercase font-semibold mb-2">主视觉</p><img src={kvImage.dataUrl} alt="KV" className="w-48 h-auto rounded-xl border border-outline-variant shadow-sm object-contain bg-white" /></div>)}
      <div className="flex-1 space-y-4">
        {cs.length>0 && (<div><p className="text-[10px] text-outline uppercase font-semibold mb-2">色板 ({cs.length}色)</p><div className="flex gap-1.5">{cs.map((c,i)=>(<div key={i} className="flex-1 max-w-[60px]"><div className="h-10 rounded-lg border border-outline-variant shadow-sm" style={{backgroundColor:c}}></div><p className="font-jetbrains text-[9px] text-on-surface-variant mt-1 text-center">{c}</p></div>))}</div></div>)}
        {analysis.titleDesign && (<div className="p-3 bg-primary-fixed/5 border border-primary/10 rounded-lg"><p className="text-[10px] text-outline uppercase font-semibold mb-1">主标题设计</p><p className="text-xs text-on-surface leading-relaxed">{analysis.titleDesign}</p></div>)}
      </div>
      <div className="flex-1 space-y-2 text-xs">
        {analysis.fonts&&<div><span className="text-outline">字体：</span><span className="text-on-surface-variant">{analysis.fonts.slice(0,3).join('、')}</span></div>}
        {analysis.layout&&<div><span className="text-outline">布局：</span><span className="text-on-surface-variant">{analysis.layout}</span></div>}
        {analysis.elements&&<div><span className="text-outline">视觉：</span><span className="text-on-surface-variant">{analysis.elements}</span></div>}
        {analysis.style&&<div><span className="text-outline">风格：</span><span className="text-on-surface-variant">{analysis.style}</span></div>}
        {positioned.length>0&&<div><span className="text-outline">定位元素：</span><span className="text-on-surface-variant">{positioned.map(e=>e.name).join('、')}（共{positioned.length}个）</span></div>}
      </div>
    </div>
    {/* Cropped elements gallery */}
    {cropped.length>0 && (<div className="mt-4 pt-4 border-t border-outline-variant"><p className="text-[10px] text-outline uppercase font-semibold mb-3">抠图元素 ({cropped.filter(e=>e.imageUrl).length}/{cropped.length}个成功)</p><div className="flex gap-3 flex-wrap">{cropped.filter(e=>e.imageUrl).map((e,i)=>(<div key={i} className="text-center"><div className="w-20 h-20 rounded-lg border border-outline-variant overflow-hidden bg-white shadow-sm"><img src={e.imageUrl} alt={e.name} className="w-full h-full object-contain" /></div><p className="font-jetbrains text-[9px] text-on-surface-variant mt-1 w-20 truncate">{e.name}</p></div>))}</div></div>)}
  </section>);
}

function Checklist({ items, selected, onToggle, onSelectAll }) {
  const all=selected.length===items.length;
  return (<section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-5 col-span-12"><div className="flex items-center justify-between mb-3"><h3 className="font-hanken text-base font-semibold flex items-center gap-2"><Icon name="checklist" className="text-primary" />目标物料 ({selected.length}/{items.length})</h3><button onClick={onSelectAll} className="text-xs text-primary hover:underline font-medium">{all?'取消全选':'全选'}</button></div><div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-1.5">{items.map((item)=>(<label key={item.id} className={`flex items-center gap-2 px-2.5 py-2 rounded-lg cursor-pointer transition-colors ${selected.includes(item.id)?'bg-primary-fixed/20 border border-primary/30':'hover:bg-surface-container border border-transparent'}`}><input type="checkbox" checked={selected.includes(item.id)} onChange={()=>onToggle(item.id)} className="rounded text-primary focus:ring-primary w-3.5 h-3.5 shrink-0" /><Icon name={item.icon} className={`text-[14px] ${selected.includes(item.id)?'text-primary':'text-on-surface-variant'}`} /><div className="min-w-0"><p className="text-[11px] font-semibold text-on-surface truncate">{item.name}</p><p className="text-[9px] text-on-surface-variant truncate">{item.size}</p></div></label>))}</div></section>);
}

function ImageViewer({ src, title, onClose }) {
  return (<div className="fixed inset-0 z-[100] bg-black/80 flex items-center justify-center p-8" onClick={onClose}><div className="relative max-w-[90vw] max-h-[90vh]" onClick={(e)=>e.stopPropagation()}><button onClick={onClose} className="absolute -top-10 right-0 text-white hover:text-primary transition-colors flex items-center gap-2"><Icon name="close" />关闭</button><img src={src} alt={title} className="max-w-full max-h-[85vh] rounded-xl shadow-2xl object-contain bg-white" />{title&&<p className="text-white text-center mt-3 text-sm opacity-70">{title}</p>}</div></div>);
}

function ResultCard({ item, result }) {
  const [viewerOpen, setViewerOpen] = useState(false);
  const [showPrompt, setShowPrompt] = useState(false);
  const imgUrl = result?.imageUrl;
  const promptText = result?.promptText || '';
  return (<><div className={`group bg-surface rounded-xl overflow-hidden transition-all duration-300 ${result?.status==='done'?'border border-outline-variant hover:border-primary hover:shadow-lg':result?.status==='error'?'border border-error/30':'border border-outline-variant'}`}><div className="aspect-[1.6] bg-surface-container-low relative overflow-hidden cursor-pointer" onClick={()=>imgUrl&&setViewerOpen(true)}>{imgUrl?(<img src={imgUrl} alt={item.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />):(<div className="w-full h-full flex flex-col items-center justify-center canvas-grid gap-2">{result?.status==='generating'?<><div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div><span className="text-xs text-on-surface-variant font-jetbrains">生成中...</span></>:result?.status==='error'?<><Icon name="error" className="text-error text-3xl" /><span className="text-xs text-error px-2 text-center">{result.error?.substring(0,50)}</span></>:<Icon name="image" className="text-on-surface-variant text-4xl opacity-30" />}</div>)}<div className="absolute top-2 right-2"><span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${result?.status==='done'?'bg-green-100 text-green-700':result?.status==='error'?'bg-red-100 text-red-700':result?.status==='generating'?'bg-blue-100 text-blue-700':'bg-amber-100 text-amber-700'}`}>{result?.status==='done'?'已生成':result?.status==='error'?'失败':result?.status==='generating'?'生成中':'等待'}</span></div>{imgUrl&&<div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center"><Icon name="zoom_in" className="text-white text-3xl opacity-0 group-hover:opacity-100 transition-opacity" /></div>}</div><div className="p-4"><h4 className="font-hanken text-base font-semibold text-on-surface">{item.name}</h4><p className="font-jetbrains text-[11px] text-on-surface-variant mt-0.5">{item.size}</p><div className="flex gap-2 mt-3"><button disabled={!imgUrl} onClick={()=>{if(!imgUrl)return;const a=document.createElement('a');a.href=imgUrl;a.target='_blank';a.rel='noopener';document.body.appendChild(a);a.click();document.body.removeChild(a)}} className="flex-1 py-1.5 bg-primary text-on-primary text-xs font-semibold rounded-lg hover:bg-primary-container transition-all active:scale-95 disabled:opacity-30">查看原图</button><button disabled={!imgUrl} onClick={()=>{if(!imgUrl)return;fetch(imgUrl).then(r=>r.blob()).then(b=>{const u=URL.createObjectURL(b);const a=document.createElement('a');a.href=u;a.download=`${item.name}.png`;document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(u)}).catch(()=>window.open(imgUrl,'_blank'))}} className="flex-1 py-1.5 border border-primary text-primary text-xs font-semibold rounded-lg hover:bg-primary-fixed/20 transition-all active:scale-95 disabled:opacity-30">下载</button></div>
        {promptText && (<div className="mt-2"><button onClick={()=>setShowPrompt(!showPrompt)} className="text-[10px] text-outline hover:text-primary flex items-center gap-1"><Icon name={showPrompt?'expand_less':'code'} className="text-[14px]" />{showPrompt?'收起':'查看'}提示词</button>{showPrompt && <p className="text-[10px] text-on-surface-variant mt-1 p-2 bg-surface-container rounded leading-relaxed whitespace-pre-wrap max-h-40 overflow-y-auto">{promptText}</p>}</div>)}
      </div></div>{viewerOpen&&imgUrl&&<ImageViewer src={imgUrl} title={`${item.name} - ${item.size}`} onClose={()=>setViewerOpen(false)} />}</>);
}

export default function Workbench() {
  const [kvImage, setKvImage] = useState(null); const [analysis, setAnalysis] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [visionModel, setVisionModel] = useState(visionModels[0].id); // Canvas extraction
  const [genModel, setGenModel] = useState(generateModels[0].id); // default: Nano Banana 2
  const customMaterials = loadCustomMaterials();
  const allChecklist = [...peripheralChecklist, ...customMaterials.map(m => ({...m, isCustom: true}))];
  const [selected, setSelected] = useState([]);
  const [results, setResults] = useState({}); const [generating, setGenerating] = useState(false);
  const [currentGen, setCurrentGen] = useState(null); const [statusMsg, setStatusMsg] = useState('');
  const [theme, setTheme] = useState('');
  const [subtitle, setSubtitle] = useState('');
  const [showConfirm, setShowConfirm] = useState(false);
  const materials = [...loadMaterials(), ...customMaterials.map(m => ({id: m.id, name: m.name, size: m.size, material: m.material, appearanceImage: m.appearanceImage}))];

  // Restore from history or session
  useEffect(() => {
    const histSaved = loadWorkbenchState();
    const sessSaved = loadSession();
    const saved = histSaved || sessSaved;
    if (saved) {
      if (saved.kvImage) setKvImage(saved.kvImage);
      if (saved.analysis) setAnalysis(saved.analysis);
      if (saved.theme) setTheme(saved.theme || '');
      if (saved.subtitle) setSubtitle(saved.subtitle || '');
      if (saved.visionModel) setVisionModel(saved.visionModel);
      if (saved.genModel) setGenModel(saved.genModel);
      if (saved.results && Object.keys(saved.results).length > 0) setResults(saved.results);
      if (saved.selected) setSelected(saved.selected);
      if (histSaved) { setStatusMsg('已从历史记录恢复，可微调参数后重新生成'); clearWorkbenchState(); }
      else { setStatusMsg('已恢复上次未完成的工作'); }
    }
  }, []);

  // Auto-save session when navigating away
  useEffect(() => {
    const save = () => saveSession({ kvImage, analysis, theme, subtitle, visionModel, genModel, selected, results });
    window.addEventListener('beforeunload', save);
    return () => { save(); window.removeEventListener('beforeunload', save); };
  }, [kvImage, analysis, theme, subtitle, visionModel, genModel, selected, results]);

  const toggleItem=(id)=>setSelected(p=>p.includes(id)?p.filter(x=>x!==id):[...p,id]);
  const selectAll=()=>selected.length===allChecklist.length?setSelected([]):setSelected(allChecklist.map(i=>i.id));

  const handleImageSet=async(img)=>{
    setKvImage(img);setAnalysis(null);setStatusMsg('');if(!img)return;
    setProcessing(true);setStatusMsg(`${visionModels.find(m=>m.id===visionModel)?.name} 分析中...`);
    try{const compressed=await compressImage(img.dataUrl,384,0.4);const r=await analyzeImage(compressed.dataUrl, visionModel, img.dataUrl);setAnalysis(r);if(r.themeHint&&!theme){setTheme(r.themeHint)};setStatusMsg('分析完成')}catch(err){setStatusMsg('分析失败: '+err.message)}
    setProcessing(false);
  };

  const startGenerate=async()=>{
    setShowConfirm(false);
    if(!kvImage||!analysis)return;
    const tg=allChecklist.filter(i=>selected.includes(i.id));if(tg.length===0)return;
    if(!theme.trim()){setStatusMsg('请先输入主题标题');return;}
    setGenerating(true);
    const localResults = {}; // Track results locally to avoid stale closure
    for(let i=0;i<tg.length;i++){
      const item=tg[i];setCurrentGen(`${item.name}(${i+1}/${tg.length})`);
      setStatusMsg(`${generateModels.find(m=>m.id===genModel)?.name} 生成: ${item.name}...`);
      setResults(p=>({...p,[item.id]:{status:'generating'}}));
      try{
        const mat = materials.find(m => m.id === item.id);
        const appearanceUrls = mat?.appearanceImage ? [mat.appearanceImage] : [];
        const result=await startNanoDraw({model:genModel,analysis,item:{...item,size:mat?.size||item.size,material:mat?.material||item.material},theme,subtitle,appearanceUrls});

        // GPT models return results directly (sync), Nano Banana needs polling
        let imgUrl;
        let promptText = '';
        if (result && result._direct) {
          imgUrl = result.results[0]?.url;
          promptText = result.promptText || '';
        } else {
          setStatusMsg(`${item.name}: 等待生成...`);
          promptText = result.promptText || '';
          const imgs = await pollNanoResult(result.id);
          imgUrl = imgs[0]?.url;
        }
        localResults[item.id] = {status:'done',imageUrl:imgUrl,title:item.name,promptText};
        setResults(p=>({...p,[item.id]:localResults[item.id]}));
        setStatusMsg(`✅ ${item.name}`);
        showToast(`【${item.name}】生成完成`, 'success');
        pushNotification('物料生成完成', `${item.name} 已生成`, 'check_circle', 'text-green-600');
      }catch(err){
        localResults[item.id] = {status:'error',error:err.message};
        setResults(p=>({...p,[item.id]:localResults[item.id]}));
        setStatusMsg(`❌ ${item.name}: ${err.message}`);
        pushNotification('生成失败', `${item.name}: ${err.message}`, 'error', 'text-error');
      }
      if(i<tg.length-1)await new Promise(r=>setTimeout(r,1000));
    }

    // Save to history with actual results
    saveHistoryEntry({
      createdAt: new Date().toLocaleString('zh-CN'),
      kvImageDataUrl: kvImage?.dataUrl || null,
      kvThumbnail: kvImage?.dataUrl || null,
      theme: theme || '未命名',
      subtitle: subtitle || '',
      analysis: analysis,
      visionModel, genModel,
      results: localResults,
    });

    setGenerating(false);setCurrentGen(null);const d=Object.values(localResults).filter(r=>r.status==='done').length;setStatusMsg(`✅ ${d}/${tg.length} 已保存到历史`);
  };

  const doneCount=Object.values(results).filter(r=>r.status==='done').length;

  return (<Layout><div className="pt-6 pb-12 px-8 max-w-[1440px] mx-auto">
    <header className="mb-5"><h2 className="font-hanken text-[24px] leading-8 font-semibold text-on-surface mb-1">视觉物料一键延展工作台</h2><p className="text-on-surface-variant text-base">上传 KV → 视觉分析 → 选择模型 → 物料库参数 → 批量生成</p></header>
    {statusMsg&&(<div className="mb-4 px-4 py-2 bg-surface-container rounded-lg border border-outline-variant text-sm text-on-surface-variant font-jetbrains flex items-center gap-2"><Icon name="info" className="text-primary text-[18px]" />{statusMsg}</div>)}

    <div className="space-y-4 mb-5">
      <div className="bento-grid"><KVUpload image={kvImage} onImageSet={handleImageSet} processing={processing} /><AnalysisCard analysis={analysis} kvImage={kvImage} /></div>
      <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-5">
        <div className="flex items-center gap-4 mb-3"><div className="flex items-center gap-2 shrink-0"><Icon name="title" className="text-primary text-[20px]" /><span className="font-semibold text-sm text-on-surface">主题标题</span></div><input value={theme} onChange={(e)=>setTheme(e.target.value)} placeholder="例如：2024品牌年度盛典" className="flex-1 px-4 py-2.5 bg-surface border border-outline-variant rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all text-sm" /><span className="text-[10px] text-on-surface-variant shrink-0">不填则 AI 推断</span></div>
        <div className="flex items-center gap-4"><div className="flex items-center gap-2 shrink-0"><Icon name="subtitles" className="text-primary text-[20px]" /><span className="font-semibold text-sm text-on-surface">主题副标题</span></div><input value={subtitle} onChange={(e)=>setSubtitle(e.target.value)} placeholder="大标题下方的小标题（可不填）" className="flex-1 px-4 py-2.5 bg-surface border border-outline-variant rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all text-sm" /><span className="text-[10px] text-on-surface-variant shrink-0">默认为空</span></div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ModelSelector label="分析模型" icon="psychology" models={visionModels} selected={visionModel} onSelect={setVisionModel} />
        <ModelSelector label="生图模型" icon="auto_awesome" models={generateModels} selected={genModel} onSelect={setGenModel} />
      </div>
      <Checklist items={allChecklist} selected={selected} onToggle={toggleItem} onSelectAll={selectAll} />
    </div>

    <div className="flex flex-col items-center justify-center my-6">
      <button onClick={()=>{if(!theme.trim()){setStatusMsg('请先输入主题标题');return};setShowConfirm(true)}} disabled={!kvImage||!analysis||generating||processing||selected.length===0}
        className={`px-10 py-4 rounded-xl font-hanken text-[20px] font-bold flex items-center gap-3 transition-all ${!kvImage||!analysis||processing||selected.length===0?'bg-outline-variant text-outline cursor-not-allowed':generating?'bg-surface-container-high text-on-surface-variant cursor-wait':'bg-primary text-on-primary hover:shadow-xl hover:shadow-primary/30 active:scale-95'}`}>
        {generating?<><span className="animate-spin"><Icon name="progress_activity" /></span>{currentGen||'生成中...'}</>:<><Icon name="auto_awesome" filled />一键生成 {selected.length} 个物料 · {generateModels.find(m=>m.id===genModel)?.name}</>}
      </button>
    </div>

    {generating&&(<div className="mb-6"><div className="w-full h-2 bg-surface-container-high rounded-full overflow-hidden"><div className="h-full processing-bar" style={{width:`${selected.length>0?(doneCount/selected.length)*100:0}%`}}></div></div><p className="text-center text-xs text-on-surface-variant mt-2 font-jetbrains">{doneCount}/{selected.length}</p></div>)}

    {Object.keys(results).length>0&&(<section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-8 shadow-sm"><div className="flex items-center justify-between mb-6"><div><h3 className="font-hanken text-[24px] leading-8 font-semibold">生成结果</h3><p className="text-on-surface-variant text-sm mt-1">{doneCount}个物料 · {generateModels.find(m=>m.id===genModel)?.name} · 已自动保存到历史</p></div></div><div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">{peripheralChecklist.filter(i=>results[i.id]).map((item)=>(<ResultCard key={item.id} item={item} result={results[item.id]} />))}</div></section>)}
  </div>

    {showConfirm && (<div className="fixed inset-0 z-[200] bg-black/60 flex items-center justify-center p-4" onClick={()=>setShowConfirm(false)}>
      <div className="bg-surface rounded-2xl shadow-2xl max-w-md w-full p-6" onClick={e=>e.stopPropagation()}>
        <h3 className="font-hanken text-lg font-semibold mb-4">确认生成信息</h3>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between"><span className="text-outline">主题标题</span><span className="font-semibold text-on-surface">{theme||'(未填)'}</span></div>
          <div className="flex justify-between"><span className="text-outline">副标题</span><span className="text-on-surface-variant">{subtitle||'(无)'}</span></div>
          <div className="flex justify-between"><span className="text-outline">分析模型</span><span className="font-jetbrains text-xs">{visionModels.find(m=>m.id===visionModel)?.name}</span></div>
          <div className="flex justify-between"><span className="text-outline">生图模型</span><span className="font-jetbrains text-xs">{generateModels.find(m=>m.id===genModel)?.name}</span></div>
          <div className="flex justify-between"><span className="text-outline">目标物料</span><span className="font-semibold text-primary">{selected.length} 个</span></div>
        </div>
        <div className="flex gap-3 mt-6">
          <button onClick={()=>setShowConfirm(false)} className="flex-1 py-2.5 border border-outline-variant rounded-lg text-sm font-semibold hover:bg-surface-container">返回修改</button>
          <button onClick={startGenerate} className="flex-1 py-2.5 bg-primary text-on-primary rounded-lg text-sm font-semibold hover:bg-primary-container active:scale-95">确认生成</button>
        </div>
      </div>
    </div>)}
  </Layout>);
}
