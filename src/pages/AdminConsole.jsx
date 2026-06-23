import { useState, useEffect } from 'react';
import Layout, { Icon, showToast } from '../components/Layout';
import ConfirmModal from '../components/ConfirmModal';
import { solutionPacks } from '../data/solutionPacks';
import { loadAllSpecs } from '../data/store';
import { listAllUsers } from '../data/auth';
import { getBackendStatus, exportAllData, cleanupOldData } from '../data/db';
import { getSupabaseConfig, testConnection } from '../data/supabase';
import { loadApprovals, approveItem, rejectItem } from '../data/collaboration';

// Default CMS data for homepage
const DEFAULT_CMS = {
  hero: { title: '专为设计小白打造的 AI 爆款视频工具', subtitle: '结合前沿 AI 模型与专业工作流，高效制作爆款视频。从 0 基础到爆款制造机，只需一键操作。', cta: '立即开始创作' },
  features: [
    { icon: 'design_services', title: '海报设计', desc: '专业模板一键生成，小白也能做出大牌感。' },
    { icon: 'inventory_2', title: '周边物料', desc: '品牌周边、宣传册、文化衫等全品类物料设计。' },
    { icon: 'description', title: '爆款脚本', desc: '深度洞察社交媒体热点，自动生成高转化脚本。' },
    { icon: 'movie_edit', title: '视频制作', desc: '智能剪辑与特效处理，快速产出高质量视频。' },
    { icon: 'aspect_ratio', title: '无线画布', desc: '突破次元限制，在无限空间中自由排版与创作。' },
    { icon: 'zoom_in', title: '图片放大', desc: 'AI超分技术，无损放大图片细节。' },
  ],
  pricing: [
    { name: '体验版', price: '免费', features: ['每月 10 次生成', '基础视觉分析', '标准物料模板', '3 天历史记录'], highlight: false },
    { name: '专业版', price: '¥99', features: ['每月 200 次生成', 'Gemini 2.5 Pro 分析', '全部物料类型', '30 天历史记录', '品牌资产管理'], highlight: true },
    { name: '企业版', price: '¥399', features: ['无限次生成', '全部 AI 模型', '团队协作与审批', 'API 接口对接', '专属客服支持'], highlight: false },
  ],
  faq: [
    { q: '生成一条视频需要多长时间？', a: '通常在 1-3 分钟内即可完成高质量视频的渲染与生成。' },
    { q: '自动去重功能能保证100%通过审核吗？', a: '我们的算法深度处理视频帧、音频和特效，极大提升了原创通过率。' },
  ],
};

function loadCMS() {
  try {
    const v = localStorage.getItem('smart_kv_cms_homepage');
    return v ? JSON.parse(v) : DEFAULT_CMS;
  } catch { return DEFAULT_CMS; }
}

function saveCMS(data) {
  localStorage.setItem('smart_kv_cms_homepage', JSON.stringify(data));
}

function EditableField({ label, value, onChange, multiline }) {
  return (
    <div className="mb-3">
      <label className="block text-[10px] text-outline uppercase font-semibold mb-1">{label}</label>
      {multiline ? (
        <textarea value={value} onChange={e => onChange(e.target.value)} className="w-full px-3 py-2 bg-surface border border-outline-variant rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary resize-y" rows={3} />
      ) : (
        <input value={value} onChange={e => onChange(e.target.value)} className="w-full px-3 py-2 bg-surface border border-outline-variant rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary" />
      )}
    </div>
  );
}

function EditableFeature({ feature, index, onChange, onDelete }) {
  return (
    <div className="p-4 bg-surface border border-outline-variant rounded-xl mb-2">
      <div className="flex gap-2 mb-2">
        <input value={feature.icon} onChange={e => onChange(index, 'icon', e.target.value)} className="w-1/4 px-2 py-1 bg-surface-container border border-outline-variant rounded text-xs font-mono" placeholder="图标" />
        <input value={feature.title} onChange={e => onChange(index, 'title', e.target.value)} className="flex-1 px-2 py-1 bg-surface-container border border-outline-variant rounded text-sm" placeholder="标题" />
        <button onClick={() => onDelete(index)} className="p-1 text-outline hover:text-error"><Icon name="delete" className="text-sm" /></button>
      </div>
      <input value={feature.desc} onChange={e => onChange(index, 'desc', e.target.value)} className="w-full px-2 py-1 bg-surface-container border border-outline-variant rounded text-xs" placeholder="描述" />
    </div>
  );
}

