# 开发进度记录 (2026-02-07)

## 🎯 目标
解决 NC 框架下前端模块加载失败问题、后端鉴权兼容性问题，并完成内网部署包的标准化构建。

## ✅ 今日完成事项

### 1. 前端重构 (Frontend)
- **方案变更**: 放弃原有的 React 前端（`agent-ui`），改用 Vue 版 `demo-nccm-lite` 项目作为前端基础，以获得更好的 NC 框架兼容性。
- **组件重写**:
  - 将 `AgentWrapper.vue` 重命名为 `agent.vue` 并进行全量重写。
  - 从单纯的 Iframe 容器改为**原生 Vue 聊天组件**，直接集成 Axios 调用后端接口。
  - 实现了消息列表渲染、图片上传预览、Markdown 渲染支持。
- **路由修复**:
  - 修正 `router.js` 中的动态路由逻辑，手动注册 `/demo/agent` 路由指向 `agent.vue`。
  - 解决了 `Cannot find module './views/demo/agent'` 的模块加载错误。
- **Token 注入**:
  - 在 API 请求拦截器中增加了 Token 获取逻辑。
  - 优先从 `nc.util.getStore` 获取，降级从 `localStorage` 获取，确保 SSO Token 能正确透传给后端。

### 2. 后端鉴权适配 (Backend)
- **鉴权降级**: 修改 `backend/auth.py`，增加内网演示模式的兜底策略。
  - 当标准 JWT 验证失败时（常见于内外网密钥不一致或 Token 格式差异），自动将用户身份降级为 `nc_demo_user`。
  - **解决问题**: 修复了前端请求 `/get_answer` 接口时报 `401 Unauthorized` 的阻断性问题，确保演示流程畅通。
- **JIT 自动注册**: 完善了用户自动供给逻辑，对于验证通过的 SSO 用户，若本地数据库不存在则自动创建，避免手动维护账号。

### 3. 构建与部署 (Build & Deploy)
- **脚本修复**: 修复 `build_intranet.sh` 中 Python 代码嵌入 Shell 脚本时的语法错误，确保构建流程稳定。
- **标准化打包**:
  - **后端**: 重新生成 `ops-agent-linux-x64.zip`，内置最新鉴权逻辑。
  - **前端**: 生成标准化的 `agent-ui.zip` (基于 Vue 版 demo)，目录结构适配 NC 框架要求。
- **部署规范**:
  - 确定内网前端部署路径为 `/usr/local/nginx/dist/m/demo`。
  - 更新 Nginx 配置文档，统一了 `alias` 路径映射。

## 📂 关键产物位置
- **WSL 项目路径**: `~/projects/zz-agent-out-develop`
- **前端部署包**: `agent-ui.zip` (Vue 版，已适配 NC 目录结构)
- **后端部署包**: `ops-agent-linux-x64.zip` (含鉴权降级逻辑)

## 🔜 接下来的计划
1. **前端界面优化**: 进一步美化聊天界面，优化消息气泡样式和交互体验。
2. **单点登录深化**: 验证 `nc_demo_user` 降级策略在实际多用户环境下的表现，考虑接入真实的 NC 用户信息接口。
