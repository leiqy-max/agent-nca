# Ops Agent 智能运维问答助手

Ops Agent 是面向运维知识场景的本地化问答系统，支持文本和图片提问、知识库文档管理、文档在线预览、问答补全与 AI 润色、权限管理和审批工作流。系统基于 RAG 技术，将上传的运维文档、Q&A 记录和历史知识转化为可检索内容，再结合大模型生成面向业务问题的回答。

项目当前同时支持三类使用方式：

- 本地开发：前端 Vite + React，后端 FastAPI，数据库 PostgreSQL + pgvector。
- Docker 快速部署：使用 `docker-compose.yml` 启动前端、后端和数据库。
- 内网部署：后端打成 Linux x64 单文件包，前端打成 NC 子目录静态包，可配合本地 Ollama 在无公网环境运行。

默认管理员账号为 `admin` / `admin123`，首次启动时后端会自动初始化基础表结构和默认账号。

## 核心能力

- 智能问答：支持文本提问和图片相关提问。
- 知识库管理：支持 PDF、DOCX、TXT、MD、XLSX 等文件入库。
- 混合检索：向量检索 + BM25 + RRF 融合 + 可选 rerank + 上下文扩展。
- 本地模型适配：支持 Ollama 聊天模型和 embedding 模型。
- 在线预览：支持知识库文档预览和溯源。
- 权限控制：支持 Admin、User、Guest 等角色。
- 诊断可观测：后端提供运行配置、模型配置和 RAG 调试信息。

## 近期更新

### 内网交付适配

- 新增后端内网单文件打包脚本 `build_intranet.sh`，输出 `ops-agent-linux-x64.zip`。
- 内网包默认携带 `config.ollama.local.yaml`，启动后读取为 `config.yaml`。
- 打包环境固定 Python 3.9.18，兼容 BCLinux 8.2 / glibc 2.28 类内网服务器。
- 固定 `bcrypt==4.0.1`，并增加 PBKDF2-SHA256 兜底，避免旧 glibc 环境启动失败。
- 修复 OpenCV / RapidOCR / PyInstaller 打包兼容问题，OCR 依赖可按需打入包内。

### 前端 NC 子目录部署

- Vite 静态资源路径改为相对路径，支持部署到 `/m/demo/agent-ui/` 等子目录。
- 新增前端内网包生成流程，`build_frontend_package.sh` 输出 `demo.zip`。
- `demo.zip` 固定目录结构为：

```text
demo/
  agent-ui/
    index.html
    assets/
```

### 本地 Ollama 与 RAG 优化

- 新增 `config.ollama.local.yaml`，支持内网本地 Ollama 聊天模型和 embedding 模型。
- 默认关闭 LLM 意图识别：`intent_classify_enabled: false`，避免 CPU 版 Ollama 每次问答前卡在意图识别。
- 增加 `rag_timeout`、`rag_num_predict`、`rag_num_ctx`、`ollama_keep_alive` 等本地推理参数。
- 支持会话上下文，聊天请求携带 `conversation_id` 并记录到 `chat_logs`。
- 增加 embedding 维度启动检查，切换 embedding 模型后可通过重建脚本重新向量化知识库。

## 快速启动

### Docker 启动

适合本地快速验证：

```bash
docker compose up -d
```

访问地址：

```text
http://localhost:5173
```

后端 API 默认映射到：

```text
http://localhost:9020
```

### 本地开发启动

后端：

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

前端：

```bash
cd frontend
npm install
npm run dev
```

如果宿主机必须保留 Node 14，可使用 Docker 构建前端，避免升级全局 Node：

```bash
./scripts/build_frontend_docker.sh
docker compose up -d
```

Windows 可运行：

```powershell
.\scripts\build_frontend_docker.bat
docker compose up -d
```

## 内网部署方法

以下流程面向内网 Linux 服务器，推荐用于 BCLinux 8.2、CentOS/RHEL 类环境。后端以单文件方式运行，前端以 NC 子目录静态资源包方式部署。

### 1. 准备基础服务

服务器需要提前准备：

- PostgreSQL 14+，并安装 `pgvector` 扩展。
- Ollama，本地可访问地址默认为 `http://127.0.0.1:11434`。
- Nginx 或 NC 平台静态资源目录，用于部署前端 `demo.zip`。

创建数据库并启用向量扩展：

```sql
CREATE DATABASE ops_agent;
\c ops_agent
CREATE EXTENSION vector;
```

拉取或准备 Ollama 模型，示例：

```bash
ollama pull qwen2.5:1.5b
ollama pull nomic-embed-text:latest
```

如使用其它 embedding 模型，请同步修改 `config.yaml` 中的 `embedding_model` 和 `embedding_dimension`。

