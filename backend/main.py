import os
import sys
import yaml
import csv
import io
import logging
import traceback

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s"
)


def _clean_config_value(value):
    if isinstance(value, str):
        return os.path.expandvars(value).strip().strip('`').strip()
    return value


# Support for Intranet Binary: Load config.yaml if exists
if os.path.exists("config.yaml"):
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            if config:
                # Parse Database Config
                if "database" in config:
                    db = config["database"]
                    if "host" in db: os.environ["DB_HOST"] = str(db["host"])
                    if "port" in db: os.environ["DB_PORT"] = str(db["port"])
                    if "user" in db: os.environ["DB_USER"] = str(db["user"])
                    if "password" in db: os.environ["DB_PASSWORD"] = str(db["password"])
                    if "dbname" in db: os.environ["DB_NAME"] = str(db["dbname"])

                # Parse LLM Config
                if "llm" in config:
                    llm = config["llm"]
                    if "provider" in llm: os.environ["LLM_PROVIDER"] = str(_clean_config_value(llm["provider"]))
                    if "api_key" in llm: os.environ["LLM_API_KEY"] = str(_clean_config_value(llm["api_key"]))
                    if "base_url" in llm: os.environ["LLM_BASE_URL"] = str(_clean_config_value(llm["base_url"]))
                    if "chat_base_url" in llm: os.environ["LLM_BASE_URL"] = str(_clean_config_value(llm["chat_base_url"]))
                    if "model" in llm: os.environ["LLM_MODEL"] = str(_clean_config_value(llm["model"]))
                    if "vision_model" in llm: os.environ["VISION_MODEL"] = str(_clean_config_value(llm["vision_model"]))
                    if "embedding_base_url" in llm: os.environ["EMBEDDING_BASE_URL"] = str(_clean_config_value(llm["embedding_base_url"]))
                    if "embedding_model" in llm: os.environ["EMBEDDING_MODEL"] = str(_clean_config_value(llm["embedding_model"]))
                    if "ollama_base_url" in llm: os.environ["OLLAMA_BASE_URL"] = str(_clean_config_value(llm["ollama_base_url"]))
                    if "timeout" in llm: os.environ["LLM_TIMEOUT"] = str(_clean_config_value(llm["timeout"]))
                    if "embedding_timeout" in llm: os.environ["EMBEDDING_TIMEOUT"] = str(_clean_config_value(llm["embedding_timeout"]))
                    if "embedding_dimension" in llm: os.environ["EMBEDDING_DIMENSION"] = str(_clean_config_value(llm["embedding_dimension"]))
                    if "classify_timeout" in llm: os.environ["LLM_CLASSIFY_TIMEOUT"] = str(_clean_config_value(llm["classify_timeout"]))
                    if "classify_num_predict" in llm: os.environ["LLM_CLASSIFY_NUM_PREDICT"] = str(_clean_config_value(llm["classify_num_predict"]))
                    if "classify_num_ctx" in llm: os.environ["LLM_CLASSIFY_NUM_CTX"] = str(_clean_config_value(llm["classify_num_ctx"]))
                    if "intent_classify_enabled" in llm: os.environ["LLM_INTENT_CLASSIFY_ENABLED"] = str(_clean_config_value(llm["intent_classify_enabled"]))
                    if "rag_timeout" in llm: os.environ["LLM_RAG_TIMEOUT"] = str(_clean_config_value(llm["rag_timeout"]))
                    if "rag_num_predict" in llm: os.environ["LLM_RAG_NUM_PREDICT"] = str(_clean_config_value(llm["rag_num_predict"]))
                    if "rag_num_ctx" in llm: os.environ["LLM_RAG_NUM_CTX"] = str(_clean_config_value(llm["rag_num_ctx"]))
                    if "rag_temperature" in llm: os.environ["LLM_RAG_TEMPERATURE"] = str(_clean_config_value(llm["rag_temperature"]))
                    if "ollama_keep_alive" in llm: os.environ["OLLAMA_KEEP_ALIVE"] = str(_clean_config_value(llm["ollama_keep_alive"]))

                if "retrieval" in config:
                    retrieval = config["retrieval"]
                    if "vector_top_k" in retrieval: os.environ["VECTOR_TOP_K"] = str(retrieval["vector_top_k"])
                    if "keyword_top_k" in retrieval: os.environ["KEYWORD_TOP_K"] = str(retrieval["keyword_top_k"])
                    if "bm25_top_k" in retrieval: os.environ["BM25_TOP_K"] = str(retrieval["bm25_top_k"])
                    if "bm25_max_docs" in retrieval: os.environ["BM25_MAX_DOCS"] = str(retrieval["bm25_max_docs"])
                    if "final_top_k" in retrieval: os.environ["FINAL_TOP_K"] = str(retrieval["final_top_k"])
                    if "fusion_top_k" in retrieval: os.environ["FUSION_TOP_K"] = str(retrieval["fusion_top_k"])
                    if "rrf_k" in retrieval: os.environ["RRF_K"] = str(retrieval["rrf_k"])
                    if "rerank_enabled" in retrieval: os.environ["RERANK_ENABLED"] = str(retrieval["rerank_enabled"])
                    if "rerank_provider" in retrieval: os.environ["RERANK_PROVIDER"] = str(retrieval["rerank_provider"])
                    if "rerank_endpoint" in retrieval: os.environ["RERANK_ENDPOINT"] = str(_clean_config_value(retrieval["rerank_endpoint"]))
                    if "rerank_timeout" in retrieval: os.environ["RERANK_TIMEOUT"] = str(retrieval["rerank_timeout"])
                    if "context_expand_window" in retrieval: os.environ["CONTEXT_EXPAND_WINDOW"] = str(retrieval["context_expand_window"])
                    if "rag_context_max_chars" in retrieval: os.environ["RAG_CONTEXT_MAX_CHARS"] = str(retrieval["rag_context_max_chars"])
                    if "short_query_max_chars" in retrieval: os.environ["SHORT_QUERY_MAX_CHARS"] = str(retrieval["short_query_max_chars"])
                    if "create_vector_index" in retrieval: os.environ["CREATE_VECTOR_INDEX"] = str(retrieval["create_vector_index"])

                # Parse Server Config
                if "server" in config:
                    srv = config["server"]
                    if "host" in srv: os.environ["HOST"] = str(srv["host"])
                    if "port" in srv: os.environ["PORT"] = str(srv["port"])

                # Parse flat keys (legacy support)
                for key, value in config.items():
                    if isinstance(value, (str, int, float, bool)):
                         os.environ[str(key)] = str(value)
                print("Loaded configuration from config.yaml")
    except Exception as e:
        print(f"Error loading config.yaml: {e}")

from fastapi import FastAPI, Request, UploadFile, File, Depends, HTTPException, status, Form, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import uuid
import os
import shutil
import jinja2 # Force import for PyInstaller
import markupsafe # Force import for PyInstaller
from collections import Counter, deque
from llm.factory import get_llm_client
from llm.embedding import embed_text
from rag.qa import answer_question
from rag.loader import load_document, load_text_content, delete_document_by_source
from db import engine
from sqlalchemy import text
from typing import Any, Dict, List
from datetime import timedelta, datetime
import io
import base64
from captcha.image import ImageCaptcha

import json

# Import Auth
from auth import (
    User, UserInDB, Token, authenticate_user, create_access_token, 
    get_current_active_user, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES,
    get_user
)

# Import DOCX Converter for server-side preview
from docx_converter import get_file_preview_html


def _mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}****{value[-4:]}"


def runtime_config_summary() -> Dict[str, Any]:
    return {
        "llm_provider": os.getenv("LLM_PROVIDER", "zhipu"),
        "llm_model": os.getenv("LLM_MODEL"),
        "vision_model": os.getenv("VISION_MODEL"),
        "llm_base_url": os.getenv("LLM_BASE_URL"),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL"),
        "embedding_model": os.getenv("EMBEDDING_MODEL"),
        "embedding_base_url": os.getenv("EMBEDDING_BASE_URL"),
        "embedding_dimension": os.getenv("EMBEDDING_DIMENSION"),
        "llm_timeout": os.getenv("LLM_TIMEOUT"),
        "llm_classify_timeout": os.getenv("LLM_CLASSIFY_TIMEOUT"),
        "llm_classify_num_predict": os.getenv("LLM_CLASSIFY_NUM_PREDICT"),
        "llm_classify_num_ctx": os.getenv("LLM_CLASSIFY_NUM_CTX"),
        "llm_intent_classify_enabled": os.getenv("LLM_INTENT_CLASSIFY_ENABLED"),
        "llm_rag_timeout": os.getenv("LLM_RAG_TIMEOUT"),
        "llm_rag_num_predict": os.getenv("LLM_RAG_NUM_PREDICT"),
        "llm_rag_num_ctx": os.getenv("LLM_RAG_NUM_CTX"),
        "llm_rag_temperature": os.getenv("LLM_RAG_TEMPERATURE"),
        "ollama_keep_alive": os.getenv("OLLAMA_KEEP_ALIVE"),
        "embedding_timeout": os.getenv("EMBEDDING_TIMEOUT"),
        "api_key": os.getenv("LLM_API_KEY", ""),
        "retrieval": {
            "vector_top_k": os.getenv("VECTOR_TOP_K"),
            "keyword_top_k": os.getenv("KEYWORD_TOP_K"),
            "bm25_top_k": os.getenv("BM25_TOP_K"),
            "bm25_max_docs": os.getenv("BM25_MAX_DOCS"),
            "final_top_k": os.getenv("FINAL_TOP_K"),
            "fusion_top_k": os.getenv("FUSION_TOP_K"),
            "rrf_k": os.getenv("RRF_K"),
            "rerank_enabled": os.getenv("RERANK_ENABLED"),
            "rerank_provider": os.getenv("RERANK_PROVIDER"),
            "rerank_endpoint": os.getenv("RERANK_ENDPOINT"),
            "context_expand_window": os.getenv("CONTEXT_EXPAND_WINDOW"),
            "rag_context_max_chars": os.getenv("RAG_CONTEXT_MAX_CHARS"),
            "short_query_max_chars": os.getenv("SHORT_QUERY_MAX_CHARS"),
            "create_vector_index": os.getenv("CREATE_VECTOR_INDEX"),
        },
        "conversation": {
            "history_turns": os.getenv("CONVERSATION_HISTORY_TURNS", "4"),
            "history_chars": os.getenv("CONVERSATION_HISTORY_CHARS", "3000"),
        },
        "return_rag_debug": os.getenv("RETURN_RAG_DEBUG", "false"),
    }


