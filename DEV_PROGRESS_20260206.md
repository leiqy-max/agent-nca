# 开发进度记录 (2026-02-06)

## 🎯 目标
将智能问答助手 (`zz-agent-out-develop`) 改造为支持嵌入 NC 框架运行的版本，并适配内网部署环境。

## ✅ 今日完成事项

### 1. 前端改造 (Frontend)
- **Base URL 调整**: 修改 `frontend/src/App.jsx`，将 Axios 默认 Base URL 设置为 `/agent-api`，以匹配 Nginx 反向代理路径。
- **Vite 配置优化**: 更新 `frontend/vite.config.js`，设置 `base: '/agent-ui/'`，并配置开发环境代理。
- **打包结构规范化**: 优化打包流程，生成的 `agent-ui.zip` 解压后自带 `agent-ui/` 根目录，符合 Nginx 静态资源部署规范。

### 2. 后端改造 (Backend)
- **双路由支持**: 重构 `backend/main.py`，引入 `APIRouter`。
  - **独立模式**: 保留根路径 `/` 访问。
  - **嵌入模式**: 新增 `/agent-api` 前缀挂载，确保在 NC 框架反向代理下能正确处理请求。

### 3. 构建系统 (Build)
- **内网构建脚本**: 升级 `build_intranet.sh`。
  - 集成前端打包逻辑（自动压缩 `frontend/dist`）。
  - 增加智能检测：若存在 `frontend/dist` 则跳过 npm 编译（避免 Windows/Linux 环境不一致问题）。
- **环境迁移**: 将项目完整迁移至 WSL 环境 (`~/projects/zz-agent-out-develop`)，并在 WSL 中验证了构建流程。

### 4. 部署文档 (Documentation)
- **更新指南**: 在 `INTRANET_GUIDE.md` 中新增 "3. NC 框架嵌入指南"。
  - 提供了完整的 Nginx `server` 配置块。
  - 提供了 NC 菜单配置方案（使用 `/demo/agent` + `AgentWrapper` 组件）。

## 📂 关键产物位置
- **WSL 项目路径**: `~/projects/zz-agent-out-develop`
- **前端部署包**: `agent-ui.zip` (位于项目根目录)
- **后端部署包**: `ops-agent-linux-x64.zip` (位于项目根目录)

## 🔜 接下来的工作建议
1. **在 WSL 中继续开发**: 您已切换到 WSL 环境，请直接在 `~/projects/zz-agent-out-develop` 目录下工作。
2. **验证部署**:
   - 将 `agent-ui.zip` 解压到 Nginx HTML 目录。
   - 启动后端服务 `ops-agent`。
   - 配置 Nginx 转发。
   - 在 NC 框架中点击菜单测试。