### 2. 构建后端内网包

在可联网或已缓存依赖的构建机上执行：

```bash
bash build_frontend_package.sh
bash build_intranet.sh
```

后端输出文件：

```text
ops-agent-linux-x64.zip
```

压缩包内包含：

```text
ops-agent
config.yaml
README.txt
```

说明：

- `build_intranet.sh` 会先把 `frontend/dist` 拷贝到 `backend/static`，因此需要先执行前端构建。
- 如需复用构建缓存，可保留 `build_env`。
- 如需干净构建，可设置 `CLEAN_BUILD_ENV=1`。

### 3. 构建前端 NC 包

执行：

```bash
bash build_frontend_package.sh
```

输出文件：

```text
demo.zip
```

部署到 NC 静态目录：

```bash
unzip -o demo.zip -d /usr/local/nginx/dist/m
```

部署后应能访问：

```text
/m/demo/agent-ui/
/m/demo/agent-ui/assets/index-*.js
/m/demo/agent-ui/assets/index-*.css
```

### 4. 部署并启动后端

将 `ops-agent-linux-x64.zip` 上传到内网服务器后执行：

```bash
mkdir -p ops-agent-linux-x64
unzip -o ops-agent-linux-x64.zip -d ops-agent-linux-x64
cd ops-agent-linux-x64
chmod +x ops-agent
./ops-agent
```

如果压缩包直接解到当前目录，则执行：

```bash
chmod +x ops-agent
./ops-agent
```

后端默认监听：

```text
0.0.0.0:9020
```

### 5. 修改内网配置

后端包中的 `config.yaml` 参考 `config.ollama.local.yaml`。常用配置如下：

```yaml
database:
  host: "localhost"
  port: 5432
  user: "ops_user"
  password: "ops_password"
  dbname: "ops_agent"

llm:
  provider: "ollama"
  ollama_base_url: "http://127.0.0.1:11434"
  model: "qwen2.5:1.5b"
  embedding_model: "nomic-embed-text:latest"
  embedding_dimension: 768
  intent_classify_enabled: false
  rag_timeout: 45
  ollama_keep_alive: "30m"

server:
  host: "0.0.0.0"
  port: 9020
```

生产环境请修改数据库账号、密码和模型名称，不要把真实密钥或生产密码提交到 Git。

### 6. Nginx 代理建议

前端页面如果通过 NC 子目录访问，可将后端 API 代理到 `9020`：

```nginx
location /agent-api/ {
    proxy_pass http://127.0.0.1:9020/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_read_timeout 180s;
    proxy_send_timeout 180s;
}
```

对于本地 Ollama + CPU 推理，建议保留较长的代理超时时间，避免后端已完成但前端链路先返回 504。

### 7. 验证部署

检查 Ollama 生成：

```bash
time curl http://127.0.0.1:11434/api/chat -d '{
  "model": "qwen2.5:1.5b",
  "messages": [{"role": "user", "content": "只回答：你好"}],
  "stream": false,
  "options": {"num_predict": 8, "num_ctx": 512}
}'
```

检查 Ollama embedding：

```bash
time curl http://127.0.0.1:11434/api/embeddings -d '{
  "model": "nomic-embed-text:latest",
  "prompt": "测试"
}'
```

检查后端启动日志，重点确认：

```text
runtime_config
llm_intent_classify_enabled=False
```

正常专业问答不应再频繁出现：

```text
purpose=classify_intent
```

### 8. 切换 embedding 模型后的处理

如果更换 embedding 模型或维度，需要重建向量表：

```bash
cd backend
python scripts/rebuild_vector_store.py --yes
```

该脚本会重建 `documents` 向量表，并重新导入已审批的上传文件和已审批的学习问答记录。

## 常用文档

- `README_QUICK_START.md`：快速启动说明。
- `README_LOCAL_OLLAMA.md`：本地 Ollama 开发说明。
- `DEPLOY.md`：完整部署指南。
- `WINDOWS_DEPLOY.md`：Windows 部署说明。
- `docs/2026-05-05-intranet-deployment-lessons.md`：内网部署问题与优化记录。

## 注意事项

- `ops-agent-linux-x64.zip` 体积较大，普通 Git 平台可能限制超过 100MB 的文件提交；建议通过内网制品库、文件服务器或 Git LFS 交付二进制包。
- 生产环境替换后端包后，先检查启动日志中的 `runtime_config`，确认实际配置已生效。
- 前端 NC 部署优先使用 `demo.zip`，不要把根路径静态包直接放到 `/m/demo/agent-ui/` 下。
- 生产配置、数据库密码、API Key 等敏感信息不要提交到仓库。
