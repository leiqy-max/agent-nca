# Ops Agent - 智能运维问答机器人

Ops Agent 是一个基于 RAG（检索增强生成）技术的智能运维问答助手，专为运维场景设计。它支持多模态（文本+图片）交互、严格的权限管理（RBAC）、知识库自动学习与人工补全，并提供完整的内网离线部署方案。

## 🚀 核心功能 (Core Features)

### 1. 智能问答 (Smart Chat)
- **多模态交互**：支持纯文本提问，也支持上传运维截图、架构图（内置图片裁剪工具）。
- **精准检索 (RAG)**：基于 `pgvector` 向量数据库，精准检索相关文档片段。
- **文档溯源**：每次回答均标注参考来源，并提供源文件直接下载链接。
- **防幻觉机制**：针对图片问题，采用"视觉模型提取文本 + 文本模型生成答案"的双阶段策略。

### 2. 知识库管理 (Knowledge Management)
- **多格式支持**：支持 PDF, DOCX, TXT, MD, XLSX 等格式。
- **在线预览**：在“知识文档”模块中，可直接在线预览 DOCX、PDF 等文档内容，无需下载。
- **热度统计**：自动统计文档下载/引用次数，展示热门文档。
- **双向同步**：支持后台自动扫描磁盘文件增量更新数据库。

### 3. 自我进化 (Self-Learning)
- **未知问题捕获**：自动记录系统无法回答的问题。
- **问答补全**：管理员或用户可手动补充问答对。
- **AI 润色**：在补充答案时，提供 **AI 润色** 功能，利用大模型自动优化语言表达，使其更专业。
- **学习记录**：所有补充的知识点经审批后自动入库，并在“学习记录”中留痕。

### 4. 权限与审批 (RBAC & Approval)
- **Admin (管理员)**：全权管理，包括文档审批、问答审批、用户管理。
- **User (普通用户)**：可使用问答、上传文档（需审批）、提交补充回答（需审批）。
- **Guest (访客)**：仅限有限次数的问答，禁止上传。

## 📂 菜单导航 (Menu Structure)

项目前端采用侧边栏导航，根据用户角色动态显示菜单：

| 菜单项 | 适用角色 | 功能描述 |
| :--- | :--- | :--- |
| **智能问答** | All | 核心对话界面，支持图片上传/裁剪。 |
| **审批中心** | Admin | **文档审批**：审核用户上传的文件。<br>**问答审批**：审核用户提交的补全问答。 |
| **未知问题** | Admin, User | 查看系统未解答的问题列表。管理员可直接解答或丢弃；用户提交解答需审批。 |
| **问答补全** | Admin, User | 手动录入 Q&A 知识对。支持 **AI 润色** 功能。 |
| **问答记录** | Admin, User | 查看历史对话日志。管理员可看全局，用户仅看自己。 |
| **学习记录** | Admin, User | 查看所有通过“未知问题”或“问答补全”习得的知识条目。 |
| **知识文档** | Admin, User | 浏览全量知识库文件。支持 **在线预览**、搜索过滤、热门下载排行。 |

## 🛠️ 技术栈 (Tech Stack)

- **Frontend**: React, Vite, TailwindCSS, Lucide Icons, Framer Motion
- **Backend**: FastAPI, LangChain, SQLAlchemy
- **Database**: PostgreSQL (with `pgvector` extension)
- **LLM**: 支持 OpenAI 接口格式的模型 (如 GLM-4, DeepSeek, Qwen 等)
- **Deployment**: Docker, PyInstaller (单文件离线包)

## 📦 部署与运行 (Deployment)

### 快速启动 (Quick Start)

详细部署步骤（包括数据库初始化、内网穿透配置等）请参考 [DEPLOY.md](DEPLOY.md)。

**1. 后端启动**
```bash
cd backend
# 安装依赖
pip install -r requirements.txt
# 启动服务 (默认端口 8000)
python main.py
```

**2. 前端启动**
```bash
cd frontend
# 安装依赖
npm install
# 开发模式启动
npm run dev
```

### 内网离线部署
对于无法连接互联网的内网环境，本项目提供了全量打包脚本，生成单文件可执行程序。
详细指南请参考 [INTRANET_GUIDE.md](INTRANET_GUIDE.md)。

## 📝 最近更新 (Latest Updates)

