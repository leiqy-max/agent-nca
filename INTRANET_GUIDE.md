# 运维智能问答助手 - 内网部署避坑指南

本指南汇总了从外网（开发环境）迁移到内网（生产环境）过程中可能遇到的所有坑及解决方案。

---

## 📦 部署包结构说明 (重要)

新版部署包 `ops-agent-linux-x64.zip` 解压后仅包含以下内容 (极简模式)：

```text
ops-agent-linux-x64/
├── ops-agent             # 主程序 (二进制文件，已内置所有前端资源)
├── config.yaml           # 配置文件 (需修改数据库和LLM地址)
├── INTRANET_GUIDE.md     # 本指南
└── README.txt            # 简易说明
```

**✅ 核心改进**: 
- **单文件运行**: 前端静态资源 (React 编译产物) 已被完整打包进 `ops-agent` 二进制文件中。
- **无需额外目录**: 部署时不再需要 `dist_frontend` 或 `templates` 文件夹。

---

## 1. 常见报错与解决方案

### Q1: 启动后界面非常简陋，和外网演示的不一样
**现象**: 浏览器访问后只显示一个简单的输入框，没有侧边栏、没有登录页、没有美观的 UI。
**原因**: 
- 这是旧版行为。新版单文件包启动后应直接显示完整 UI。
- 如果仍显示简陋界面，说明启动的可能是旧版二进制文件，或者构建过程中静态资源打包失败。
**解决方案**:
- 确保运行的是最新编译的 `ops-agent` 文件。
- 清除浏览器缓存 (Ctrl+F5) 重试。

### Q2: 报错 `GLIBC_2.38 not found` (或类似版本错误)
**现象**: `./ops-agent: /lib64/libm.so.6: version 'GLIBC_2.38' not found`
**原因**: 内网服务器 (如 BCLinux 8.2, CentOS 7) 的 GLIBC 版本过低 (通常为 2.28 或 2.17)，而程序编译环境使用了高版本 GLIBC。
**解决方案**:
- 本部署包已集成 **Portable Python** (基于 musl/旧版 glibc 编译)，理论上兼容 GLIBC 2.17+。
- 且构建时已排除高版本系统库 (`libgcc_s`, `libstdc++`)，确保使用系统自带库或兼容库。

### Q3: 报错 `ModuleNotFoundError: jinja2` 或 `AssertionError: jinja2 must be installed`
**现象**: 启动时崩溃，提示缺少 jinja2。
**解决方案**:
- 新版构建已修复此问题 (强制打包 jinja2/markupsafe)。

### Q4: 数据库连接失败 `Connection refused`
**现象**: 启动失败，日志提示无法连接数据库。
**解决方案**:
- 检查 `config.yaml` 中的 `[database]` 配置。
- 确认内网 PostgreSQL 已安装 `pgvector` 插件 (`CREATE EXTENSION vector;`)。
- 检查防火墙是否允许 5432 端口通信。

### Q5: 提问报错 `500 Internal Server Error` (Input should be a valid string)
**现象**: 提问时后端报错 `openai.UnprocessableEntityError: ... 'input': ['...']`。
**原因**: 内网部署的某些大模型接口（如旧版 vLLM 或特定本地推理框架）不支持 OpenAI 协议中的“列表格式输入” (Batch Input)，仅支持单字符串输入。
**解决方案**:
- 新版程序已针对此问题做了兼容性修复（强制使用单字符串格式调用 Embedding 接口）。
- 请确保使用的是最新构建的二进制文件。

### Q6: 访问管理页面报错 `401 Unauthorized`
**现象**: 日志中出现大量 `GET /admin/... 401 Unauthorized`。
**原因**: 这是正常的安全拦截。新版系统开启了完整的 RBAC 权限控制，在未登录状态下，前端尝试获取后台数据会被拒绝。
**解决方案**:
- 请在页面上使用 `admin` / `admin123` 登录，登录后即可正常访问。

### Q7: 知识文档页面点击报错 (白屏/TypeError)
**现象**: 点击左侧“知识文档”菜单后，页面变白或报错。
**原因**: 前端代码中 `File` 图标组件与浏览器全局 `File` 对象命名冲突。
**解决方案**:
- 已在源码中修复该冲突 (重命名组件为 `FileIcon`)。
- 请使用最新编译的二进制文件。

### Q8: 数据库字段缺失报错
**现象**: 日志提示 `column "download_count" of relation "uploaded_files" does not exist`。
**原因**: 新功能依赖数据库新增字段。
**解决方案**:
- 程序启动时会自动尝试执行数据库迁移 (Add Columns)。
- 如果自动迁移失败（因权限不足），请手动执行 SQL:
  ```sql
  ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS download_count INTEGER DEFAULT 0;
  ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS file_size INTEGER DEFAULT 0;
  ```

---

## 2. 部署步骤 (标准流程)

1.  **上传与解压**:
    ```bash
    # 上传 zip 包到内网服务器
    unzip ops-agent-linux-x64.zip
    cd ops-agent-linux-x64
    chmod +x ops-agent
    ```

2.  **配置数据库**:
    - 确保 PostgreSQL 12+ 运行正常。
    - 执行: `psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"`

3.  **修改配置**:
    - 编辑 `config.yaml`:
      ```yaml
      database:
        host: "192.168.1.100"  # 内网数据库IP
        ...
      llm:
        chat_base_url: "http://192.168.1.200:8000/v1" # 内网大模型地址
      server:
        host: "0.0.0.0"
        port: 9020
      ```

4.  **启动服务**:
    ```bash
    ./ops-agent
    ```
    - 观察日志，出现 `Application startup complete` 即为成功。

