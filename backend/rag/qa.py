# rag/qa.py
from typing import Any, Dict, List, Optional
import os
import logging
import json
import re
import time
from rag.retriever import retrieve_similar_documents
from ocr_engine import ocr_engine
import base64
import tempfile
import uuid
from sqlalchemy import text

from db import engine
from llm.factory import get_llm_client

logger = logging.getLogger(__name__)

MAX_HISTORY_CHARS = int(os.getenv("CONVERSATION_HISTORY_CHARS", "3000"))
CONTEXT_EXPAND_WINDOW = int(os.getenv("CONTEXT_EXPAND_WINDOW", "1"))
SOURCE_CONTEXT_MAX_CHUNKS = int(os.getenv("SOURCE_CONTEXT_MAX_CHUNKS", "8"))
UNKNOWN_ANSWER = "未在现有运维知识库中找到标准处置方案，请联系后台支撑。"

def call_llm(prompt: str, image: Optional[str] = None, trace_id: str = "-", purpose: str = "answer") -> str:
    """
    调用统一 LLM 接口生成回答
    支持 ZhipuAI 和 Ollama (通过 LLM_PROVIDER 环境变量切换)
    """
    try:
        provider = os.getenv("LLM_PROVIDER", "zhipu").lower()

        model = os.getenv("VISION_MODEL")
        if not model and image:
            if provider == "zhipu":
                model = "glm-4v"
            elif provider == "ollama":
                model = "llava"
            elif provider in ["deepseek-v3", "openai", "siliconflow"]:
                # In intranet, the model name might be different. 
                # If not provided in config.yaml, use a common generic name or the hardcoded one.
                model = "Qwen/Qwen2.5-VL-7B-Instruct"

        base_url = os.getenv("OLLAMA_BASE_URL") or os.getenv("LLM_BASE_URL")
        started_at = time.perf_counter()
        client = get_llm_client(model=model)

        messages = []
        if image:
            if provider in ["zhipu", "deepseek-v3", "openai", "siliconflow"]:
                messages = [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image}}
                    ]
                }]
            else:
                messages = [{"role": "user", "content": prompt, "images": [image]}]
        else:
            messages = [{"role": "user", "content": prompt}]

        logger.info(
            "[LLM][%s] start purpose=%s provider=%s model=%s base_url=%s is_vision=%s message_count=%s prompt=%s",
            trace_id,
            purpose,
            provider,
            getattr(client, "model", model or os.getenv("LLM_MODEL")),
            base_url,
            bool(image),
            len(messages),
            prompt,
        )
        if provider == "ollama" and purpose == "classify_intent":
            classify_timeout = int(os.getenv("LLM_CLASSIFY_TIMEOUT", "15"))
            classify_num_predict = int(os.getenv("LLM_CLASSIFY_NUM_PREDICT", "8"))
            answer = client.chat(
                messages,
                temperature=0.0,
                timeout=classify_timeout,
                options={
                    "num_predict": classify_num_predict,
                    "num_ctx": int(os.getenv("LLM_CLASSIFY_NUM_CTX", "512")),
                },
            )
        else:
            answer = client.chat(messages)
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info(
            "[LLM][%s] done purpose=%s provider=%s model=%s elapsed_ms=%s answer=%s",
            trace_id,
            purpose,
            provider,
            getattr(client, "model", model or os.getenv("LLM_MODEL")),
            elapsed_ms,
            answer,
        )
        return answer
    except Exception as e:
        logger.exception("[LLM][%s] failed purpose=%s error=%s prompt=%s", trace_id, purpose, e, prompt)
        return f"调用 LLM 失败: {str(e)}"


SYSTEM_PROMPT = """你是一名资深运维工程师助手。

你的任务是根据用户问题和提供的【参考文档】进行回答。

处理规则如下：

1. **针对闲聊或通用问题**（如问候、夸奖、询问天气、常识等）：
   - 请忽略参考文档，直接用自然、流畅、友好的语气回答用户。
   - **不要**在回答中提及“未在知识库找到”或引用文档。
   - 直接输出回复内容，不要输出“属于闲聊”等分类标签。

2. **针对专业运维或业务咨询**（涉及具体设备、流程、故障、指标等）：
   - 必须严格依据【参考文档】回答。
   - 只能使用【参考文档】中明确出现的信息组织答案，不得补充常识、推测、建议性语言或模型自身知识。
   - **关键校验**：检索系统可能会返回不相关的文档。请务必先判断【参考文档】的内容是否真的与用户问题（或图片展示的报错）对口。
     - 例如：用户问的是“数据库连接失败”，但文档是“服务器登录指南”，这属于**无关文档**。
   - 如果【参考文档】与用户问题**无关**，或者无法解决该问题，请直接忽略文档，并明确输出：“未在现有运维知识库中找到标准处置方案，请联系后台支撑。”
   - 禁止强行关联不相关的文档，禁止编造文档中不存在的内容。
   - 引用格式（仅在文档相关时使用）：根据《[文档名称]》[章节]（上传时间：YYYY-MM-DD），标准处理流程如下：...

请直接根据上述规则输出回答。
"""