- **[重构] 侧边栏导航**：采用分组分级结构（智能助手/知识共建/运维管理），提升易用性。
- **[新增] 全局日志**：管理员可查看所有用户的交互日志（提问、审批、文档上传）。
- **[优化] 进化历程管理**：管理员可删除学习记录，并同步清理向量数据库。
- **[新增] AI 润色功能**：在“问答补全”中引入大模型辅助写作。
- **[新增] 文档在线预览**：前端集成 `docx-preview`，解决下载查看的繁琐。
- **[优化] 审批工作流**：普通用户提交的知识贡献（文档/问答）均纳入审批流。


---


以下是一份标准化文档模板，用于规范在移动内网环境下开发和部署“运维知识智能体”类 AI 生成程序。该文档融合了您提供的两套方案核心要点，聚焦合规性、可落地性、运维场景适配性，适用于向技术团队、安全审计、项目管理及客户方交付使用。

AI 智能体系统建设规范（运维知识问答类）  
版本：1.0  
适用场景：移动内网环境 · 运维知识智能助手  
编制单位：XXX 资源室 / AI 工程组  
生效日期：2026年1月

一、方案定位与目标

一句话定义：  
基于移动现有私有大模型 API，在完全内网隔离环境下，构建一套不训练、不外传、可追溯的运维知识智能问答系统（RAG 架构），实现“问一句，得标准答案”。

核心目标
- ✅ 快速响应一线运维人员对告警、故障、操作规程的查询需求  
- ✅ 减少人工翻查手册、依赖专家经验  
- ✅ 所有数据不出内网，符合央企数据安全与合规要求  
- ✅ 回答内容可溯源、可审计、可管控，不替代人工决策  

二、技术架构原则
原则   说明
零公网依赖   所有组件部署于客户内网，无任何外部网络调用

复用现有资源   直接对接移动已有的私有大模型 API 与 Embedding 服务

非训练型学习   采用 RAG（检索增强生成），不微调模型参数

工具型定位   定位为“智能检索工具”，非自主决策系统

权限最小化   按角色控制文档可见范围，支持系统级/文档级隔离

三、系统架构（逻辑分层）

【移动内网】
│
├─ 使用层
│   ├─ Web 运维助手（主入口）
│   ├─ 内部门户嵌入（可选）
│   └─ 未来扩展：工单系统联动
│
├─ 智能体服务层
│   ├─ 问题意图识别（告警 / 故障 / 操作）
│   ├─ 多文档综合推理
│   └─ 回答策略控制（引用优先 / 禁止自由发挥）
│
├─ 知识检索层（RAG）
│   ├─ 文档解析（结构化拆分）
│   ├─ 向量 + 关键词混合检索
│   └─ Top-K 片段召回 + 权重排序
│
├─ 模型服务层
│   ├─ 私有大模型 API（Qwen / DeepSeek 等）
│   └─ Embedding 接口（用于向量化）
│
├─ 数据层
│   ├─ 运维文档库（PDF / Word / Excel / Wiki）
│   ├─ 向量数据库（Milvus / pgvector）
│   └─ 元数据表（含更新时间、责任人、权限标签）
│
└─ 安全与审计
    ├─ 统一身份认证（SSO）
    ├─ 操作日志全留痕
    └─ 问答记录可回溯（含提问人、时间、命中文档）

四、运维知识处理规范（关键差异化）

4.1 文档类型与拆分策略
文档类型         拆分规则
运维手册         按章节 + 操作步骤拆分，保留上下文

故障处理流程     强制保留：现象 → 原因 → 步骤 → 验证 → 回滚 → 注意事项

告警说明         提取：告警码、触发条件、影响范围、处置建议

操作规程         高亮“禁止项”“风险提示”“前置条件”

FAQ              整条作为高权重知识单元，不做切割

❌ 禁止简单按字数（如每500字）机械切分  
✅ 必须保留语义完整性与操作逻辑链

4.2 向量化与检索优化
- 使用领域适配的 Embedding 模型（如 bge-m3 或客户指定模型）
- 支持关键词+向量混合检索，提升告警码等精确匹配效果
- 设置相关性阈值，低于阈值时返回“未找到标准方案”

五、智能体回答规范（必须遵守）

5.1 回答生成原则
- 只基于命中文档作答，无资料支撑时明确提示：
  > “未在现有运维知识库中找到标准处置方案，请联系后台支撑。”
- 禁止自由发挥、推测、建议性语言
- 优先输出标准流程，而非“可能”“建议”“可以尝试”

5.2 回答格式要求（强制包含）
根据《[文档名称]》[章节]（更新时间：YYYY-MM-DD），标准处理流程如下：

1）[步骤1]
2）[步骤2]
...

