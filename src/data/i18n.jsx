// Internationalization framework
const TRANSLATIONS = {
  'zh-CN': {
    app: { name: 'Miketv', subtitle: 'AI 视觉工厂', tagline: '视频与图像智能创作平台' },
    nav: { dashboard: '工作总览', workbench: 'AI 生图', video: '视频创作', materials: '物料库', brand: '品牌管理', history: '历史记录', admin: '管理控制台' },
    actions: { generate: '生成', download: '下载', save: '保存', delete: '删除', cancel: '取消', confirm: '确认', retry: '重试', share: '分享', edit: '编辑', view: '查看', close: '关闭', search: '搜索', upload: '上传', login: '登录', register: '注册', logout: '退出登录', subscribe: '立即订阅', start: '立即开始创作', preview: '预览' },
    workbench: { uploadKV: '拖放 / 点击上传主 KV 视觉设计图', themeTitle: '主题标题', themeSubtitle: '主题副标题', negativePrompt: '负面提示词', seed: '随机种子', analyzeModel: '分析模型', generateModel: '生图模型', targetMaterials: '目标物料', generateBtn: '一键生成', previewFirst: '预览首张', saveTemplate: '保存为模板', aiRecommend: 'AI 智能推荐', solutionPack: '行业方案包' },
    video: { textToVideo: '文生视频', imageToVideo: '图生视频', myVideos: '我的视频', script: 'AI 脚本', template: '快速模板', aspectRatio: '画面比例', duration: '时长', generateScript: 'AI 生成脚本', generateVideo: '开始生成视频' },
    dashboard: { welcome: '欢迎回来', newProject: '新建项目', uploadKV: '上传 KV', loadTemplate: '加载模板', viewHistory: '历史记录', videoCreate: '视频创作', onboarding: '快速开始' },
    quota: { used: '已用', remaining: '剩余', unlimited: '无限', upgrade: '升级套餐' },
    errors: { networkError: '网络连接失败', quotaExceeded: '配额不足，请升级套餐', generationFailed: '生成失败，请重试' },
  },
  en: {
    app: { name: 'Miketv', subtitle: 'AI Visual Factory', tagline: 'Video & Image Intelligent Creation Platform' },
    nav: { dashboard: 'Dashboard', workbench: 'AI Image', video: 'Video Studio', materials: 'Materials', brand: 'Brand Kit', history: 'History', admin: 'Admin' },
    actions: { generate: 'Generate', download: 'Download', save: 'Save', delete: 'Delete', cancel: 'Cancel', confirm: 'Confirm', retry: 'Retry', share: 'Share', edit: 'Edit', view: 'View', close: 'Close', search: 'Search', upload: 'Upload', login: 'Login', register: 'Register', logout: 'Logout', subscribe: 'Subscribe', start: 'Start Creating', preview: 'Preview' },
    workbench: { uploadKV: 'Drag & drop or click to upload KV design', themeTitle: 'Theme Title', themeSubtitle: 'Subtitle', negativePrompt: 'Negative Prompt', seed: 'Seed', analyzeModel: 'Analysis Model', generateModel: 'Generation Model', targetMaterials: 'Target Materials', generateBtn: 'Generate All', previewFirst: 'Preview First', saveTemplate: 'Save Template', aiRecommend: 'AI Recommendations', solutionPack: 'Solution Packs' },
    video: { textToVideo: 'Text to Video', imageToVideo: 'Image to Video', myVideos: 'My Videos', script: 'AI Script', template: 'Templates', aspectRatio: 'Aspect Ratio', duration: 'Duration', generateScript: 'Generate Script', generateVideo: 'Generate Video' },
    dashboard: { welcome: 'Welcome back', newProject: 'New Project', uploadKV: 'Upload KV', loadTemplate: 'Load Template', viewHistory: 'History', videoCreate: 'Video Studio', onboarding: 'Quick Start' },
    quota: { used: 'Used', remaining: 'Remaining', unlimited: 'Unlimited', upgrade: 'Upgrade Plan' },
    errors: { networkError: 'Network connection failed', quotaExceeded: 'Quota exceeded, please upgrade', generationFailed: 'Generation failed, please retry' },
  },
};

let currentLocale = 'zh-CN';

import { createContext, useContext, useState, useCallback } from 'react';

export const LocaleContext = createContext(null);
export const useLocale = () => useContext(LocaleContext) || { locale: 'zh-CN', t: (k) => k };

export function LocaleProvider({ children }) {
  const [locale, setLocaleState] = useState(() => {
    try { return localStorage.getItem('miketv_locale') || 'zh-CN'; } catch { return 'zh-CN'; }
  });

  const setLocale = useCallback((l) => {
    setLocaleState(l);
    try { localStorage.setItem('miketv_locale', l); } catch {}
  }, []);

  const t = useCallback((path) => {
    const keys = path.split('.');
    let value = TRANSLATIONS[locale] || TRANSLATIONS['zh-CN'];
    for (const key of keys) { value = value?.[key]; if (!value) break; }
    return value || path;
  }, [locale]);

  return (
    <LocaleContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </LocaleContext.Provider>
  );
}

export function setLocaleExternal(locale) {
  try { localStorage.setItem('miketv_locale', locale); } catch {}
}

export function getLocale() {
  try { return localStorage.getItem('miketv_locale') || 'zh-CN'; } catch { return 'zh-CN'; }
}

export function t(path) {
  const locale = getLocale();
  const keys = path.split('.');
  let value = TRANSLATIONS[locale] || TRANSLATIONS['zh-CN'];
  for (const key of keys) {
    value = value?.[key];
    if (!value) break;
  }
  return value || path;
}

export { TRANSLATIONS };
