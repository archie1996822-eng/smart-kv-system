import { useState, useEffect } from 'react';
import Layout, { Icon, showToast } from '../components/Layout';
import { loadBrandKit, saveBrandKit, importFromAnalysis } from '../data/brandKit';
import { loadTemplates, deleteTemplate, createTemplateFromWorkbench } from '../data/templates';
import { loadWorkbenchState } from '../data/store';

export default function BrandKit() {
  const [kit, setKit] = useState(null);
  const [newColor, setNewColor] = useState('#');
  const [newFont, setNewFont] = useState('');
  const [newTheme, setNewTheme] = useState('');
  const [logoDataUrl, setLogoDataUrl] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [newTemplateName, setNewTemplateName] = useState('');
  const [showImportAnalysis, setShowImportAnalysis] = useState(false);

  useEffect(() => {
    setKit(loadBrandKit());
    setTemplates(loadTemplates());
  }, []);

  const handleSave = () => {
    if (!kit) return;
    saveBrandKit(kit);
    showToast('品牌资产已保存', 'success');
  };

  const addColor = () => {
    if (!newColor || newColor.length < 4) return;
    setKit(k => ({ ...k, colors: [...k.colors, newColor].slice(0, 10) }));
    setNewColor('#');
  };

  const removeColor = (i) => {
    setKit(k => ({ ...k, colors: k.colors.filter((_, idx) => idx !== i) }));
  };

  const addFont = () => {
    if (!newFont.trim()) return;
    setKit(k => ({ ...k, fonts: [...k.fonts, newFont.trim()].slice(0, 10) }));
    setNewFont('');
  };

  const removeFont = (i) => {
    setKit(k => ({ ...k, fonts: k.fonts.filter((_, idx) => idx !== i) }));
  };

  const addTheme = () => {
    if (!newTheme.trim()) return;
    setKit(k => ({ ...k, themes: [...k.themes, newTheme.trim()].slice(0, 20) }));
    setNewTheme('');
  };

  const removeTheme = (i) => {
    setKit(k => ({ ...k, themes: k.themes.filter((_, idx) => idx !== i) }));
  };

  const handleLogoUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      setLogoDataUrl(ev.target.result);
      setKit(k => ({ ...k, logoUrl: ev.target.result }));
    };
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  const handleImportAnalysis = () => {
    const saved = loadWorkbenchState();
    if (!saved?.analysis) {
      showToast('没有可用的分析数据，请先在 Workbench 中分析KV图', 'error');
      return;
    }
    const updated = importFromAnalysis(saved.analysis);
    setKit(updated);
    showToast('已从分析结果导入色板和字体', 'success');
  };

  const handleLoadTemplate = (tpl) => {
    // Save template data to localStorage for Workbench to pick up
    const state = {
      theme: tpl.theme || '',
      subtitle: tpl.subtitle || '',
      visionModel: tpl.visionModel || '',
      genModel: tpl.genModel || '',
      selected: tpl.selected || [],
    };
    localStorage.setItem('smart_kv_' + (kit?.name || 'default') + '_template_load', JSON.stringify(state));
    showToast(`已加载模板"${tpl.name}"，请前往 Workbench`, 'success');
  };

  const handleDeleteTemplate = (id) => {
    if (!confirm('确定删除此模板？')) return;
    deleteTemplate(id);
    setTemplates(loadTemplates());
    showToast('模板已删除', 'success');
  };

  if (!kit) return <Layout><div className="p-8">加载中...</div></Layout>;

  return (<Layout>
    <div className="p-4 md:p-8 max-w-[1440px] mx-auto">
      <div className="mb-8 flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
        <div>
          <h2 className="font-hanken text-[24px] leading-8 font-semibold text-on-surface">品牌资产管理</h2>
          <p className="text-on-surface-variant mt-1">管理品牌色板、字体和Logo，供 AI 生成时自动调用。</p>
        </div>
        <div className="flex gap-3">
          <button onClick={handleImportAnalysis} className="px-4 py-2 border border-primary text-primary rounded-lg text-sm font-medium hover:bg-primary/10 transition-all flex items-center gap-2"><Icon name="auto_fix" />从分析导入</button>
          <button onClick={handleSave} className="px-6 py-2 bg-primary text-on-primary rounded-lg font-semibold hover:shadow-lg transition-all">保存修改</button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Colors */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6">
          <h3 className="font-hanken text-lg font-semibold mb-4 flex items-center gap-2"><Icon name="palette" className="text-primary" />品牌色板</h3>
          <div className="flex flex-wrap gap-2 mb-4">
            {kit.colors.map((c, i) => (
              <div key={i} className="relative group">
                <div className="w-12 h-12 rounded-lg border border-outline-variant shadow-sm" style={{ backgroundColor: c }} />
                <button onClick={() => removeColor(i)} className="absolute -top-1 -right-1 w-5 h-5 bg-error text-white rounded-full text-[10px] opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">×</button>
                <p className="font-jetbrains text-[9px] text-on-surface-variant mt-1 text-center">{c}</p>
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <input className="flex-1 px-3 py-2 bg-surface border border-outline-variant rounded-lg text-sm font-jetbrains" placeholder="#HEX颜色" value={newColor} onChange={e => setNewColor(e.target.value)} onKeyDown={e => e.key === 'Enter' && addColor()} />
            <button onClick={addColor} className="px-4 py-2 bg-primary text-on-primary rounded-lg text-sm">添加</button>
          </div>
        </div>

        {/* Fonts */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6">
          <h3 className="font-hanken text-lg font-semibold mb-4 flex items-center gap-2"><Icon name="font_download" className="text-primary" />品牌字体</h3>
          <div className="flex flex-wrap gap-2 mb-4">
            {kit.fonts.map((f, i) => (
              <span key={i} className="inline-flex items-center gap-1 px-3 py-1.5 bg-surface-container rounded-lg border border-outline-variant text-sm group">
                {f}
                <button onClick={() => removeFont(i)} className="text-outline hover:text-error opacity-0 group-hover:opacity-100 transition-opacity">×</button>
              </span>
            ))}
          </div>
          <div className="flex gap-2">
            <input className="flex-1 px-3 py-2 bg-surface border border-outline-variant rounded-lg text-sm" placeholder="字体名称" value={newFont} onChange={e => setNewFont(e.target.value)} onKeyDown={e => e.key === 'Enter' && addFont()} />
            <button onClick={addFont} className="px-4 py-2 bg-primary text-on-primary rounded-lg text-sm">添加</button>
          </div>
        </div>

        {/* Logo */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6">
          <h3 className="font-hanken text-lg font-semibold mb-4 flex items-center gap-2"><Icon name="image" className="text-primary" />品牌 Logo</h3>
          {(kit.logoUrl || logoDataUrl) ? (
            <div className="relative inline-block group">
              <img src={kit.logoUrl || logoDataUrl} alt="Brand Logo" className="h-20 rounded-lg border border-outline-variant bg-white p-2 object-contain" />
              <button onClick={() => { setLogoDataUrl(null); setKit(k => ({ ...k, logoUrl: null })); }} className="absolute -top-2 -right-2 w-6 h-6 bg-error text-white rounded-full text-xs opacity-0 group-hover:opacity-100 transition-opacity">×</button>
            </div>
          ) : (
            <label className="inline-flex flex-col items-center justify-center w-32 h-20 border-2 border-dashed border-outline-variant rounded-lg cursor-pointer hover:border-primary transition-colors">
              <Icon name="cloud_upload" className="text-outline-variant text-2xl" />
              <span className="text-[10px] text-outline">上传 Logo</span>
              <input type="file" accept="image/*" className="hidden" onChange={handleLogoUpload} />
            </label>
          )}
        </div>

        {/* Themes */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6">
          <h3 className="font-hanken text-lg font-semibold mb-4 flex items-center gap-2"><Icon name="bookmark" className="text-primary" />常用主题</h3>
          <div className="flex flex-wrap gap-2 mb-4">
            {kit.themes.map((t, i) => (
              <span key={i} className="inline-flex items-center gap-1 px-3 py-1.5 bg-primary-fixed/10 border border-primary/20 rounded-lg text-sm text-primary group">
                {t}
                <button onClick={() => removeTheme(i)} className="text-outline hover:text-error opacity-0 group-hover:opacity-100 transition-opacity">×</button>
              </span>
            ))}
          </div>
          <div className="flex gap-2">
            <input className="flex-1 px-3 py-2 bg-surface border border-outline-variant rounded-lg text-sm" placeholder="新主题" value={newTheme} onChange={e => setNewTheme(e.target.value)} onKeyDown={e => e.key === 'Enter' && addTheme()} />
            <button onClick={addTheme} className="px-4 py-2 bg-primary text-on-primary rounded-lg text-sm">添加</button>
          </div>
        </div>
      </div>

      {/* Templates Section */}
      <div className="mt-10">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-hanken text-[24px] leading-8 font-semibold text-on-surface">工作台模板</h2>
          <span className="text-sm text-on-surface-variant">{templates.length} 个模板</span>
        </div>
        {templates.length === 0 ? (
          <div className="text-center py-12 bg-surface-container-lowest border border-dashed border-outline-variant rounded-xl">
            <Icon name="dashboard_customize" className="text-4xl text-outline-variant mb-2" />
            <p className="text-on-surface-variant">暂无模板。在 Workbench 中配置好参数后可保存为模板。</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map(tpl => (
              <div key={tpl.id} className="bg-surface-container-lowest border border-outline-variant rounded-xl p-5 hover:border-primary/50 transition-all">
                <h4 className="font-semibold text-on-surface mb-2">{tpl.name}</h4>
                <div className="space-y-1 text-xs text-on-surface-variant mb-3">
                  <p>主题: {tpl.theme || '未设置'}</p>
                  <p>物料数: {tpl.selected?.length || 0} 个</p>
                  <p className="text-outline">创建于 {tpl.createdAt?.slice(0, 10)}</p>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleLoadTemplate(tpl)} className="flex-1 py-2 bg-primary/10 text-primary rounded-lg text-sm font-medium hover:bg-primary/20">加载模板</button>
                  <button onClick={() => handleDeleteTemplate(tpl.id)} className="px-3 py-2 border border-outline-variant rounded-lg text-sm text-outline hover:text-error hover:border-error/50"><Icon name="delete" className="text-sm" /></button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  </Layout>);
}