依据来源：《XX平台告警处理规范 v3.2》，2024-09

六、权限与角色管理
角色           权限范围
一线运维       查询、问答

二线专家       查询 + 反馈错误/缺失 + 修订建议

管理人员       查询 + 使用统计 + 热点问题分析

系统管理员     文档上传/更新/删除 + 权限配置

- 支持跨系统隔离（如 A 系统人员不可见 B 系统文档）  
- 所有文档需标注所属系统、密级、责任人

七、实施路径建议
阶段         周期       交付物
验证阶段     1–2 周     Web Demo + 50+ 文档问答准确率报告

正式部署     1–2 月     完整系统 + 权限体系 + 审计日志

深化运营     持续       工单联动 / 自动生成周报 / Agent 扩展

八、风险与边界声明（必须向客户明示）

1. 非替代人工：本系统为辅助工具，不承担决策责任  
2. 质量依赖输入：老旧、矛盾、缺失文档将直接影响回答准确性  
3. 责任边界清晰：涉及生产变更、安全操作、法律合规的回答，必须由人工复核  
4. 严禁越权访问：权限设计需通过客户安全团队评审  

九、附录：推荐技术栈（内网可用）
组件             推荐选项
大模型           Qwen2.5-7B/14B, DeepSeek-LLM（私有部署）

向量数据库       Milvus, pgvector（兼容 PostgreSQL）

文档解析         Unstructured, LlamaParse（支持表格/公式）

推理框架         vLLM, Ollama（内网适配版）

前端 UI          React + Ant Design（符合中移动风格）

编制说明：本规范适用于所有基于 RAG 架构的内网知识问答类 AI 系统开发，后续同类项目应以此为基准进行设计与验收。

---


# 部署指南 (Deployment Guide)

本文档将指导您如何在新的机器上部署本项目，包括运行环境配置、数据库初始化、Cloudflare 配置等。

## 1. 环境准备 (Prerequisites)

在开始之前，请确保您的服务器或本地机器安装了以下软件：

*   **操作系统**: Linux (推荐 Ubuntu/Debian/CentOS) 或 macOS
*   **Python**: 3.10 或更高版本
*   **Node.js**: 18.0 或更高版本 (用于前端构建)
*   **PostgreSQL**: 14.0 或更高版本 (必须支持并安装 `vector` 插件)

## 2. 数据库初始化 (Database Initialization)

本项目后端启动时会自动检查并创建所需的数据库表结构和默认数据。您只需要创建一个空的数据库并安装 `vector` 插件。

1.  **安装 PostgreSQL 和 pgvector**:
    *   **Ubuntu/Debian**:
        ```bash
        sudo apt install postgresql postgresql-contrib
        # 此时可能需要根据具体版本安装 pgvector，例如 postgresql-16-pgvector
        # 或者从源码编译安装 pgvector (https://github.com/pgvector/pgvector)
        ```

2.  **创建数据库**:
    登录到 PostgreSQL 并创建数据库（例如 `ops_agent`）：
    ```sql
    CREATE DATABASE ops_agent;
    \c ops_agent
    CREATE EXTENSION vector;
    ```

3.  **配置数据库连接**:
    修改 `backend/.env` 文件（如果没有则复制 `.env.example`），填入正确的数据库连接信息：
    ```ini
    DB_HOST=localhost
    DB_PORT=5432
    DB_USER=your_username
    DB_PASSWORD=your_password
    DB_NAME=ops_agent
    ```

## 3. 后端部署 (Backend Setup)

1.  进入后端目录：
    ```bash
    cd backend
    ```

2.  创建并激活虚拟环境（推荐）：
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  安装依赖：
    ```bash
    pip install -r requirements.txt
    ```

4.  启动后端服务：
    ```bash
    python main.py
    ```
    *   服务默认运行在 `http://0.0.0.0:8000`
    *   **首次启动**时，系统会自动初始化数据库表，并创建默认管理员账号：
        *   用户名: `admin`
        *   密码: `admin123`

## 4. 前端部署 (Frontend Setup)

1.  进入前端目录：
    ```bash
    cd frontend
    ```

2.  安装依赖：
    ```bash
    npm install
    ```

3.  **开发模式运行** (用于调试)：
    ```bash
    npm run dev
    ```
    访问: `http://localhost:5173`