CHAT_PROMPT = """你是一名资深运维工程师助手。

请判断用户的意图：
1. 如果是**闲聊**（如打招呼、问名字、天气、夸奖等）：请自然、友好地回应。
2. 如果是**专业技术问题**或**业务咨询**：由于未检索到相关文档，请明确告知用户“未在现有运维知识库中找到标准处置方案，请联系后台支撑。”。
"""

CLASSIFY_PROMPT = """你是一个意图识别助手。
请判断用户的输入是“闲聊”还是“专业问题”。
- 闲聊：打招呼、问候、夸奖、询问天气、个人情感等非技术类内容。
- 专业问题：涉及运维、技术、业务流程、故障排查、系统操作等内容。

用户输入：{question}

请仅输出类别名称（“闲聊”或“专业问题”），不要包含其他文字。"""


TECHNICAL_INTENT_KEYWORDS = (
    "报错",
    "错误",
    "失败",
    "异常",
    "故障",
    "告警",
    "无法",
    "不能",
    "不同步",
    "未同步",
    "找不到",
    "工单",
    "基站",
    "电路",
    "批量",
    "修改",
    "同步",
    "资源",
    "派发",
    "流程",
    "步骤",
    "配置",
    "登录",
    "接口",
    "数据库",
)

CHITCHAT_INTENT_PHRASES = {
    "你好",
    "您好",
    "hello",
    "hi",
    "你是谁",
    "谢谢",
    "辛苦了",
}

STABLE_CHITCHAT_PHRASES = {
    "\u4f60\u597d",
    "\u60a8\u597d",
    "hello",
    "hi",
    "\u4f60\u662f\u8c01",
    "\u8c22\u8c22",
    "\u8f9b\u82e6\u4e86",
}

STABLE_TECHNICAL_KEYWORDS = (
    "\u62a5\u9519",
    "\u9519\u8bef",
    "\u5931\u8d25",
    "\u5f02\u5e38",
    "\u6545\u969c",
    "\u544a\u8b66",
    "\u65e0\u6cd5",
    "\u4e0d\u80fd",
    "\u672a\u540c\u6b65",
    "\u540c\u6b65",
    "\u6821\u9a8c",
    "\u7ecf\u7eac\u5ea6",
    "\u5929\u7ebf",
    "\u5929\u9762",
    "\u8d44\u6e90",
    "\u5de5\u5355",
    "\u57fa\u7ad9",
    "\u7535\u8def",
    "\u6d41\u7a0b",
    "\u6279\u91cf",
    "\u4fee\u6539",
    "\u914d\u7f6e",
    "\u63a5\u53e3",
    "\u6570\u636e\u5e93",
)


LOW_INFORMATION_ANSWER = "\u8bf7\u8f93\u5165\u66f4\u5177\u4f53\u7684\u95ee\u9898\uff0c\u4f8b\u5982\u6545\u969c\u73b0\u8c61\u3001\u62a5\u9519\u4fe1\u606f\u6216\u9700\u8981\u67e5\u8be2\u7684\u4e1a\u52a1\u540d\u79f0\u3002"


def is_low_information_question(question: str) -> bool:
    compact_question = "".join((question or "").split())
    if not compact_question:
        return True
    if len(compact_question) <= 1 and not re.search(r"[\u4e00-\u9fffA-Za-z]", compact_question):
        return True
    if len(compact_question) <= 2 and re.fullmatch(r"[\d\W_]+", compact_question):
        return True
    return False


def classify_intent(question: str, trace_id: str = "-") -> str:
    """
    判断用户意图
    """
    compact_question = "".join((question or "").lower().split())
    if compact_question in CHITCHAT_INTENT_PHRASES or compact_question in STABLE_CHITCHAT_PHRASES:
        logger.info("[QA][%s] intent_heuristic=chitchat question=%s", trace_id, question)
        return "chitchat"
    if any(keyword in compact_question for keyword in TECHNICAL_INTENT_KEYWORDS):
        logger.info("[QA][%s] intent_heuristic=technical question=%s", trace_id, question)
        return "technical"
    if any(keyword in compact_question for keyword in STABLE_TECHNICAL_KEYWORDS):
        logger.info("[QA][%s] intent_heuristic=technical question=%s", trace_id, question)
        return "technical"

    if os.getenv("LLM_INTENT_CLASSIFY_ENABLED", "false").lower() not in {"1", "true", "yes"}:
        logger.info("[QA][%s] intent_default=technical llm_classify_disabled question=%s", trace_id, question)
        return "technical"

    try:
        prompt = CLASSIFY_PROMPT.format(question=question)
        response = call_llm(prompt, trace_id=trace_id, purpose="classify_intent")
        logger.info("[QA][%s] intent_response=%s question=%s", trace_id, response, question)
        if "闲聊" in response:
            return "chitchat"
        return "technical"
    except Exception:
        logger.exception("[QA][%s] classify_intent_failed question=%s", trace_id, question)
        # Fallback to technical if classification fails
        return "technical"


