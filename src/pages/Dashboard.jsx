import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout, { Icon, showToast } from '../components/Layout';
import { useUser } from '../data/auth';
import { getTodayStats, loadHistory } from '../data/store';
import { loadProjects, createProject, deleteProject, getProjectStats } from '../data/projects';
import { loadTemplates } from '../data/templates';
import { SkeletonStats, SkeletonCard } from '../components/Skeleton';
import ConfirmModal from '../components/ConfirmModal';

function StatCard({ label, value, unit, icon, color }) {
  return (
    <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-5 flex items-center gap-4">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${color} bg-opacity-10`} style={{ backgroundColor: 'var(--color-primary-container)' }}>
        <Icon name={icon} className={`text-2xl ${color}`} />
      </div>
      <div>
        <p className="text-xs text-on-surface-variant">{label}</p>
        <p className="font-hanken text-2xl font-bold text-on-surface">
          {value}<span className="text-sm font-normal text-on-surface-variant ml-1">{unit}</span>
        </p>
      </div>
    </div>
  );
}

function ProjectCard({ project, onEnter, onDeleteClick }) {
  return (
    <div className="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden hover:border-primary/50 hover:shadow-md transition-all group cursor-pointer" onClick={onEnter}>
      <div className="h-32 bg-surface-container flex items-center justify-center relative">
        {project.thumbnailUrl ? (
          <img src={project.thumbnailUrl} alt={project.name} className="w-full h-full object-cover" />
        ) : (
          <Icon name="folder" className="text-5xl text-outline-variant" />
        )}
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center">
          <span className="opacity-0 group-hover:opacity-100 bg-primary text-on-primary px-4 py-2 rounded-lg text-sm font-semibold transition-all">进入项目</span>
        </div>
      </div>
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <h4 className="font-semibold text-on-surface truncate">{project.name}</h4>
            <p className="text-xs text-on-surface-variant mt-1">{project.materialCount || 0} 个物料</p>
          </div>
          <button onClick={(e) => { e.stopPropagation(); onDeleteClick(project); }} className="p-1.5 hover:bg-error/10 rounded-full text-outline hover:text-error opacity-0 group-hover:opacity-100 transition-all shrink-0">
            <Icon name="delete" className="text-sm" />
          </button>
        </div>
        <p className="text-[10px] text-outline mt-3">{project.createdAt?.slice(0, 10)}</p>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const user = useUser();
  const navigate = useNavigate();
  const [stats, setStats] = useState({ todayCalls: 0, monthCalls: 0, todayCost: 0, monthCost: 0, totalCalls: 0, totalCost: 0 });
  const [projectStats, setProjectStats] = useState({ total: 0, active: 0, totalMaterials: 0 });
  const [projects, setProjects] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [history, setHistory] = useState([]);
  const [showNewProject, setShowNewProject] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState(null); // { id, name }

  useEffect(() => {
    setStats(getTodayStats());
    setProjectStats(getProjectStats());
    setProjects(loadProjects().slice(0, 6));
    setTemplates(loadTemplates());
    setHistory(loadHistory().slice(0, 5));
  }, []);

  const handleCreateProject = () => {
    if (!newProjectName.trim()) return;
    const proj = createProject({ name: newProjectName.trim() });
    setShowNewProject(false);
    setNewProjectName('');
    setProjects(loadProjects().slice(0, 6));
    setProjectStats(getProjectStats());
    showToast(`项目"${proj.name}"已创建`, 'success');
    navigate(`/workbench?project=${proj.id}`);
  };

  const handleDeleteProject = () => {
    if (!deleteConfirm) return;
    deleteProject(deleteConfirm.id);
    setProjects(loadProjects().slice(0, 6));
    setProjectStats(getProjectStats());
    showToast('项目已删除', 'success');
    setDeleteConfirm(null);
  };

  const handleEnterProject = (id) => {
    navigate(`/workbench?project=${id}`);
  };

  return (
    <Layout>
      <div className="p-4 md:p-8 max-w-[1440px] mx-auto">
        {/* Welcome */}
        <div className="mb-8">
          <h2 className="font-hanken text-[28px] leading-9 font-semibold text-on-surface">
            欢迎回来，{user?.displayName || '用户'}
          </h2>
          <p className="text-on-surface-variant mt-1">{new Date().toLocaleDateString('zh-CN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </div>

        {/* Onboarding checklist for new users */}
        {projects.length === 0 && history.length === 0 && (
          <div className="mb-8 bg-surface-container-lowest border border-primary/20 rounded-xl p-6">
            <h4 className="font-semibold text-on-surface mb-3 flex items-center gap-2">
              <Icon name="rocket_launch" className="text-primary" />快速开始
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {[
                { step: 1, icon: 'cloud_upload', title: '上传KV主视觉', desc: '在工作台上传你的品牌主视觉图', action: () => navigate('/workbench') },
                { step: 2, icon: 'psychology', title: 'AI 视觉分析', desc: '自动提取色板、字体、布局', action: () => navigate('/workbench') },
                { step: 3, icon: 'auto_awesome', title: '批量生成物料', desc: '一键生成 12+ 种周边物料', action: () => navigate('/workbench') },
                { step: 4, icon: 'bookmark', title: '保存模板', desc: '保存配置方便下次复用', action: () => navigate('/brand-kit') },
              ].map(item => (
                <button key={item.step} onClick={item.action} className="flex items-start gap-3 p-3 rounded-xl border border-outline-variant hover:border-primary hover:bg-primary/5 transition-all text-left group">
                  <div className="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center shrink-0 group-hover:bg-primary group-hover:text-on-primary transition-colors">
                    <Icon name={item.icon} className="text-lg" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-on-surface">第{item.step}步: {item.title}</p>
                    <p className="text-[10px] text-on-surface-variant mt-0.5">{item.desc}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard label="活跃项目" value={projectStats.active} unit="个" icon="folder" color="text-primary" />
          <StatCard label="物料总数" value={projectStats.totalMaterials} unit="个" icon="inventory_2" color="text-secondary" />
          <StatCard label="今日生成" value={stats.todayCalls} unit="次" icon="auto_awesome" color="text-tertiary" />
          <StatCard label="本月费用" value={`¥${stats.monthCost.toFixed(2)}`} unit="" icon="payments" color="text-primary" />
        </div>

        {/* Quick Actions */}
        <div className="flex flex-wrap gap-3 mb-8">
          <button onClick={() => setShowNewProject(true)} className="px-5 py-3 bg-primary text-on-primary rounded-xl font-semibold hover:shadow-lg active:scale-95 transition-all flex items-center gap-2">
            <Icon name="add" />新建项目
          </button>
          <button onClick={() => navigate('/workbench')} className="px-5 py-3 border border-primary text-primary rounded-xl font-semibold hover:bg-primary/10 active:scale-95 transition-all flex items-center gap-2">
            <Icon name="cloud_upload" />上传 KV
          </button>
          <button onClick={() => navigate('/brand-kit')} className="px-5 py-3 border border-outline-variant text-on-surface-variant rounded-xl font-semibold hover:bg-surface-container active:scale-95 transition-all flex items-center gap-2">
            <Icon name="auto_fix" />加载模板
          </button>
          <button onClick={() => navigate('/video-studio')} className="px-5 py-3 border border-outline-variant text-on-surface-variant rounded-xl font-semibold hover:bg-surface-container active:scale-95 transition-all flex items-center gap-2">
            <Icon name="videocam" />视频创作
          </button>
          <button onClick={() => navigate('/history')} className="px-5 py-3 border border-outline-variant text-on-surface-variant rounded-xl font-semibold hover:bg-surface-container active:scale-95 transition-all flex items-center gap-2">
            <Icon name="history" />历史记录
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Projects */}
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-hanken text-xl font-semibold text-on-surface">最近项目</h3>
              <button onClick={() => setShowNewProject(true)} className="text-sm text-primary hover:underline">+ 新建</button>
            </div>
            {projects.length === 0 ? (
              <div className="text-center py-16 bg-surface-container-lowest border border-dashed border-outline-variant rounded-xl">
                <Icon name="folder_open" className="text-5xl text-outline-variant mb-3" />
                <p className="text-on-surface-variant mb-4">还没有项目，创建一个开始吧</p>
                <button onClick={() => setShowNewProject(true)} className="px-6 py-2 bg-primary text-on-primary rounded-lg font-semibold hover:shadow">新建项目</button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {projects.map(p => (
                  <ProjectCard key={p.id} project={p} onEnter={() => handleEnterProject(p.id)} onDeleteClick={(proj) => setDeleteConfirm(proj)} />
                ))}
              </div>
            )}
          </div>

          {/* Sidebar: Templates + Recent Activity */}
          <div className="space-y-6">
            {/* Templates */}
            <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-5">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-sm text-on-surface">我的模板</h4>
                <span className="text-xs text-outline">{templates.length} 个</span>
              </div>
              {templates.length === 0 ? (
                <p className="text-xs text-on-surface-variant">暂无模板，在 Workbench 中保存</p>
              ) : (
                <div className="space-y-2">
                  {templates.slice(0, 5).map(t => (
                    <button key={t.id} onClick={() => {
                      localStorage.setItem('smart_kv_default_template_load', JSON.stringify({ theme: t.theme, subtitle: t.subtitle, visionModel: t.visionModel, genModel: t.genModel, selected: t.selected }));
                      navigate('/workbench');
                    }} className="w-full text-left px-3 py-2 rounded-lg hover:bg-surface-container transition-colors text-sm flex items-center gap-2">
                      <Icon name="bookmark" className="text-primary text-sm shrink-0" />
                      <span className="text-on-surface truncate">{t.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Recent Activity */}
            <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-5">
              <h4 className="font-semibold text-sm text-on-surface mb-3">最近生成</h4>
              {history.length === 0 ? (
                <p className="text-xs text-on-surface-variant">暂无记录</p>
              ) : (
                <div className="space-y-3">
                  {history.map((h, i) => (
                    <div key={i} className="flex items-center gap-3 text-sm">
                      <div className="w-10 h-10 rounded-lg bg-surface-container shrink-0 flex items-center justify-center overflow-hidden">
                        {h.kvThumbnail ? <img src={h.kvThumbnail} alt="" className="w-full h-full object-cover" /> : <Icon name="image" className="text-outline-variant" />}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-medium text-on-surface truncate">{h.theme || '未命名'}</p>
                        <p className="text-[10px] text-outline">{h.createdAt}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* New Project Modal */}
        {showNewProject && (
          <div className="fixed inset-0 z-[200] bg-black/60 flex items-center justify-center p-4" onClick={() => setShowNewProject(false)}>
            <div className="bg-surface rounded-2xl shadow-2xl max-w-md w-full p-6" onClick={e => e.stopPropagation()}>
              <h3 className="font-hanken text-lg font-semibold mb-4">新建项目</h3>
              <input
                className="w-full px-4 py-3 bg-surface-container border border-outline-variant rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary"
                placeholder="项目名称（例如：2024年度盛典）"
                value={newProjectName}
                onChange={e => setNewProjectName(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleCreateProject()}
                autoFocus
              />
              <div className="flex gap-3 mt-6">
                <button onClick={() => setShowNewProject(false)} className="flex-1 py-2.5 border border-outline-variant rounded-lg text-sm hover:bg-surface-container">取消</button>
                <button onClick={handleCreateProject} className="flex-1 py-2.5 bg-primary text-on-primary rounded-lg text-sm font-semibold hover:shadow">创建</button>
              </div>
            </div>
          </div>
        )}
      </div>
      <ConfirmModal open={!!deleteConfirm} onClose={() => setDeleteConfirm(null)} onConfirm={handleDeleteProject} title="删除项目" message={`确定删除项目"${deleteConfirm?.name}"？此操作不可撤销。`} confirmText="删除" variant="danger" icon="delete" />
    </Layout>
  );
}
