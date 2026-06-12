import { useState } from 'react';
import Layout, { Icon } from '../components/Layout';
import { handSignTexts, bagSpecs, exportFormats, extensionItems } from '../data/mockData';

export default function PreviewExport() {
  const [selectedBagType, setSelectedBagType] = useState('canvas');
  const [selectedText, setSelectedText] = useState(0);
  const [exportFmts, setExportFmts] = useState(exportFormats);

  const toggleFormat = (id) => { setExportFmts(fmts => fmts.map(f => f.id===id?{...f,checked:!f.checked}:f)); };

  return (<Layout>
    <div className="p-8 min-h-screen">
      <div className="flex items-end justify-between mb-8">
        <div>
          <h2 className="font-hanken text-[24px] leading-8 font-semibold text-on-surface">周边预览与导出</h2>
          <p className="text-on-surface-variant text-base">已完成 24 个 SKU 的 3D 渲染，准备进入量产对接流程</p>
        </div>
        <div className="flex gap-3">
          <button className="px-4 py-2 border border-primary text-primary hover:bg-primary-container/10 transition-all rounded-lg flex items-center gap-2 font-medium"><Icon name="download" />批量导出所有 Mockup</button>
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
              <img alt="手举牌预览" className="max-h-[400px] w-auto drop-shadow-2xl hover:scale-105 transition-transform duration-500" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCJdTRNRzh5q7tzLiyvpVovKEaOz9G9XdIOi-_Fz9DTgOO2rlzX8I3I0ZXb5AuTOp7HRXJ1zSvfim8bE8lmv2f9kuNtmCzYrAoFnSA6qR0k2Vmn2Zxk1FF0CphgfKdfa3w89miPEOfZ5CDyMJVdD2U0eHqm35WVzrMTD9ISxnbBCdtUBx-gkxnkY1HcszwY5n7VVPNDOn-iyDh2jZVpf7UH4cvc5z5ZyaLJak0Ku5LzWpk3Rpzk4yxVHdM0W83ibr-fycyG1qi0ScM" />
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
                {handSignTexts.map((text, i) => (<button key={i} onClick={()=>setSelectedText(i)} className={`px-3 py-1 rounded text-sm font-medium transition-all ${selectedText===i?'bg-white border border-primary text-primary':'bg-white border border-outline-variant text-on-surface-variant'}`}>{text}</button>))}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button className="w-10 h-10 rounded-lg border border-outline-variant flex items-center justify-center hover:bg-white transition-colors"><Icon name="refresh" /></button>
              <button className="w-10 h-10 rounded-lg border border-outline-variant flex items-center justify-center hover:bg-white transition-colors"><Icon name="zoom_in" /></button>
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
                  <span className="text-sm opacity-70">供应商：虹口物料厂</span>
                  <span className="font-jetbrains px-2 py-0.5 bg-secondary-container text-on-secondary-fixed text-[10px] font-semibold rounded">待排期</span>
                </div>
                <p>预计交付：2024.11.24</p>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm"><span>生产进度</span><span className="font-jetbrains">35%</span></div>
                <div className="w-full h-2 bg-white/20 rounded-full overflow-hidden"><div className="w-[35%] h-full bg-secondary-container"></div></div>
              </div>
            </div>
            <button className="w-full bg-white text-on-background py-3 rounded-lg font-semibold hover:bg-surface-variant transition-colors flex items-center justify-center gap-2"><Icon name="send" />推送至生产线</button>
          </div>

          <div className="bg-white border border-outline-variant rounded-xl p-6 flex-1">
            <h4 className="font-hanken text-[20px] leading-7 font-semibold mb-4">延展适配</h4>
            <div className="space-y-6">
              {extensionItems.map((item, i) => (
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
                    <input checked={fmt.checked} onChange={()=>toggleFormat(fmt.id)} className="rounded text-primary focus:ring-primary w-4 h-4" type="checkbox" />
                    <span className="font-jetbrains text-xs">{fmt.label}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        </aside>

        {/* 3D Bag Mockup */}
        <section className="col-span-12 bg-white border border-outline-variant rounded-xl overflow-hidden mt-2">
          <div className="p-6 border-b border-outline-variant flex justify-between items-center bg-white">
            <h3 className="font-hanken text-[20px] leading-7 font-semibold flex items-center gap-2"><Icon name="shopping_bag" className="text-primary" />3D Mockup 预览：帆布袋与手提袋</h3>
            <div className="flex gap-2">
              {[{id:'paper',label:'手提袋'},{id:'canvas',label:'帆布袋'},{id:'gift',label:'礼品盒'}].map(btn => (
                <button key={btn.id} onClick={()=>setSelectedBagType(btn.id)} className={`px-3 py-1 rounded text-sm font-medium transition-all ${selectedBagType===btn.id?'bg-primary text-white':'bg-surface-container text-on-surface-variant hover:bg-primary hover:text-white'}`}>{btn.label}</button>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-outline-variant">
            <div className="bg-surface-container-lowest p-8 flex items-center justify-center min-h-[400px]">
              <div className="relative w-full max-w-lg group">
                <img alt="3D 帆布袋 Mockup" className="w-full h-auto object-contain drop-shadow-xl hover:rotate-2 transition-transform duration-700" src="https://lh3.googleusercontent.com/aida-public/AB6AXuClVCUCHQNhHjvEgdaW1uUlXtPlyjRxBSBM1_OSAWmtvLtvde32hgnseTlYouDlg7L-HzP8HmJS2m-_VuLAb-ydMCiiQjbTRi9zSpJP297Ua04NQtMSjnWwMvj7q4Y9X_SiI9oqs1kuOVNUtsWNmdFv-UBr-DWfbsM7iPtY6PPe-pCjKUn33dkrLDG3dF2UOr6ncyi5u0Osv-s0YMm8DEWXDYlJfdnrBaKEO2lFw4IjD03ADXRkYY-Z5TuFFjhY8wYYcEBjv5ciQA4" />
                <div className="absolute inset-0 bg-primary/10 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <button className="bg-white text-primary px-6 py-3 rounded-full font-semibold shadow-xl flex items-center gap-2"><Icon name="3d_rotation" />查看 3D 全景</button>
                </div>
              </div>
            </div>
            <div className="bg-white p-8">
              <h4 className="font-hanken text-[20px] leading-7 font-semibold mb-6">工艺规范</h4>
              <div className="grid grid-cols-2 gap-6 mb-8">
                {bagSpecs.map((spec, i) => (
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
                  {[{label:'宽度',value:'350mm',pct:'20%'},{label:'高度',value:'400mm',pct:'40%'},{label:'侧边',value:'100mm',pct:'10%'}].map((dim,i)=>(
                    <div key={i} className="flex items-center gap-3">
                      <span className="font-jetbrains text-xs w-12">{dim.label}</span>
                      <div className="flex-1 h-px bg-outline-variant relative">
                        <div className="font-jetbrains absolute left-0 -top-2 px-2 bg-white text-[10px]" style={{marginLeft:dim.pct}}>{dim.value}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      <div className="fixed bottom-8 right-8 z-50 flex flex-col items-end gap-3">
        <button className="bg-secondary-container text-on-secondary-fixed w-14 h-14 rounded-full shadow-2xl flex items-center justify-center hover:scale-110 transition-transform active:scale-95 group relative">
          <Icon name="chat_bubble" />
          <span className="absolute right-16 bg-white px-3 py-1 rounded shadow-lg text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap text-on-background border border-outline-variant">咨询物料专家</span>
        </button>
        <div className="flex gap-3 bg-white p-2 rounded-xl shadow-2xl border border-outline-variant">
          <button className="bg-primary text-white px-8 py-3 rounded-lg font-semibold hover:bg-on-primary-fixed-variant transition-all active:scale-95 flex items-center gap-2"><Icon name="file_download" />一键打包下载 (124MB)</button>
        </div>
      </div>
    </div>
  </Layout>);
}