def build_context(docs):
    context_parts = []
    for i, doc in enumerate(docs, 1):
        # doc structure: (id, content, metadata, distance)
        content = doc[1]
        metadata = doc[2]
        
        context_parts.append(
            f"""【文档 {i}】
内容：
{content}

元数据：
{metadata}
"""
        )
    return "\n".join(context_parts)


def build_prompt(question: str, context: str) -> str:
    return f"""
【参考文档】
{context}

【用户问题】
{question}
"""

def _compact_history(history: Optional[List[Dict[str, Any]]]) -> List[Dict[str, str]]:
    if not history:
        return []

    compacted = []
    total_chars = 0
    for item in reversed(history):
        role = item.get("role")
        content = str(item.get("content") or "").strip()
        if role not in {"user", "assistant"} or not content:
            continue

        remaining = MAX_HISTORY_CHARS - total_chars
        if remaining <= 0:
            break
        if len(content) > remaining:
            content = content[:remaining]

        compacted.append({"role": role, "content": content})
        total_chars += len(content)

    return list(reversed(compacted))


def _format_history(history: Optional[List[Dict[str, Any]]]) -> str:
    compacted = _compact_history(history)
    if not compacted:
        return ""

    role_names = {"user": "用户", "assistant": "助手"}
    lines = []
    for item in compacted:
        lines.append(f"{role_names[item['role']]}：{item['content']}")
    return "\n".join(lines)


def _build_retrieval_query(question: str, history: Optional[List[Dict[str, Any]]]) -> str:
    history_text = _format_history(history)
    if not history_text:
        return question
    return f"历史对话：\n{history_text}\n\n当前问题：{question}"


def _build_debug_payload(docs, valid_docs, retrieval_debug, current_threshold):
    candidates = []
    for doc in docs:
        meta = doc[2] or {}
        retrieval_meta = doc[4] if len(doc) > 4 and isinstance(doc[4], dict) else {}
        candidates.append({
            "id": doc[0],
            "filename": meta.get("filename"),
            "source": meta.get("source"),
            "distance": doc[3] if len(doc) > 3 else None,
            "rrf_score": retrieval_meta.get("rrf_score"),
            "vector_rank": retrieval_meta.get("vector_rank"),
            "keyword_rank": retrieval_meta.get("keyword_rank"),
            "preview": (doc[1] or "")[:160],
            "content": doc[1],
            "metadata": meta,
        })

    return {
        "retrieval": retrieval_debug or {},
        "threshold": current_threshold,
        "candidate_count": len(docs),
        "valid_doc_count": len(valid_docs),
        "candidates": candidates,
    }


def _has_document_source(doc) -> bool:
    meta = doc[2] or {}
    return bool(meta.get("source"))


def _expand_neighbor_docs(trace_id: str, docs):
    if not docs or CONTEXT_EXPAND_WINDOW <= 0:
        return docs

    source_bounds = {}
    source_order = []
    for doc in docs:
        meta = doc[2] or {}
        source = meta.get("source")
        if not source:
            continue
        doc_id = int(doc[0])
        if source not in source_bounds:
            source_bounds[source] = [doc_id, doc_id]
            source_order.append(source)
        else:
            source_bounds[source][0] = min(source_bounds[source][0], doc_id)
            source_bounds[source][1] = max(source_bounds[source][1], doc_id)

    if not source_bounds:
        return docs

    docs_by_source = {}
    try:
        with engine.connect() as conn:
            for source, (min_id, max_id) in source_bounds.items():
                rows = conn.execute(
                    text("""
                        SELECT id, content, metadata
                        FROM documents
                        WHERE metadata->>'source' = :source
                          AND id BETWEEN :min_id AND :max_id
                        ORDER BY id ASC
                    """),
                    {
                        "source": source,
                        "min_id": min_id - CONTEXT_EXPAND_WINDOW,
                        "max_id": max_id + CONTEXT_EXPAND_WINDOW,
                    },
                ).fetchall()
                docs_by_source[source] = [
                    (
                        row[0],
                        row[1],
                        row[2],
                        0.0 if any(row[0] == doc[0] for doc in docs) else 1.0,
                        {
                            "rrf_score": None,
                            "vector_rank": None,
                            "keyword_rank": None,
                            "context_expanded": True,
                        },
                    )
                    for row in rows
                ]
    except Exception:
        logger.exception("[RETRIEVAL][%s] expand_neighbor_docs_failed", trace_id)
        return docs

    ordered = []
    seen_ids = set()
    for source in source_order:
        for doc in docs_by_source.get(source, []):
            if doc[0] not in seen_ids:
                ordered.append(doc)
                seen_ids.add(doc[0])
    for doc in docs:
        if doc[0] not in seen_ids:
            ordered.append(doc)
            seen_ids.add(doc[0])

    logger.info(
        "[RETRIEVAL][%s] context_expanded seed_count=%s expanded_count=%s window=%s ids=%s",
        trace_id,
        len(docs),
        len(ordered),
        CONTEXT_EXPAND_WINDOW,
        [doc[0] for doc in ordered],
    )
    return ordered


