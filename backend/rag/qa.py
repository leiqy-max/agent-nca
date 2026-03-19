# rag/qa.py
from typing import List, Dict, Optional
import os
import logging
from rag.retriever import retrieve_similar_documents
from ocr_engine import ocr_engine
import base64
import tempfile
import uuid

from llm.factory import get_llm_client

logger = logging.getLogger(__name__)

def call_llm(prompt: str, image: Optional[str] = None) -> str:
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
            
        return client.chat(messages)
    except Exception as e:
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


def classify_intent(question: str) -> str:
    """
    判断用户意图
    """
    try:
        prompt = CLASSIFY_PROMPT.format(question=question)
        response = call_llm(prompt)
        if "闲聊" in response:
            return "chitchat"
        return "technical"
    except Exception:
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

def answer_question(question: str, image: Optional[str] = None, kb_type: str = "user") -> Dict:
    ocr_text = ""
    if image:
        trace_id = uuid.uuid4().hex[:8]
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
                vision_text = call_llm(vision_prompt, image=image)
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

    # 0. Intent Classification
    # Skip classification if image/OCR is present (usually technical) or if explicitly technical
    if not image and not ocr_text:
        intent = classify_intent(question)
        if intent == "chitchat":
            # Direct chat without retrieval
            chat_prompt = f"用户输入：{question}\n\n请自然、友好地回应用户。不要提及知识库或文档。"
            answer = call_llm(chat_prompt, image=image)
            return {
                "answer": answer,
                "sources": []
            }

    # 1. 检索 (传入 kb_type)
    # Define threshold for similarity distance (lower is better for cosine distance in pgvector)
    # Using L2 distance (<->): 
    # 0.8 ~= Cosine Sim 0.68 (Too strict)
    # 1.2 ~= Cosine Sim 0.28 (Reasonable for retrieval)
    # 1.4 ~= Relaxed for broader recall
    SIMILARITY_THRESHOLD = 1.45
    
    try:
        docs = retrieve_similar_documents(question, kb_type=kb_type, top_k=5)
    except Exception:
        logger.exception("[RAG] Retrieval failed, fallback to direct LLM answer")
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

    sources = []
    seen_filenames = set()
    if docs:
        for doc in docs:
            # doc structure: (id, content, metadata, distance)
            distance = doc[3] if len(doc) > 3 else 1.0
            
            # Filter by dynamic threshold
            if distance > current_threshold:
                continue
                
            meta = doc[2]
            if meta and "filename" in meta:
                filename = meta.get("filename")
                if filename not in seen_filenames:
                    sources.append({
                        "id": doc[0],
                        "filename": filename,
                        "source": meta.get("source"),
                        "score": distance
                    })
                    seen_filenames.add(filename)
    
    # Re-check docs after filtering using the dynamic threshold
    valid_docs = [d for d in docs if (d[3] if len(d) > 3 else 1.0) <= current_threshold]

    # 2. 构建 Prompt
    context = build_context(valid_docs) if valid_docs else "（未检索到相关文档）"
    
    # 组合 System Prompt 和 User Prompt
    full_prompt = f"{SYSTEM_PROMPT}\n\n{build_prompt(question, context)}"

    # 3. 调用 LLM
    answer = call_llm(full_prompt, image=image)
    
    return {
        "answer": answer,
        "sources": sources
    }