5.  **验证功能**:
    - 访问 `http://IP:9020`
    - 使用 `admin` / `admin123` 登录
    - 检查左侧菜单是否有“知识文档”
    - 尝试上传和搜索文档

---

## 3. NC 框架嵌入指南 (推荐)

### 3.1 架构说明
NC 框架采用模块化设计，而本助手作为独立 React 应用，推荐使用 **Iframe 嵌入** 方式集成。这种方式既保留了独立部署的灵活性，又能完美融入 NC 框架。

### 3.2 资源准备
部署包中已生成 `agent-ui.zip`，解压后包含完整的静态资源：
1. **解压前端包**: 
   ```bash
   # 创建标准模块目录
   mkdir -p /usr/local/nginx/dist/m/demo
   
   # 解压资源到指定目录 (保持包内结构)
   unzip agent-ui.zip -d /usr/local/nginx/dist/m/demo
   ```
2. **启动后端**: 运行 `ops-agent` 服务 (监听 9020 端口)。

### 3.3 Nginx 配置 (核心)
在 NC 框架的主 Nginx 配置文件中添加以下 Location 块。
**特别注意**: 必须针对 `agent-ui` 单独配置 `try_files` 和 `X-Frame-Options`，否则会出现 404 错误或“拒绝连接”的 Iframe 拦截问题。

```nginx
server {
    listen       6001; # 假设 NC 监听端口
    # ... 其他原有配置 ...

    # 1. 外层 Vue 容器 (NC 模块入口)
    location /m/demo/ {
        alias /usr/local/nginx/dist/m/demo/;
        index index.html;
        try_files $uri $uri/ /m/demo/index.html;
        
        # 允许 Iframe 嵌入 (覆盖全局设置)
        add_header X-Frame-Options ""; 
    }
    
    # 2. 内嵌 React 助手 (Iframe 目标)
    # 必须单独配置! 否则会错误加载外层的 index.html
    location /m/demo/agent-ui/ {
        alias /usr/local/nginx/dist/m/demo/agent-ui/;
        index index.html;
        try_files $uri $uri/ /m/demo/agent-ui/index.html;
        
        # 允许 Iframe 嵌入 (关键)
        add_header X-Frame-Options "";
    }

    # 3. 后端 API 转发
    location /agent-api/ {
        proxy_pass http://127.0.0.1:9020/agent-api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3.4 菜单配置 (关键)
为了实现 Token 自动透传，**不要**直接填写 URL，而是使用 NC 框架的组件封装：

1. **菜单路径**: `/demo/agent`
2. **组件路径**: `views/demo/AgentWrapper.vue` (如需自行实现，参考下文)
3. **工作原理**: 
   - 用户点击菜单 `/demo/agent`
   - NC 框架加载 `AgentWrapper` 组件
   - 组件自动获取当前用户 Token，拼接成 `/agent-ui/?token=xxx`
   - 组件内部渲染 Iframe 加载该 URL

**附: AgentWrapper.vue 参考实现**:
```vue
<template>
  <div class="agent-wrapper" style="height: 100%; width: 100%;">
    <iframe :src="iframeSrc" style="width: 100%; height: 100%; border: none;"></iframe>
  </div>
</template>
<script>
export default {
  data() { return { iframeSrc: '' } },
  mounted() {
    // 自动获取 NC 框架中的 Token
    const token = window.nc?.token || localStorage.getItem('token');
    const user = window.nc?.current?.user?.name || 'User';
    // 拼接目标地址
    this.iframeSrc = `/agent-ui/?token=${encodeURIComponent(token)}&username=${encodeURIComponent(user)}`;
  }
}
</script>
```

### 3.5 验证步骤
1. 登录 NC 系统。
2. 点击菜单 `/demo/agent`。
3. 确认页面内嵌显示问答助手，且右上角显示当前登录用户名（说明 SSO 成功）。


---

## 4. 2026-02-06 进展记录

### 4.1 问题描述
内网 NC 框架下，Agent 子菜单点击后无法加载。
- **原因**: 框架请求 GET \.../m/demo/views/views-demo-Dashboard...js\ 失败。
- **分析**: 即使是 Iframe 嵌入，NC 框架的前端路由加载器（Webpack）仍需先找到对应的 Vue 组件定义文件才能渲染外层容器。

### 4.2 解决方案
为满足 NC 框架的文件路径和模块加载要求，需在前端包中手动构建欺骗 Webpack 的文件结构：

1.  **文件结构**:
    需在前端静态资源包中包含以下层级：
    \rontend/public/views/demo/
       \AgentWrapper.vue\ (Iframe 容器组件)
       \iews-demo-agent.js\ (Webpack chunk 注册文件)

2.  **核心代码**:
    - \AgentWrapper.vue\: 简单的 Iframe 容器，指向 \/agent-ui/\。
    - \iews-demo-agent.js\: 手动调用 \window['webpackJsonp'].push\ 注册模块 \iews-demo-agent\，将 \AgentWrapper.vue\ 映射到模块中。

3.  **构建脚本 (\uild_intranet.py\)**:
    编写了 Python 脚本自动化打包过程：
    - 复制 \dist\ (构建产物) 到根目录。
    - 复制 \iews\ 文件夹结构。
    - 压缩为 \gent-ui.zip\。

### 4.3 当前状态与下一步
- **已完成**: 方案设计与代码逻辑验证。
- **待处理**:
    - 因环境终端限制，部分文件写入失败，需手动创建或使用更稳健的方式写入：
      - \rontend/public/views/demo/AgentWrapper.vue
      - \rontend/public/views/demo/views-demo-agent.js
      - \uild_intranet.py
    - 执行构建脚本生成最终的 \gent-ui.zip\。
