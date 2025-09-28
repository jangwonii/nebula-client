import re

def split_sentences_ko(text: str) -> list[str]:
    """한국어 텍스트를 문장 단위로 분할합니다."""
    if not text or not text.strip():
        return []
    
    # 한국어 문장 종결 패턴 (마침표, 느낌표, 물음표)
    sentence_endings = r"[.!?]+"
    
    # 문장 분할
    sentences = re.split(sentence_endings, text)
    
    # 빈 문장 제거 및 공백 정리
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences