---
priority: P0
last_verified: 2026-06-24
auto_generated_from: src/App.jsx, src/pages/*.jsx, src/data/*.js
version: 1
---

# 功能状态矩阵

图例: ✅ 已完成 | 🟡 框架就绪等API | 🔴 未做 | ❌ 已移除

## 页面

| 路由 | 页面 | 状态 | 说明 |
|------|------|------|------|
| `/` | Home (营销页) | ✅ | CMS 可编辑 |
| `/login` | Login | ✅ | Tailwind + Miketv 品牌 |
| `/app` | Dashboard | ✅ | 项目/统计/快捷操作/Onboarding |
| `/workbench` | AI 生图 | ✅ | 上传KV→分析→批量生成 |
| `/video-studio` | 视频创作 | 🟡 | 框架就绪，等中转站 API |
| `/material-lib` | 物料库 | ✅ | CRUD |
| `/brand-kit` | 品牌管理 | ✅ | 色板/字体/Logo/主题 |
| `/history` | 历史记录 | ✅ | 查看/恢复/版本对比 |
| `/admin` | 管理控制台 | ✅ | CMS + 用户 + 存储 + 审批 |
| `/export-center` | 导出中心 | ✅ | 手举牌/袋型/生产对接 |
| `/share/:key` | 分享查看 | ✅ | 无需登录 |

## 核心功能

| 功能 | 状态 | 模块 |
|------|------|------|
| AI 图像分析 (Gemini) | ✅ | stitchApi.js |
| AI 物料生成 (Nano Banana + GPT-Image 2) | ✅ | stitchApi.js |
| A/B 变体生成 (1-4) | ✅ | Workbench |
| 负面提示词 + Seed | ✅ | Workbench |
| 质量评分 A/B/C | ✅ | qualityCheck.js |
| AI 智能推荐物料 | ✅ | recommendations.js |
| AI 文案生成 (5 个 LLM) | ✅ | stitchApi.js |
| 图片编辑 (文字/去底/放大) | ✅ | ImageEditor.jsx |
| 多格式导出 PNG/JPEG/WebP | ✅ | exportUtils.js |
| 批量下载 + 分享 | ✅ | Workbench |
| 收藏系统 | ✅ | favorites.js |
| 模板保存/加载 | ✅ | templates.js + BrandKit |
| 行业方案包 (6套) | ✅ | solutionPacks.js |
| 提示词库 | ✅ | promptLibrary.js |
| 用量配额 | ✅ | quota.js |
| 暗色/浅色主题切换 | ✅ | theme.jsx |
| 命令面板 Ctrl+K | ✅ | CommandPalette.jsx |
| 全局搜索 | ✅ | Layout |
| 撤销 Ctrl+Z | ✅ | Workbench |
| 移动端底部导航 | ✅ | Layout |
| 错误追踪 | ✅ | errorTracker.js |
| PWA | ✅ | manifest.json |
| i18n 中英文 | ✅ | i18n.js + Layout |
| SEO meta | ✅ | index.html |

## 后端/存储

| 功能 | 状态 | 模块 |
|------|------|------|
| localStorage (元数据) | ✅ | store.js |
| IndexedDB (图片 Blob) | ✅ | db.js |
| Supabase (云同步) | ✅ | supabase.js + .env |
| 协作审批流 | ✅ | collaboration.js + AdminConsole |
| 支付框架 | ✅ | payment.js |
| 错误日志 | ✅ | errorTracker.js + AdminConsole |
| 数据导出/导入 | ✅ | db.js + AdminConsole |
| 单元测试 | ✅ | 7 tests passing |

## 等 API Key 的

| 功能 | 状态 | 需要什么 |
|------|------|----------|
| 视频真实生成 | 🟡 | 中转站 API 地址和格式 |
| Supabase Auth (OAuth) | 🟡 | 无需额外配置，代码就绪 |