def _source_payload_from_doc(doc):
    meta = doc[2] or {}
    retrieval_meta = doc[4] if len(doc) > 4 and isinstance(doc[4], dict) else {}
    return {
        "id": doc[0],
        "filename": meta.get("filename") or meta.get("source") or meta.get("type") or f"document-{doc[0]}",
        "source": meta.get("source"),
        "score": doc[3] if len(doc) > 3 else None,
        "rrf_score": retrieval_meta.get("rrf_score"),
        "vector_rank": retrieval_meta.get("vector_rank"),
        "keyword_rank": retrieval_meta.get("keyword_rank"),
    }


def _try_direct_adjacent_answer(question: str, valid_docs):
    normalized_question = (question or "").strip()
    if not normalized_question:
        return None
    if len(normalized_question) < 6:
        return None

    for index, doc in enumerate(valid_docs[:-1]):
        content = (doc[1] or "").strip()
        meta = doc[2] or {}
        next_doc = valid_docs[index + 1]
        next_meta = next_doc[2] or {}
        next_content = (next_doc[1] or "").strip()

        if not next_content:
            continue
        if meta.get("source") != next_meta.get("source"):
            continue
        if normalized_question not in content:
            continue
        if len(content) > len(normalized_question) + 16:
            continue

        filename = meta.get("filename") or meta.get("source") or "参考文档"
        upload_time = (meta.get("upload_time") or meta.get("created_at") or "")[:19]
        if upload_time:
            answer = f"根据《{filename}》（上传时间：{upload_time}），{next_content}"
        else:
            answer = next_content
        return {
            "answer": answer,
            "source_doc": doc,
            "answer_doc": next_doc,
        }

    return None


def _log_valid_docs(trace_id: str, valid_docs):
    for idx, doc in enumerate(valid_docs, 1):
        meta = doc[2] or {}
        retrieval_meta = doc[4] if len(doc) > 4 and isinstance(doc[4], dict) else {}
        logger.info(
            "[RETRIEVAL][%s] valid_doc index=%s id=%s filename=%s source=%s distance=%s rrf_score=%s vector_rank=%s keyword_rank=%s content=%s metadata=%s",
            trace_id,
            idx,
            doc[0],
            meta.get("filename"),
            meta.get("source"),
            doc[3] if len(doc) > 3 else None,
            retrieval_meta.get("rrf_score"),
            retrieval_meta.get("vector_rank"),
            retrieval_meta.get("keyword_rank"),
            doc[1],
            json.dumps(meta, ensure_ascii=False),
        )


# Optimized helpers. These intentionally override the earlier compatibility
# versions so older deployments can keep running while the RAG path uses the
# richer chunk metadata added by the current ingestion pipeline.
def _build_debug_payload(docs, valid_docs, retrieval_debug, current_threshold):
    candidates = []
    for doc in docs:
        meta = doc[2] or {}
        retrieval_meta = doc[4] if len(doc) > 4 and isinstance(doc[4], dict) else {}
        candidates.append({
            "id": doc[0],
            "filename": meta.get("filename"),
            "source": meta.get("source"),
            "chunk_index": meta.get("chunk_index"),
            "chunk_type": meta.get("chunk_type"),
            "distance": doc[3] if len(doc) > 3 else None,
            "rrf_score": retrieval_meta.get("rrf_score"),
            "vector_rank": retrieval_meta.get("vector_rank"),
            "keyword_rank": retrieval_meta.get("keyword_rank"),
            "bm25_score": retrieval_meta.get("bm25_score"),
            "rerank_score": retrieval_meta.get("rerank_score"),
            "rerank_provider": retrieval_meta.get("rerank_provider"),
            "preview": (doc[1] or "")[:160],
            "content": doc[1],
            "metadata": meta,
        })

    return {
        "retrieval": retrieval_debug or {},
        "threshold": current_threshold,
        "candidate_count": len(docs),
        "valid_doc_count": len(valid_docs),
        "candidates": candidates,
    }


