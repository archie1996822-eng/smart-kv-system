import { useState } from 'react';
import Layout, { Icon, showToast } from '../components/Layout';

const BAG_DATA = {
  paper: {
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuClVCUCHQNhHjvEgdaW1uUlXtPlyjRxBSBM1_OSAWmtvLtvde32hgnseTlYouDlg7L-HzP8HmJS2m-_VuLAb-ydMCiiQjbTRi9zSpJP297Ua04NQtMSjnWwMvj7q4Y9X_SiI9oqs1kuOVNUtsWNmdFv-UBr-DWfbsM7iPtY6PPe-pCjKUn33dkrLDG3dF2UOr6ncyi5u0Osv-s0YMm8DEWXDYlJfdnrBaKEO2lFw4IjD03ADXRkYY-Z5TuFFjhY8wYYcEBjv5ciQA4',
    specs: [
      { label: '纸张克重', value: '250g', note: '白卡纸' },
      { label: '印刷工艺', value: '四色+专色', note: '正面覆哑膜' },
      { label: '提手规格', value: '三股绳', note: '蓝色棉绳' },
      { label: '起订量', value: '500个', note: '7-10天交货' },
    ],
    dims: [
      { label: '宽度', value: '320mm', pct: '20%' },
      { label: '高度', value: '270mm', pct: '40%' },
      { label: '侧边', value: '100mm', pct: '10%' },
    ],
  },
  canvas: {
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuClVCUCHQNhHjvEgdaW1uUlXtPlyjRxBSBM1_OSAWmtvLtvde32hgnseTlYouDlg7L-HzP8HmJS2m-_VuLAb-ydMCiiQjbTRi9zSpJP297Ua04NQtMSjnWwMvj7q4Y9X_SiI9oqs1kuOVNUtsWNmdFv-UBr-DWfbsM7iPtY6PPe-pCjKUn33dkrLDG3dF2UOr6ncyi5u0Osv-s0YMm8DEWXDYlJfdnrBaKEO2lFw4IjD03ADXRkYY-Z5TuFFjhY8wYYcEBjv5ciQA4',
    specs: [
      { label: '布料材质', value: '12安帆布', note: '纯棉水洗' },
      { label: '印花工艺', value: '丝网印4色', note: '环保油墨' },
      { label: '提手规格', value: '加固织带', note: '承重15kg' },
      { label: '起订量', value: '200个', note: '10-14天交货' },
    ],
    dims: [
      { label: '宽度', value: '350mm', pct: '20%' },
      { label: '高度', value: '400mm', pct: '40%' },
      { label: '侧边', value: '100mm', pct: '10%' },
    ],
  },
  gift: {
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuClVCUCHQNhHjvEgdaW1uUlXtPlyjRxBSBM1_OSAWmtvLtvde32hgnseTlYouDlg7L-HzP8HmJS2m-_VuLAb-ydMCiiQjbTRi9zSpJP297Ua04NQtMSjnWwMvj7q4Y9X_SiI9oqs1kuOVNUtsWNmdFv-UBr-DWfbsM7iPtY6PPe-pCjKUn33dkrLDG3dF2UOr6ncyi5u0Osv-s0YMm8DEWXDYlJfdnrBaKEO2lFw4IjD03ADXRkYY-Z5TuFFjhY8wYYcEBjv5ciQA4',
    specs: [
      { label: '盒型材质', value: '灰板裱糊', note: '157g铜版纸' },
      { label: '表面工艺', value: '烫金+UV', note: '局部上光' },
      { label: '内衬规格', value: '植绒内托', note: 'EVA定制' },
      { label: '起订量', value: '300个', note: '15-20天交货' },
    ],
    dims: [
      { label: '长度', value: '300mm', pct: '20%' },
      { label: '宽度', value: '200mm', pct: '40%' },
      { label: '高度', value: '80mm', pct: '10%' },
    ],
  },
};