4.  **生产环境构建**:
    ```bash
    npm run build
    ```
    构建完成后，`dist` 目录即为静态资源文件。您可以使用 Nginx 或其他 Web 服务器进行托管。

    **Nginx 配置示例**:
    ```nginx
    server {
        listen 80;
        server_name your_domain.com;

        location / {
            root /path/to/ops-agent/frontend/dist;
            try_files $uri $uri/ /index.html;
        }

        # 代理后端 API
        location /api/ {
            proxy_pass http://localhost:8000/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        # 代理文档相关 API (如果前端直接请求 /documents)
        location /documents/ {
            proxy_pass http://localhost:8000/documents/;
        }
    }
    ```

## 5. Cloudflare Tunnel 初始化 (Cloudflare Initialization)

如果您希望将服务暴露到公网，推荐使用 Cloudflare Tunnel，无需配置防火墙端口转发。

1.  **安装 Cloudflared**:
    请参考 Cloudflare 官方文档下载对应系统的 `cloudflared` 二进制文件或安装包。
    ```bash
    # Ubuntu 示例
    curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    sudo dpkg -i cloudflared.deb
    ```

2.  **登录 Cloudflare**:
    ```bash
    cloudflared tunnel login
    ```
    这将打开浏览器进行授权，选择您的域名。

3.  **创建 Tunnel**:
    ```bash
    cloudflared tunnel create ops-agent
    ```
    记下生成的 Tunnel ID。

4.  **配置 DNS (CNAME)**:
    将您的域名指向该 Tunnel：
    ```bash
    cloudflared tunnel route dns ops-agent ops-agent.yourdomain.com
    ```

5.  **编写配置文件 (`config.yml`)**:
    创建一个 `config.yml` 文件：
    ```yaml
    tunnel: <Tunnel-UUID>
    credentials-file: /root/.cloudflared/<Tunnel-UUID>.json

    ingress:
      - hostname: ops-agent.yourdomain.com
        service: http://localhost:80  # 如果使用 Nginx 托管前端
        # 或者直接指向前端开发服务 (不推荐用于生产)
        # service: http://localhost:5173 
      - service: http_status:404
    ```

6.  **启动 Tunnel**:
    ```bash
    cloudflared tunnel run ops-agent
    ```
    或者安装为系统服务：
    ```bash
    sudo cloudflared service install
    sudo systemctl start cloudflared
    ```

---
**注意**: 
*   请确保后端服务正常运行且端口 (8000) 可被访问。
*   如果前端和后端分离部署，请确保 Nginx 或 Cloudflare 配置了正确的 API 反向代理，避免跨域问题。


---


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


---


# 开发进度日志 (Development Progress)

## 📌 项目概述
本项目 (`agent-nca`) 旨在将智能问答助手集成到 NC 框架中，主要采用 **Iframe 嵌入** 方案，通过外层 Vue 框架加载内层 React 应用，实现无缝的用户体验。

---
0212
# 项目规则与规范 (Project Rules & Guidelines)

## 1. 项目概述 (Overview)
**agent-nca** 是一个专为 NC 框架定制的智能运维问答助手。它采用 **混合架构**，将现代化的 React 应用嵌入到传统的 NC Vue 框架中，既保证了与现有系统的无缝集成，又利用了 React 生态的优势。

### 核心架构
*   **外层 (NC Shell)**: 基于 Vue 2.x 的 NC 框架模块，负责菜单路由、用户鉴权 (SSO) 和 Iframe 容器管理。
*   **内层 (Agent UI)**: 基于 React + Vite 的现代化 SPA，负责核心问答交互、知识库管理等功能，运行在 Iframe 中。
*   **后端 (Backend)**: 基于 FastAPI + LangChain + PostgreSQL (pgvector) 的 RAG 智能问答服务。

## 2. 部署规范 (Deployment)

### 2.1 路径与端口
*   **前端部署路径**: `/usr/local/nginx/dist/m/demo`
    *   **NC 模块根目录**: `/usr/local/nginx/dist/m/demo` (包含 `demo.js`, `views/`)
    *   **React 应用目录**: `/usr/local/nginx/dist/m/demo/agent-ui`
*   **后端服务端口**: `9020` (Docker/Systemd)
*   **Nginx 代理**: 
    *   前端访问: `/m/demo/agent-ui/` -> Alias 映射
    *   API 转发: `/agent-api/` -> `http://127.0.0.1:9020/agent-api/`

### 2.2 产物结构
构建脚本 (`build_intranet.sh`) 必须生成以下标准产物：
1.  **ops-agent-linux-x64.zip**: 后端单文件部署包（包含 Python 环境、依赖库、静态资源）。
2.  **demo.zip**: 前端完整模块包（包含 Vue 外壳 + React 内嵌应用），**严禁包含** 测试文件 (`Menu1`, `TestPage` 等)。
3.  **agent-ui.zip**: 仅包含 React 前端静态资源（作为备用或独立部署用）。

