from pydantic import BaseModel


class KeywordExtractionRequest(BaseModel):
    text: str
    

class KeywordExtractionResponse(BaseModel):
    keywords: list
    key_sentences: list