function EditablePricing({ plan, index, onChange }) {
  return (
    <div className={`p-4 bg-surface border rounded-xl mb-2 ${plan.highlight ? 'border-primary/50 bg-primary/5' : 'border-outline-variant'}`}>
      <div className="flex gap-2 mb-2">
        <input value={plan.name} onChange={e => onChange(index, 'name', e.target.value)} className="flex-1 px-2 py-1 bg-surface-container border border-outline-variant rounded text-sm" placeholder="方案名" />
        <input value={plan.price} onChange={e => onChange(index, 'price', e.target.value)} className="w-20 px-2 py-1 bg-surface-container border border-outline-variant rounded text-sm" placeholder="价格" />
        <label className="flex items-center gap-1 text-xs"><input type="checkbox" checked={plan.highlight} onChange={e => onChange(index, 'highlight', e.target.checked)} />推荐</label>
      </div>
      <input
        value={plan.features.join(', ')}
        onChange={e => onChange(index, 'features', e.target.value.split(/[,，]/).map(s => s.trim()).filter(Boolean))}
        className="w-full px-2 py-1 bg-surface-container border border-outline-variant rounded text-xs"
        placeholder="功能列表（逗号分隔）"
      />
    </div>
  );
}

function EditableFAQ({ faq, index, onChange, onDelete }) {
  return (
    <div className="p-3 bg-surface border border-outline-variant rounded-xl mb-2">
      <div className="flex justify-between mb-1">
        <input value={faq.q} onChange={e => onChange(index, 'q', e.target.value)} className="flex-1 px-2 py-1 bg-surface-container border border-outline-variant rounded text-sm font-semibold" placeholder="问题" />
        <button onClick={() => onDelete(index)} className="p-1 text-outline hover:text-error"><Icon name="delete" className="text-sm" /></button>
      </div>
      <input value={faq.a} onChange={e => onChange(index, 'a', e.target.value)} className="w-full px-2 py-1 bg-surface-container border border-outline-variant rounded text-xs" placeholder="回答" />
    </div>
  );
}

export default function AdminConsole() {
  const [cms, setCMS] = useState(DEFAULT_CMS);
  const [tab, setTab] = useState('hero');
  const [specs, setSpecs] = useState([]);
  const [users, setUsers] = useState([]);
  const [storageInfo, setStorageInfo] = useState({ used: 0, total: 5120, pct: 0 });
  const [resetConfirmOpen, setResetConfirmOpen] = useState(false);
  const [supabaseStatus, setSupabaseStatus] = useState(null);

  useEffect(() => {
    setCMS(loadCMS());
    setSpecs(loadAllSpecs());
    setUsers(listAllUsers());

    // Calculate storage usage
    let used = 0;
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith('smart_kv_')) {
        used += (localStorage.getItem(key) || '').length;
      }
    }
    setStorageInfo({ used, total: 5120 * 1024, pct: ((used / (5120 * 1024)) * 100).toFixed(1) });
  }, []);

  const updateCMS = (section, key, value) => {
    const newCMS = { ...cms, [section]: { ...cms[section], [key]: value } };
    setCMS(newCMS);
    saveCMS(newCMS);
    showToast(`${section}.${key} 已更新`, 'success');
  };

  const updateFeature = (index, key, value) => {
    const features = [...cms.features];
    features[index] = { ...features[index], [key]: value };
    updateCMS('features', null, features);
    setCMS({ ...cms, features });
  };

  const deleteFeature = (index) => {
    const features = cms.features.filter((_, i) => i !== index);
    setCMS({ ...cms, features });
    saveCMS({ ...cms, features });
  };

  const addFeature = () => {
    const features = [...cms.features, { icon: 'star', title: '新功能', desc: '描述' }];
    setCMS({ ...cms, features });
    saveCMS({ ...cms, features });
  };

  const updatePricing = (index, key, value) => {
    const pricing = [...cms.pricing];
    pricing[index] = { ...pricing[index], [key]: value };
    setCMS({ ...cms, pricing });
    saveCMS({ ...cms, pricing });
  };

  const updateFAQ = (index, key, value) => {
    const faq = [...cms.faq];
    faq[index] = { ...faq[index], [key]: value };
    setCMS({ ...cms, faq });
    saveCMS({ ...cms, faq });
  };

  const deleteFAQ = (index) => {
    const faq = cms.faq.filter((_, i) => i !== index);
    setCMS({ ...cms, faq });
    saveCMS({ ...cms, faq });
  };

  const addFAQ = () => {
    const faq = [...cms.faq, { q: '新问题', a: '新回答' }];
    setCMS({ ...cms, faq });
    saveCMS({ ...cms, faq });
  };

  const handleReset = () => {
    localStorage.removeItem('smart_kv_cms_homepage');
    setCMS(DEFAULT_CMS);
    setResetConfirmOpen(false);
    showToast('已恢复默认设置', 'success');
  };

  const handleExportData = () => {
    const data = {};
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith('smart_kv_')) {
        try { data[key] = JSON.parse(localStorage.getItem(key)); } catch { data[key] = localStorage.getItem(key); }
      }
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'miketv-backup-' + new Date().toISOString().slice(0, 10) + '.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('数据已导出', 'success');
  };

  const tabs = [
    { id: 'hero', label: 'Hero 区', icon: 'home' },
    { id: 'features', label: '功能卡片', icon: 'grid_view' },
    { id: 'pricing', label: '定价方案', icon: 'payments' },
    { id: 'faq', label: 'FAQ', icon: 'quiz' },
    { id: 'system', label: '系统', icon: 'settings' },
  ];

  return (
    <Layout>
      <div className="p-4 md:p-8 max-w-[1440px] mx-auto">
        <div className="mb-8 flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
          <div>
            <h2 className="font-hanken text-[24px] leading-8 font-semibold text-on-surface flex items-center gap-2">
              <Icon name="admin_panel_settings" className="text-primary text-3xl" />管理控制台
            </h2>
            <p className="text-on-surface-variant mt-1">CMS 主页管理 · 规格概览 · 用户管理 · 数据维护</p>
          </div>
          <div className="flex gap-2">
            <button onClick={handleExportData} className="px-4 py-2 border border-outline-variant rounded-lg text-sm hover:bg-surface-container flex items-center gap-1">
              <Icon name="download" className="text-sm" />导出备份
            </button>
            <button onClick={() => setResetConfirmOpen(true)} className="px-4 py-2 border border-error/50 text-error rounded-lg text-sm hover:bg-error/5 flex items-center gap-1">
              <Icon name="restart_alt" className="text-sm" />恢复默认
            </button>
          </div>
        </div>

        {/* Tab bar */}
        <div className="flex gap-1 mb-6 overflow-x-auto pb-2">
          {tabs.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)} className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all flex items-center gap-2 ${tab === t.id ? 'bg-primary text-on-primary' : 'text-on-surface-variant hover:bg-surface-container'}`}>
              <Icon name={t.icon} className="text-[16px]" />{t.label}
            </button>
          ))}
        </div>

        {/* Hero CMS */}
        {tab === 'hero' && (
          <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6">
            <h3 className="font-semibold text-lg mb-4">首页 Hero 区域</h3>
            <EditableField label="主标题" value={cms.hero.title} onChange={v => updateCMS('hero', 'title', v)} multiline />
            <EditableField label="副标题" value={cms.hero.subtitle} onChange={v => updateCMS('hero', 'subtitle', v)} multiline />
            <EditableField label="CTA 按钮文字" value={cms.hero.cta} onChange={v => updateCMS('hero', 'cta', v)} />
            <div className="mt-4 p-3 bg-surface rounded-lg border border-outline-variant">
              <p className="text-xs text-outline mb-2">预览效果:</p>
              <div className="bg-background rounded-lg p-6 text-center border border-outline-variant">
                <h1 className="text-2xl font-bold text-primary mb-2">{cms.hero.title}</h1>
                <p className="text-sm text-on-surface-variant mb-4">{cms.hero.subtitle}</p>
                <span className="inline-block px-6 py-2 bg-primary text-on-primary rounded-full text-sm font-semibold">{cms.hero.cta}</span>
              </div>
            </div>
          </div>
        )}

        {/* Features CMS */}
        {tab === 'features' && (
          <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-semibold text-lg">功能卡片 ({cms.features.length})</h3>
              <button onClick={addFeature} className="px-3 py-1.5 bg-primary text-on-primary rounded-lg text-sm flex items-center gap-1">
                <Icon name="add" className="text-sm" />新增
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {cms.features.map((f, i) => (
                <EditableFeature key={i} feature={f} index={i} onChange={updateFeature} onDelete={deleteFeature} />
              ))}
            </div>
          </div>
        )}

        {/* Pricing CMS */}
        {tab === 'pricing' && (
          <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6">
            <h3 className="font-semibold text-lg mb-4">定价方案</h3>
            {cms.pricing.map((p, i) => (
              <EditablePricing key={i} plan={p} index={i} onChange={updatePricing} />
            ))}
          </div>
        )}

        {/* FAQ CMS */}
        {tab === 'faq' && (
          <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-semibold text-lg">FAQ ({cms.faq.length})</h3>
              <button onClick={addFAQ} className="px-3 py-1.5 bg-primary text-on-primary rounded-lg text-sm flex items-center gap-1">
                <Icon name="add" className="text-sm" />新增
              </button>
            </div>
            {cms.faq.map((f, i) => (
              <EditableFAQ key={i} faq={f} index={i} onChange={updateFAQ} onDelete={deleteFAQ} />
            ))}
          </div>
        )}

        {/* System tab */}
        {tab === 'system' && (
          <div className="space-y-6">
            {/* Backend Status */}
            <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6">
              <h3 className="font-semibold text-lg mb-4">后端状态</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div className="p-3 bg-surface rounded-lg border border-outline-variant">
                  <p className="font-semibold text-on-surface">localStorage</p>
                  <p className="text-green-600 text-xs">✅ 已激活</p>
                  <p className="text-[10px] text-outline mt-1">元数据存储</p>
                </div>
                <div className="p-3 bg-surface rounded-lg border border-outline-variant">
                  <p className="font-semibold text-on-surface">IndexedDB</p>
                  <p className="text-green-600 text-xs">✅ 已激活</p>
                  <p className="text-[10px] text-outline mt-1">图片/视频 Blob 存储</p>
                </div>
                <div className="p-3 bg-surface rounded-lg border border-outline-variant">
                  <p className="font-semibold text-on-surface">Supabase</p>
                  <p className={`text-xs ${getSupabaseConfig().configured ? 'text-green-600' : 'text-amber-600'}`}>
                    {getSupabaseConfig().configured ? '✅ 已配置' : '⚠ 未配置'}
                  </p>
                  <p className="text-[10px] text-outline mt-1">{getSupabaseConfig().status}</p>
                  {getSupabaseConfig().configured && (
                    <div className="mt-2">
                      <button onClick={async () => {
                        setSupabaseStatus({ loading: true });
                        const result = await testConnection();
                        setSupabaseStatus(result);
                      }} className="px-2 py-1 bg-primary text-on-primary rounded text-[10px] font-semibold hover:shadow">
                        {supabaseStatus?.loading ? '测试中...' : '测试连接'}
                      </button>
                      {supabaseStatus && !supabaseStatus.loading && (
                        <p className={`text-[9px] mt-1 ${supabaseStatus.ok ? 'text-green-600' : 'text-error'}`}>
                          {supabaseStatus.ok ? supabaseStatus.message : supabaseStatus.error}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Storage */}
            <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6">
              <h3 className="font-semibold text-lg mb-4">存储用量</h3>
              <div className="flex items-center gap-4 mb-2">
                <div className="flex-1 h-4 bg-surface-container-high rounded-full overflow-hidden">
                  <div className={`h-full rounded-full transition-all ${storageInfo.pct > 80 ? 'bg-error' : storageInfo.pct > 50 ? 'bg-amber-500' : 'bg-primary'}`} style={{ width: `${Math.min(storageInfo.pct, 100)}%` }} />
                </div>
                <span className="font-jetbrains text-sm font-semibold">{storageInfo.pct}%</span>
              </div>
              <p className="text-xs text-on-surface-variant">
                已用 {(storageInfo.used / 1024).toFixed(1)} KB / {storageInfo.total / 1024} KB
                {storageInfo.pct > 80 && <span className="text-error ml-2">⚠ 存储空间即将耗尽，请导出备份或清理旧数据</span>}
              </p>
              <div className="flex gap-2 mt-3">
                <button onClick={handleExportData} className="px-3 py-1.5 border border-outline-variant rounded-lg text-xs hover:bg-surface-container flex items-center gap-1">
                  <Icon name="download" className="text-sm" />导出备份
                </button>
                <button onClick={() => {
                  const count = cleanupOldData(90);
                  showToast(`已清理 ${count} 条90天前的旧数据`, 'success');
                }} className="px-3 py-1.5 border border-outline-variant rounded-lg text-xs hover:bg-surface-container flex items-center gap-1">
                  <Icon name="cleaning_services" className="text-sm" />清理旧数据
                </button>
              </div>
            </div>

            {/* Users */}
            <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6">
              <h3 className="font-semibold text-lg mb-4">用户管理 ({users.length} 人)</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-outline-variant text-left text-outline">
                    <th className="py-2 pr-4">用户名</th><th className="py-2 pr-4">显示名</th><th className="py-2">角色</th>
                  </tr></thead>
                  <tbody>
                    {users.map(u => (
                      <tr key={u.username} className="border-b border-outline-variant/50">
                        <td className="py-2 pr-4 font-mono text-xs">{u.username}</td>
                        <td className="py-2 pr-4">{u.displayName}</td>
                        <td className="py-2"><span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${u.role === 'admin' ? 'bg-primary/10 text-primary' : 'bg-surface-container text-on-surface-variant'}`}>{u.role}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Approvals */}
            <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6">
              <h3 className="font-semibold text-lg mb-4">待审核 ({loadApprovals().filter(a=>a.status==='pending').length} 项)</h3>
              {loadApprovals().filter(a=>a.status==='pending').length === 0 ? (
                <p className="text-xs text-on-surface-variant">暂无待审核项目</p>
              ) : (
                <div className="space-y-2">
                  {loadApprovals().filter(a=>a.status==='pending').slice(0, 10).map(a => (
                    <div key={a.id} className="flex items-center gap-3 p-3 bg-surface rounded-lg border border-outline-variant">
                      {a.imageUrl && <img src={a.imageUrl} alt="" className="w-12 h-12 rounded object-cover" />}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-on-surface truncate">{a.projectName}</p>
                        <p className="text-[10px] text-outline">提交者: {a.submittedBy} · {a.submittedAt?.slice(0,10)}</p>
                      </div>
                      <button onClick={() => { approveItem(a.id, '管理员'); showToast('已通过', 'success'); }} className="px-3 py-1.5 bg-green-100 text-green-700 rounded-lg text-xs font-semibold hover:bg-green-200">通过</button>
                      <button onClick={() => { rejectItem(a.id, '管理员', '请修改后重新提交'); showToast('已驳回', 'info'); }} className="px-3 py-1.5 bg-red-100 text-red-700 rounded-lg text-xs font-semibold hover:bg-red-200">驳回</button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Specs overview */}
            <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6">
              <h3 className="font-semibold text-lg mb-4">物料规格概览 ({specs.length} 项)</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {specs.slice(0, 12).map(s => (
                  <div key={s.id} className="flex items-center gap-2 p-2 rounded-lg hover:bg-surface-container text-xs">
                    <Icon name={s.icon || 'image'} className="text-primary text-sm" />
                    <span className="text-on-surface">{s.name}</span>
                    <span className="text-outline font-mono">{s.width}×{s.height}</span>
                    <span className={`ml-auto px-1.5 py-0.5 rounded text-[9px] ${s.status === 'approved' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>{s.status}</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-outline mt-3">编辑规格请前往「物料库」页面</p>
            </div>
          </div>
        )}
      </div>
      <ConfirmModal open={resetConfirmOpen} onClose={() => setResetConfirmOpen(false)} onConfirm={handleReset} title="恢复默认设置" message="确定恢复默认设置？所有自定义内容将丢失。" confirmText="确定恢复" variant="danger" icon="warning" />
    </Layout>
  );
}