def ensure_app_schema_migrations(trace_id: str = "startup") -> None:
    with engine.begin() as conn:
        logger.info("[DB][%s] ensuring application schema migrations", trace_id)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_logs (
                id SERIAL PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT,
                feedback VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("ALTER TABLE chat_logs ADD COLUMN IF NOT EXISTS username VARCHAR(50)"))
        conn.execute(text("ALTER TABLE chat_logs ADD COLUMN IF NOT EXISTS image_path VARCHAR(512)"))
        conn.execute(text("ALTER TABLE chat_logs ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'normal'"))
        conn.execute(text("ALTER TABLE chat_logs ADD COLUMN IF NOT EXISTS sources JSONB"))
        conn.execute(text("ALTER TABLE chat_logs ADD COLUMN IF NOT EXISTS conversation_id VARCHAR(64)"))
        conn.execute(text("ALTER TABLE chat_logs ADD COLUMN IF NOT EXISTS rag_debug JSONB"))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS learned_qa (
                id SERIAL PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("ALTER TABLE learned_qa ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'approved'"))
        conn.execute(text("ALTER TABLE learned_qa ADD COLUMN IF NOT EXISTS username VARCHAR(50)"))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS question_history (
                id SERIAL PRIMARY KEY,
                question TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        logger.info("[DB][%s] application schema migrations complete", trace_id)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _run_optional_schema_sql(trace_id: str, name: str, sql: str) -> None:
    try:
        with engine.begin() as conn:
            conn.execute(text(sql))
        logger.info("[DB][%s] schema_sql_ok name=%s", trace_id, name)
    except Exception as exc:
        logger.warning("[DB][%s] schema_sql_skipped name=%s error=%s", trace_id, name, exc, exc_info=True)


def ensure_document_indexes(trace_id: str = "startup") -> None:
    logger.info("[DB][%s] ensuring document indexes", trace_id)
    index_sql = {
        "documents_metadata_gin": """
            CREATE INDEX IF NOT EXISTS idx_documents_metadata_gin
            ON documents USING GIN (metadata)
        """,
        "documents_kb_type": """
            CREATE INDEX IF NOT EXISTS idx_documents_kb_type
            ON documents ((metadata->>'kb_type'))
        """,
        "documents_source": """
            CREATE INDEX IF NOT EXISTS idx_documents_source
            ON documents ((metadata->>'source'))
        """,
        "documents_source_chunk": """
            CREATE INDEX IF NOT EXISTS idx_documents_source_chunk
            ON documents ((metadata->>'source'), ((metadata->>'chunk_index')::int))
            WHERE metadata ? 'chunk_index'
        """,
        "documents_text_simple_gin": """
            CREATE INDEX IF NOT EXISTS idx_documents_text_simple_gin
            ON documents USING GIN (to_tsvector('simple', COALESCE(content, '')))
        """,
    }
    for name, sql in index_sql.items():
        _run_optional_schema_sql(trace_id, name, sql)

    if _env_bool("CREATE_VECTOR_INDEX", True):
        _run_optional_schema_sql(
            trace_id,
            "documents_embedding_hnsw",
            """
                CREATE INDEX IF NOT EXISTS idx_documents_embedding_hnsw
                ON documents USING hnsw (embedding vector_l2_ops)
            """,
        )


# 数据库初始化 (适配 Docker/Mac 首次运行)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    try:
        logger.info(f"[Startup] runtime_config={json.dumps(runtime_config_summary(), ensure_ascii=False)}")
        configured_dim = int(os.getenv("EMBEDDING_DIMENSION", "1024"))
        ensure_app_schema_migrations("startup")
        if "EMBEDDING_DIMENSION" not in os.environ:
            try:
                probe_vector = embed_text("embedding dimension probe")
                if probe_vector:
                    configured_dim = len(probe_vector)
                    os.environ["EMBEDDING_DIMENSION"] = str(configured_dim)
                    logger.info(f"[Startup] detected embedding dimension={configured_dim}")
            except Exception as e:
                logger.warning(f"[Startup] failed to probe embedding dimension, fallback to {configured_dim}: {e}")

        with engine.connect() as conn:
            # 启用 pgvector 扩展
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            vector_meta = conn.execute(text("""
                SELECT a.atttypmod
                FROM pg_attribute a
                JOIN pg_class c ON a.attrelid = c.oid
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE c.relname = 'documents'
                  AND a.attname = 'embedding'
                  AND a.atttypid = 'vector'::regtype
                  AND n.nspname = current_schema()
            """)).fetchone()

            if vector_meta:
                current_dim = vector_meta[0] if vector_meta[0] and vector_meta[0] > 0 else None
                if current_dim and current_dim != configured_dim:
                    doc_count = conn.execute(text("SELECT COUNT(*) FROM documents")).scalar() or 0
                    if doc_count == 0:
                        conn.execute(text(f"ALTER TABLE documents ALTER COLUMN embedding TYPE vector({configured_dim})"))
                        logger.info(f"[Startup] updated documents.embedding dimension {current_dim} -> {configured_dim}")
                    else:
                        raise RuntimeError(
                            f"documents.embedding dimension is {current_dim}, but the current embedding model outputs {configured_dim}. "
                            "Clear and rebuild the vector table before switching embedding models."
                        )
            # 创建 documents 表 (Zhipu embedding-2 维度为 1024)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    metadata JSONB,
                    embedding vector(%d)
                )
            """ % configured_dim))
            # 创建 chat_logs 表 (用于记录完整问答和反馈)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id SERIAL PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT,
                    feedback VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            # Add username column if not exists
            try:
                conn.execute(text("ALTER TABLE chat_logs ADD COLUMN IF NOT EXISTS username VARCHAR(50)"))
                conn.execute(text("ALTER TABLE chat_logs ADD COLUMN IF NOT EXISTS image_path VARCHAR(512)"))
                conn.execute(text("ALTER TABLE chat_logs ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'normal'"))
                conn.execute(text("ALTER TABLE chat_logs ADD COLUMN IF NOT EXISTS sources JSONB"))
                conn.execute(text("ALTER TABLE chat_logs ADD COLUMN IF NOT EXISTS conversation_id VARCHAR(64)"))
                conn.execute(text("ALTER TABLE chat_logs ADD COLUMN IF NOT EXISTS rag_debug JSONB"))
            except Exception as e:
                print(f"Migration note: {e}")

            # Create learned_qa table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS learned_qa (
                    id SERIAL PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            try:
                conn.execute(text("ALTER TABLE learned_qa ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'approved'"))
                conn.execute(text("ALTER TABLE learned_qa ADD COLUMN IF NOT EXISTS username VARCHAR(50)"))
            except Exception as e:
                print(f"Migration note (learned_qa): {e}")
            
            # 创建 question_history 表 (保留旧表定义以免报错，后续可迁移)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS question_history (
                    id SERIAL PRIMARY KEY,
                    question TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Create Users Table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL
                )
            """))

            # Create Admin Whitelist Table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS admin_whitelist (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            # Seed default admin in whitelist if empty
            result = conn.execute(text("SELECT username FROM admin_whitelist WHERE username = 'admin'")).fetchone()
            if not result:
                conn.execute(text("INSERT INTO admin_whitelist (username) VALUES ('admin')"))
                print("Created default admin in whitelist")

            # Create Uploaded Files Table (for approval workflow)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS uploaded_files (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    file_path VARCHAR(512) NOT NULL,
                    uploader VARCHAR(50) NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, rejected
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            # Add new columns for Knowledge Docs feature
            try:
                conn.execute(text("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS download_count INTEGER DEFAULT 0"))
                conn.execute(text("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS file_size INTEGER DEFAULT 0"))
                conn.execute(text("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS kb_type VARCHAR(20) DEFAULT 'user'"))
            except Exception as e:
                print(f"Migration note (uploaded_files): {e}")
            conn.commit()
            
            # Seed Default Users
            # Check if admin exists
            result = conn.execute(text("SELECT username FROM users WHERE username = 'admin'")).fetchone()
            if not result:
                admin_pwd = get_password_hash("admin123")
                conn.execute(text("INSERT INTO users (username, hashed_password, role) VALUES ('admin', :pwd, 'admin')"), {"pwd": admin_pwd})
                print("Created default admin user")
            
            result = conn.execute(text("SELECT username FROM users WHERE username = 'user'")).fetchone()
            if not result:
                user_pwd = get_password_hash("user123")
                conn.execute(text("INSERT INTO users (username, hashed_password, role) VALUES ('user', :pwd, 'user')"), {"pwd": user_pwd})
                print("Created default normal user")
                
            conn.commit()

        ensure_document_indexes("startup")
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Database initialization failed: {e}")
    
    yield
    # Shutdown logic (if any)

