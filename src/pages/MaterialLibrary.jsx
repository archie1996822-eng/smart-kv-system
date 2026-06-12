import { useState, useRef } from 'react';
import Layout, { Icon } from '../components/Layout';
import { loadMaterials, saveMaterial, loadCustomMaterials, saveCustomMaterial, deleteCustomMaterial } from '../data/store';

function ImageUpload({ image, onSet, itemName }) {
  const inputRef = useRef(null);
  const handleFile = (file) => {
    if (!file || !file.type.startsWith('image/')) return;
    const r = new FileReader();
    r.onload = (e) => onSet(e.target.result);
    r.readAsDataURL(file);
  };
  return (<div className="relative">
    <div onClick={() => inputRef.current?.click()}
      className={`w-full aspect-[1.6] rounded-lg border-2 border-dashed flex items-center justify-center cursor-pointer transition-all ${image ? 'border-primary bg-surface-container-low' : 'border-outline-variant hover:border-primary hover:bg-surface-container-low'}`}>
      {image ? (<img src={image} alt={itemName} className="w-full h-full object-contain rounded-lg" />)
      : (<div className="text-center p-2"><Icon name="add_photo_alternate" className="text-on-surface-variant text-2xl mb-1" /><p className="text-[10px] text-on-surface-variant">上传外观图</p></div>)}
    </div>
    {image && (<button onClick={(e) => { e.stopPropagation(); onSet(null); }} className="absolute top-1 right-1 bg-white/90 hover:bg-white p-1 rounded-full shadow"><Icon name="close" className="text-xs text-error" /></button>)}
    <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])} />
  </div>);
}

function MaterialCard({ item, onSave }) {
  const [image, setImage] = useState(item.appearanceImage);
  const [editMode, setEditMode] = useState(false);
  const [size, setSize] = useState(item.size);
  const [material, setMaterial] = useState(item.material);
  const [category, setCategory] = useState(item.category);

  const handleSave = () => {
    const data = { appearanceImage: image, size, material, category };
    saveMaterial(item.id, data);
    onSave();
    setEditMode(false);
  };

  return (<div className="bg-surface border border-outline-variant rounded-xl overflow-hidden hover:shadow-lg transition-all">
    <ImageUpload image={image} onSet={setImage} itemName={item.name} />
    <div className="p-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-hanken text-base font-semibold text-on-surface flex items-center gap-2">
          <Icon name={item.icon} className="text-primary text-[18px]" />{item.name}
        </h4>
        <button onClick={() => setEditMode(!editMode)} className="text-xs text-primary hover:underline">{editMode ? '取消' : '编辑'}</button>
      </div>
      {editMode ? (<div className="space-y-2">
        <div><label className="text-[10px] text-outline uppercase font-semibold">尺寸</label><input value={size} onChange={(e) => setSize(e.target.value)} className="w-full mt-0.5 px-2 py-1.5 bg-surface-container border border-outline-variant rounded text-xs focus:ring-1 focus:ring-primary outline-none" /></div>
        <div><label className="text-[10px] text-outline uppercase font-semibold">材质/工艺</label><input value={material} onChange={(e) => setMaterial(e.target.value)} className="w-full mt-0.5 px-2 py-1.5 bg-surface-container border border-outline-variant rounded text-xs focus:ring-1 focus:ring-primary outline-none" /></div>
        <div><label className="text-[10px] text-outline uppercase font-semibold">分类</label><select value={category} onChange={(e) => setCategory(e.target.value)} className="w-full mt-0.5 px-2 py-1.5 bg-surface-container border border-outline-variant rounded text-xs focus:ring-1 focus:ring-primary outline-none"><option>互动周边</option><option>场馆指引</option><option>基础物料</option></select></div>
        <button onClick={handleSave} className="w-full py-1.5 bg-primary text-on-primary text-xs font-semibold rounded-lg hover:bg-primary-container transition-all active:scale-95">保存配置</button>
      </div>) : (<div className="space-y-1 text-xs">
        <div className="flex justify-between"><span className="text-outline">尺寸</span><span className="font-jetbrains text-on-surface-variant">{size}</span></div>
        <div className="flex justify-between"><span className="text-outline">材质</span><span className="text-on-surface-variant truncate ml-2 max-w-[180px]">{material}</span></div>
        <div className="flex justify-between"><span className="text-outline">分类</span><span className="text-on-surface-variant">{category}</span></div>
        {image && <div className="pt-1"><span className="px-2 py-0.5 bg-green-100 text-green-700 text-[10px] rounded-full font-semibold">已有外观图</span></div>}
      </div>)}
    </div>
  </div>);
}

