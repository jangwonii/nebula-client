# -*- coding: utf-8 -*-
import re
import fitz  # PyMuPDF
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer

# === 1) PDF 앞 N페이지 텍스트 추출 ===
def extract_pdf_head_text(path: str, n_pages: int = 1) -> str:
    with fitz.open(path) as doc:
        pages = min(n_pages, doc.page_count)
        parts = []
        for i in range(pages):
            page = doc.load_page(i)
            parts.append(page.get_text("text") or "")
    text = "\n".join(parts)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

# === 2) 한국어 문장 분할 ===
def split_sentences_ko(text: str):
    text = re.sub(r"\s+", " ", text)
    sents = re.split(r"(?<=[\.!\?])\s+(?=[가-힣A-Z0-9])", text)
    fixed = []
    for s in sents:
        fixed += re.split(r"(?<=다\.)\s+(?=[가-힣A-Z0-9])", s)
    return [s.strip() for s in fixed if len(s.strip()) >= 8]

# === 3) KeyBERT 분석 (최상위 1개만) ===
def keybert_analyze(text: str):
    embed = SentenceTransformer("jhgan/ko-sroberta-multitask")
    kb = KeyBERT(model=embed)


    # 중요 문장 1개
    sents = split_sentences_ko(text)
    if len(sents) == 0:
        key_sents = []
    else:
        key_sents = kb.extract_keywords(
            sents,
            keyphrase_ngram_range=(5, 10),
            use_mmr=False,
            top_n=1
        )

    return key_sents

