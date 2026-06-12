import { useState } from 'react';
import Layout, { Icon } from '../components/Layout';
import { specData, statsData, extensionItems } from '../data/mockData';

const statusBadge = (status) => {
  switch (status) {
    case 'approved': return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">已核准</span>;
    case 'reviewing': return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">审核中</span>;
    case 'draft': return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">草稿</span>;
    default: return null;
  }
};

export default function SpecManagement() {
  const [currentPage, setCurrentPage] = useState(1);
  const [editData, setEditData] = useState({ name: '户外灯箱海报', width: 1200, height: 1800, material: 'PET背喷灯箱片' });

  return (<Layout>
    <div className="p-8 max-w-[1440px] mx-auto">
      <div className="mb-8 flex justify-between items-end">
        <div>
          <h2 className="font-hanken text-[24px] leading-8 font-semibold text-on-surface">尺寸与规格管理</h2>
          <p className="text-on-surface-variant mt-1">维护全局物料的标准尺寸、推荐材质与生产工艺参数。</p>
        </div>
        <div className="flex space-x-3">
          <button className="flex items-center space-x-2 px-4 py-2 border border-outline text-on-surface-variant rounded-lg hover:bg-surface-container transition-colors"><Icon name="filter_list" /><span>筛选</span></button>
          <button className="flex items-center space-x-2 px-4 py-2 border border-outline text-on-surface-variant rounded-lg hover:bg-surface-container transition-colors"><Icon name="download" /><span>下载配置</span></button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-8">
        {statsData.map((stat, i) => (
          <div key={i} className="bg-surface-container-lowest p-6 rounded-xl border border-outline-variant flex flex-col justify-between">
            <span className="text-on-surface-variant font-medium text-sm">{stat.label}</span>
            <div className="mt-4 flex items-baseline space-x-2">
              <span className={`font-hanken text-[48px] leading-[56px] font-bold tracking-[-0.02em] ${stat.color}`}>{stat.value}</span>
              <span className="text-on-surface-variant">{stat.unit}</span>
            </div>
          </div>
        ))}
        <div className="bg-surface-container-lowest p-6 rounded-xl border border-outline-variant flex items-center justify-center">
          <div className="text-center">
            <p className="text-on-surface-variant text-sm mb-2">更新于 2小时前</p>
            <button className="text-primary font-semibold flex items-center space-x-1 hover:underline"><span>查看同步日志</span><Icon name="arrow_forward" className="text-sm" /></button>
          </div>
        </div>
      </div>

      <div className="bg-surface-container-lowest rounded-xl border border-outline-variant overflow-hidden mb-8">
        <div className="overflow-x-auto custom-scrollbar">
          <table className="w-full text-left border-collapse">
            <thead><tr className="bg-surface-container text-on-surface-variant border-b border-outline-variant">
              <th className="px-6 py-4 font-semibold text-sm tracking-wider">物料名称</th><th className="px-6 py-4 font-semibold text-sm tracking-wider">建议尺寸 (mm/px)</th><th className="px-6 py-4 font-semibold text-sm tracking-wider">建议材质</th><th className="px-6 py-4 font-semibold text-sm tracking-wider">工艺要求</th><th className="px-6 py-4 font-semibold text-sm tracking-wider">状态</th><th className="px-6 py-4 font-semibold text-sm tracking-wider text-right">操作</th>
            </tr></thead>
            <tbody className="divide-y divide-outline-variant">
              {specData.map((row) => (
                <tr key={row.id} className="spec-table-row transition-colors cursor-pointer group">
                  <td className="px-6 py-5"><div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-primary-container/10 rounded-lg flex items-center justify-center text-primary"><Icon name={row.icon} /></div>
                    <div><p className="font-semibold text-on-surface">{row.name}</p><p className="text-xs text-on-surface-variant">CODE: {row.id}</p></div>
                  </div></td>
                  <td className="px-6 py-5"><span className="font-jetbrains text-xs bg-surface-container px-2 py-1 rounded">{row.size}</span></td>
                  <td className="px-6 py-5 text-on-surface-variant">{row.material}</td>
                  <td className="px-6 py-5"><div className="flex flex-wrap gap-2">{row.crafts.map((c, i) => (<span key={i} className="px-2 py-0.5 bg-secondary-container/20 text-secondary text-[11px] rounded border border-secondary-container">{c}</span>))}</div></td>
                  <td className="px-6 py-5">{statusBadge(row.status)}</td>
                  <td className="px-6 py-5 text-right"><div className="flex justify-end space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-2 hover:bg-surface-container rounded-full text-on-surface-variant transition-colors"><Icon name="edit" /></button>
                    <button className="p-2 hover:bg-error-container/20 hover:text-error rounded-full text-on-surface-variant transition-colors"><Icon name="delete" /></button>
                  </div></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="px-6 py-4 bg-surface-container-low border-t border-outline-variant flex items-center justify-between">
          <p className="text-xs text-on-surface-variant">显示 1-{specData.length} 条，共 124 条记录</p>
          <div className="flex space-x-1">
            <button className="w-8 h-8 flex items-center justify-center rounded border border-outline-variant hover:bg-surface-container transition-colors disabled:opacity-30" disabled><Icon name="chevron_left" /></button>
            {[1,2,3].map(p => (<button key={p} onClick={() => setCurrentPage(p)} className={`w-8 h-8 flex items-center justify-center rounded text-xs font-medium transition-colors ${currentPage===p?'bg-primary text-on-primary':'border border-outline-variant hover:bg-surface-container'}`}>{p}</button>))}
            <button className="w-8 h-8 flex items-center justify-center rounded border border-outline-variant hover:bg-surface-container transition-colors"><Icon name="chevron_right" /></button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 bg-surface-container-lowest p-8 rounded-xl border border-outline-variant">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-hanken text-[20px] leading-7 font-semibold text-on-surface">物料细节解析 (实时预览)</h3>
            <div className="flex items-center space-x-2 text-primary"><Icon name="auto_fix" /><span className="text-sm font-semibold">AI 智能辅助设定</span></div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-6">
              <div><label className="block text-sm font-semibold text-on-surface-variant mb-2">物料名称</label><input className="w-full px-4 py-3 bg-surface border border-outline-variant rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all" value={editData.name} onChange={(e) => setEditData({...editData, name: e.target.value})} /></div>
              <div className="grid grid-cols-2 gap-4">
                <div><label className="block text-sm font-semibold text-on-surface-variant mb-2">宽度 (mm)</label><div className="relative"><input className="w-full px-4 py-3 bg-surface border border-outline-variant rounded-lg focus:ring-2 focus:ring-primary outline-none transition-all" type="number" value={editData.width} onChange={(e) => setEditData({...editData, width: e.target.value})} /><span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-on-surface-variant font-jetbrains">mm</span></div></div>
                <div><label className="block text-sm font-semibold text-on-surface-variant mb-2">高度 (mm)</label><div className="relative"><input className="w-full px-4 py-3 bg-surface border border-outline-variant rounded-lg focus:ring-2 focus:ring-primary outline-none transition-all" type="number" value={editData.height} onChange={(e) => setEditData({...editData, height: e.target.value})} /><span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-on-surface-variant font-jetbrains">mm</span></div></div>
              </div>
              <div><label className="block text-sm font-semibold text-on-surface-variant mb-2">建议材质</label><select className="w-full px-4 py-3 bg-surface border border-outline-variant rounded-lg focus:ring-2 focus:ring-primary outline-none transition-all"><option>PET背喷灯箱片</option><option>PP背胶海报</option><option>157g 哑粉纸</option><option>铝合金板材</option></select></div>
            </div>
            <div className="bg-surface rounded-lg border border-dashed border-outline flex flex-col items-center justify-center p-6 relative">
              <div className="w-full aspect-[2/3] bg-white rounded shadow-lg border border-outline-variant flex flex-col items-center justify-center p-4 relative z-10">
                <div className="w-2/3 h-2/3 bg-surface-container-highest rounded border border-outline-variant flex items-center justify-center opacity-40"><Icon name="image" className="text-4xl" /></div>
                <div className="absolute inset-x-0 bottom-0 p-4 border-t border-outline-variant"><div className="w-full h-2 bg-surface-container rounded-full mb-2"></div><div className="w-2/3 h-2 bg-surface-container rounded-full"></div></div>
                <div className="absolute -left-6 top-0 bottom-0 flex flex-col items-center justify-center"><div className="w-px h-full bg-primary relative"><div className="absolute top-0 -left-1 w-2 h-px bg-primary"></div><div className="absolute bottom-0 -left-1 w-2 h-px bg-primary"></div></div><span className="absolute -left-14 font-jetbrains text-[10px] text-primary" style={{transform:'rotate(-90deg)'}}>{editData.height}mm</span></div>
                <div className="absolute -bottom-6 left-0 right-0 flex items-center justify-center"><div className="h-px w-full bg-primary relative"><div className="absolute left-0 -top-1 w-px h-2 bg-primary"></div><div className="absolute right-0 -top-1 w-px h-2 bg-primary"></div></div><span className="absolute -bottom-4 font-jetbrains text-[10px] text-primary">{editData.width}mm</span></div>
              </div>
              <p className="mt-8 text-xs text-on-surface-variant font-medium">预览比例: 1:15 (渲染自规格参数)</p>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-outline-variant flex justify-end space-x-4">
            <button className="px-6 py-2 border border-outline text-on-surface-variant rounded-lg hover:bg-surface-container transition-colors">重置修改</button>
            <button className="px-8 py-2 bg-primary text-on-primary rounded-lg font-semibold hover:shadow-lg active:scale-95 transition-all">保存规格更新</button>
          </div>
        </div>
        <div className="lg:col-span-1 bg-surface-container-lowest p-6 rounded-xl border border-outline-variant h-full">
          <h4 className="font-semibold text-on-surface mb-4">关联自动化延展</h4>
          <p className="text-xs text-on-surface-variant mb-6">基于当前规格，系统将自动适配以下子尺寸：</p>
          <div className="space-y-4">
            {extensionItems.map((item, i) => (
              <div key={i} className={`flex items-center p-3 bg-surface rounded-lg border border-outline-variant ${item.status==='pending'?'opacity-60':''}`}>
                <div className="w-12 h-12 bg-white rounded border border-outline-variant flex items-center justify-center mr-4"><Icon name={item.icon} className="text-primary" /></div>
                <div><p className="text-sm font-semibold">{item.name}</p><p className="font-jetbrains text-[10px] text-on-surface-variant">{item.size}</p></div>
                <Icon name={item.status==='ready'?'check_circle':'pending'} className={`ml-auto ${item.status==='ready'?'text-green-500':'text-on-surface-variant'}`} />
              </div>
            ))}
          </div>
          <div className="mt-8 p-4 bg-primary-container/10 rounded-lg border border-primary-container/20">
            <div className="flex items-start space-x-3"><Icon name="info" className="text-primary" /><p className="text-xs text-on-primary-container leading-relaxed">修改"户外灯箱海报"的比例可能会导致 3 个自动化工作流失效。建议在修改前先备份当前的延展逻辑。</p></div>
          </div>
        </div>
      </div>
    </div>
  </Layout>);
}
