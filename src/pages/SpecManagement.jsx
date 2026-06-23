import { useState, useEffect } from 'react';
import Layout, { Icon, showToast } from '../components/Layout';
import ConfirmModal from '../components/ConfirmModal';
import { loadAllSpecs, saveSpec, deleteSpec, addSpec, getSpecStats } from '../data/store';

const ITEMS_PER_PAGE = 8;

function statusBadge(status) {
  switch (status) {
    case 'approved': return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">已核准</span>;
    case 'reviewing': return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">审核中</span>;
    case 'draft': return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">草稿</span>;
    default: return null;
  }
}

export default function SpecManagement() {
  const [specs, setSpecs] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [filterStatus, setFilterStatus] = useState('all');
  const [showFilter, setShowFilter] = useState(false);
  const [editData, setEditData] = useState(null);
  const [editingSpec, setEditingSpec] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newSpec, setNewSpec] = useState({ name: '', icon: 'image', width: 800, height: 1200, material: '', crafts: '', category: '', status: 'draft' });
  const [stats, setStats] = useState({ total: 0, approved: 0, templates: 0, exceptionRate: '0%' });
  const [deleteSpecConfirm, setDeleteSpecConfirm] = useState(null);

  useEffect(() => {
    refreshData();
  }, []);

  const refreshData = () => {
    setSpecs(loadAllSpecs());
    setStats(getSpecStats());
  };

  // Filter & paginate
  const filtered = filterStatus === 'all' ? specs : specs.filter(s => s.status === filterStatus);
  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE);
  const pagedSpecs = filtered.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE);

  const handleEdit = (spec) => {
    setEditingSpec(spec.id);
    setEditData({ ...spec });
  };

  const handleSaveEdit = () => {
    if (!editData || !editingSpec) return;
    saveSpec(editData);
    setEditingSpec(null);
    setEditData(null);
    refreshData();
    showToast('规格已保存', 'success');
  };

  const handleDelete = () => {
    if (!deleteSpecConfirm) return;
    deleteSpec(deleteSpecConfirm);
    setDeleteSpecConfirm(null);
    refreshData();
    showToast('规格已删除', 'success');
  };

  const handleAdd = () => {
    const data = {
      ...newSpec,
      crafts: newSpec.crafts.split(/[,，]/).map(c => c.trim()).filter(Boolean),
      width: Number(newSpec.width),
      height: Number(newSpec.height),
    };
    if (!data.name || !data.material) { showToast('请填写名称和材质', 'error'); return; }
    addSpec(data);
    setShowAddForm(false);
    setNewSpec({ name: '', icon: 'image', width: 800, height: 1200, material: '', crafts: '', category: '', status: 'draft' });
    refreshData();
    showToast('新规格已添加', 'success');
  };

  const handleDownload = () => {
    const data = JSON.stringify(specs, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'spec-config.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('配置已下载', 'success');
  };

  return (<Layout>
    <div className="p-4 md:p-8 max-w-[1440px] mx-auto">
      <div className="mb-8 flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
        <div>
          <h2 className="font-hanken text-[24px] leading-8 font-semibold text-on-surface">尺寸与规格管理</h2>
          <p className="text-on-surface-variant mt-1">维护全局物料的标准尺寸、推荐材质与生产工艺参数。</p>
        </div>
        <div className="flex space-x-3">
          <div className="relative">
            <button onClick={() => setShowFilter(!showFilter)} className="flex items-center space-x-2 px-4 py-2 border border-outline text-on-surface-variant rounded-lg hover:bg-surface-container transition-colors"><Icon name="filter_list" /><span>筛选</span></button>
            {showFilter && (
              <div className="absolute top-full mt-2 right-0 bg-surface border border-outline-variant rounded-xl shadow-lg p-2 z-50 min-w-[160px]">
                {['all', 'approved', 'reviewing', 'draft'].map(s => (
                  <button key={s} onClick={() => { setFilterStatus(s); setCurrentPage(1); setShowFilter(false); }} className={`block w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${filterStatus===s?'bg-primary/10 text-primary font-semibold':'text-on-surface-variant hover:bg-surface-container'}`}>
                    {s==='all'?'全部':s==='approved'?'已核准':s==='reviewing'?'审核中':'草稿'}
                  </button>
                ))}
              </div>
            )}
          </div>
          <button onClick={handleDownload} className="flex items-center space-x-2 px-4 py-2 border border-outline text-on-surface-variant rounded-lg hover:bg-surface-container transition-colors"><Icon name="download" /><span>下载配置</span></button>
          <button onClick={() => setShowAddForm(true)} className="flex items-center space-x-2 px-4 py-2 bg-primary text-on-primary rounded-lg font-semibold hover:shadow-lg transition-all"><Icon name="add" /><span>新增</span></button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { label: '总物料规格', value: stats.total, unit: '项', color: 'text-primary' },
          { label: '活跃生产模板', value: stats.templates, unit: '套', color: 'text-secondary' },
          { label: '工艺异常率', value: stats.exceptionRate, unit: '', color: 'text-tertiary' },
          { label: '已核准', value: stats.approved, unit: '项', color: 'text-green-600' },
        ].map((stat, i) => (
          <div key={i} className="bg-surface-container-lowest p-6 rounded-xl border border-outline-variant flex flex-col justify-between">
            <span className="text-on-surface-variant font-medium text-sm">{stat.label}</span>
            <div className="mt-4 flex items-baseline space-x-2">
              <span className={`font-hanken text-[48px] leading-[56px] font-bold tracking-[-0.02em] ${stat.color}`}>{stat.value}</span>
              <span className="text-on-surface-variant">{stat.unit}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Add form modal */}
      {showAddForm && (
        <div className="fixed inset-0 z-[200] bg-black/60 flex items-center justify-center p-4" onClick={() => setShowAddForm(false)}>
          <div className="bg-surface rounded-2xl shadow-2xl max-w-md w-full p-6" onClick={e => e.stopPropagation()}>
            <h3 className="font-hanken text-lg font-semibold mb-4">新增物料规格</h3>
            <div className="space-y-3">
              <input className="w-full px-3 py-2 bg-surface-container border border-outline-variant rounded-lg text-sm" placeholder="物料名称 *" value={newSpec.name} onChange={e => setNewSpec({...newSpec, name: e.target.value})} />
              <div className="grid grid-cols-2 gap-3">
                <input className="w-full px-3 py-2 bg-surface-container border border-outline-variant rounded-lg text-sm" type="number" placeholder="宽度 mm" value={newSpec.width} onChange={e => setNewSpec({...newSpec, width: e.target.value})} />
                <input className="w-full px-3 py-2 bg-surface-container border border-outline-variant rounded-lg text-sm" type="number" placeholder="高度 mm" value={newSpec.height} onChange={e => setNewSpec({...newSpec, height: e.target.value})} />
              </div>
              <input className="w-full px-3 py-2 bg-surface-container border border-outline-variant rounded-lg text-sm" placeholder="建议材质 *" value={newSpec.material} onChange={e => setNewSpec({...newSpec, material: e.target.value})} />
              <input className="w-full px-3 py-2 bg-surface-container border border-outline-variant rounded-lg text-sm" placeholder="工艺要求 (逗号分隔)" value={newSpec.crafts} onChange={e => setNewSpec({...newSpec, crafts: e.target.value})} />
              <input className="w-full px-3 py-2 bg-surface-container border border-outline-variant rounded-lg text-sm" placeholder="分类" value={newSpec.category} onChange={e => setNewSpec({...newSpec, category: e.target.value})} />
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={() => setShowAddForm(false)} className="flex-1 py-2.5 border border-outline-variant rounded-lg text-sm hover:bg-surface-container">取消</button>
              <button onClick={handleAdd} className="flex-1 py-2.5 bg-primary text-on-primary rounded-lg text-sm font-semibold">添加</button>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-surface-container-lowest rounded-xl border border-outline-variant overflow-hidden mb-8">
        <div className="overflow-x-auto custom-scrollbar">
          <table className="w-full text-left border-collapse">
            <thead><tr className="bg-surface-container text-on-surface-variant border-b border-outline-variant">
              <th className="px-6 py-4 font-semibold text-sm tracking-wider">物料名称</th>
              <th className="px-6 py-4 font-semibold text-sm tracking-wider">尺寸</th>
              <th className="px-6 py-4 font-semibold text-sm tracking-wider">材质</th>
              <th className="px-6 py-4 font-semibold text-sm tracking-wider">工艺</th>
              <th className="px-6 py-4 font-semibold text-sm tracking-wider">状态</th>
              <th className="px-6 py-4 font-semibold text-sm tracking-wider text-right">操作</th>
            </tr></thead>
            <tbody className="divide-y divide-outline-variant">
              {pagedSpecs.map((row) => (
                <tr key={row.id} className="spec-table-row transition-colors cursor-pointer group">
                  <td className="px-6 py-5">
                    {editingSpec === row.id ? (
                      <input className="px-2 py-1 bg-surface border border-outline-variant rounded text-sm w-full" value={editData?.name || ''} onChange={e => setEditData({...editData, name: e.target.value})} />
                    ) : (
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-primary-container/10 rounded-lg flex items-center justify-center text-primary"><Icon name={row.icon || 'image'} /></div>
                        <div><p className="font-semibold text-on-surface">{row.name}</p><p className="text-xs text-on-surface-variant">CODE: {row.id}</p></div>
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-5">
                    {editingSpec === row.id ? (
                      <div className="flex gap-1"><input className="w-16 px-1 py-0.5 bg-surface border border-outline-variant rounded text-xs font-jetbrains" type="number" value={editData?.width || 0} onChange={e => setEditData({...editData, width: Number(e.target.value)})} /><span className="text-xs text-outline">×</span><input className="w-16 px-1 py-0.5 bg-surface border border-outline-variant rounded text-xs font-jetbrains" type="number" value={editData?.height || 0} onChange={e => setEditData({...editData, height: Number(e.target.value)})} /></div>
                    ) : (
                      <span className="font-jetbrains text-xs bg-surface-container px-2 py-1 rounded">{row.width} × {row.height} mm</span>
                    )}
                  </td>
                  <td className="px-6 py-5 text-on-surface-variant">
                    {editingSpec === row.id ? (
                      <input className="px-2 py-1 bg-surface border border-outline-variant rounded text-sm w-full" value={editData?.material || ''} onChange={e => setEditData({...editData, material: e.target.value})} />
                    ) : row.material}
                  </td>
                  <td className="px-6 py-5">
                    {editingSpec === row.id ? (
                      <input className="px-2 py-1 bg-surface border border-outline-variant rounded text-sm w-full" value={(editData?.crafts || []).join(', ')} onChange={e => setEditData({...editData, crafts: e.target.value.split(/[,，]/).map(c => c.trim()).filter(Boolean)})} />
                    ) : (
                      <div className="flex flex-wrap gap-2">{(row.crafts || []).map((c, i) => (<span key={i} className="px-2 py-0.5 bg-secondary-container/20 text-secondary text-[11px] rounded border border-secondary-container">{c}</span>))}</div>
                    )}
                  </td>
                  <td className="px-6 py-5">
                    {editingSpec === row.id ? (
                      <select className="px-2 py-1 bg-surface border border-outline-variant rounded text-xs" value={editData?.status || 'draft'} onChange={e => setEditData({...editData, status: e.target.value})}>
                        <option value="approved">已核准</option><option value="reviewing">审核中</option><option value="draft">草稿</option>
                      </select>
                    ) : statusBadge(row.status)}
                  </td>
                  <td className="px-6 py-5 text-right">
                    {editingSpec === row.id ? (
                      <div className="flex justify-end space-x-2">
                        <button onClick={handleSaveEdit} className="px-3 py-1.5 bg-primary text-on-primary text-xs rounded-lg hover:shadow">保存</button>
                        <button onClick={() => { setEditingSpec(null); setEditData(null); }} className="px-3 py-1.5 border border-outline-variant text-xs rounded-lg hover:bg-surface-container">取消</button>
                      </div>
                    ) : (
                      <div className="flex justify-end space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button onClick={() => handleEdit(row)} className="p-2 hover:bg-surface-container rounded-full text-on-surface-variant transition-colors"><Icon name="edit" /></button>
                        <button onClick={() => setDeleteSpecConfirm(row.id)} className="p-2 hover:bg-error-container/20 hover:text-error rounded-full text-on-surface-variant transition-colors"><Icon name="delete" /></button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
              {pagedSpecs.length === 0 && (
                <tr><td colSpan={6} className="px-6 py-12 text-center text-on-surface-variant">暂无匹配的规格数据</td></tr>
              )}
            </tbody>
          </table>
        </div>
        {/* Pagination */}
        <div className="px-6 py-4 bg-surface-container-low border-t border-outline-variant flex items-center justify-between">
          <p className="text-xs text-on-surface-variant">
            显示 {(currentPage-1)*ITEMS_PER_PAGE+1}-{Math.min(currentPage*ITEMS_PER_PAGE, filtered.length)} 条，共 {filtered.length} 条
          </p>
          <div className="flex space-x-1">
            <button onClick={() => setCurrentPage(p => Math.max(1, p-1))} disabled={currentPage===1} className="w-8 h-8 flex items-center justify-center rounded border border-outline-variant hover:bg-surface-container transition-colors disabled:opacity-30"><Icon name="chevron_left" /></button>
            {Array.from({length: totalPages}, (_, i) => i+1).slice(Math.max(0, currentPage-3), Math.min(totalPages, currentPage+2)).map(p => (
              <button key={p} onClick={() => setCurrentPage(p)} className={`w-8 h-8 flex items-center justify-center rounded text-xs font-medium transition-colors ${currentPage===p?'bg-primary text-on-primary':'border border-outline-variant hover:bg-surface-container'}`}>{p}</button>
            ))}
            <button onClick={() => setCurrentPage(p => Math.min(totalPages, p+1))} disabled={currentPage===totalPages} className="w-8 h-8 flex items-center justify-center rounded border border-outline-variant hover:bg-surface-container transition-colors disabled:opacity-30"><Icon name="chevron_right" /></button>
          </div>
        </div>
      </div>

      {/* Preview & Edit Panel */}
      {editData && editingSpec && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 bg-surface-container-lowest p-8 rounded-xl border border-outline-variant">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-hanken text-[20px] leading-7 font-semibold text-on-surface">物料细节解析 (实时预览)</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-6">
                <div><label className="block text-sm font-semibold text-on-surface-variant mb-2">物料名称</label><input className="w-full px-4 py-3 bg-surface border border-outline-variant rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all" value={editData.name} onChange={(e) => setEditData({...editData, name: e.target.value})} /></div>
                <div className="grid grid-cols-2 gap-4">
                  <div><label className="block text-sm font-semibold text-on-surface-variant mb-2">宽度 (mm)</label><input className="w-full px-4 py-3 bg-surface border border-outline-variant rounded-lg focus:ring-2 focus:ring-primary outline-none transition-all" type="number" value={editData.width} onChange={(e) => setEditData({...editData, width: Number(e.target.value)})} /></div>
                  <div><label className="block text-sm font-semibold text-on-surface-variant mb-2">高度 (mm)</label><input className="w-full px-4 py-3 bg-surface border border-outline-variant rounded-lg focus:ring-2 focus:ring-primary outline-none transition-all" type="number" value={editData.height} onChange={(e) => setEditData({...editData, height: Number(e.target.value)})} /></div>
                </div>
                <div><label className="block text-sm font-semibold text-on-surface-variant mb-2">建议材质</label><input className="w-full px-4 py-3 bg-surface border border-outline-variant rounded-lg focus:ring-2 focus:ring-primary outline-none transition-all" value={editData.material} onChange={(e) => setEditData({...editData, material: e.target.value})} /></div>
              </div>
              <div className="bg-surface rounded-lg border border-dashed border-outline flex flex-col items-center justify-center p-6 relative">
                <div className="w-full aspect-[2/3] bg-white rounded shadow-lg border border-outline-variant flex flex-col items-center justify-center p-4 relative z-10" style={{maxWidth: editData.width / 10, maxHeight: editData.height / 10}}>
                  <div className="w-2/3 h-2/3 bg-surface-container-highest rounded border border-outline-variant flex items-center justify-center opacity-40"><Icon name="image" className="text-4xl" /></div>
                  <div className="absolute inset-x-0 bottom-0 p-4 border-t border-outline-variant"><div className="w-full h-2 bg-surface-container rounded-full mb-2"></div></div>
                  <div className="absolute -left-6 top-0 bottom-0 flex flex-col items-center justify-center">
                    <span className="absolute -left-14 font-jetbrains text-[10px] text-primary" style={{transform:'rotate(-90deg)'}}>{editData.height}mm</span>
                  </div>
                  <div className="absolute -bottom-6 left-0 right-0 flex items-center justify-center">
                    <span className="absolute -bottom-4 font-jetbrains text-[10px] text-primary">{editData.width}mm</span>
                  </div>
                </div>
                <p className="mt-8 text-xs text-on-surface-variant font-medium">预览比例: ≈1:15</p>
              </div>
            </div>
            <div className="mt-8 pt-8 border-t border-outline-variant flex justify-end space-x-4">
              <button onClick={() => { handleEdit(specs.find(s => s.id === editingSpec)); }} className="px-6 py-2 border border-outline text-on-surface-variant rounded-lg hover:bg-surface-container transition-colors">重置修改</button>
              <button onClick={handleSaveEdit} className="px-8 py-2 bg-primary text-on-primary rounded-lg font-semibold hover:shadow-lg active:scale-95 transition-all">保存规格更新</button>
            </div>
          </div>
          <div className="lg:col-span-1 bg-surface-container-lowest p-6 rounded-xl border border-outline-variant h-full">
            <h4 className="font-semibold text-on-surface mb-4">关联自动化延展</h4>
            <p className="text-xs text-on-surface-variant mb-6">基于当前规格，系统将自动适配以下子尺寸：</p>
            <div className="space-y-4">
              {[
                { name: '朋友圈海报', size: '1080 × 1920 px', icon: 'phone_iphone' },
                { name: '网页横幅', size: '1920 × 600 px', icon: 'web' },
                { name: '圆形贴纸', size: '200 × 200 mm', icon: 'lens' },
              ].map((item, i) => (
                <div key={i} className="flex items-center p-3 bg-surface rounded-lg border border-outline-variant">
                  <div className="w-12 h-12 bg-white rounded border border-outline-variant flex items-center justify-center mr-4"><Icon name={item.icon} className="text-primary" /></div>
                  <div><p className="text-sm font-semibold">{item.name}</p><p className="font-jetbrains text-[10px] text-on-surface-variant">{item.size}</p></div>
                  <Icon name="check_circle" className="ml-auto text-green-500" />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  </Layout>);
}