def _expand_neighbor_docs(trace_id: str, docs):
    if not docs or CONTEXT_EXPAND_WINDOW <= 0:
        return docs

    source_bounds = {}
    index_bounds = {}
    source_chunk_totals = {}
    source_order = []
    for doc in docs:
        meta = doc[2] or {}
        source = meta.get("source")
        if not source:
            continue

        doc_id = int(doc[0])
        if source not in source_bounds:
            source_bounds[source] = [doc_id, doc_id]
            source_order.append(source)
        else:
            source_bounds[source][0] = min(source_bounds[source][0], doc_id)
            source_bounds[source][1] = max(source_bounds[source][1], doc_id)

        try:
            chunk_index = int(meta.get("chunk_index"))
            if source not in index_bounds:
                index_bounds[source] = [chunk_index, chunk_index]
            else:
                index_bounds[source][0] = min(index_bounds[source][0], chunk_index)
                index_bounds[source][1] = max(index_bounds[source][1], chunk_index)
        except (TypeError, ValueError):
            pass
        try:
            chunk_total = int(meta.get("chunk_total"))
            if 0 < chunk_total <= SOURCE_CONTEXT_MAX_CHUNKS:
                source_chunk_totals[source] = chunk_total
        except (TypeError, ValueError):
            pass

    if not source_bounds:
        return docs

    docs_by_source = {}
    original_docs_by_id = {doc[0]: doc for doc in docs}
    seed_ids = {doc[0] for doc in docs}
    try:
        with engine.connect() as conn:
            for source, (min_id, max_id) in source_bounds.items():
                rows = []
                if source in source_chunk_totals:
                    rows = conn.execute(
                        text("""
                            SELECT id, content, metadata
                            FROM documents
                            WHERE metadata->>'source' = :source
                              AND metadata ? 'chunk_index'
                              AND (metadata->>'chunk_index')::int BETWEEN 1 AND :chunk_total
                            ORDER BY (metadata->>'chunk_index')::int ASC, id ASC
                        """),
                        {
                            "source": source,
                            "chunk_total": source_chunk_totals[source],
                        },
                    ).fetchall()
                elif source in index_bounds:
                    min_idx, max_idx = index_bounds[source]
                    rows = conn.execute(
                        text("""
                            SELECT id, content, metadata
                            FROM documents
                            WHERE metadata->>'source' = :source
                              AND metadata ? 'chunk_index'
                              AND (metadata->>'chunk_index')::int BETWEEN :min_idx AND :max_idx
                            ORDER BY (metadata->>'chunk_index')::int ASC, id ASC
                        """),
                        {
                            "source": source,
                            "min_idx": min_idx - CONTEXT_EXPAND_WINDOW,
                            "max_idx": max_idx + CONTEXT_EXPAND_WINDOW,
                        },
                    ).fetchall()

                if not rows:
                    rows = conn.execute(
                        text("""
                            SELECT id, content, metadata
                            FROM documents
                            WHERE metadata->>'source' = :source
                              AND id BETWEEN :min_id AND :max_id
                            ORDER BY id ASC
                        """),
                        {
                            "source": source,
                            "min_id": min_id - CONTEXT_EXPAND_WINDOW,
                            "max_id": max_id + CONTEXT_EXPAND_WINDOW,
                        },
                    ).fetchall()

                docs_by_source[source] = [
                    (
                        row[0],
                        row[1],
                        row[2],
                        original_docs_by_id[row[0]][3] if row[0] in original_docs_by_id else 1.0,
                        dict(original_docs_by_id[row[0]][4]) if row[0] in original_docs_by_id and len(original_docs_by_id[row[0]]) > 4 and isinstance(original_docs_by_id[row[0]][4], dict) else {
                            "rrf_score": None,
                            "vector_rank": None,
                            "keyword_rank": None,
                            "bm25_score": None,
                            "rerank_score": None,
                            "context_expanded": True,
                        },
                    )
                    for row in rows
                ]
                for idx, doc in enumerate(docs_by_source[source]):
                    retrieval_meta = dict(doc[4]) if len(doc) > 4 and isinstance(doc[4], dict) else {}
                    retrieval_meta["context_expanded"] = doc[0] not in seed_ids
                    docs_by_source[source][idx] = (doc[0], doc[1], doc[2], doc[3], retrieval_meta)
    except Exception:
        logger.exception("[RETRIEVAL][%s] expand_neighbor_docs_failed", trace_id)
        return docs

    ordered = []
    seen_ids = set()
    for source in source_order:
        for doc in docs_by_source.get(source, []):
            if doc[0] not in seen_ids:
                ordered.append(doc)
                seen_ids.add(doc[0])
    for doc in docs:
        if doc[0] not in seen_ids:
            ordered.append(doc)
            seen_ids.add(doc[0])

    logger.info(
        "[RETRIEVAL][%s] context_expanded seed_count=%s expanded_count=%s window=%s ids=%s",
        trace_id,
        len(docs),
        len(ordered),
        CONTEXT_EXPAND_WINDOW,
        [doc[0] for doc in ordered],
    )
    return ordered


def _source_payload_from_doc(doc):
    meta = doc[2] or {}
    retrieval_meta = doc[4] if len(doc) > 4 and isinstance(doc[4], dict) else {}
    return {
        "id": doc[0],
        "filename": meta.get("filename") or meta.get("source") or meta.get("type") or f"document-{doc[0]}",
        "source": meta.get("source"),
        "score": doc[3] if len(doc) > 3 else None,
        "rrf_score": retrieval_meta.get("rrf_score"),
        "vector_rank": retrieval_meta.get("vector_rank"),
        "keyword_rank": retrieval_meta.get("keyword_rank"),
        "bm25_score": retrieval_meta.get("bm25_score"),
        "rerank_score": retrieval_meta.get("rerank_score"),
    }


def _compact_match_text(value: str) -> str:
    return "".join(str(value or "").lower().split())


def _format_source_answer(answer: str, meta: Dict[str, Any]) -> str:
    answer = (answer or "").strip()
    filename = meta.get("filename") or meta.get("source") or "参考文档"
    upload_time = (meta.get("upload_time") or meta.get("created_at") or "")[:19]
    if upload_time:
        return f"根据《{filename}》（上传时间：{upload_time}），{answer}"
    return answer