function AddNewForm({ onAdd }) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [size, setSize] = useState('');
  const [material, setMaterial] = useState('');
  const [category, setCategory] = useState('基础物料');
  const [appearanceImage, setAppearanceImage] = useState(null);
  const inputRef = useRef(null);

  const handleAdd = () => {
    if (!name.trim() || !size.trim()) return;
    const item = {
      id: 'custom_' + Date.now(),
      name: name.trim(), size: size.trim(),
      material: material.trim() || '待定',
      category, icon: 'add_circle',
      appearanceImage,
    };
    saveCustomMaterial(item);
    onAdd();
    setName(''); setSize(''); setMaterial(''); setAppearanceImage(null); setOpen(false);
  };

  const handleImage = (file) => {
    if (!file?.type.startsWith('image/')) return;
    const r = new FileReader();
    r.onload = e => setAppearanceImage(e.target.result);
    r.readAsDataURL(file);
  };

  if (!open) return (<button onClick={()=>setOpen(true)} className="bg-surface border-2 border-dashed border-outline-variant hover:border-primary rounded-xl p-8 flex flex-col items-center justify-center min-h-[200px] transition-all cursor-pointer group"><Icon name="add_circle" className="text-outline-variant group-hover:text-primary text-3xl mb-2 transition-colors" /><span className="text-on-surface-variant group-hover:text-primary font-semibold text-sm transition-colors">新增自定义物料</span></button>);

  return (<div className="bg-surface border-2 border-primary rounded-xl p-5 space-y-3">
    <div className="flex items-center justify-between"><h4 className="font-hanken font-semibold text-primary">新建物料</h4><button onClick={()=>setOpen(false)} className="text-xs text-on-surface-variant hover:text-error">取消</button></div>
    <input value={name} onChange={e=>setName(e.target.value)} placeholder="物料名称（必填）" className="w-full px-3 py-2 bg-surface-container border border-outline-variant rounded-lg text-sm focus:ring-1 focus:ring-primary outline-none" />
    <input value={size} onChange={e=>setSize(e.target.value)} placeholder="尺寸规格（必填）如：200×300mm" className="w-full px-3 py-2 bg-surface-container border border-outline-variant rounded-lg text-sm focus:ring-1 focus:ring-primary outline-none" />
    <input value={material} onChange={e=>setMaterial(e.target.value)} placeholder="材质工艺" className="w-full px-3 py-2 bg-surface-container border border-outline-variant rounded-lg text-sm focus:ring-1 focus:ring-primary outline-none" />
    <select value={category} onChange={e=>setCategory(e.target.value)} className="w-full px-3 py-2 bg-surface-container border border-outline-variant rounded-lg text-sm"><option>互动周边</option><option>场馆指引</option><option>基础物料</option></select>
    <div className="flex gap-2">
      <div onClick={()=>inputRef.current?.click()} className={`flex-1 border-2 border-dashed rounded-lg flex items-center justify-center cursor-pointer h-16 transition-all ${appearanceImage?'border-primary bg-surface-container-low':'border-outline-variant hover:border-primary'}`}>{appearanceImage?<img src={appearanceImage} alt="" className="h-full object-contain rounded" />:<span className="text-[10px] text-on-surface-variant">上传外观图</span>}</div>
      <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={e=>e.target.files[0]&&handleImage(e.target.files[0])} />
      <button onClick={handleAdd} className="px-6 py-2 bg-primary text-on-primary rounded-lg font-semibold text-sm hover:bg-primary-container transition-all active:scale-95">添加</button>
    </div>
  </div>);
}

function CustomMaterialCard({ item, onDelete, onRefresh }) {
  return (<div className="bg-surface border border-primary/30 rounded-xl overflow-hidden">
    <div className="aspect-[1.6] bg-surface-container-low flex items-center justify-center">{item.appearanceImage ? <img src={item.appearanceImage} alt="" className="w-full h-full object-contain" /> : <Icon name="add_circle" className="text-on-surface-variant text-3xl opacity-30" />}</div>
    <div className="p-3">
      <div className="flex items-center justify-between"><h4 className="font-hanken text-sm font-semibold text-on-surface">{item.name}</h4><button onClick={()=>{deleteCustomMaterial(item.id);onRefresh()}} className="text-[10px] text-error hover:underline">删除</button></div>
      <p className="font-jetbrains text-[10px] text-on-surface-variant mt-0.5">{item.size} · {item.material}</p>
      <span className="text-[9px] px-1.5 py-0.5 bg-primary/10 text-primary rounded-full mt-1 inline-block">自定义</span>
    </div>
  </div>);
}

export default function MaterialLibraryPage() {
  const [items, setItems] = useState(loadMaterials());
  const [customItems, setCustomItems] = useState(loadCustomMaterials());
  const [msg, setMsg] = useState('');
  const refresh = () => { setItems(loadMaterials()); setCustomItems(loadCustomMaterials()); setMsg('已保存'); setTimeout(()=>setMsg(''),2000); };

  return (<Layout>
    <div className="p-8 max-w-[1600px] mx-auto">
      <div className="flex items-end justify-between mb-6">
        <div><h2 className="font-hanken text-[24px] leading-8 font-semibold text-on-surface">物料库</h2><p className="text-on-surface-variant mt-1 text-sm">管理基础物料参数和外观形态图，可新增自定义物料（自动同步到工作台）</p></div>
        {msg && <span className="text-xs text-green-600 font-semibold">{msg}</span>}
      </div>

      {/* Preset materials */}
      <h3 className="font-hanken text-sm font-semibold text-outline uppercase tracking-wider mb-3">预设物料（12个）</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8">
        {items.map((item) => (<MaterialCard key={item.id} item={item} onSave={refresh} />))}
      </div>

      {/* Custom materials */}
      {customItems.length > 0 && (<><h3 className="font-hanken text-sm font-semibold text-outline uppercase tracking-wider mb-3">自定义物料（{customItems.length}个）</h3><div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8">{customItems.map(item=>(<CustomMaterialCard key={item.id} item={item} onDelete={()=>{deleteCustomMaterial(item.id);refresh()}} onRefresh={refresh} />))}</div></>)}

      {/* Add new */}
      <h3 className="font-hanken text-sm font-semibold text-outline uppercase tracking-wider mb-3">新增物料</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <AddNewForm onAdd={refresh} />
      </div>
    </div>
  </Layout>);
}
