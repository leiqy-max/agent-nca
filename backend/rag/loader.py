import json
import logging
import os
import re
import hashlib
import time
from sqlalchemy import text
from db import engine
from llm.embedding import embed_text
from rag.splitter import split_ops_doc

logger = logging.getLogger(__name__)

try:
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph
except ImportError:
    Document = None
    Table = None
    Paragraph = None

try:
    import pandas as pd
except ImportError:
    pd = None

def _normalize_cell_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _iter_docx_blocks(doc):
    parent_elm = doc.element.body
    for child in parent_elm.iterchildren():
        if Paragraph is not None and child.tag.endswith("}p"):
            yield Paragraph(child, doc)
        elif Table is not None and child.tag.endswith("}tbl"):
            yield Table(child, doc)


def _dedupe_merged_cells(cells):
    values = []
    last = None
    for cell in cells:
        value = _normalize_cell_text(cell.text)
        if value and value != last:
            values.append(value)
        last = value
    return values


def _table_to_text(table, table_index: int) -> list[str]:
    rows = []
    for row in table.rows:
        cells = _dedupe_merged_cells(row.cells)
        if cells:
            rows.append(cells)

    if not rows:
        return []

    lines = [f"【表格 {table_index}】"]
    header = rows[0]
    has_header = len(rows) > 1 and any(
        key in " ".join(header) for key in ("问题", "答案", "处理", "步骤", "说明", "原因", "现象")
    )

    for row_index, cells in enumerate(rows, start=1):
        if has_header and row_index == 1:
            lines.append("表头：" + " | ".join(header))
            continue
        if has_header and len(cells) == len(header):
            pairs = [
                f"{header[col_index]}：{cells[col_index]}"
                for col_index in range(len(cells))
                if header[col_index] and cells[col_index]
            ]
            line = "；".join(pairs)
        else:
            line = " | ".join(cells)
        if line:
            lines.append(line)
    return lines


def _read_docx_content(file_path: str) -> str:
    doc = Document(file_path)
    lines = []
    table_index = 0

    for block in _iter_docx_blocks(doc):
        if Paragraph is not None and isinstance(block, Paragraph):
            text_value = _normalize_cell_text(block.text)
            if text_value:
                lines.append(text_value)
        elif Table is not None and isinstance(block, Table):
            table_index += 1
            lines.extend(_table_to_text(block, table_index))

    return "\n".join(lines)


def read_file_content(file_path: str) -> str:
    """
    Read content from file based on extension.
    """
    suffix = os.path.splitext(file_path)[1].lower()
    if suffix == ".docx":
        if not Document:
            raise ImportError("python-docx is not installed, cannot read .docx files")
        return _read_docx_content(file_path)
    
    elif suffix in {".xlsx", ".xls"}:
        if not pd:
            raise ImportError("pandas/openpyxl is not installed, cannot read Excel files")
        # Read all sheets
        xls = pd.ExcelFile(file_path)
        text_content = []
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            text_content.append(f"Sheet: {sheet_name}")
            text_content.append(df.fillna("").to_csv(index=False, sep="\t"))
        return "\n\n".join(text_content)

    elif suffix == ".csv":
        if not pd:
            raise ImportError("pandas is not installed, cannot read CSV files")
        df = pd.read_csv(file_path)
        return df.fillna("").to_csv(index=False, sep="\t")
        
    else:
        # Default to text/md
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

def delete_document_by_source(source: str, trace_id: str = "-"):
    """
    Delete existing documents with the same source to avoid duplication.
    """
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM documents WHERE metadata->>'source' = :source"),
                {"source": source}
            )
            logger.info(
                "[INGEST][%s] deleted_existing source=%s rowcount=%s",
                trace_id,
                source,
                result.rowcount,
            )
    except Exception as e:
        logger.exception("[INGEST][%s] delete_existing_failed source=%s error=%s", trace_id, source, e)

