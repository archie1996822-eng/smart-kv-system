---
priority: P0
last_verified: 2026-06-24
auto_generated_from: src/**/*.jsx, src/**/*.js
---

# 已知陷阱 / 不该做的事

## JavaScript / React

1. ❌ **不要用 async forEach**
   - forEach 不等待 Promise，异常无法被 try/catch 捕获
   - 正确: `for...of` 或 `.forEach(() => { ... }).catch(() => {})`

2. ❌ **不要在 JSX 中写大段逻辑**
   - 渲染阻塞，调试困难
   - 正确: 提取为 const 或在 useCallback 中

3. ❌ **不要创建 .js 文件包含 JSX**
   - Vite 不会 transform JSX in .js
   - 正确: 用 .jsx 扩展名

4. ❌ **不要假设可选链存在**
   - `analysis.colors[0]` 会崩溃
   - 正确: `analysis?.colors?.[0]`

## 本项目特定

5. ❌ **不要直接用 localStorage 改 CMS**
   - CMS 数据键是 `smart_kv_cms_homepage`，直接改会绕过版本锁
   - 正确: 用 AdminConsole 的 saveCMS()

6. ❌ **不要在 Workbench 外调用 toggleItem/selectAll**
   - 这些函数依赖 Workbench 的闭包状态
   - 它们需要 pushUndo() 调用，外部调用会丢失撤销栈

7. ❌ **不要删除 toggleItem 或 selectAll 函数**
   - 这两个函数已多次在编辑中被意外删除
   - Checklist 组件依赖它们

8. ❌ **不要修改 index.css 的 @theme 块而不更新 .home-dark 和 html.app-dark**
   - 三处必须保持一致的 token 名称

9. ❌ **不要在生产环境忘记 .env**
   - VITE_SUPABASE_URL 和 VITE_SUPABASE_ANON_KEY 缺一不可
   - 已在 .gitignore 中

10. ❌ **prompt() 和 confirm() 已废弃**
    - 全部替换为 ConfirmModal / PromptModal