def _extract_answer_from_content(content: str) -> Optional[Dict[str, str]]:
    for pattern in (
        r"问题\s*[:：]\s*(?P<question>.+?)\n答案\s*[:：]\s*(?P<answer>.+)",
        r"问\s*[:：]\s*(?P<question>.+?)\n答\s*[:：]\s*(?P<answer>.+)",
    ):
        match = re.search(pattern, content or "", flags=re.S)
        if match:
            return {
                "question": (match.group("question") or "").strip(),
                "answer": (match.group("answer") or "").strip(),
            }
    return None


def _query_terms(value: str) -> List[str]:
    terms = re.findall(r"[\u4e00-\u9fff]{2,}|[a-z0-9_./:-]+", (value or "").lower())
    expanded: List[str] = []
    for term in terms:
        expanded.append(term)
        if re.fullmatch(r"[\u4e00-\u9fff]+", term) and len(term) > 2:
            expanded.extend(term[idx:idx + 2] for idx in range(len(term) - 1))
    return [term for term in expanded if len(term) >= 2]


def _clean_direct_answer_line(content: str, meta: Dict[str, Any]) -> str:
    qa_answer = str(meta.get("qa_answer") or "").strip()
    if qa_answer:
        return qa_answer

    extracted = _extract_answer_from_content(content)
    if extracted and extracted.get("answer"):
        return extracted["answer"]

    line = (content or "").strip()
    line = re.sub(r"^问题\s*[:：]\s*", "", line)
    line = re.sub(r"\n答案\s*[:：]\s*", "：", line)
    return line.strip().rstrip("：:")


def _try_direct_source_answer(question: str, valid_docs):
    terms = _query_terms(question)
    if not terms:
        return None

    source_groups: Dict[str, List[Any]] = {}
    source_order: List[str] = []
    for doc in valid_docs:
        meta = doc[2] or {}
        source = meta.get("source")
        if not source:
            continue
        if source not in source_groups:
            source_groups[source] = []
            source_order.append(source)
        source_groups[source].append(doc)

    for source in source_order:
        docs = source_groups[source]
        first_meta = docs[0][2] or {}
        filename = str(first_meta.get("filename") or source)
        combined_text = _compact_match_text(filename + "\n" + "\n".join(doc[1] or "" for doc in docs))
        matched_terms = [term for term in terms if _compact_match_text(term) in combined_text]
        if len(matched_terms) < min(2, len(set(terms))):
            continue

        lines: List[str] = []
        seen = set()
        for doc in sorted(docs, key=lambda item: ((item[2] or {}).get("chunk_index") or 999999, item[0])):
            meta = doc[2] or {}
            line = _clean_direct_answer_line(doc[1] or "", meta)
            if not line:
                continue
            if len(line) > 260:
                line = line[:260].rstrip("，。；; ") + "..."
            normalized = _compact_match_text(line)
            if normalized and normalized not in seen:
                lines.append(line)
                seen.add(normalized)
            if len(lines) >= 4:
                break

        if lines:
            answer = "；".join(line.rstrip("。；;") for line in lines) + "。"
            return {
                "answer": _format_source_answer(answer, first_meta),
                "source_doc": docs[0],
                "answer_doc": docs[-1],
                "match_type": "direct_source",
            }

    return None


def _try_direct_structured_answer(question: str, valid_docs):
    normalized_question = _compact_match_text(question)
    if len(normalized_question) < 4:
        return None

    for doc in valid_docs:
        content = doc[1] or ""
        meta = doc[2] or {}
        qa_question = str(meta.get("qa_question") or "")
        qa_answer = str(meta.get("qa_answer") or "")
        if not qa_question or not qa_answer:
            extracted = _extract_answer_from_content(content)
            if extracted:
                qa_question = qa_question or extracted["question"]
                qa_answer = qa_answer or extracted["answer"]

        normalized_doc_question = _compact_match_text(qa_question)
        normalized_content = _compact_match_text(content)
        if not qa_answer:
            continue
        question_match = bool(normalized_doc_question) and (
            normalized_question in normalized_doc_question
            or normalized_doc_question in normalized_question
        )
        if question_match or normalized_question in normalized_content:
            return {
                "answer": _format_source_answer(qa_answer, meta),
                "source_doc": doc,
                "answer_doc": doc,
                "match_type": "structured_qa",
            }

    return None


def _try_direct_adjacent_answer(question: str, valid_docs):
    structured = _try_direct_structured_answer(question, valid_docs)
    if structured:
        return structured

    source_answer = _try_direct_source_answer(question, valid_docs)
    if source_answer:
        return source_answer

    normalized_question = (question or "").strip()
    if not normalized_question or len(normalized_question) < 6:
        return None

    for index, doc in enumerate(valid_docs[:-1]):
        content = (doc[1] or "").strip()
        meta = doc[2] or {}
        next_doc = valid_docs[index + 1]
        next_meta = next_doc[2] or {}
        next_content = (next_doc[1] or "").strip()

        if not next_content:
            continue
        if meta.get("source") != next_meta.get("source"):
            continue
        if normalized_question not in content:
            continue
        if len(content) > len(normalized_question) + 16:
            continue

        return {
            "answer": _format_source_answer(next_content, meta),
            "source_doc": doc,
            "answer_doc": next_doc,
            "match_type": "adjacent_chunk",
        }

    return None