## 3. 开发规范 (Development Rules)

### 3.1 前端开发
*   **路由模式**: React 应用必须使用 **`HashRouter`**，避免与 NC 框架的 History 路由冲突。
*   **Base URL**: Vite 配置中的 `base` 必须设置为 `/m/demo/agent-ui/`。
*   **鉴权**: 优先从 URL 参数或 `nc.util.getStore` 获取 Token，开发环境支持降级模式。
*   **访客模式**: 必须通过 `userRole` 判断，对 Guest 用户隐藏 "运行简报"、"进化历程"、"数据看板" 等敏感菜单。

### 3.2 后端开发
*   **兼容性**: 必须兼容 Linux GLIBC 2.17+ (CentOS 7)，构建时需排除高版本系统库。
*   **数据库**: 使用 PostgreSQL + pgvector，向量维度固定为 **1024**。
*   **静态资源**: 生产环境使用 `StaticFiles` 挂载前端资源，实现单端口服务。
*   **接口规范**: 所有 API 需支持 `/agent-api` 前缀。

### 3.3 构建与发布
*   **脚本**: 统一使用 `build_intranet.sh` 进行构建。
*   **清理**: 构建结束后必须自动清理所有中间产物 (`build_env`, `dist`, `build`, `*.spec`)，保持项目根目录整洁。
*   **校验**: 发布前必须验证 `demo.zip` 的目录结构是否符合 NC 模块规范。

## 4. 常见问题 (Troubleshooting)
*   **500 错误**: 检查向量数据库维度是否匹配 (1024 vs 1536)。
*   **404 错误 (Iframe)**: 检查 Nginx `try_files` 配置是否针对 `agent-ui` 独立设置。
*   **权限错误**: 检查 `X-Frame-Options` 是否允许 Iframe 嵌入。


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


---


# Git 分支管理新手指南

## 1. 什么是分支 (Branch)？
想象你的代码是一棵树的主干（`main` 分支）。
当你想要开发一个新功能或者尝试修复一个 Bug 时，为了不影响主干的稳定性，你可以从主干上“长”出一个新的树枝（新分支）。
在这个新树枝上，你可以随意修改代码。哪怕改乱了，也不会影响到主干。等你觉得新功能完美了，再把这个树枝合并回主干。

## 2. 常用命令速查表

| 你的目的 | 终端命令 | 说明 |
| :--- | :--- | :--- |
| **查看所有分支** | `git branch -a` | 列出本地和远程的所有分支。当前所在分支前会有 `*` 号。 |
| **创建并切换** | `git checkout -b <新分支名>` | **最常用**。创建一个新分支并立即跳过去。 |
| **仅切换分支** | `git checkout <分支名>` | 在已有的分支之间跳来跳去。 |
| **仅创建分支** | `git branch <新分支名>` | 创建一个新分支，但人还留在老分支上（不常用）。 |
| **删除分支** | `git branch -d <分支名>` | 删除一个不需要的分支。**注意**：不能删除当前所在的分支。 |
| **合并分支** | `git merge <分支名>` | 把别的分支的代码合并到当前分支来。 |

## 3. 实战场景演示

### 场景一：开发一个新功能（比如“登录页面”）
1.  **切出新分支**：先确保自己在主分支，然后切出一个叫 `feature-login` 的分支。
    ```bash
    git checkout main
    git checkout -b feature-login
    ```
2.  **安心写代码**：在这个分支上修改文件、测试。
3.  **提交保存**：
    ```bash
    git add .
    git commit -m "完成登录页面开发"
    ```
4.  **合并回主干**（功能开发完了，要上线）：
    ```bash
    git checkout main       # 先切回主分支
    git merge feature-login # 把 feature-login 的成果合并过来
    ```
5.  **清理战场**：
    ```bash
    git branch -d feature-login # 删除已经合并过的功能分支
    ```

### 场景二：放弃尝试
如果你在 `test-idea` 分支上乱改一通，最后发现思路不对，想完全放弃：
```bash
git checkout main          # 回到安全的主分支
git branch -D test-idea    # 强制删除那个乱改的分支（注意是大写 D）
```

## 4. 远程分支（GitHub 上的分支）
如果想把你的新分支推送到 GitHub 上给同事看：
```bash
git push origin <分支名>
```
例如：`git push origin feature-login`