def load_document(file_path: str, metadata: dict, kb_type: str = "user", trace_id: str = "-"):
    started_at = time.perf_counter()
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    logger.info(
        "[INGEST][%s] load_document_start path=%s size=%s kb_type=%s metadata=%s",
        trace_id,
        file_path,
        file_size,
        kb_type,
        json.dumps(metadata, ensure_ascii=False),
    )
    try:
        content = read_file_content(file_path)
    except Exception as e:
        logger.exception("[INGEST][%s] read_file_failed path=%s error=%s", trace_id, file_path, e)
        return

    if not content.strip():
        logger.warning("[INGEST][%s] empty_content path=%s", trace_id, file_path)
        return

    logger.info(
        "[INGEST][%s] read_file_done path=%s content_len=%s content=%s",
        trace_id,
        file_path,
        len(content),
        content,
    )

    # Add kb_type to metadata
    metadata["kb_type"] = kb_type

    # Deduplicate before inserting
    if "source" in metadata:
        delete_document_by_source(metadata["source"], trace_id=trace_id)

    inserted = load_text_content(content, metadata, trace_id=trace_id)
    elapsed_ms = int((time.perf_counter() - started_at) * 1000)
    logger.info(
        "[INGEST][%s] load_document_done path=%s inserted_chunks=%s elapsed_ms=%s",
        trace_id,
        file_path,
        inserted,
        elapsed_ms,
    )

def _build_chunk_payload(chunk_item, base_metadata: dict, index: int, total: int):
    chunk_metadata = dict(base_metadata or {})
    if isinstance(chunk_item, dict):
        chunk = str(chunk_item.get("content") or "").strip()
        chunk_metadata.update(chunk_item.get("metadata") or {})
    else:
        chunk = str(chunk_item or "").strip()

    chunk_metadata["chunk_index"] = index
    chunk_metadata["chunk_total"] = total
    chunk_metadata["chunk_hash"] = hashlib.sha1(chunk.encode("utf-8")).hexdigest()
    chunk_metadata.setdefault("chunk_type", "text")
    return chunk, chunk_metadata


def load_text_content(content: str, metadata: dict, trace_id: str = "-") -> int:
    started_at = time.perf_counter()
    chunks = split_ops_doc(content)
    logger.info(
        "[INGEST][%s] split_done content_len=%s chunk_count=%s metadata=%s",
        trace_id,
        len(content or ""),
        len(chunks),
        json.dumps(metadata, ensure_ascii=False),
    )

    inserted_count = 0
    with engine.begin() as conn:
        for idx, chunk_item in enumerate(chunks, 1):
            chunk, chunk_metadata = _build_chunk_payload(chunk_item, metadata, idx, len(chunks))
            if not chunk:
                continue
            logger.info(
                "[INGEST][%s] chunk_start index=%s/%s char_len=%s chunk_type=%s metadata=%s content=%s",
                trace_id,
                idx,
                len(chunks),
                len(chunk or ""),
                chunk_metadata.get("chunk_type"),
                json.dumps(chunk_metadata, ensure_ascii=False),
                chunk,
            )
            vector = embed_text(chunk, trace_id=trace_id)
            result = conn.execute(
                text("""
                    INSERT INTO documents (content, metadata, embedding)
                    VALUES (:content, :metadata, :embedding)
                """),
                {
                    "content": chunk,
                    "metadata": json.dumps(chunk_metadata, ensure_ascii=False),
                    "embedding": vector
                }
            )
            inserted_count += result.rowcount or 1
            logger.info(
                "[INGEST][%s] chunk_inserted index=%s/%s embedding_dim=%s rowcount=%s",
                trace_id,
                idx,
                len(chunks),
                len(vector or []),
                result.rowcount,
            )

    elapsed_ms = int((time.perf_counter() - started_at) * 1000)
    logger.info(
        "[INGEST][%s] load_text_done chunk_count=%s inserted=%s elapsed_ms=%s",
        trace_id,
        len(chunks),
        inserted_count,
        elapsed_ms,
    )
    return inserted_count