def _log_valid_docs(trace_id: str, valid_docs):
    for idx, doc in enumerate(valid_docs, 1):
        meta = doc[2] or {}
        retrieval_meta = doc[4] if len(doc) > 4 and isinstance(doc[4], dict) else {}
        logger.info(
            "[RETRIEVAL][%s] valid_doc index=%s id=%s filename=%s source=%s chunk_index=%s chunk_type=%s distance=%s rrf_score=%s vector_rank=%s bm25_rank=%s bm25_score=%s rerank_score=%s content=%s metadata=%s",
            trace_id,
            idx,
            doc[0],
            meta.get("filename"),
            meta.get("source"),
            meta.get("chunk_index"),
            meta.get("chunk_type"),
            doc[3] if len(doc) > 3 else None,
            retrieval_meta.get("rrf_score"),
            retrieval_meta.get("vector_rank"),
            retrieval_meta.get("keyword_rank"),
            retrieval_meta.get("bm25_score"),
            retrieval_meta.get("rerank_score"),
            doc[1],
            json.dumps(meta, ensure_ascii=False),
        )


def answer_question(
    question: str,
    image: Optional[str] = None,
    kb_type: str = "user",
    history: Optional[List[Dict[str, Any]]] = None,
    debug: bool = False,
    trace_id: Optional[str] = None,
) -> Dict:
    trace_id = trace_id or uuid.uuid4().hex[:8]
    started_at = time.perf_counter()
    history_text = _format_history(history)
    ocr_text = ""
    if image:
        tmp_path = None
        logger.info(f"[OCR][{trace_id}] Processing image for text extraction...")
        try:
            if "," in image:
                _, encoded = image.split(",", 1)
            else:
                encoded = image

            img_data = base64.b64decode(encoded)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(img_data)
                tmp_path = tmp.name

            logger.info(f"[OCR][{trace_id}] Decoded image bytes={len(img_data)} temp={tmp_path}")

            # Check if ocr_engine and the inner .ocr object are available
            ocr_text = ""
            if ocr_engine and ocr_engine.ocr:
                ocr_text = ocr_engine.extract_text(tmp_path)
            else:
                logger.warning(f"[OCR][{trace_id}] OCR engine not ready, proceeding to Vision Fallback.")

            if ocr_text:
                logger.info(f"[OCR][{trace_id}] Extracted chars={len(ocr_text)} preview={ocr_text[:80]}")
                question = f"{question}\n\n【图片识别内容】\n{ocr_text}"
                # 关键修复：既然本地 OCR 成功了，就不需要再让大模型处理图片了
                # 将 image 置为 None，确保后续只调用纯语言模型
                image = None
            else:
                logger.info(f"[OCR][{trace_id}] No text detected in image")
                vision_prompt = "请提取并输出图片中的关键文字、报错码、报错上下文。仅输出识别结果，不要解释。"
                vision_text = call_llm(vision_prompt, image=image, trace_id=trace_id, purpose="vision_ocr_fallback")
                if vision_text and not vision_text.startswith("调用 LLM 失败"):
                    ocr_text = vision_text.strip()
                    logger.info(f"[OCR][{trace_id}] Vision fallback chars={len(ocr_text)} preview={ocr_text[:80]}")
                    question = f"{question}\n\n【图片识别内容】\n{ocr_text}"
                else:
                    logger.warning(f"[OCR][{trace_id}] Vision fallback failed: {vision_text[:120] if vision_text else ''}")
        except Exception:
            logger.exception(f"[OCR][{trace_id}] Failed to process image")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    if not image and not ocr_text and is_low_information_question(question):
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info("[QA][%s] low_information_question elapsed_ms=%s question=%s", trace_id, elapsed_ms, question)
        return {
            "answer": LOW_INFORMATION_ANSWER,
            "sources": [],
            "debug": {"intent": "low_information", "history_used": bool(history_text)} if debug else None,
        }

    # 0. Intent Classification
    # Skip classification if image/OCR is present (usually technical) or if explicitly technical
    if not image and not ocr_text:
        intent = classify_intent(question, trace_id=trace_id)
        if intent == "chitchat":
            # Direct chat without retrieval
            history_block = f"【历史对话】\n{history_text}\n\n" if history_text else ""
            chat_prompt = f"{history_block}用户输入：{question}\n\n请自然、友好地回应用户。不要提及知识库或文档。"
            answer = call_llm(chat_prompt, image=image, trace_id=trace_id, purpose="chitchat")
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
            logger.info("[QA][%s] chitchat_done elapsed_ms=%s answer=%s", trace_id, elapsed_ms, answer)
            return {
                "answer": answer,
                "sources": [],
                "debug": {"intent": intent, "history_used": bool(history_text)} if debug else None,
            }

    # 1. 检索 (传入 kb_type)
    # Define threshold for similarity distance (lower is better for cosine distance in pgvector)
    # Using L2 distance (<->): 
    # 0.8 ~= Cosine Sim 0.68 (Too strict)
    # 1.2 ~= Cosine Sim 0.28 (Reasonable for retrieval)
    # 1.4 ~= Relaxed for broader recall
    SIMILARITY_THRESHOLD = 1.45
    
    retrieval_query = _build_retrieval_query(question, history)
    retrieval_debug = None
    try:
        docs, retrieval_debug = retrieve_similar_documents(
            retrieval_query,
            kb_type=kb_type,
            top_k=int(os.getenv("FINAL_TOP_K", "5")),
            return_debug=True,
            trace_id=trace_id,
        )
    except Exception:
        logger.exception("[RETRIEVAL][%s] retrieval_failed strict_unknown question=%s", trace_id, question)
        docs = []

    # Dynamic Thresholding Strategy:
    # If we find a very high-quality match (e.g., keyword match with distance 0.0 or very close vector match),
    # we should significantly tighten the threshold to exclude irrelevant "noise" documents.
    current_threshold = SIMILARITY_THRESHOLD
    if docs:
        # Get the best (minimum) distance
        min_dist = min([d[3] if len(d) > 3 else 1.0 for d in docs])
        
        # If best match is extremely close (e.g. < 0.2, likely a keyword match or perfect vector match)
        if min_dist < 0.2:
             # Tighten threshold to only include other very strong matches.
             # 0.5 allows for some variation but cuts off the ~1.2 noise.
             current_threshold = 0.5 

    # Re-check docs after filtering using the dynamic threshold
    valid_docs = [
        d for d in docs
        if (d[3] if len(d) > 3 else 1.0) <= current_threshold
        or (len(d) > 4 and isinstance(d[4], dict) and d[4].get("keyword_rank"))
    ]
    valid_docs = _expand_neighbor_docs(trace_id, valid_docs)
    valid_docs_with_source = [d for d in valid_docs if _has_document_source(d)]
    _log_valid_docs(trace_id, valid_docs)

    sources = []
    seen_sources = set()
    ranked_source_docs = sorted(
        valid_docs_with_source,
        key=lambda d: (
            d[3] if len(d) > 3 and d[3] is not None else 9999,
            d[0],
        ),
    )
    for doc in ranked_source_docs:
        meta = doc[2] or {}
        source_key = meta.get("source") or meta.get("filename") or str(doc[0])
        if source_key in seen_sources:
            continue
        sources.append(_source_payload_from_doc(doc))
        seen_sources.add(source_key)

    if not valid_docs_with_source:
        debug_payload = _build_debug_payload(docs, valid_docs, retrieval_debug, current_threshold)
        debug_payload["history_used"] = bool(history_text)
        debug_payload["strict_unknown_reason"] = "no_valid_document_source" if valid_docs else "no_valid_docs"
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info(
            "[QA][%s] strict_unknown reason=%s elapsed_ms=%s debug=%s",
            trace_id,
            debug_payload["strict_unknown_reason"],
            elapsed_ms,
            json.dumps(debug_payload, ensure_ascii=False),
        )
        result = {
            "answer": UNKNOWN_ANSWER,
            "sources": [],
            "debug": debug_payload,
        }
        if not debug:
            result.pop("debug", None)
        return result

    # 2. 构建 Prompt
    direct_answer = _try_direct_adjacent_answer(question, valid_docs_with_source)
    if direct_answer:
        answer = direct_answer["answer"]
        source_payload = _source_payload_from_doc(direct_answer["source_doc"])
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info(
            "[QA][%s] direct_answer elapsed_ms=%s match_type=%s source_id=%s answer_id=%s answer=%s",
            trace_id,
            elapsed_ms,
            direct_answer.get("match_type"),
            direct_answer["source_doc"][0],
            direct_answer["answer_doc"][0],
            answer,
        )
        result = {
            "answer": answer,
            "sources": [source_payload],
        }
        if debug:
            result["debug"] = _build_debug_payload(docs, valid_docs, retrieval_debug, current_threshold)
            result["debug"]["history_used"] = bool(history_text)
            result["debug"]["direct_answer"] = {
                "source_id": direct_answer["source_doc"][0],
                "answer_id": direct_answer["answer_doc"][0],
                "match_type": direct_answer.get("match_type"),
            }
        return result

    context = build_context(valid_docs_with_source)
    
    # 组合 System Prompt 和 User Prompt
    history_block = f"\n【历史对话】\n{history_text}\n" if history_text else ""
    full_prompt = f"{SYSTEM_PROMPT}{history_block}\n\n{build_prompt(question, context)}"

    # 3. 调用 LLM
    answer = call_llm(full_prompt, image=image, trace_id=trace_id, purpose="rag_answer")

    result = {
        "answer": answer,
        "sources": sources
    }
    elapsed_ms = int((time.perf_counter() - started_at) * 1000)
    logger.info(
        "[QA][%s] rag_answer_done elapsed_ms=%s sources=%s answer=%s",
        trace_id,
        elapsed_ms,
        json.dumps(sources, ensure_ascii=False),
        answer,
    )
    if debug:
        result["debug"] = _build_debug_payload(docs, valid_docs, retrieval_debug, current_threshold)
        result["debug"]["history_used"] = bool(history_text)
    return result
