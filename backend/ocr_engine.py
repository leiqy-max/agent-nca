import os
import sys
import logging

logger = logging.getLogger(__name__)

class OCREngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OCREngine, cls).__new__(cls)
            cls._instance.ocr = None
            logger.info("[OCR] Initializing Light-Weight OCR Engine (RapidOCR)...")

            try:
                from rapidocr_onnxruntime import RapidOCR
                cls._instance.ocr = RapidOCR()
                logger.info("[OCR] RapidOCR Engine initialized successfully.")
            except Exception as e:
                logger.exception(f"[OCR] Failed to initialize RapidOCR Engine: {e}")
                cls._instance.ocr = None

        return cls._instance

    def extract_text(self, image_path):
        if not self.ocr:
            logger.warning("[OCR] Engine not ready, skipping OCR extraction")
            return ""

        if not os.path.exists(image_path):
            logger.warning(f"[OCR] Image file not found: {image_path}")
            return ""

        try:
            result, _ = self.ocr(image_path)
            if not result:
                return ""

            # rapidocr returns a list of tuples: [([[x1,y1], [x2,y2], [x3,y3], [x4,y4]], text, confidence), ...]
            extracted_texts = [item[1] for item in result if item and len(item) > 1]
            return "\n".join(extracted_texts)
        except Exception as e:
            logger.error(f"[OCR] Error during extraction: {e}")
            return ""

# 单例模式导出
ocr_engine = OCREngine()
