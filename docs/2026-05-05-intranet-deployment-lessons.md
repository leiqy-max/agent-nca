# 2026-05-05 内网部署与问答优化经验记录

## 背景

本次将 Ops Agent 从开发环境迁移到内网 Linux 生产环境，目标是完成后端二进制包、前端 NC 子目录包、本地 Ollama 大模型、pgvector 知识库和混合检索链路的可用性验证。

目标内网机器为 8 核 CPU、125GiB 内存、BCLinux 8.2 类环境，glibc 基线约为 2.28，主要运行 CPU 版 Ollama。

## 关键问题与处理

### 1. Python 3.9 类型语法兼容

现象：二进制启动时报错：

```text
TypeError: unsupported operand type(s) for |: '_GenericAlias' and 'NoneType'
```

原因：打包环境使用 Python 3.9，代码里使用了 `Dict[...] | None` 这类 Python 3.10+ 类型语法。

处理：改为 `Optional[Dict[...]]`，并用 Python 3.9 执行 `py_compile` 验证。

### 2. bcrypt 与 glibc 不兼容

现象：内网启动时报错：

```text
ImportError: /lib64/libc.so.6: version `GLIBC_2.33' not found
```

原因：打包进二进制的 `bcrypt` native so 依赖过高版本 glibc。

处理：

- 固定 `bcrypt==4.0.1`，其 so 最高依赖 `GLIBC_2.28`。
- `auth.py` 改为懒加载 bcrypt。
- bcrypt 不可用时使用标准库 PBKDF2-SHA256 兜底，避免认证模块启动即崩。

验证：

```bash
strings bcrypt/_bcrypt.abi3.so | grep GLIBC_
```

确认无 `GLIBC_2.33`。

### 3. OpenCV / RapidOCR / PyInstaller 打包问题

现象：复用构建 venv 时，`rapidocr_onnxruntime` 导入失败：

```text
ModuleNotFoundError: No module named 'cv2'
```

原因：`opencv-python` 和 `opencv-python-headless` 共用 `cv2` 文件。卸载非 headless 包后，pip 认为 headless 已安装，但实际 `cv2` 目录可能已被删除。

处理：

- 固定 `opencv-python-headless==4.10.0.84`。
- 卸载 GUI OpenCV 后强制重装 headless。
- 不再删除 OpenCV metadata，避免 PyInstaller `hook-cv2.py` 无法定位包。

### 4. 前端 NC 子目录部署 404

现象：页面访问 `/m/demo/agent-ui/`，但 JS/CSS 请求到 `/assets/...`，返回 404。

原因：Vite `base` 为 `/`，构建出的静态资源使用根路径。

处理：

- Vite `base` 改为 `./`。
- 生成 `release/demo.zip`，结构固定为：

```text
demo/
  agent-ui/
    index.html
    assets/
```

验证：

```text
/m/demo/agent-ui/                          200
/m/demo/agent-ui/assets/index-*.js         200
/m/demo/agent-ui/assets/index-*.css        200
```

### 5. Ollama 意图识别导致问答慢 120 秒

现象：普通问题两分钟才回复，日志显示：

```text
[LLM] start purpose=classify_intent
...
Read timed out. (read timeout=120)
```

实际耗时拆分：

```text
classify_intent: 120s
embedding:       约 5s
BM25:            约 0.1s
```

原因：每次 RAG 前先让本地 `qwen2.5:1.5b` 做意图识别，CPU Ollama 冷启动或推理阻塞时会卡满 120 秒。

处理：

- 默认关闭 LLM 意图识别：`intent_classify_enabled: false`。
- 明确闲聊才走闲聊，其它默认作为专业问题直接检索。
- 补充稳定中文关键词，避免编码问题导致“天线、经纬度、校验”等专业词不命中。
- 低信息输入如 `1`、空输入、纯符号直接提示补充问题，不进 LLM。
- 保留可选配置：

```yaml
llm:
  classify_timeout: 15
  classify_num_predict: 8
  classify_num_ctx: 512
  intent_classify_enabled: false
  ollama_keep_alive: "30m"
```

新包启动日志应包含：

```text
"llm_intent_classify_enabled": "False"
```

正常专业问答日志不应再出现：

```text
purpose=classify_intent
```

### 6. 混合检索链路

当前检索链路为：

```text
向量检索 + 本地 BM25 + RRF 融合 + 可选 rerank + 上下文扩展
```

小规模内网部署优先采用 PostgreSQL + pgvector + 应用内 BM25，避免引入过多外部组件。后续数据量明显增大时，再考虑 ParadeDB、Elasticsearch/OpenSearch 或独立 rerank 服务。

## 交付注意事项

- GitHub 普通仓库不能直接提交超过 100MB 的后端二进制 zip。`release/ops-agent-linux-x64.zip` 应通过制品库、GitHub Release、内网文件服务器或 Git LFS 交付。
- 生产替换后端包后，先检查启动日志中的 `runtime_config`，确认配置确实生效。
- 切换 embedding 模型或维度后，需要重新向量化文档，避免旧向量维度与新模型不一致。
- 前端 NC 场景优先部署 `demo.zip`，不要把纯根路径静态包直接放到 `/m/demo/agent-ui/` 下。

## 推荐验证命令

Ollama 生成：

```bash
time curl http://127.0.0.1:11434/api/chat -d '{
  "model": "qwen2.5:1.5b",
  "messages": [{"role": "user", "content": "只回答：你好"}],
  "stream": false,
  "options": {"num_predict": 8, "num_ctx": 512}
}'
```

Ollama embedding：

```bash
time curl http://127.0.0.1:11434/api/embeddings -d '{
  "model": "nomic-embed-text:latest",
  "prompt": "测试"
}'
```

后端启动：

```bash
unzip -o ops-agent-linux-x64.zip
chmod +x ops-agent
./ops-agent
```

前端 NC 包：

```bash
unzip -o demo.zip -d /usr/local/nginx/dist/m
```