# 初始化 FastAPI
app = FastAPI(lifespan=lifespan)
api_router = APIRouter()

# Mount user images directory
if not os.path.exists("user_images"):
    os.makedirs("user_images")
app.mount("/user_images", StaticFiles(directory="user_images"), name="user_images")

# Mount uploads directory for file preview
upload_dir = "uploads"
if not os.path.exists(upload_dir):
    os.makedirs(upload_dir)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

# CAPTCHA Store (In-memory for simplicity)
CAPTCHA_STORE = {}

# Local file persistence for questions
QUESTION_HISTORY_FILE = "question_history.json"

def load_question_history():
    if os.path.exists(QUESTION_HISTORY_FILE):
        try:
            with open(QUESTION_HISTORY_FILE, "r", encoding="utf-8") as f:
                return deque(json.load(f), maxlen=500)
        except Exception as e:
            print(f"Error loading question history: {e}")
    return deque(maxlen=500)

def save_question_history(buffer):
    try:
        with open(QUESTION_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(list(buffer), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving question history: {e}")

question_buffer = load_question_history()


def normalize_conversation_id(raw_id: str = None) -> str:
    value = (raw_id or "").strip()
    if value and len(value) <= 64:
        return value
    return uuid.uuid4().hex


def request_history_to_messages(history: List[Any] = None) -> List[Dict[str, str]]:
    if not history:
        return []

    messages = []
    for item in history[-20:]:
        role = item.role
        content = (item.content or "").strip()
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})
    return messages


def load_conversation_history(username: str, conversation_id: str, limit: int = None) -> List[Dict[str, str]]:
    if not conversation_id:
        return []

    turn_limit = limit or int(os.getenv("CONVERSATION_HISTORY_TURNS", "4"))
    query = text("""
        SELECT question, answer
        FROM chat_logs
        WHERE username = :username
          AND conversation_id = :conversation_id
          AND answer IS NOT NULL
        ORDER BY created_at DESC
        LIMIT :limit
    """)
    params = {"username": username, "conversation_id": conversation_id, "limit": turn_limit}
    try:
        with engine.connect() as conn:
            rows = conn.execute(query, params).fetchall()
    except Exception as exc:
        logger.exception(
            "[DB] load_conversation_history failed; running schema migration and retrying "
            "username=%s conversation_id=%s error=%s",
            username,
            conversation_id,
            exc,
        )
        ensure_app_schema_migrations("conversation_history_retry")
        with engine.connect() as conn:
            rows = conn.execute(query, params).fetchall()

    messages = []
    for row in reversed(rows):
        question, answer = row
        if question:
            messages.append({"role": "user", "content": question})
        if answer:
            messages.append({"role": "assistant", "content": answer})
    return messages


# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应限制为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 使用 Jinja2 模板
templates = Jinja2Templates(directory="templates")

# Frontend Static Files Logic
# If frozen (PyInstaller), sys._MEIPASS/static
# If dev/local, check backend/static or frontend/dist (fallback)

if getattr(sys, 'frozen', False):
    # PyInstaller bundled mode
    BASE_DIR = sys._MEIPASS
    STATIC_DIR = os.path.join(BASE_DIR, "static")
else:
    # Development mode
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_DIR = os.path.join(BASE_DIR, "static")
    
    # Fallback for dev if static doesn't exist but dist_frontend does (legacy/dev support)
    if not os.path.exists(STATIC_DIR) and os.path.exists("dist_frontend"):
        STATIC_DIR = "dist_frontend"

if os.path.exists(STATIC_DIR):
    # Mount assets (CSS, JS, Images from Vite build)
    app.mount("/assets", StaticFiles(directory=f"{STATIC_DIR}/assets"), name="assets")
    # Support for NC Embedding (mapped path)
    app.mount("/agent-ui/assets", StaticFiles(directory=f"{STATIC_DIR}/assets"), name="assets_embedded")
    # Support for full NC path (when accessed directly via port 9020 but app requests this path)
    app.mount("/m/demo/agent-ui/assets", StaticFiles(directory=f"{STATIC_DIR}/assets"), name="assets_full_nc")

from typing import List, Optional

# 创建一个 Pydantic 模型来接收请求的 body
class ChatHistoryItem(BaseModel):
    role: str
    content: str


class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None
    conversation_id: Optional[str] = None
    history: Optional[List[ChatHistoryItem]] = None

class PolishRequest(BaseModel):
    question: str
    draft_answer: str

class FeedbackRequest(BaseModel):
    question_id: int
    status: str  # 'solved' or 'unsolved'

# 显示前端页面 (Standalone Root)
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    if os.path.exists(STATIC_DIR):
        return FileResponse(f"{STATIC_DIR}/index.html")
    return templates.TemplateResponse("index.html", {"request": request})

# 显示前端页面 (NC Embedding Path)
@app.get("/agent-ui", response_class=HTMLResponse)
@app.get("/agent-ui/", response_class=HTMLResponse)
@app.get("/m/demo/agent-ui", response_class=HTMLResponse)
@app.get("/m/demo/agent-ui/", response_class=HTMLResponse)
async def get_agent_ui_index(request: Request):
    if os.path.exists(STATIC_DIR):
        return FileResponse(f"{STATIC_DIR}/index.html")
    return templates.TemplateResponse("index.html", {"request": request})

@api_router.get("/captcha")
def get_captcha():
    image = ImageCaptcha(width=280, height=90)
    # Generate 4 char code
    captcha_text = "".join([str(uuid.uuid4().hex[i]) for i in range(4)])
    captcha_id = str(uuid.uuid4())
    
    data = image.generate(captcha_text)
    image_b64 = base64.b64encode(data.read()).decode('utf-8')
    
    CAPTCHA_STORE[captcha_id] = captcha_text
    # Cleanup old captchas? (Skipped for now, but in prod use Redis with TTL)
    
    return {"captcha_id": captcha_id, "image": f"data:image/png;base64,{image_b64}"}

# Login Endpoint
@api_router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    captcha_id: str = Form(None),
    captcha_code: str = Form(None)
):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role, "username": user.username}

class RegisterRequest(BaseModel):
    username: str
    password: str

@api_router.post("/register", response_model=Token)
async def register(request: RegisterRequest):
    if request.username == "admin":
         raise HTTPException(status_code=400, detail="Cannot register as admin")

    # Check if user exists
    with engine.begin() as conn:
        existing = conn.execute(text("SELECT username FROM users WHERE username = :u"), {"u": request.username}).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Create user (force role='user')
        hashed_pwd = get_password_hash(request.password)
        conn.execute(
            text("INSERT INTO users (username, hashed_password, role) VALUES (:u, :p, 'user')"),
            {"u": request.username, "p": hashed_pwd}
        )
    
    # Auto login
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.username, "role": "user"}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": "user", "username": request.username}

class DirectLoginRequest(BaseModel):
    username: str

@api_router.post("/sso-login", response_model=Token)
async def sso_login(request: DirectLoginRequest):
    username = request.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty")
        
    # 1. Determine Role
    # Check Admin Whitelist
    role = "user"
    with engine.connect() as conn:
        res = conn.execute(text("SELECT username FROM admin_whitelist WHERE username = :u"), {"u": username}).fetchone()
        if res:
            role = "admin"
            
    # 2. JIT Provisioning (Ensure user exists in users table)
    user = get_user(username)
    if not user:
        try:
            with engine.begin() as conn:
                # Use a dummy password hash since they auth via SSO
                dummy_pwd = get_password_hash(f"sso_{username}_{uuid.uuid4()}")
                conn.execute(
                    text("INSERT INTO users (username, hashed_password, role) VALUES (:u, :p, :r)"),
                    {"u": username, "p": dummy_pwd, "r": role}
                )
            user = get_user(username)
            print(f"[Auth] JIT Provisioned user via SSO: {username} (Role: {role})")
        except Exception as e:
            print(f"[Auth] Error JIT provisioning user {username}: {e}")
            raise HTTPException(status_code=500, detail="Login failed during provisioning")
    else:
        # Update role if changed (e.g. added/removed from whitelist)
        if user.role != role:
            with engine.begin() as conn:
                conn.execute(text("UPDATE users SET role = :r WHERE username = :u"), {"r": role, "u": username})
            user.role = role # Update local object
            print(f"[Auth] Updated role for {username} to {role}")

    # 3. Issue Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role, "username": user.username}

