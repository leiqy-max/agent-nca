# 开发进度日志 (Development Progress)

## 📌 项目概述
本项目 (`agent-nca`) 旨在将智能问答助手集成到 NC 框架中，主要采用 **Iframe 嵌入** 方案，通过外层 Vue 框架加载内层 React 应用，实现无缝的用户体验。

---

## 📅 2026-02-08 (最新优化与问题修复)

### 🎯 目标
解决 NC 框架嵌入时的路径 404 问题、跨域问题，以及优化构建产物的目录结构。

### ✅ 关键问题与解决方案 (Troubleshooting)

#### 1. 前端路由模式冲突 (Router Mode Conflict)
*   **问题描述**: React 应用使用 `BrowserRouter` (History Mode)，依赖 Nginx 的 `try_files` 配置。但在 NC 框架下，主框架接管了路由，导致子应用刷新后出现 404 或 `NS_BINDING_ABORTED`。
*   **解决方案**: 
    *   将 `BrowserRouter` 切换为 **`HashRouter`**。
    *   **优势**: 路由状态由 URL hash (`#`) 管理，完全由浏览器客户端处理，不依赖 Nginx 配置，彻底规避了路径冲突。

#### 2. 构建产物目录嵌套 (Nested Directory Issue)
*   **问题描述**: Webpack 配置中的 `chunkFilename` 使用了多余的路径前缀 (`views/`)，导致打包后的文件出现在 `views/views/` 深层目录下，NC 框架无法正确加载。
*   **解决方案**:
    *   修改 `webpack.build.common.js`，移除 `chunkFilename` 中的路径前缀。
    *   使用 `webpack.NamedChunksPlugin` 显式控制 Chunk 名称，确保扁平化输出。
    *   **结果**: 所有视图 JS 文件直接输出到 `dist/m/demo/views/` 根目录下，符合框架规范。

#### 3. 部署包结构优化 (Package Structure)
*   **问题描述**: 早期的 zip 包中包含了冗余的文件夹（如 `agent-ui` 子目录），导致解压后路径层级不对。
*   **解决方案**:
    *   手动清理 zip 包，只保留标准结构：`demo.js` 在根目录，组件在 `views/` 目录。
    *   最终产物结构：
        ```text
        demo.zip
        ├── demo.js
        └── views/
            ├── views-demo-agent.js
            └── ...
        ```

### 🚀 优化点 (Optimizations)
*   **原生 Vue 适配**: 在 `agent-nc` 分支中实现了不依赖 Iframe 的原生 Vue 版本，虽然目前功能较少（仅聊天），但加载速度更快，作为备选方案。
*   **Iframe 交互**: 在 `agent-nca` 中保留了 Iframe 方案，适合快速集成已有的 React 完整应用，功能最全。

---

## 📅 2026-02-07 (NC 框架适配与鉴权)

### ✅ 完成事项
#### 1. 前端重构 (Frontend)
*   **方案变更**: 引入 Vue 版 `demo-nccm-lite` 作为外壳。
*   **组件重写**:
    *   将 `AgentWrapper.vue` 重命名为 `agent.vue`。
    *   修正 `router.js` 动态路由逻辑，手动注册 `/demo/agent`。
*   **Token 注入**: 在 API 请求拦截器中增加 Token 获取逻辑（`nc.util.getStore` > `localStorage`）。

#### 2. 后端鉴权适配 (Backend)
*   **鉴权降级**: 修改 `backend/auth.py`，增加内网演示模式兜底策略。当 JWT 验证失败时，自动降级为 `nc_demo_user`，解决 `401 Unauthorized` 问题。
*   **JIT 自动注册**: 验证通过的 SSO 用户若本地不存在则自动创建。

#### 3. 构建与部署 (Build)
*   **脚本修复**: 修复 `build_intranet.sh` 语法错误。
*   **部署规范**: 确定内网前端部署路径为 `/usr/local/nginx/dist/m/demo`。

---

## 📅 2026-02-06 (环境迁移与基础配置)

### ✅ 完成事项
#### 1. 前端改造
*   **Base URL**: 设置 Axios Base URL 为 `/agent-api`。
*   **Vite 配置**: 设置 `base: '/agent-ui/'`。

#### 2. 后端改造
*   **双路由支持**: `backend/main.py` 引入 `APIRouter`，同时支持根路径和 `/agent-api` 前缀。

#### 3. 构建系统
*   **脚本升级**: `build_intranet.sh` 集成前端打包逻辑。
*   **环境迁移**: 项目迁移至 WSL 环境。

#### 4. 文档
*   **Nginx 配置**: 提供完整的 `server` 配置块和 NC 菜单配置方案。

---

## 📂 关键产物说明
*   **agent-nc**: 原生 Vue 方案代码库。
*   **agent-nca**: Iframe React 方案代码库（当前主推）。
*   **demo.zip**: 最终部署包，包含外层 Vue 框架 + 内层 React 应用（或原生 Vue 组件）。
*   **ops-agent-linux-x64.zip**: 后端部署包。