const HAND_SIGN_TEXTS = ['甲方说的都对', '别改了', '今晚出稿', '终版FINAL'];
const HAND_SIGN_IMAGES = [
  'https://lh3.googleusercontent.com/aida-public/AB6AXuCJdTRNRzh5q7tzLiyvpVovKEaOz9G9XdIOi-_Fz9DTgOO2rlzX8I3I0ZXb5AuTOp7HRXJ1zSvfim8bE8lmv2f9kuNtmCzYrAoFnSA6qR0k2Vmn2Zxk1FF0CphgfKdfa3w89miPEOfZ5CDyMJVdD2U0eHqm35WVzrMTD9ISxnbBCdtUBx-gkxnkY1HcszwY5n7VVPNDOn-iyDh2jZVpf7UH4cvc5z5ZyaLJak0Ku5LzWpk3Rpzk4yxVHdM0W83ibr-fycyG1qi0ScM',
];

export default function PreviewExport() {
  const [selectedBagType, setSelectedBagType] = useState('canvas');
  const [selectedText, setSelectedText] = useState(0);
  const [exportFmts, setExportFmts] = useState([
    { id: 'pdf', label: 'PDF 矢量文件', checked: true },
    { id: 'png', label: 'PNG 透明背景', checked: true },
  ]);
  const [showChat, setShowChat] = useState(false);
  const [chatMsg, setChatMsg] = useState('');
  const [chatHistory, setChatHistory] = useState([
    { from: 'expert', msg: '你好！我是物料专家，有什么可以帮助你的？' },
  ]);
  const [production, setProduction] = useState({
    supplier: '虹口物料厂', status: '待排期', delivery: '2024.11.24', progress: 35,
  });

  const bag = BAG_DATA[selectedBagType];

  const toggleFormat = (id) => {
    setExportFmts(fmts => fmts.map(f => f.id === id ? { ...f, checked: !f.checked } : f));
  };

  const handleExport = () => {
    const checked = exportFmts.filter(f => f.checked);
    if (checked.length === 0) { showToast('请选择导出格式', 'error'); return; }
    const formats = checked.map(f => f.label).join('、');
    showToast(`正在准备导出 ${formats}...`, 'success');
    // Simulate: download a placeholder
    setTimeout(() => {
      const a = document.createElement('a');
      a.href = bag.img;
      a.download = `bag-mockup-${selectedBagType}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }, 500);
  };

  const handleBatchExport = () => {
    showToast('正在打包所有 Mockup...', 'success');
    setTimeout(() => {
      const a = document.createElement('a');
      a.href = bag.img;
      a.download = `mockup-batch-${selectedBagType}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      showToast('导出完成!', 'success');
    }, 800);
  };

  const sendChat = () => {
    if (!chatMsg.trim()) return;
    setChatHistory(h => [...h, { from: 'user', msg: chatMsg }]);
    const userMsg = chatMsg;
    setChatMsg('');
    setTimeout(() => {
      setChatHistory(h => [...h, {
        from: 'expert',
        msg: userMsg.includes('价格') ? '目前帆布袋丝网印4色单价约¥8.5/个（200个起），手提纸袋约¥3.2/个（500个起）。需要更详细的报价吗？'
          : userMsg.includes('时间') ? '帆布袋生产周期约10-14天，手提纸袋约7-10天，加急可缩短至5天（加收30%加急费）。'
          : '收到你的问题！关于物料生产，建议你提供具体数量和工艺需求，我可以帮你估算成本和排期。',
      }]);
    }, 1000);
  };

  return (<Layout>
    <div className="p-4 md:p-8 min-h-screen">
      <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between mb-8 gap-4">
        <div>
          <h2 className="font-hanken text-[24px] leading-8 font-semibold text-on-surface">周边预览与导出</h2>
          <p className="text-on-surface-variant text-base">已完成 24 个 SKU 的 3D 渲染，准备进入量产对接流程</p>
        </div>
        <div className="flex gap-3">
          <button onClick={handleBatchExport} className="px-4 py-2 border border-primary text-primary hover:bg-primary-container/10 transition-all rounded-lg flex items-center gap-2 font-medium"><Icon name="download" />批量导出所有 Mockup</button>
        </div>
      </div>

      <div className="bento-grid">
        {/* Handheld Signboard */}
        <section className="col-span-12 lg:col-span-8 bg-white border border-outline-variant rounded-xl overflow-hidden flex flex-col">
          <div className="p-6 border-b border-outline-variant flex justify-between items-center">
            <h3 className="font-hanken text-[20px] leading-7 font-semibold flex items-center gap-2"><Icon name="cut" className="text-primary" />手举牌：异形切割预览</h3>
            <div className="flex items-center gap-4">
              <span className="font-jetbrains px-3 py-1 bg-secondary-container/20 text-secondary text-xs rounded-full">3MM PVC 板</span>
              <span className="font-jetbrains px-3 py-1 bg-primary-container/10 text-primary text-xs rounded-full">异形模切</span>
            </div>
          </div>
          <div className="flex-1 p-12 bg-surface-container-lowest flex items-center justify-center relative min-h-[500px]">
            <div className="relative group cursor-zoom-in">
              <div className="absolute -inset-4 border-2 border-dashed border-primary/30 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="relative">
                <img alt="手举牌预览" className="max-h-[400px] w-auto drop-shadow-2xl hover:scale-105 transition-transform duration-500" src={HAND_SIGN_IMAGES[0]} />
                {/* Text overlay based on selection */}
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <span className="text-2xl md:text-4xl font-bold text-white drop-shadow-[0_2px_8px_rgba(0,0,0,0.8)] transform -rotate-3 select-none">{HAND_SIGN_TEXTS[selectedText]}</span>
                </div>
              </div>
              <div className="absolute -top-4 -right-4 bg-white shadow-lg p-2 rounded-lg border border-outline-variant flex flex-col gap-1">
                <span className="font-jetbrains text-[10px] text-outline uppercase tracking-wider text-center font-semibold">Cut Path</span>
                <div className="w-16 h-1 bg-error rounded-full"></div>
              </div>
            </div>
            <div className="absolute left-8 bottom-8 flex flex-col gap-2">
              <div className="font-jetbrains flex items-center gap-2 text-outline"><Icon name="straighten" className="text-sm" /><span className="text-xs">450mm x 320mm</span></div>
            </div>
          </div>
          <div className="p-4 bg-surface-container-low flex gap-4">
            <div className="flex-1">
              <p className="font-jetbrains text-xs text-on-surface-variant uppercase mb-2 font-semibold">趣味文案库</p>
              <div className="flex gap-2 flex-wrap">
                {HAND_SIGN_TEXTS.map((text, i) => (
                  <button key={i} onClick={() => setSelectedText(i)} className={`px-3 py-1 rounded text-sm font-medium transition-all ${selectedText===i?'bg-white border border-primary text-primary shadow-sm':'bg-white border border-outline-variant text-on-surface-variant hover:border-primary/50'}`}>{text}</button>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => setSelectedText(Math.floor(Math.random() * HAND_SIGN_TEXTS.length))} className="w-10 h-10 rounded-lg border border-outline-variant flex items-center justify-center hover:bg-white transition-colors"><Icon name="refresh" /></button>
              <button onClick={() => { const img = document.querySelector('img[alt="手举牌预览"]'); if(img) img.classList.toggle('scale-150'); }} className="w-10 h-10 rounded-lg border border-outline-variant flex items-center justify-center hover:bg-white transition-colors"><Icon name="zoom_in" /></button>
            </div>
          </div>
        </section>

        {/* Production Task */}
        <aside className="col-span-12 lg:col-span-4 flex flex-col gap-4">
          <div className="bg-inverse-surface text-white p-6 rounded-xl flex flex-col gap-4">
            <h3 className="font-hanken text-[20px] leading-7 font-semibold">生产对接</h3>
            <div className="space-y-4">
              <div className="bg-white/10 p-4 rounded-lg border border-white/5">
                <div className="flex justify-between items-center mb-2">
                  <input className="text-sm bg-transparent border-b border-white/30 outline-none w-32" value={production.supplier} onChange={e => setProduction({...production, supplier: e.target.value})} />
                  <select className="font-jetbrains px-2 py-0.5 bg-secondary-container text-on-secondary-fixed text-[10px] font-semibold rounded" value={production.status} onChange={e => setProduction({...production, status: e.target.value})}>
                    <option>待排期</option><option>生产中</option><option>已完成</option>
                  </select>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm opacity-70">预计交付：</span>
                  <input className="text-sm bg-transparent border-b border-white/30 outline-none w-28" value={production.delivery} onChange={e => setProduction({...production, delivery: e.target.value})} />
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm"><span>生产进度</span><span className="font-jetbrains">{production.progress}%</span></div>
                <div className="w-full h-2 bg-white/20 rounded-full overflow-hidden"><div className="h-full bg-secondary-container transition-all duration-500" style={{width: `${production.progress}%`}}></div></div>
                <input type="range" min="0" max="100" value={production.progress} onChange={e => setProduction({...production, progress: Number(e.target.value)})} className="w-full" />
              </div>
            </div>
            <button onClick={() => showToast('已推送至生产线!', 'success')} className="w-full bg-white text-on-background py-3 rounded-lg font-semibold hover:bg-surface-variant transition-colors flex items-center justify-center gap-2"><Icon name="send" />推送至生产线</button>
          </div>

          <div className="bg-white border border-outline-variant rounded-xl p-6 flex-1">
            <h4 className="font-hanken text-[20px] leading-7 font-semibold mb-4">延展适配</h4>
            <div className="space-y-6">
              {[
                { name: '社交媒体海报', size: '1080 × 1920 px', icon: 'phone_iphone' },
                { name: '网页横幅', size: '1920 × 600 px', icon: 'web' },
                { name: '圆形贴纸', size: '200 × 200 mm', icon: 'lens' },
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-surface-container rounded-lg flex items-center justify-center"><Icon name={item.icon} className="text-primary" /></div>
                  <div className="flex-1"><p className="font-semibold">{item.name}</p><p className="font-jetbrains text-xs text-outline">{item.size}</p></div>
                  <Icon name="check_circle" className="text-secondary" />
                </div>
              ))}
            </div>
            <div className="mt-8 pt-6 border-t border-outline-variant">
              <p className="text-xs text-outline mb-4 font-semibold">导出格式</p>
              <div className="grid grid-cols-2 gap-2">
                {exportFmts.map((fmt) => (
                  <label key={fmt.id} className="flex items-center gap-2 p-2 border border-outline-variant rounded cursor-pointer hover:bg-surface-container-low">
                    <input checked={fmt.checked} onChange={() => toggleFormat(fmt.id)} className="rounded text-primary focus:ring-primary w-4 h-4" type="checkbox" />
                    <span className="font-jetbrains text-xs">{fmt.label}</span>
                  </label>
                ))}
              </div>
              <button onClick={handleExport} className="w-full mt-4 py-2 bg-primary text-on-primary rounded-lg text-sm font-semibold hover:shadow-lg">导出选中格式</button>
            </div>
          </div>
        </aside>

        {/* 3D Bag Mockup */}
        <section className="col-span-12 bg-white border border-outline-variant rounded-xl overflow-hidden mt-2">
          <div className="p-6 border-b border-outline-variant flex justify-between items-center bg-white flex-wrap gap-2">
            <h3 className="font-hanken text-[20px] leading-7 font-semibold flex items-center gap-2"><Icon name="shopping_bag" className="text-primary" />3D Mockup 预览：帆布袋与手提袋</h3>
            <div className="flex gap-2">
              {[
                { id: 'paper', label: '手提袋' },
                { id: 'canvas', label: '帆布袋' },
                { id: 'gift', label: '礼品盒' },
              ].map(btn => (
                <button key={btn.id} onClick={() => setSelectedBagType(btn.id)} className={`px-3 py-1 rounded text-sm font-medium transition-all ${selectedBagType===btn.id?'bg-primary text-white':'bg-surface-container text-on-surface-variant hover:bg-primary hover:text-white'}`}>{btn.label}</button>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-outline-variant">
            <div className="bg-surface-container-lowest p-8 flex items-center justify-center min-h-[400px]">
              <div className="relative w-full max-w-lg group">
                <img alt="3D 帆布袋 Mockup" className="w-full h-auto object-contain drop-shadow-xl hover:rotate-2 transition-transform duration-700" src={bag.img} />
                <div className="absolute inset-0 bg-primary/10 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <button onClick={() => showToast('3D全景查看功能即将上线', 'info')} className="bg-white text-primary px-6 py-3 rounded-full font-semibold shadow-xl flex items-center gap-2"><Icon name="3d_rotation" />查看 3D 全景</button>
                </div>
              </div>
            </div>
            <div className="bg-white p-8">
              <h4 className="font-hanken text-[20px] leading-7 font-semibold mb-6">工艺规范</h4>
              <div className="grid grid-cols-2 gap-6 mb-8">
                {bag.specs.map((spec, i) => (
                  <div key={i} className="spec-card p-4 rounded-xl bg-white">
                    <p className="font-jetbrains text-xs text-outline uppercase mb-2 font-semibold">{spec.label}</p>
                    <p className="font-hanken text-[20px] leading-7 font-semibold">{spec.value}</p>
                    <p className="text-xs text-on-surface-variant mt-1">{spec.note}</p>
                  </div>
                ))}
              </div>
              <div>
                <p className="text-sm font-semibold mb-4">尺寸参数</p>
                <div className="space-y-4">
                  {bag.dims.map((dim, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="font-jetbrains text-xs w-12">{dim.label}</span>
                      <div className="flex-1 h-px bg-outline-variant relative">
                        <div className="font-jetbrains absolute left-0 -top-2 px-2 bg-white text-[10px]" style={{ marginLeft: dim.pct }}>{dim.value}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Chat FAB */}
      <div className="fixed bottom-8 right-8 z-50 flex flex-col items-end gap-3">
        {showChat && (
          <div className="bg-white rounded-2xl shadow-2xl border border-outline-variant w-80 mb-2 overflow-hidden">
            <div className="p-4 bg-primary text-white flex items-center justify-between">
              <span className="font-semibold flex items-center gap-2"><Icon name="chat_bubble" />物料专家</span>
              <button onClick={() => setShowChat(false)}><Icon name="close" /></button>
            </div>
            <div className="h-64 overflow-y-auto p-4 space-y-3 text-sm">
              {chatHistory.map((h, i) => (
                <div key={i} className={`flex ${h.from==='user'?'justify-end':'justify-start'}`}>
                  <div className={`max-w-[80%] px-3 py-2 rounded-xl ${h.from==='user'?'bg-primary text-white':'bg-surface-container text-on-surface'}`}>{h.msg}</div>
                </div>
              ))}
            </div>
            <div className="p-3 border-t border-outline-variant flex gap-2">
              <input className="flex-1 px-3 py-2 bg-surface-container border border-outline-variant rounded-lg text-sm outline-none focus:border-primary" placeholder="输入问题..." value={chatMsg} onChange={e => setChatMsg(e.target.value)} onKeyDown={e => e.key==='Enter'&&sendChat()} />
              <button onClick={sendChat} className="px-3 py-2 bg-primary text-white rounded-lg"><Icon name="send" /></button>
            </div>
          </div>
        )}
        <button onClick={() => setShowChat(!showChat)} className="bg-secondary-container text-on-secondary-fixed w-14 h-14 rounded-full shadow-2xl flex items-center justify-center hover:scale-110 transition-transform active:scale-95">
          <Icon name="chat_bubble" />
        </button>
        <div className="flex gap-3 bg-white p-2 rounded-xl shadow-2xl border border-outline-variant">
          <button onClick={handleBatchExport} className="bg-primary text-white px-8 py-3 rounded-lg font-semibold hover:bg-on-primary-fixed-variant transition-all active:scale-95 flex items-center gap-2"><Icon name="file_download" />一键打包下载</button>
        </div>
      </div>
    </div>
  </Layout>);
}
