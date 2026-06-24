---
priority: P1
last_verified: 2026-06-24
version: 1
---

# 已知 Bug 和运行风险

## 未修复

| # | Bug | 严重度 | 复现步骤 | 状态 |
|---|-----|--------|----------|------|
| 1 | 大图 base64 塞满 localStorage | 中 | 连续生成 5+ 次不清理 | 🟡 已有 IndexedDB 迁移 |
| 2 | ImageEditor CORS 跨域报错 | 低 | 编辑外部 URL 图片 | 🟡 已加 onerror 容错 |
| 3 | 撤销栈 useRef 不触发重渲染 | 低 | 快速连续 Ctrl+Z | 🟢 已改用 useState |
| 4 | Supabase 同步静默失败 | 低 | 网络异常时云同步不报错 | 🟡 已加 .catch(() => {}) |

## 已修复

| # | Bug | 修复 commit |
|---|-----|------------|
| 1 | `toggleItem`/`selectAll` 丢失 | fd9ec86 |
| 2 | async forEach 未捕获异常 | fd9ec86 |
| 3 | `pushUndo()` 从未调用 | c42cab3 |
| 4 | `friendlyError` 未使用 | c42cab3 |
| 5 | `STORAGE_PREFIX` bug | 第一轮 |
| 6 | 确认弹窗用原生 confirm() | dba4131 |
