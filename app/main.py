import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status

from app.schemas.folder import (
    FolderContentsResponse,
    FolderSelectionRequest,
    FolderSnapshotRequest,
    FolderSnapshotResponse,
    SnapshotPageInfo,
)
from app.schemas.keyword import KeywordExtractionRequest, KeywordExtractionResponse
from app.services.folder_inspection import DirectoryInspectionError, inspect_directory
from app.services.folder_snapshot import snapshot_directory
from app.services.text_analysis.keyword_extractor import keybert_analyze


load_dotenv()

app = FastAPI(title="Nebula Client API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def root() -> dict:
    return {"message": "Nebula Client API"}


@app.post("/folders/inspect", response_model=FolderContentsResponse)
def inspect_folder(payload: FolderSelectionRequest) -> FolderContentsResponse:
    try:
        return inspect_directory(payload.path)
    except DirectoryInspectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@app.post("/folders/snapshot", response_model=FolderSnapshotResponse)
def snapshot_folder(payload: FolderSnapshotRequest) -> FolderSnapshotResponse:
    try:
        result = snapshot_directory(payload.path, payload.page_size)
    except DirectoryInspectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return FolderSnapshotResponse(
        directory=result.directory,
        generated_at=result.generated_at,
        total_entries=result.total_entries,
        page_size=result.page_size,
        page_count=result.page_count,
        pages=[
            SnapshotPageInfo(
                page=page.page,
                path=str(page.path),
                entry_count=page.entry_count,
            )
            for page in result.pages
        ],
    )


@app.post("/text/keywords", response_model=KeywordExtractionResponse)
def extract_keywords(payload: KeywordExtractionRequest) -> KeywordExtractionResponse:
    """텍스트에서 키워드와 중요 문장을 추출합니다."""
    try:
        keywords, key_sentences = keybert_analyze(payload.text)
        return KeywordExtractionResponse(
             keywords=keywords,
             key_sentences=key_sentences
         )
    except Exception as exc:
         raise HTTPException(
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             detail=f"키워드 추출 중 오류가 발생했습니다: {str(exc)}"
         ) from exc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )