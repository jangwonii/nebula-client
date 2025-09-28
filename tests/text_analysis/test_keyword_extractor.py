"""Tests for keyword_extractor.keybert_analyze."""

from __future__ import annotations

from typing import Any, List, Sequence, Tuple

import pytest

from app.services.text_analysis import keyword_extractor


class FakeKeyBERT:
    """Lightweight stand-in for KeyBERT used in tests."""

    def __init__(
        self,
        keyword_result: Sequence[Tuple[str, float]],
        sentence_result: Sequence[Sequence[Tuple[str, float]]],
        *,
        raise_on_empty: bool = True,
    ) -> None:
        self._keyword_result = list(keyword_result)
        self._sentence_result = [list(items) for items in sentence_result]
        self._raise_on_empty = raise_on_empty

    def extract_keywords(self, target: Any, **kwargs: Any) -> List[Any]:
        if isinstance(target, list):
            return [list(items) for items in self._sentence_result]

        if not isinstance(target, str):
            raise TypeError("target must be a string")

        if not target.strip() and self._raise_on_empty:
            raise ValueError("empty vocabulary; perhaps the text only contains stop words")

        top_n = kwargs.get("top_n", len(self._keyword_result))
        return list(self._keyword_result[:top_n])


def _patch_models(monkeypatch: pytest.MonkeyPatch, fake: FakeKeyBERT) -> None:
    monkeypatch.setattr(keyword_extractor, "_get_models", lambda: (fake, object()))


def test_keybert_analyze_returns_keywords_and_sentences(monkeypatch: pytest.MonkeyPatch) -> None:
    keyword_candidates = [
        ("한국 키워드", 0.91),
        ("텍스트 분석", 0.83),
        ("PDF 추출", 0.72),
    ]
    sentence_candidates = [
        [("네뷸라 프로젝트는 PDF에서 텍스트를 추출합니다", 0.88)],
        [("또한 한국어 키워드를 분석합니다", 0.79)],
    ]
    fake_kb = FakeKeyBERT(keyword_candidates, sentence_candidates, raise_on_empty=False)
    _patch_models(monkeypatch, fake_kb)

    text = "네뷸라 프로젝트는 PDF에서 텍스트를 추출합니다. 또한 한국어 키워드를 분석합니다!"

    keywords, key_sentences = keyword_extractor.keybert_analyze(text, top_n_keywords=2)

    assert keywords == keyword_candidates[:2]
    assert key_sentences == [items[0] for items in sentence_candidates]


def test_keybert_analyze_rejects_non_string(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_kb = FakeKeyBERT([], [], raise_on_empty=False)
    _patch_models(monkeypatch, fake_kb)

    with pytest.raises(TypeError):
        keyword_extractor.keybert_analyze(123)  # type: ignore[arg-type]


def test_keybert_analyze_propagates_empty_text_error(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_kb = FakeKeyBERT([], [], raise_on_empty=True)
    _patch_models(monkeypatch, fake_kb)

    with pytest.raises(ValueError, match="empty vocabulary"):
        keyword_extractor.keybert_analyze("   ")
