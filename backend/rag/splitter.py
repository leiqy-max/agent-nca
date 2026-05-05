import re
from typing import Dict, List, Optional, Union


Chunk = Union[str, Dict[str, object]]

MAX_CHUNK_SIZE = 700
CHUNK_OVERLAP = 120

_QUESTION_WORDS = (
    "问题",
    "报错",
    "错误",
    "失败",
    "异常",
    "故障",
    "无法",
    "不能",
    "不一致",
    "不同步",
    "未同步",
    "找不到",
    "如何",
    "怎么",
    "为什么",
    "告警",
    "调整",
    "修改",
    "派发",
)

_SECTION_SEPARATORS = (
    "\n处理步骤",
    "\n故障现象",
    "\n告警说明",
    "\n注意事项",
    "\n原因分析",
    "\n解决方案",
    "\n操作步骤",
)


def _normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", (line or "").strip())


def _strip_question_prefix(line: str) -> str:
    line = _normalize_line(line)
    line = re.sub(r"^(问题|问|Q|q)\s*[:：]\s*", "", line)
    line = re.sub(r"^\d+\s*[、.)．]\s*", "", line)
    return line.strip()


def _strip_answer_prefix(line: str) -> str:
    line = _normalize_line(line)
    return re.sub(r"^(答案|答|A|a|处理|解决|说明)\s*[:：]\s*", "", line).strip()


def _looks_like_title(line: str, index: int) -> bool:
    clean = _normalize_line(line)
    return index <= 1 and len(clean) <= 30 and clean.endswith(("问题", "手册", "指南", "操作手册"))


def _looks_like_question(line: str, index: int = 99) -> bool:
    clean = _normalize_line(line)
    if not clean or _looks_like_title(clean, index):
        return False
    if len(clean) > 120:
        return False
    if re.match(r"^(问题|问|Q|q)\s*[:：]", clean):
        return True
    if re.match(r"^\d+\s*[、.)．]", clean):
        return True
    if clean.endswith(("?", "？")):
        return True
    return any(word in clean for word in _QUESTION_WORDS)


def _looks_like_answer(line: str) -> bool:
    clean = _normalize_line(line)
    if not clean:
        return False
    if re.match(r"^(答案|答|A|a|处理|解决|说明)\s*[:：]", clean):
        return True
    return len(clean) <= 1000


def _split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[。！？!?；;])\s*|\n+", text)
    return [part.strip() for part in parts if part and part.strip()]


def _split_large_text(text: str, max_size: int = MAX_CHUNK_SIZE) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= max_size:
        return [text]

    chunks: List[str] = []
    current = ""
    for sentence in _split_sentences(text):
        candidate = f"{current}{sentence}" if not current else f"{current}{sentence}"
        if len(candidate) <= max_size:
            current = candidate
            continue

        if current:
            chunks.append(current.strip())
            current = current[-CHUNK_OVERLAP:] if len(current) > CHUNK_OVERLAP else current
        if len(sentence) > max_size:
            start = 0
            while start < len(sentence):
                chunks.append(sentence[start:start + max_size].strip())
                start += max_size - CHUNK_OVERLAP
            current = ""
        else:
            current = sentence

    if current.strip():
        chunks.append(current.strip())
    return [chunk for chunk in chunks if chunk]


def _extract_inline_qa(line: str) -> Optional[Dict[str, object]]:
    match = re.search(
        r"(?:问题|问|Q)\s*[:：]\s*(?P<q>.+?)\s*(?:答案|答|A)\s*[:：]\s*(?P<a>.+)",
        line,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    question = _strip_question_prefix(match.group("q"))
    answer = _strip_answer_prefix(match.group("a"))
    if not question or not answer:
        return None
    return {
        "content": f"问题：{question}\n答案：{answer}",
        "metadata": {
            "chunk_type": "qa_pair",
            "qa_question": question,
            "qa_answer": answer,
        },
    }


def _extract_qa_pairs(lines: List[str]) -> tuple[List[Chunk], set[int]]:
    chunks: List[Chunk] = []
    used: set[int] = set()

    for idx, line in enumerate(lines):
        if idx in used:
            continue

        inline = _extract_inline_qa(line)
        if inline:
            chunks.append(inline)
            used.add(idx)
            continue

        if not _looks_like_question(line, idx):
            continue

        answer_parts: List[str] = []
        cursor = idx + 1
        while cursor < len(lines):
            candidate = lines[cursor]
            if not candidate:
                cursor += 1
                continue
            if _looks_like_question(candidate, cursor):
                break
            if candidate.startswith("【图片"):
                cursor += 1
                continue
            if _looks_like_answer(candidate):
                answer_parts.append(_strip_answer_prefix(candidate))
                used.add(cursor)
            if len("\n".join(answer_parts)) >= 900:
                break
            cursor += 1

        question = _strip_question_prefix(line)
        answer = "\n".join(part for part in answer_parts if part).strip()
        if question and answer:
            chunks.append({
                "content": f"问题：{question}\n答案：{answer}",
                "metadata": {
                    "chunk_type": "qa_pair",
                    "qa_question": question,
                    "qa_answer": answer,
                },
            })
            used.add(idx)

    return chunks, used


def _split_by_sections(text: str) -> List[str]:
    chunks = [text]
    for separator in _SECTION_SEPARATORS:
        next_chunks: List[str] = []
        for chunk in chunks:
            if separator not in chunk:
                next_chunks.append(chunk)
                continue
            parts = chunk.split(separator)
            for idx, part in enumerate(parts):
                if idx > 0:
                    part = separator.strip() + "\n" + part
                if part.strip():
                    next_chunks.append(part.strip())
        chunks = next_chunks

    final_chunks: List[str] = []
    for chunk in chunks:
        final_chunks.extend(_split_large_text(chunk))
    return final_chunks


def split_ops_doc(text: str) -> List[Chunk]:
    """
    Split operations documents into retrieval-friendly chunks.

    The splitter keeps FAQ-like adjacent paragraphs together as one chunk so
    short questions such as "姿态仪数据未同步" retrieve the answer in the same
    context, while long manuals still fall back to section/sentence chunks.
    """
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [_normalize_line(line) for line in text.split("\n")]
    lines = [line for line in lines if line]
    if not lines:
        return []

    qa_chunks, used_line_indexes = _extract_qa_pairs(lines)

    remaining_blocks: List[str] = []
    current: List[str] = []
    for idx, line in enumerate(lines):
        if idx in used_line_indexes:
            if current:
                remaining_blocks.append("\n".join(current))
                current = []
            continue
        current.append(line)
    if current:
        remaining_blocks.append("\n".join(current))

    chunks: List[Chunk] = []
    chunks.extend(qa_chunks)

    for block in remaining_blocks:
        for chunk in _split_by_sections(block):
            clean = chunk.strip()
            if clean:
                chunks.append(clean)

    seen = set()
    deduped: List[Chunk] = []
    for chunk in chunks:
        content = chunk.get("content") if isinstance(chunk, dict) else chunk
        content = (content or "").strip()
        if not content or content in seen:
            continue
        seen.add(content)
        if isinstance(chunk, dict):
            chunk["content"] = content
            deduped.append(chunk)
        else:
            deduped.append(content)
    return deduped
