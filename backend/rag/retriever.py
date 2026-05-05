import logging
import math
import os
import re
import time
from collections import Counter
from typing import Dict, List, Sequence

import requests
from sqlalchemy import text

from db import engine
from llm.embedding import embed_text

logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _kb_filter_clause(kb_type: str) -> str:
    if kb_type == "all":
        return ""
    return "WHERE (metadata->>'kb_type' = :kb_type OR metadata->>'kb_type' IS NULL)"


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", (value or "").lower())


def _tokenize(text_value: str) -> List[str]:
    text_value = (text_value or "").lower()
    tokens: List[str] = []
    for part in re.findall(r"[\u4e00-\u9fff]+|[a-z0-9_./:-]+", text_value):
        if re.fullmatch(r"[\u4e00-\u9fff]+", part):
            if len(part) == 1:
                tokens.append(part)
                continue
            tokens.extend(part)
            tokens.extend(part[idx:idx + 2] for idx in range(len(part) - 1))
            if len(part) <= 10:
                tokens.append(part)
        else:
            tokens.append(part)
    return [token for token in tokens if token]


def _document_text_for_rank(content: str, metadata: Dict) -> str:
    meta_parts = []
    for key in ("filename", "qa_question", "qa_answer", "section"):
        value = (metadata or {}).get(key)
        if value:
            meta_parts.append(str(value))
    return "\n".join([content or "", *meta_parts])


def _vector_search(query_embedding, kb_type: str, top_k: int):
    clause = _kb_filter_clause(kb_type)
    sql = f"""
        SELECT id, content, metadata, embedding <-> (:query_embedding)::vector AS distance
        FROM documents
        {clause}
        ORDER BY distance ASC
        LIMIT :top_k
    """
    params = {"query_embedding": query_embedding, "top_k": top_k}
    if kb_type != "all":
        params["kb_type"] = kb_type

    with engine.connect() as connection:
        return connection.execute(text(sql), params).fetchall()


def _fetch_bm25_corpus(kb_type: str, max_docs: int):
    clause = _kb_filter_clause(kb_type)
    sql = f"""
        SELECT id, content, metadata
        FROM documents
        {clause}
        ORDER BY id DESC
        LIMIT :max_docs
    """
    params = {"max_docs": max_docs}
    if kb_type != "all":
        params["kb_type"] = kb_type
    with engine.connect() as connection:
        return connection.execute(text(sql), params).fetchall()


