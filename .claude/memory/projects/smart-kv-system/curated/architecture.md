---
priority: P0
last_verified: 2026-06-24
version: 1
---

# 系统架构

## 路由设计

```
/              → Home (营销页，暗色主题)
/login         → Login (Miketv 品牌)
/app           → Dashboard (登录后首页)
/workbench     → AI 生图
/video-studio  → 视频创作
/material-lib  → 物料库
/brand-kit     → 品牌管理
/history       → 历史记录
/admin         → 管理控制台 (仅 admin)
/export-center → 导出中心
/share/:key    → 分享查看 (无需登录)
```

## 数据流

```
用户上传 KV → compressImage() → analyzeImage() (Gemini)
  → 提取 colors/fonts/layout/elements
  → buildPrompt() → startNanoDraw() → pollNanoResult()
  → 结果存入 localStorage + IndexedDB + Supabase
```

## 三层存储

```
localStorage  → 元数据/配置 (< 100KB/条)
IndexedDB     → 大图 Blob (> 50KB)
Supabase      → 云端同步 (3 张表: projects, generations, favorites)
```

## 配色 Token

- 浅色: 靛蓝系 (`#4f46e5` primary, `#f8fafc` background)
- 暗色: 靛蓝系 (`#818cf8` primary, `#0a0a14` background)
- 主色: indigo, 辅色: cyan, 强调: violet
- 定义位置: `src/index.css` 的 `@theme` 块 + `html.app-dark` + `.home-dark`

## 关键依赖

- React 19 + React Router 7
- Tailwind v4 (通过 @tailwindcss/vite 插件)
- @supabase/supabase-js
- Material Symbols Outlined (图标)
- Google Fonts: Inter, Hanken Grotesk, JetBrains Mono