@api_router.post("/guest-token", response_model=Token)
async def guest_token():
    # Generate random guest ID
    guest_id = f"guest_{uuid.uuid4().hex[:8]}"
    
    # Add guest user with a pre-computed bcrypt hash (guest accounts don't use password login)
    # Using a pre-computed hash avoids runtime bcrypt issues
    with engine.begin() as conn:
        # Pre-computed bcrypt hash for "guest_placeholder"
        placeholder_pwd = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqYqYqYqYq"
        conn.execute(
            text("INSERT INTO users (username, hashed_password, role) VALUES (:u, :p, 'guest')"),
            {"u": guest_id, "p": placeholder_pwd}
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": guest_id, "role": "guest"}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": "guest", "username": guest_id}

# 文档上传接口
@api_router.post("/upload_doc")
def upload_document(
    files: List[UploadFile] = File(...),
    target_kb: str = Form("admin"), # 'admin' (Ops KB) or 'user' (User KB)
    current_user: User = Depends(get_current_active_user)
):
    trace_id = uuid.uuid4().hex[:8]
    logger.info(
        "[INGEST][%s] upload_doc_start user=%s role=%s target_kb=%s file_count=%s",
        trace_id,
        current_user.username,
        current_user.role,
        target_kb,
        len(files or []),
    )
    if current_user.role == 'guest':
        raise HTTPException(status_code=403, detail="访客用户禁止上传知识库")
        
    results = []
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    # Determine status based on role
    # Admin -> Approved (Direct Ingestion)
    # User -> Pending (Needs Approval)
    is_admin = current_user.role == 'admin'
    status_code = "approved" if is_admin else "pending"
    
    # KB Type determination
    # If admin, use target_kb (default 'admin' which is Ops KB)
    # If user, forcing to 'user' eventually, but initially pending
    kb_type = target_kb if is_admin else 'user'
    
    MAX_FILE_SIZE = 100 * 1024 * 1024 # 100MB

    for file in files:
        try:
            logger.info("[INGEST][%s] upload_file_start filename=%s content_type=%s", trace_id, file.filename, file.content_type)
            # Check file size
            file.file.seek(0, 2)
            size = file.file.tell()
            file.file.seek(0)
            logger.info("[INGEST][%s] upload_file_size filename=%s size=%s", trace_id, file.filename, size)
            
            if size > MAX_FILE_SIZE:
                 logger.warning("[INGEST][%s] upload_file_rejected_size filename=%s size=%s", trace_id, file.filename, size)
                 results.append({"filename": file.filename, "status": "error", "message": "文件大小超过100MB限制"})
                 continue

            # Sanitize filename to prevent path traversal
            safe_filename = os.path.basename(file.filename)
            file_path = os.path.join(upload_dir, safe_filename)
            
            # 保存文件
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            logger.info("[INGEST][%s] upload_file_saved filename=%s path=%s", trace_id, safe_filename, file_path)
                
            # Record in uploaded_files table
            with engine.begin() as conn:
                conn.execute(
                    text("INSERT INTO uploaded_files (filename, file_path, uploader, status, file_size, kb_type) VALUES (:f, :p, :u, :s, :sz, :k)"),
                    {"f": safe_filename, "p": file_path, "u": current_user.username, "s": status_code, "sz": size, "k": kb_type}
                )

            if is_admin:
                # 入库
                metadata = {
                    "source": file_path,
                    "filename": safe_filename,
                    "type": "user_upload",
                    "uploader": current_user.username,
                    "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # 调用 loader 进行入库，传入 kb_type
                load_document(file_path, metadata, kb_type=kb_type, trace_id=trace_id)
                results.append({"filename": file.filename, "status": "success", "message": f"上传并入库成功 ({kb_type} 库)"})
            else:
                results.append({"filename": file.filename, "status": "pending", "message": "上传成功，等待管理员审批"})
            
        except Exception as e:
            logger.exception("[INGEST][%s] upload_file_failed filename=%s error=%s", trace_id, file.filename, e)
            results.append({"filename": file.filename, "status": "error", "message": str(e)})

    logger.info("[INGEST][%s] upload_doc_done results=%s", trace_id, json.dumps(results, ensure_ascii=False))
    return {"results": results}

@api_router.get("/pending_docs")
def get_pending_docs(current_user: User = Depends(get_current_active_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Permission denied")
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, filename, uploader, created_at FROM uploaded_files WHERE status = 'pending' ORDER BY created_at DESC")).fetchall()
        # Convert to list of dicts
        docs = [{"id": row[0], "filename": row[1], "uploader": row[2], "created_at": str(row[3])} for row in result]
    return {"docs": docs}

@api_router.get("/download_doc/{doc_id}")
def download_doc(doc_id: int, current_user: User = Depends(get_current_active_user)):
    # Allow admin and user, block guest
    if current_user.role == 'guest':
        raise HTTPException(status_code=403, detail="访客用户禁止下载文档")
        
    if current_user.role not in ['admin', 'user']:
         raise HTTPException(status_code=403, detail="Permission denied")
    
    with engine.connect() as conn:
        row = conn.execute(text("SELECT filename, file_path FROM uploaded_files WHERE id = :id"), {"id": doc_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Document not found")
        
        filename, file_path = row
        
        if not os.path.exists(file_path):
             raise HTTPException(status_code=404, detail="File not found on disk")
             
        return FileResponse(path=file_path, filename=filename, media_type='application/octet-stream')

@api_router.get("/download_source/{doc_id}")
def download_source(doc_id: int, current_user: User = Depends(get_current_active_user)):
    """
    Download document based on vector DB document ID.
    Used for retrieving sources referenced in RAG answers.
    """
    if current_user.role == 'guest':
        raise HTTPException(status_code=403, detail="访客用户禁止下载文档")

    with engine.connect() as conn:
        # Get source path from documents table metadata
        row = conn.execute(
            text("SELECT metadata->>'source' as source, metadata->>'filename' as filename FROM documents WHERE id = :id"), 
            {"id": doc_id}
        ).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = row[0]
        filename = row[1]
        
        if not file_path or not os.path.exists(file_path):
             raise HTTPException(status_code=404, detail="File not found on disk")
             
        # Security check: Ensure file is within allowed directories (optional but recommended)
        # For now, we assume internal files are safe to read if they are in the DB.
             
        return FileResponse(path=file_path, filename=filename or os.path.basename(file_path), media_type='application/octet-stream')

@api_router.post("/approve_doc/{doc_id}")
def approve_doc(doc_id: int, current_user: User = Depends(get_current_active_user)):
    trace_id = uuid.uuid4().hex[:8]
    logger.info("[INGEST][%s] approve_doc_start user=%s doc_id=%s", trace_id, current_user.username, doc_id)
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Permission denied")
    
    with engine.begin() as conn:
        # Get file info
        row = conn.execute(text("SELECT filename, file_path, uploader, created_at FROM uploaded_files WHERE id = :id AND status = 'pending'"), {"id": doc_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Document not found or not pending")
        
        filename, file_path, uploader, created_at = row
        
        # Ingest
        try:
            metadata = {
                "source": file_path,
                "filename": filename,
                "type": "user_upload",
                "uploader": uploader,
                "upload_time": created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            # Approve -> Ingest into 'user' KB (since uploader was likely 'user')
            load_document(file_path, metadata, kb_type="user", trace_id=trace_id)
            
            # Update status
            conn.execute(text("UPDATE uploaded_files SET status = 'approved' WHERE id = :id"), {"id": doc_id})
        except Exception as e:
            logger.exception("[INGEST][%s] approve_doc_failed doc_id=%s error=%s", trace_id, doc_id, e)
            raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    logger.info("[INGEST][%s] approve_doc_done doc_id=%s filename=%s", trace_id, doc_id, filename)
    return {"message": "Document approved and ingested"}

@api_router.post("/reject_doc/{doc_id}")
def reject_doc(doc_id: int, current_user: User = Depends(get_current_active_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Permission denied")
    
    with engine.begin() as conn:
        result = conn.execute(text("UPDATE uploaded_files SET status = 'rejected' WHERE id = :id AND status = 'pending'"), {"id": doc_id})
        if result.rowcount == 0:
             raise HTTPException(status_code=404, detail="Document not found or not pending")
    
    return {"message": "Document rejected"}

@api_router.get("/admin/chat_logs")
def get_admin_chat_logs(
    page: int = 1, 
    limit: int = 20, 
    scope: str = 'all', 
    filter_date: str = None,
    current_user: User = Depends(get_current_active_user)
):
    # Scope: 'all' (default, admin only) or 'me' (current user)
    
    offset = (page - 1) * limit
    
    # Determine filtering
    filter_username = None
    if current_user.role != 'admin':
        # Non-admins can only see their own logs
        filter_username = current_user.username
    elif scope == 'me':
        # Admin explicitly requested their own logs
        filter_username = current_user.username
    
    with engine.connect() as conn:
        # Build Query Components
        where_clauses = []
        params = {"limit": limit, "offset": offset}
        
        if filter_username:
            where_clauses.append("username = :username")
            params["username"] = filter_username
            
        # Date filter
        if filter_date == 'today':
            where_clauses.append("created_at::date = CURRENT_DATE")
        elif filter_date == 'month':
            where_clauses.append("date_trunc('month', created_at) = date_trunc('month', CURRENT_DATE)")
            
        where_str = ""
        if where_clauses:
            where_str = "WHERE " + " AND ".join(where_clauses)
        
        # Build Count Query
        count_sql = f"SELECT COUNT(*) FROM chat_logs {where_str}"
        
        # Build Data Query
        data_sql = f"SELECT id, username, question, answer, image_path, created_at, sources, conversation_id FROM chat_logs {where_str} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            
        total = conn.execute(text(count_sql), params).scalar()
        result = conn.execute(text(data_sql), params).fetchall()
        
        logs = []
        for row in result:
            logs.append({
                "id": row[0],
                "username": row[1],
                "question": row[2],
                "answer": row[3],
                "image_path": row[4],
                "created_at": str(row[5]),
                "sources": row[6] if row[6] else [],
                "conversation_id": row[7],
            })
            
    return {"total": total, "logs": logs, "page": page, "limit": limit}

@api_router.get("/admin/global_logs")
def get_global_logs(page: int = 1, limit: int = 20, current_user: User = Depends(get_current_active_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Permission denied")
        
    offset = (page - 1) * limit
    with engine.connect() as conn:
        # Union Query for Global Logs
        # We cast columns to text to ensure compatibility
        sql = """
        SELECT type, id, username, content, status, created_at, details FROM (
            SELECT 'chat' as type, id, username, question as content, status, created_at, answer as details FROM chat_logs
            UNION ALL
            SELECT 'doc_upload' as type, id, uploader as username, filename as content, status, created_at, file_path as details FROM uploaded_files
            UNION ALL
            SELECT 'qa_submission' as type, id, username, question as content, status, created_at, answer as details FROM learned_qa
        ) as unified_logs
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
        """
        
        count_sql = """
        SELECT COUNT(*) FROM (
            SELECT id FROM chat_logs
            UNION ALL
            SELECT id FROM uploaded_files
            UNION ALL
            SELECT id FROM learned_qa
        ) as unified_count
        """
        
        total = conn.execute(text(count_sql)).scalar()
        result = conn.execute(text(sql), {"limit": limit, "offset": offset}).fetchall()
        
        logs = []
        for row in result:
            logs.append({
                "type": row[0],
                "id": row[1],
                "username": row[2],
                "content": row[3],
                "status": row[4],
                "created_at": str(row[5]),
                "details": row[6]
            })
            
    return {"total": total, "logs": logs, "page": page, "limit": limit}

@api_router.get("/admin/export_global_logs")
def export_global_logs(current_user: User = Depends(get_current_active_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Permission denied")
        
    with engine.connect() as conn:
        # Union Query for Global Logs (No Pagination)
        # We cast columns to text to ensure compatibility
        sql = """
        SELECT type, id, username, content, status, created_at, details FROM (
            SELECT 'chat' as type, id, username, question as content, status, created_at, answer as details FROM chat_logs
            UNION ALL
            SELECT 'doc_upload' as type, id, uploader as username, filename as content, status, created_at, file_path as details FROM uploaded_files
            UNION ALL
            SELECT 'qa_submission' as type, id, username, question as content, status, created_at, answer as details FROM learned_qa
        ) as unified_logs
        ORDER BY created_at DESC
        """
        
        result = conn.execute(text(sql)).fetchall()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Type', 'ID', 'Username', 'Content', 'Status', 'Created At', 'Details'])
        
        for row in result:
            writer.writerow([
                row[0], 
                row[1], 
                row[2], 
                row[3], 
                row[4], 
                str(row[5]), 
                row[6]
            ])
            
        output.seek(0)
        
        # Use utf-8-sig for Excel compatibility with Chinese characters
        return StreamingResponse(
            iter([output.getvalue().encode('utf-8-sig')]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=global_logs.csv"}
        )


@api_router.post("/reprocess_docs")
def reprocess_docs(force: bool = False):
    """
    Trigger ingestion of files in the uploads directory.
    Also handles deletion of files that are no longer on disk (Sync).
    """
    trace_id = uuid.uuid4().hex[:8]
    logger.info("[INGEST][%s] reprocess_docs_start force=%s", trace_id, force)
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        logger.warning("[INGEST][%s] reprocess_docs_missing_upload_dir path=%s", trace_id, upload_dir)
        return {"message": "Uploads directory does not exist", "count": 0}
    
    # 1. Get all files on disk
    disk_files = set()
    for filename in os.listdir(upload_dir):
        file_path = os.path.join(upload_dir, filename)
        if os.path.isfile(file_path):
             disk_files.add(file_path)
             
    # 2. Get all sources in DB
    db_files = set()
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT DISTINCT metadata->>'source' FROM documents")).fetchall()
            # Only consider files that look like they are in 'uploads/' to avoid deleting other things
            for row in result:
                source = row[0]
                if source and source.startswith(upload_dir + os.sep):
                    db_files.add(source)
    except Exception as e:
        logger.exception("[INGEST][%s] reprocess_docs_fetch_sources_failed error=%s", trace_id, e)
        return {"message": f"Database error: {str(e)}", "processed": 0}

    # 3. Calculate diff
    # Files to add: on disk but not in DB
    files_to_add = disk_files - db_files
    # Files to delete: in DB but not on disk
    files_to_delete = db_files - disk_files
    
    deleted_count = 0
    processed_count = 0
    skipped_count = 0
    errors = []
    
    # 4. Handle Deletions
    if files_to_delete:
        try:
            with engine.begin() as conn:
                for source in files_to_delete:
                    # Delete from documents (vector store)
                    doc_res = conn.execute(text("DELETE FROM documents WHERE metadata->>'source' = :s"), {"s": source})
                    # Delete from uploaded_files table to sync UI status
                    file_res = conn.execute(text("DELETE FROM uploaded_files WHERE file_path = :s"), {"s": source})
                    logger.info(
                        "[INGEST][%s] reprocess_deleted_missing source=%s documents_deleted=%s uploaded_files_deleted=%s",
                        trace_id,
                        source,
                        doc_res.rowcount,
                        file_res.rowcount,
                    )
                    deleted_count += 1
        except Exception as e:
             logger.exception("[INGEST][%s] reprocess_delete_failed error=%s", trace_id, e)
             errors.append(f"Deletion error: {str(e)}")

    # 5. Handle Additions
    files_to_process = disk_files if force else files_to_add
    
    if not force:
        skipped_count = len(disk_files) - len(files_to_add)

    for file_path in files_to_process:
        try:
             filename = os.path.basename(file_path)
             upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
             metadata = {
                 "source": file_path,
                 "filename": filename,
                 "type": "manual_reprocess",
                 "upload_time": upload_time
             }
             # Default to user KB for auto-reprocess
             load_document(file_path, metadata, kb_type="user", trace_id=trace_id)
             processed_count += 1
             
             # Add to uploaded_files if not exists (to show in Admin UI)
             with engine.begin() as conn:
                 res = conn.execute(text("SELECT id FROM uploaded_files WHERE file_path = :p"), {"p": file_path}).fetchone()
                 if not res:
                     file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                     conn.execute(
                        text("INSERT INTO uploaded_files (filename, file_path, uploader, status, file_size, kb_type) VALUES (:f, :p, :u, :s, :sz, :k)"),
                        {"f": filename, "p": file_path, "u": "system_scan", "s": "approved", "sz": file_size, "k": "user"}
                    )
        except Exception as e:
             logger.exception("[INGEST][%s] reprocess_file_failed path=%s error=%s", trace_id, file_path, e)
             errors.append(f"{os.path.basename(file_path)}: {str(e)}")
             
    msg = f"已同步：新增 {processed_count} 个，剔除 {deleted_count} 个"
    if skipped_count > 0:
        msg += f"，跳过 {skipped_count} 个现有文件"
    if errors:
        msg += f" (有 {len(errors)} 个错误)"
    
    result = {
        "message": msg,
        "processed": processed_count,
        "deleted": deleted_count,
        "skipped": skipped_count,
        "errors": errors
    }
    logger.info("[INGEST][%s] reprocess_docs_done result=%s", trace_id, json.dumps(result, ensure_ascii=False))
    return result

@api_router.get("/hot_questions")
def get_hot_questions():
    questions = []
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT question, COUNT(*) as count 
                FROM chat_logs 
                GROUP BY question 
                ORDER BY count DESC 
                LIMIT 10
            """)).fetchall()
            questions = [row[0] for row in result]
    except Exception as e:
        print(f"Database error in hot_questions (using buffer fallback): {e}")
        # Fallback to buffer if DB fails
        questions = [q for q, _ in Counter(question_buffer).most_common(10)]
    
    try:
        # Fill with default questions if not enough
        default_questions = [
            "系统无法登录怎么办？",
            "数据库连接超时如何排查？",
            "服务器 CPU 使用率过高",
            "如何查看系统日志？",
            "应用部署失败，报错 502",
            "磁盘空间不足怎么清理？",
            "规划天线经纬度和铁塔经纬度误差在多少米校验",
            "如何新增知识库文档？",
            "Nginx 配置反向代理",
            "内存泄漏排查步骤"
        ]
        for q in default_questions:
            if len(questions) >= 10:
                break
            if q not in questions:
                questions.append(q)
        return {"questions": questions}
    except Exception as e:
        print(f"Error processing hot questions: {e}")
        return {"questions": default_questions}

class LearnRequest(BaseModel):
    question_id: int
    answer: str

class ManualQARequest(BaseModel):
    question: str
    answer: str

@api_router.get("/admin/unknown_questions")
def get_unknown_questions(page: int = 1, limit: int = 20, current_user: User = Depends(get_current_active_user)):
    if current_user.role not in ['admin', 'user']:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    offset = (page - 1) * limit
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM chat_logs WHERE status = 'unknown'")).scalar()
        result = conn.execute(
            text("SELECT id, username, question, answer, image_path, created_at FROM chat_logs WHERE status = 'unknown' ORDER BY created_at DESC LIMIT :limit OFFSET :offset"),
            {"limit": limit, "offset": offset}
        ).fetchall()
        
        logs = []
        for row in result:
            logs.append({
                "id": row[0],
                "username": row[1],
                "question": row[2],
                "answer": row[3],
                "image_path": row[4],
                "created_at": str(row[5])
            })
            
    return {"total": total, "logs": logs, "page": page, "limit": limit}

@api_router.post("/admin/learn")
def learn_question(req: LearnRequest, current_user: User = Depends(get_current_active_user)):
    trace_id = uuid.uuid4().hex[:8]
    logger.info(
        "[INGEST][%s] learn_question_start user=%s role=%s question_id=%s answer=%s",
        trace_id,
        current_user.username,
        current_user.role,
        req.question_id,
        req.answer,
    )
    if current_user.role not in ['admin', 'user']:
        raise HTTPException(status_code=403, detail="Permission denied")
        
    is_admin = (current_user.role == 'admin')
    
    with engine.begin() as conn:
        # Get question text
        row = conn.execute(text("SELECT question FROM chat_logs WHERE id = :id"), {"id": req.question_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Question log not found")
        question = row[0]
        
        if is_admin:
            # 1. Update chat_logs status
            conn.execute(text("UPDATE chat_logs SET status = 'learned' WHERE id = :id"), {"id": req.question_id})
            
            # 2. Insert into learned_qa
            conn.execute(
                text("INSERT INTO learned_qa (question, answer, status, username) VALUES (:q, :a, 'approved', :u)"),
                {"q": question, "a": req.answer, "u": current_user.username}
            )
            
            # 3. Ingest into Vector DB
            metadata = {
                "source": "learned_qa",
                "type": "learned_qa",
                "question": question,
                "added_by": current_user.username,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            # Combine Q and A for better retrieval context
            content = f"问题：{question}\n答案：{req.answer}"
            
            # Call load_text_content inside try/except block AFTER transaction or assume safe
            # We'll set a flag to do it outside
            do_ingest = True
            ingest_content = content
            ingest_metadata = metadata
        else:
            # Regular user: Submit for approval
            # 1. Update chat_logs status to remove from unknown list
            conn.execute(text("UPDATE chat_logs SET status = 'pending_learn' WHERE id = :id"), {"id": req.question_id})
            
            # 2. Insert into learned_qa with pending status
            conn.execute(
                text("INSERT INTO learned_qa (question, answer, status, username) VALUES (:q, :a, 'pending', :u)"),
                {"q": question, "a": req.answer, "u": current_user.username}
            )
            do_ingest = False

    if do_ingest:
        try:
            load_text_content(ingest_content, ingest_metadata, trace_id=trace_id)
        except Exception as e:
            logger.exception("[INGEST][%s] learn_question_ingest_failed error=%s", trace_id, e)
            return {"status": "partial_success", "message": "Learned but vector ingestion failed"}

    logger.info("[INGEST][%s] learn_question_done is_admin=%s do_ingest=%s", trace_id, is_admin, do_ingest)
    return {"status": "success", "message": "Question learned and ingested" if is_admin else "Question submitted for approval"}

@api_router.post("/admin/polish_answer")
def polish_answer(req: PolishRequest, current_user: User = Depends(get_current_active_user)):
    try:
        llm = get_llm_client()
        prompt = f"""
你是一个专业的运维助手。请对以下问答对中的答案进行**轻微润色**。
要求：
1. 保持原意，不要过度发散或添加无关信息。
2. 专业术语准确，语言言简意赅。
3. 仅在必要时进行语法或逻辑修正。

问题：{req.question}
草稿答案：{req.draft_answer}

请直接输出优化后的答案内容，不要包含任何解释或开场白。
"""
        # llm.chat expects a list of messages
        messages = [{"role": "user", "content": prompt}]
        polished_answer = llm.chat(messages)
        return {"status": "success", "polished_answer": polished_answer.strip()}
    except Exception as e:
        print(f"Error polishing answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/add_qa")
def add_qa(req: ManualQARequest, current_user: User = Depends(get_current_active_user)):
    trace_id = uuid.uuid4().hex[:8]
    logger.info(
        "[INGEST][%s] add_qa_start user=%s role=%s question=%s answer=%s",
        trace_id,
        current_user.username,
        current_user.role,
        req.question,
        req.answer,
    )
    # Regular users can now submit, but with pending status
    # if current_user.role != 'admin':
    #     raise HTTPException(status_code=403, detail="Permission denied")
        
    question = req.question.strip()
    answer = req.answer.strip()
    
    if not question or not answer:
        raise HTTPException(status_code=400, detail="Question and Answer cannot be empty")

    status = 'approved' if current_user.role == 'admin' else 'pending'

    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO learned_qa (question, answer, status, username) VALUES (:q, :a, :s, :u)"),
            {"q": question, "a": answer, "s": status, "u": current_user.username}
        )
        
        # Only ingest if approved immediately (Admin)
        if status == 'approved':
             # Ingest logic similar to learn
             content = f"问题：{question}\n答案：{answer}"
             metadata = {
                "source": "manual_qa",
                "type": "manual_qa",
                "question": question,
                "added_by": current_user.username,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
             }
             try:
                 load_text_content(content, metadata, trace_id=trace_id)
             except Exception as e:
                 logger.exception("[INGEST][%s] add_qa_ingest_failed error=%s", trace_id, e)

    logger.info("[INGEST][%s] add_qa_done status=%s", trace_id, status)
    return {"status": "success", "message": "Q&A added" if status == 'approved' else "Q&A submitted for approval"}

@api_router.delete("/admin/delete_qa/{qa_id}")
def delete_qa(qa_id: int, current_user: User = Depends(get_current_active_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Permission denied")
        
    with engine.begin() as conn:
        # 1. Get question to delete from vector db
        row = conn.execute(text("SELECT question FROM learned_qa WHERE id = :id"), {"id": qa_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="QA not found")
        question = row[0]
        
        # 2. Delete from SQL
        conn.execute(text("DELETE FROM learned_qa WHERE id = :id"), {"id": qa_id})
        
        # 3. Delete from Vector DB
        # We delete where metadata->>'question' matches the question
        # Safe to assume question is unique enough for this context, and we restrict by type just in case
        conn.execute(
            text("DELETE FROM documents WHERE metadata->>'question' = :q AND (metadata->>'type' = 'manual_qa' OR metadata->>'type' = 'learned_qa')"),
            {"q": question}
        )
        
    return {"message": "QA deleted successfully"}

@api_router.get("/api/dashboard/stats")
def get_dashboard_stats(current_user: User = Depends(get_current_active_user)):
    """
    Get dashboard statistics based on user role.
    """
    stats = {}
    
    with engine.connect() as conn:
        if current_user.role == 'admin':
            # 1. Today's Questions
            today_count = conn.execute(text("SELECT COUNT(*) FROM chat_logs WHERE created_at::date = CURRENT_DATE")).scalar()
            
            # 2. This Month's Questions
            month_count = conn.execute(text("SELECT COUNT(*) FROM chat_logs WHERE date_trunc('month', created_at) = date_trunc('month', CURRENT_DATE)")).scalar()
            
            # 3. Pending Questions (Unknown status)
            pending_count = conn.execute(text("SELECT COUNT(*) FROM chat_logs WHERE status = 'unknown'")).scalar()
            
            # 4. This Month's Learned Knowledge (Approved)
            learned_month_count = conn.execute(text("SELECT COUNT(*) FROM learned_qa WHERE status = 'approved' AND date_trunc('month', created_at) = date_trunc('month', CURRENT_DATE)")).scalar()
            
            stats = {
                "today_questions": today_count,
                "month_questions": month_count,
                "pending_questions": pending_count,
                "month_learned": learned_month_count
            }
        else:
            # User View
            # 1. My Total Questions
            my_questions = conn.execute(text("SELECT COUNT(*) FROM chat_logs WHERE username = :u"), {"u": current_user.username}).scalar()
            
            # 2. My Contributions (Approved Learned QA)
            my_contributions = conn.execute(text("SELECT COUNT(*) FROM learned_qa WHERE username = :u AND status = 'approved'"), {"u": current_user.username}).scalar()
            
            stats = {
                "my_questions": my_questions,
                "my_contributions": my_contributions
            }
            
    return stats

@api_router.get("/admin/learning_records")
def get_learning_records(
    page: int = 1, 
    limit: int = 10, 
    scope: str = 'all',
    filter_date: str = None,
    current_user: User = Depends(get_current_active_user)
):
    # Both admin and user can view learning records
    offset = (page - 1) * limit
    
    with engine.connect() as conn:
        # Build Query
        where_clauses = []
        params = {"limit": limit, "offset": offset}
        
        # Scope filter
        if scope == 'me':
            where_clauses.append("username = :username")
            params["username"] = current_user.username
            
        # Date filter (Dashboard context: 'month' implies 'approved' + 'current month')
        if filter_date == 'month':
            where_clauses.append("date_trunc('month', created_at) = date_trunc('month', CURRENT_DATE)")
            where_clauses.append("status = 'approved'")
            
        where_str = ""
        if where_clauses:
            where_str = "WHERE " + " AND ".join(where_clauses)
            
        # Get total count
        count_sql = f"SELECT COUNT(*) FROM learned_qa {where_str}"
        total = conn.execute(text(count_sql), params).scalar()
        
        # Get records
        data_sql = f"""
            SELECT id, question, answer, status, username, created_at 
            FROM learned_qa 
            {where_str}
            ORDER BY id DESC 
            LIMIT :limit OFFSET :offset
        """
        
        rows = conn.execute(text(data_sql), params).fetchall()
        
        records = []
        for row in rows:
            records.append({
                "id": row[0],
                "question": row[1],
                "answer": row[2],
                "status": row[3],
                "username": row[4],
                "created_at": row[5].strftime("%Y-%m-%d %H:%M:%S") if row[5] else ""
            })
            
        return {"records": records, "total": total}

@api_router.get("/admin/pending_qa")
def get_pending_qa(page: int = 1, limit: int = 20, current_user: User = Depends(get_current_active_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Permission denied")
    
    offset = (page - 1) * limit
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM learned_qa WHERE status = 'pending'")).scalar()
        
        result = conn.execute(
            text("SELECT id, question, answer, username, created_at FROM learned_qa WHERE status = 'pending' ORDER BY created_at DESC LIMIT :limit OFFSET :offset"),
            {"limit": limit, "offset": offset}
        ).fetchall()
        
        items = []
        for row in result:
            items.append({
                "id": row[0],
                "question": row[1],
                "answer": row[2],
                "username": row[3],
                "created_at": str(row[4])
            })
            
    return {"total": total, "items": items, "page": page, "limit": limit}

@api_router.post("/admin/approve_qa/{qa_id}")
def approve_qa(qa_id: int, current_user: User = Depends(get_current_active_user)):
    trace_id = uuid.uuid4().hex[:8]
    logger.info("[INGEST][%s] approve_qa_start user=%s qa_id=%s", trace_id, current_user.username, qa_id)
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Permission denied")
        
    with engine.begin() as conn:
        row = conn.execute(text("SELECT question, answer, username FROM learned_qa WHERE id = :id"), {"id": qa_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="QA not found")
            
        question, answer, username = row
        
        # Update status
        conn.execute(text("UPDATE learned_qa SET status = 'approved' WHERE id = :id"), {"id": qa_id})
        
        # Ingest
        metadata = {
            "source": "learned_qa",
            "type": "learned_qa",
            "question": question,
            "added_by": username or current_user.username,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        content = f"问题：{question}\n答案：{answer}"
        
    try:
        load_text_content(content, metadata, trace_id=trace_id)
    except Exception as e:
        logger.exception("[INGEST][%s] approve_qa_ingest_failed qa_id=%s error=%s", trace_id, qa_id, e)
        return {"status": "partial_success", "message": "Approved but vector ingestion failed"}
    logger.info("[INGEST][%s] approve_qa_done qa_id=%s", trace_id, qa_id)
    return {"status": "success", "message": "QA approved and added to KB"}

@api_router.post("/admin/reject_qa/{qa_id}")
def reject_qa(qa_id: int, current_user: User = Depends(get_current_active_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Permission denied")
        
    with engine.begin() as conn:
        # Update status to rejected (or delete?) - Let's keep it as rejected
        result = conn.execute(text("UPDATE learned_qa SET status = 'rejected' WHERE id = :id"), {"id": qa_id})
        if result.rowcount == 0:
             raise HTTPException(status_code=404, detail="QA not found")
             
    return {"status": "success", "message": "QA rejected"}

@api_router.post("/admin/discard_unknown/{id}")
def discard_unknown_question(id: int, current_user: User = Depends(get_current_active_user)):
    if current_user.role not in ['admin', 'user']:
        raise HTTPException(status_code=403, detail="Permission denied")
        
    with engine.begin() as conn:
        result = conn.execute(text("UPDATE chat_logs SET status = 'discarded' WHERE id = :id"), {"id": id})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Question log not found")
            
    return {"status": "success", "message": "Question discarded"}

# 接受用户问题并返回答案
@api_router.post("/get_answer")
def get_answer(req: QuestionRequest, current_user: User = Depends(get_current_active_user)):
    trace_id = uuid.uuid4().hex[:8]
    question = req.question
    image_data = req.image
    conversation_id = normalize_conversation_id(req.conversation_id)
    request_history = request_history_to_messages(req.history)
    question_preview = (question or "").replace("\n", "\\n")[:300]
    logger.info(
        f"[QA][{trace_id}] request start user={current_user.username} role={current_user.role} "
        f"conversation_id={conversation_id} q_len={len(question or '')} "
        f"has_image={bool(image_data)} question='{question_preview}'"
    )

    try:
        if current_user.role == 'guest':
            with engine.connect() as conn:
                count = conn.execute(text("SELECT COUNT(*) FROM chat_logs WHERE username = :u"), {"u": current_user.username}).scalar()
                if count >= 5:
                    logger.info(f"[QA][{trace_id}] guest limit reached user={current_user.username} count={count}")
                    return {
                        "answer": "您是访客用户，提问次数已达上限 (5次)。请注册或登录以继续使用。",
                        "sources": [],
                        "images": []
                    }

        question_buffer.appendleft(question)
        save_question_history(question_buffer)

        with engine.begin() as conn:
            conn.execute(text("INSERT INTO question_history (question) VALUES (:q)"), {"q": question})

        saved_image_path = None
        if image_data:
            try:
                if "," in image_data:
                    _, encoded = image_data.split(",", 1)
                else:
                    encoded = image_data

                data = base64.b64decode(encoded)
                filename = f"{uuid.uuid4()}.png"
                save_path = os.path.join("user_images", filename)
                with open(save_path, "wb") as f:
                    f.write(data)
                saved_image_path = filename
                logger.info(f"[QA][{trace_id}] image saved file={filename} bytes={len(data)}")
            except Exception:
                logger.exception(f"[QA][{trace_id}] failed to save user image")

        answer = None
        sources = []
        images = []
        rag_debug = None
        is_learned = False
        conversation_history = request_history or load_conversation_history(
            current_user.username,
            conversation_id,
        )

        if not image_data:
            with engine.connect() as conn:
                try:
                    learned = conn.execute(text("SELECT answer FROM learned_qa WHERE question = :q ORDER BY created_at DESC LIMIT 1"), {"q": question}).fetchone()
                    if learned:
                        answer = learned[0]
                        is_learned = True
                        logger.info(f"[QA][{trace_id}] answered by learned_qa")
                except Exception:
                    logger.exception(f"[QA][{trace_id}] error checking learned_qa")

        if not answer:
            kb_type = current_user.role
            if kb_type == 'guest':
                kb_type = 'user'
            elif kb_type == 'admin':
                kb_type = 'all'

            logger.info(
                "[QA][%s] invoking rag kb_type=%s provider=%s model=%s embedding_model=%s return_debug=%s",
                trace_id,
                kb_type,
                os.getenv("LLM_PROVIDER"),
                os.getenv("LLM_MODEL"),
                os.getenv("EMBEDDING_MODEL"),
                os.getenv("RETURN_RAG_DEBUG", "false"),
            )
            rag_result = answer_question(
                question,
                image_data,
                kb_type=kb_type,
                history=conversation_history,
                debug=True,
                trace_id=trace_id,
            )
            if isinstance(rag_result, dict):
                answer = rag_result.get("answer")
                sources = rag_result.get("sources", [])
                rag_debug = rag_result.get("debug")
            else:
                answer = rag_result
                sources = []
            logger.info(f"[QA][{trace_id}] rag done answer_len={len(answer or '')} sources={len(sources)}")

        status_code = "normal"
        if is_learned:
            status_code = "learned"
        else:
            unknown_keywords = ["未在现有运维知识库中找到", "我不知道", "无法回答"]
            for kw in unknown_keywords:
                if kw in (answer or ""):
                    status_code = "unknown"
                    sources = []
                    break

        insert_chat_log_sql = text("""
            INSERT INTO chat_logs
                (question, answer, username, image_path, status, sources, conversation_id, rag_debug)
            VALUES
                (:q, :a, :u, :i, :s, :src, :conversation_id, :rag_debug)
            RETURNING id
        """)
        insert_chat_log_params = {
            "q": question,
            "a": answer,
            "u": current_user.username,
            "i": saved_image_path,
            "s": status_code,
            "src": json.dumps(sources),
            "conversation_id": conversation_id,
            "rag_debug": json.dumps(rag_debug, ensure_ascii=False) if rag_debug else None,
        }
        try:
            with engine.begin() as conn:
                result = conn.execute(insert_chat_log_sql, insert_chat_log_params)
                question_id = result.scalar()
        except Exception as exc:
            logger.exception(
                "[QA][%s] insert_chat_log failed; running schema migration and retrying params=%s error=%s",
                trace_id,
                json.dumps(insert_chat_log_params, ensure_ascii=False, default=str),
                exc,
            )
            ensure_app_schema_migrations(f"{trace_id}_insert_retry")
            with engine.begin() as conn:
                result = conn.execute(insert_chat_log_sql, insert_chat_log_params)
                question_id = result.scalar()

        answer_preview = (answer or "").replace("\n", "\\n")[:500]
        logger.info(
            f"[QA][{trace_id}] request done status={status_code} question_id={question_id} "
            f"answer_len={len(answer or '')} answer='{answer_preview}' sources={json.dumps(sources, ensure_ascii=False)[:500]}"
        )
        response = {
            "answer": answer,
            "sources": sources,
            "images": images,
            "question_id": question_id,
            "conversation_id": conversation_id,
        }
        if rag_debug:
            if os.getenv("RETURN_RAG_DEBUG", "false").lower() == "true":
                response["debug"] = rag_debug
        return response
    except HTTPException:
        raise
    except Exception as exc:
        error_detail = {
            "message": "问答处理失败",
            "trace_id": trace_id,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "question": question,
            "user": current_user.username,
            "role": current_user.role,
            "conversation_id": conversation_id,
            "runtime_config": runtime_config_summary(),
            "traceback": traceback.format_exc(),
        }
        logger.exception(
            "[QA][%s] get_answer failed detail=%s",
            trace_id,
            json.dumps(error_detail, ensure_ascii=False, default=str),
        )
        raise HTTPException(status_code=500, detail=error_detail)

@api_router.post("/feedback")
def submit_feedback(request: FeedbackRequest):
    try:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE chat_logs SET feedback = :status WHERE id = :id"),
                {"status": request.status, "id": request.question_id}
            )
        return {"message": "Feedback received"}
    except Exception as e:
        print(f"Error saving feedback: {e}")
        return {"error": str(e)}


@api_router.get("/debug/db_status")
def debug_db_status():
    info = {"buffer_len": len(question_buffer)}
    try:
        with engine.connect() as conn:
            exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'question_history'
                )
            """)).scalar()
            info["question_history_exists"] = bool(exists)
            if exists:
                count = conn.execute(text("SELECT COUNT(*) FROM question_history")).scalar()
                info["question_history_count"] = int(count)
            
            # Check users
            users_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
            info["users_count"] = int(users_count)
            
            return info
    except Exception as e:
        return {"error": str(e)}


@api_router.get("/debug/runtime_config")
def debug_runtime_config(current_user: User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    return runtime_config_summary()


# Knowledge Documents APIs

@api_router.get("/documents/search")
def search_documents(
    q: str = "", 
    page: int = 1, 
    limit: int = 20, 
    current_user: User = Depends(get_current_active_user)
):
    try:
        # Allow all users to search approved documents
        offset = (page - 1) * limit
        
        with engine.connect() as conn:
            # Build query
            base_query = "SELECT id, filename, uploader, created_at, file_size, download_count, kb_type FROM uploaded_files WHERE status = 'approved'"
            params = {"limit": limit, "offset": offset}
            
            if q:
                base_query += " AND filename ILIKE :q"
                params["q"] = f"%{q}%"
                
            # Count total
            count_query = f"SELECT COUNT(*) FROM ({base_query}) as sub"
            total = conn.execute(text(count_query), params).scalar()
            
            # Get data
            data_query = base_query + " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            result = conn.execute(text(data_query), params).fetchall()
            
            docs = []
            for row in result:
                docs.append({
                    "id": row[0],
                    "filename": row[1],
                    "uploader": row[2],
                    "created_at": str(row[3]),
                    "file_size": row[4] if row[4] is not None else 0,
                    "download_count": row[5] if row[5] is not None else 0,
                    "kb_type": row[6] if row[6] else "user"
                })
            
        return {"total": total, "docs": docs, "page": page, "limit": limit}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/documents/hot")
def get_hot_documents(limit: int = 10, current_user: User = Depends(get_current_active_user)):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, filename, download_count FROM uploaded_files WHERE status = 'approved' ORDER BY download_count DESC LIMIT :limit"),
            {"limit": limit}
        ).fetchall()
        
        docs = []
        for row in result:
            docs.append({
                "id": row[0],
                "filename": row[1],
                "download_count": row[2] if row[2] is not None else 0
            })
            
    return {"docs": docs}

@api_router.get("/documents/{doc_id}/preview")
def preview_document_html(doc_id: int, current_user: User = Depends(get_current_active_user)):
    """
    Server-side preview: Convert DOCX/TXT to HTML and return
    This avoids client-side file download for preview
    """
    if current_user.role == 'guest':
        raise HTTPException(status_code=403, detail="访客用户禁止预览文档")

    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT filename, file_path FROM uploaded_files WHERE id = :id AND status = 'approved'"),
            {"id": doc_id}
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Document not found or not approved")

        filename, file_path = row

        if not os.path.exists(file_path):
             raise HTTPException(status_code=404, detail="File not found on disk")

        # Increment download count (preview counts as view)
        conn.execute(text("UPDATE uploaded_files SET download_count = COALESCE(download_count, 0) + 1 WHERE id = :id"), {"id": doc_id})

    # Try to convert to HTML
    html_content = get_file_preview_html(file_path, filename)

    if html_content:
        return HTMLResponse(content=html_content)
    else:
        # Unsupported format, return error page
        ext = os.path.splitext(filename)[1].lower()
        error_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>预览不支持</title>
    <style>
        body {{
            font-family: "Microsoft YaHei", Arial, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            background: #f5f5f5;
        }}
        .container {{
            text-align: center;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h2 {{ color: #666; }}
        p {{ color: #999; margin: 20px 0; }}
        .file-info {{ color: #333; font-weight: bold; }}
        a {{
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }}
        a:hover {{ background: #0056b3; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>📄 该文件格式暂不支持在线预览</h2>
        <p class="file-info">{filename} ({ext})</p>
        <p>支持的格式：DOCX, TXT, PDF 和常见图片格式。</p>
        <p>当前访问环境可能禁止下载文件，请联系管理员转换为可在线预览格式。</p>
    </div>
</body>
</html>
"""
        return HTMLResponse(content=error_html)

@api_router.get("/documents/{doc_id}")
def download_knowledge_doc(doc_id: int, preview: bool = False, current_user: User = Depends(get_current_active_user)):
    if current_user.role == 'guest':
        raise HTTPException(status_code=403, detail="访客用户禁止下载文档")
    
    with engine.begin() as conn: # Use begin for update transaction
        row = conn.execute(
            text("SELECT filename, file_path FROM uploaded_files WHERE id = :id AND status = 'approved'"), 
            {"id": doc_id}
        ).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Document not found or not approved")
        
        filename, file_path = row
        
        if not os.path.exists(file_path):
             raise HTTPException(status_code=404, detail="File not found on disk")
        
        # Increment download count
        conn.execute(text("UPDATE uploaded_files SET download_count = COALESCE(download_count, 0) + 1 WHERE id = :id"), {"id": doc_id})
        
        disposition = "inline" if preview else "attachment"
        
        # Determine media type for preview if possible, else generic
        media_type = 'application/octet-stream'
        if preview:
             ext = os.path.splitext(filename)[1].lower()
             if ext == '.pdf': media_type = 'application/pdf'
             elif ext in ['.jpg', '.jpeg']: media_type = 'image/jpeg'
             elif ext == '.png': media_type = 'image/png'
             elif ext == '.txt': media_type = 'text/plain'
        
        return FileResponse(
            path=file_path, 
            filename=filename, 
            media_type=media_type,
            content_disposition_type=disposition
        )

@api_router.delete("/documents/{doc_id}")
def delete_document(doc_id: int, current_user: User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete documents")
        
    # Get file info and delete from DB in a transaction
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT filename, file_path FROM uploaded_files WHERE id = :id"), 
            {"id": doc_id}
        ).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Document not found")
            
        filename, file_path = row
        
        # 1. Delete from uploaded_files
        conn.execute(text("DELETE FROM uploaded_files WHERE id = :id"), {"id": doc_id})
        
    # 2. Delete from Vector DB (documents table) using helper
    # This ensures consistency using the 'source' (file_path) metadata
    delete_document_by_source(file_path)
        
    # 3. Delete physical file
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            # Continue even if file delete fails
            
    return {"status": "success", "message": f"Document '{filename}' deleted from database and knowledge base."}

# Include the router twice: once for root (standalone) and once for agent-api (embedding)
app.include_router(api_router)
app.include_router(api_router, prefix="/agent-api")

# SPA Catch-all route (Must be last)
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    DIST_DIR = "dist_frontend"
    # Logic for standalone serving if not matched above
    if os.path.exists(DIST_DIR):
        if "." not in full_path.split("/")[-1]: 
            return FileResponse(f"{DIST_DIR}/index.html")
    
    # Fallback to 404
    raise HTTPException(status_code=404, detail="Not Found")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    print(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