def _bm25_score(
    query_tokens: Sequence[str],
    doc_tf: Counter,
    doc_len: int,
    avg_doc_len: float,
    doc_freq: Dict[str, int],
    doc_count: int,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    if not query_tokens or not doc_tf or doc_len <= 0 or avg_doc_len <= 0:
        return 0.0

    score = 0.0
    for token in query_tokens:
        tf = doc_tf.get(token, 0)
        if tf <= 0:
            continue
        df = doc_freq.get(token, 0)
        idf = math.log(1.0 + (doc_count - df + 0.5) / (df + 0.5))
        denom = tf + k1 * (1 - b + b * doc_len / avg_doc_len)
        score += idf * (tf * (k1 + 1)) / denom
    return score


def _bm25_search(query: str, kb_type: str, top_k: int, trace_id: str = "-"):
    query = (query or "").strip()
    query_tokens = _tokenize(query)
    if not query_tokens:
        return [], {"doc_count": 0, "query_tokens": []}

    max_docs = int(os.getenv("BM25_MAX_DOCS", "50000"))
    rows = _fetch_bm25_corpus(kb_type=kb_type, max_docs=max_docs)
    if not rows:
        return [], {"doc_count": 0, "query_tokens": query_tokens}

    tokenized_docs = []
    doc_freq: Dict[str, int] = {}
    total_len = 0
    for row in rows:
        metadata = row[2] or {}
        rank_text = _document_text_for_rank(row[1], metadata)
        tokens = _tokenize(rank_text)
        tf = Counter(tokens)
        doc_len = len(tokens)
        total_len += doc_len
        for token in set(query_tokens):
            if token in tf:
                doc_freq[token] = doc_freq.get(token, 0) + 1
        tokenized_docs.append((row, tf, doc_len))

    avg_doc_len = total_len / max(len(tokenized_docs), 1)
    compact_query = _compact(query)
    scored = []
    for row, tf, doc_len in tokenized_docs:
        content = row[1] or ""
        metadata = row[2] or {}
        score = _bm25_score(query_tokens, tf, doc_len, avg_doc_len, doc_freq, len(tokenized_docs))

        compact_content = _compact(content)
        qa_question = _compact(str(metadata.get("qa_question") or ""))
        if compact_query and compact_query in compact_content:
            score += 25.0
        if compact_query and qa_question and (compact_query in qa_question or qa_question in compact_query):
            score += 30.0
        if metadata.get("chunk_type") == "qa_pair":
            score += 2.0

        if score > 0:
            scored.append((row[0], content, metadata, score))

    scored.sort(key=lambda item: (-item[3], item[0]))
    debug = {
        "doc_count": len(rows),
        "query_tokens": query_tokens,
        "avg_doc_len": avg_doc_len,
        "max_docs": max_docs,
    }
    logger.info(
        "[RETRIEVAL][%s] bm25_scored doc_count=%s matched=%s top_k=%s query_tokens=%s",
        trace_id,
        len(rows),
        len(scored),
        top_k,
        query_tokens,
    )
    return scored[:top_k], debug


def _merge_reciprocal_rank(vector_docs, bm25_docs, pool_top_k: int, rrf_k: int):
    merged = {}

    for rank, doc in enumerate(vector_docs, start=1):
        entry = merged.setdefault(
            doc[0],
            {
                "id": doc[0],
                "content": doc[1],
                "metadata": doc[2],
                "distance": doc[3],
                "vector_rank": None,
                "keyword_rank": None,
                "bm25_score": None,
                "rrf_score": 0.0,
            },
        )
        entry["vector_rank"] = rank
        entry["distance"] = doc[3]
        entry["rrf_score"] += 1.0 / (rrf_k + rank)

    for rank, doc in enumerate(bm25_docs, start=1):
        entry = merged.setdefault(
            doc[0],
            {
                "id": doc[0],
                "content": doc[1],
                "metadata": doc[2],
                "distance": 9999.0,
                "vector_rank": None,
                "keyword_rank": None,
                "bm25_score": None,
                "rrf_score": 0.0,
            },
        )
        entry["keyword_rank"] = rank
        entry["bm25_score"] = doc[3]
        entry["rrf_score"] += 1.0 / (rrf_k + rank)

    ranked = sorted(
        merged.values(),
        key=lambda item: (
            -item["rrf_score"],
            -(item["bm25_score"] or 0.0),
            item["distance"],
            item["id"],
        ),
    )

    return [
        (
            item["id"],
            item["content"],
            item["metadata"],
            item["distance"],
            {
                "rrf_score": item["rrf_score"],
                "vector_rank": item["vector_rank"],
                "keyword_rank": item["keyword_rank"],
                "bm25_score": item["bm25_score"],
            },
        )
        for item in ranked[:pool_top_k]
    ]


def _local_rerank_score(query: str, doc) -> float:
    content = doc[1] or ""
    metadata = doc[2] or {}
    retrieval_meta = doc[4] if len(doc) > 4 and isinstance(doc[4], dict) else {}

    query_tokens = set(_tokenize(query))
    doc_tokens = set(_tokenize(_document_text_for_rank(content, metadata)))
    overlap = len(query_tokens & doc_tokens) / max(len(query_tokens), 1)

    compact_query = _compact(query)
    compact_content = _compact(content)
    qa_question = _compact(str(metadata.get("qa_question") or ""))
    exact = 1.0 if compact_query and compact_query in compact_content else 0.0
    qa_exact = 1.0 if compact_query and qa_question and (compact_query in qa_question or qa_question in compact_query) else 0.0

    distance = doc[3] if len(doc) > 3 and doc[3] is not None else 9999.0
    vector_component = 0.0 if distance >= 9999 else 1.0 / (1.0 + float(distance))
    bm25_component = min(float(retrieval_meta.get("bm25_score") or 0.0) / 20.0, 1.5)
    rrf_component = min(float(retrieval_meta.get("rrf_score") or 0.0) * 60.0, 1.5)
    qa_pair_bonus = 0.5 if metadata.get("chunk_type") == "qa_pair" else 0.0

    return (
        exact * 4.0
        + qa_exact * 4.0
        + overlap * 2.0
        + bm25_component * 1.5
        + vector_component
        + rrf_component
        + qa_pair_bonus
    )


def _attach_rerank_score(doc, score: float, provider: str, rank: int):
    retrieval_meta = dict(doc[4]) if len(doc) > 4 and isinstance(doc[4], dict) else {}
    retrieval_meta["rerank_score"] = score
    retrieval_meta["rerank_provider"] = provider
    retrieval_meta["rerank_rank"] = rank
    return (doc[0], doc[1], doc[2], doc[3], retrieval_meta)


def _http_rerank(query: str, docs, top_k: int, endpoint: str, trace_id: str):
    payload = {
        "query": query,
        "documents": [doc[1] or "" for doc in docs],
        "top_n": top_k,
    }
    timeout = float(os.getenv("RERANK_TIMEOUT", "30"))
    response = requests.post(endpoint, json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    results = data.get("results") or data.get("data") or []

    ranked = []
    for item in results:
        index = item.get("index")
        if index is None:
            index = item.get("document_index")
        try:
            index = int(index)
        except (TypeError, ValueError):
            continue
        if index >= len(docs):
            continue
        score = item.get("relevance_score", item.get("score", 0.0))
        ranked.append((index, float(score)))

    if not ranked and isinstance(data.get("scores"), list):
        ranked = [(idx, float(score)) for idx, score in enumerate(data["scores"]) if idx < len(docs)]

    ranked.sort(key=lambda item: (-item[1], item[0]))
    logger.info("[RETRIEVAL][%s] http_rerank_done count=%s endpoint=%s", trace_id, len(ranked), endpoint)
    return [_attach_rerank_score(docs[index], score, "http", rank) for rank, (index, score) in enumerate(ranked[:top_k], 1)]


def _rerank_documents(query: str, docs, top_k: int, trace_id: str = "-"):
    if not docs:
        return docs, {"enabled": False, "provider": "none"}

    enabled = _env_bool("RERANK_ENABLED", True)
    provider = os.getenv("RERANK_PROVIDER", "local").strip().lower()
    if not enabled or provider == "none":
        return docs[:top_k], {"enabled": False, "provider": provider}

    if provider == "http":
        endpoint = os.getenv("RERANK_ENDPOINT", "").strip()
        if endpoint:
            try:
                ranked = _http_rerank(query, docs, top_k, endpoint, trace_id)
                if ranked:
                    return ranked, {"enabled": True, "provider": "http", "endpoint": endpoint}
            except Exception as exc:
                logger.exception("[RETRIEVAL][%s] http_rerank_failed endpoint=%s error=%s", trace_id, endpoint, exc)

    scored = [(_local_rerank_score(query, doc), doc) for doc in docs]
    scored.sort(key=lambda item: (-item[0], item[1][0]))
    ranked = [
        _attach_rerank_score(doc, score, "local", rank)
        for rank, (score, doc) in enumerate(scored[:top_k], 1)
    ]
    return ranked, {"enabled": True, "provider": "local"}


def retrieve_similar_documents(
    query: str,
    kb_type: str = "user",
    top_k: int = 5,
    return_debug: bool = False,
    trace_id: str = "-",
):
    started_at = time.perf_counter()
    vector_top_k = int(os.getenv("VECTOR_TOP_K", str(max(top_k * 3, 12))))
    bm25_top_k = int(os.getenv("BM25_TOP_K", os.getenv("KEYWORD_TOP_K", str(max(top_k * 4, 20)))))
    final_top_k = int(os.getenv("FINAL_TOP_K", str(top_k)))
    fusion_top_k = int(os.getenv("FUSION_TOP_K", str(max(final_top_k * 4, final_top_k))))
    rrf_k = int(os.getenv("RRF_K", "60"))

    logger.info(
        "[RETRIEVAL][%s] start kb_type=%s vector_top_k=%s bm25_top_k=%s fusion_top_k=%s final_top_k=%s rrf_k=%s query=%s",
        trace_id,
        kb_type,
        vector_top_k,
        bm25_top_k,
        fusion_top_k,
        final_top_k,
        rrf_k,
        query,
    )

    query_embedding = embed_text(query, trace_id=trace_id)
    vector_docs = _vector_search(query_embedding, kb_type=kb_type, top_k=vector_top_k)
    logger.info("[RETRIEVAL][%s] vector_done count=%s", trace_id, len(vector_docs))

    bm25_docs = []
    bm25_debug = {}
    try:
        bm25_docs, bm25_debug = _bm25_search(query, kb_type=kb_type, top_k=bm25_top_k, trace_id=trace_id)
        logger.info("[RETRIEVAL][%s] bm25_done count=%s", trace_id, len(bm25_docs))
    except Exception as e:
        logger.exception("[RETRIEVAL][%s] bm25_failed error=%s", trace_id, e)

    debug = {
        "query": query,
        "kb_type": kb_type,
        "vector_top_k": vector_top_k,
        "bm25_top_k": bm25_top_k,
        "fusion_top_k": fusion_top_k,
        "final_top_k": final_top_k,
        "rrf_k": rrf_k,
        "vector_count": len(vector_docs),
        "keyword_count": len(bm25_docs),
        "bm25_count": len(bm25_docs),
        "bm25": bm25_debug,
    }

    if not vector_docs and not bm25_docs:
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        debug["elapsed_ms"] = elapsed_ms
        logger.info("[RETRIEVAL][%s] no_candidates elapsed_ms=%s", trace_id, elapsed_ms)
        return ([], debug) if return_debug else []

    fused_docs = _merge_reciprocal_rank(vector_docs, bm25_docs, pool_top_k=fusion_top_k, rrf_k=rrf_k)
    docs, rerank_debug = _rerank_documents(query, fused_docs, top_k=final_top_k, trace_id=trace_id)
    debug["merged_count"] = len(fused_docs)
    debug["rerank"] = rerank_debug
    debug["elapsed_ms"] = int((time.perf_counter() - started_at) * 1000)

    for idx, doc in enumerate(docs, 1):
        meta = doc[2] or {}
        retrieval_meta = doc[4] if len(doc) > 4 and isinstance(doc[4], dict) else {}
        logger.info(
            "[RETRIEVAL][%s] candidate index=%s id=%s filename=%s source=%s chunk_index=%s chunk_type=%s distance=%s rrf_score=%s vector_rank=%s bm25_rank=%s bm25_score=%s rerank_score=%s content=%s metadata=%s",
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
            meta,
        )
    logger.info(
        "[RETRIEVAL][%s] done merged_count=%s final_count=%s elapsed_ms=%s",
        trace_id,
        len(fused_docs),
        len(docs),
        debug["elapsed_ms"],
    )
    return (docs, debug) if return_debug else docs
