# Miketv 知识管理系统

## 项目
- **名称**: smart-kv-system (品牌名: Miketv)
- **定位**: AI 视频与图像智能创作平台
- **仓库**: archie1996822-eng/smart-kv-system
- **部署**: GitHub Pages (自动部署)

## 导航

| 我想要... | 看这个 |
|-----------|--------|
| 了解系统整体架构 | [curated/architecture.md](projects/smart-kv-system/curated/architecture.md) |
| 查看所有功能状态 | [curated/features.md](projects/smart-kv-system/curated/features.md) |
| 查看组件清单 | [curated/components.md](projects/smart-kv-system/curated/components.md) |
| 查看数据模块 | [curated/data-modules.md](projects/smart-kv-system/curated/data-modules.md) |
| 查看设计规范 | [curated/style-guide.md](projects/smart-kv-system/curated/style-guide.md) |
| 查看 API 接入状态 | [curated/api-status.md](projects/smart-kv-system/curated/api-status.md) |
| 查看已知 Bug | [curated/bugs.md](projects/smart-kv-system/curated/bugs.md) |
| 查看关键决策 | [curated/decisions.md](projects/smart-kv-system/curated/decisions.md) |
| 查看变更日志 | [curated/changelog.md](projects/smart-kv-system/curated/changelog.md) |
| 查看陷阱/不该做的事 | [curated/anti-patterns.md](projects/smart-kv-system/curated/anti-patterns.md) |
| 查看机器生成的数据 | [generated/](projects/smart-kv-system/generated/) |
| 继续上次的工作 | [tasks/active.md](projects/smart-kv-system/tasks/active.md) |
| 查看上次会话 | [sessions/](projects/smart-kv-system/sessions/) |

## 防幻觉检查清单

加载 INDEX 后自动执行：
- [ ] `.config.json` commit 是否等于 `git rev-parse HEAD`？
- [ ] `generated/` 文件是否比 `curated/` 新？
- [ ] `curated/` 中是否有 `last_verified > 7 天` 的文件？
- [ ] `tasks/active.md` 是否存在？
- [ ] `sessions/` 最近一条是否在今天？

## 上下文压缩触发条件
- 消息数 > 80 条
- **或** token 使用 > 70%

压缩时：
1. 保留 INDEX + .config.json + sessions/latest + tasks/active
2. P0 curated 保留关键数据行
3. P1 curated 保留标题+一行摘要
4. P2 curated 丢弃（可恢复）
5. generated/ 全丢弃（可重新生成）
6. 对话历史压缩为决策摘要
