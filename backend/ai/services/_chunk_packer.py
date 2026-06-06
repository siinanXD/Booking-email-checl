"""Interne Chunking-Logik: Token-Zählung, Segment-Splitting, Chunk-Packing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

MIN_CHUNK_TOKENS = 32
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")


@lru_cache(maxsize=4)
def _encoding_for_model(model: str) -> Any:
    import tiktoken

    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str, *, embedding_model: str = "text-embedding-3-small") -> int:
    """Zählt Tokens für das konfigurierte Embedding-Modell."""
    if not text:
        return 0
    enc = _encoding_for_model(embedding_model)
    return len(enc.encode(text))


@dataclass(frozen=True)
class _TextSegment:
    text: str
    char_start: int
    char_end: int
    token_count: int


def _emit_with_hard_split(
    text: str,
    start: int,
    *,
    embedding_model: str,
    max_segment_tokens: int,
    overlap_tokens: int,
    out: list[_TextSegment],
) -> None:
    """Fügt ein Segment hinzu; übergroße Texte werden hart an Wortgrenzen geteilt.

    Garantiert (bis auf ein einzelnes überlanges Wort), dass kein Segment das
    Token-Limit überschreitet. Verhindert, dass `_pack_body_chunks` ein einzelnes
    riesiges Segment sieht (das sonst keinen Fortschritt erlauben würde).
    """
    tokens = count_tokens(text, embedding_model=embedding_model)
    if tokens <= max_segment_tokens:
        out.append(_TextSegment(text, start, start + len(text), tokens))
        return

    # Übergroßen Text in Fenster teilen, die höchstens so groß wie das gewünschte
    # Overlap sind – so können mehrere Sub-Segmente in einen Chunk passen und der
    # Overlap am Übergang trifft ungefähr overlap_tokens (statt grob zu überschießen).
    if overlap_tokens > 0:
        target_tokens = max(1, min(max_segment_tokens, overlap_tokens))
    else:
        target_tokens = max(MIN_CHUNK_TOKENS, max_segment_tokens // 2)
    current: list[str] = []
    seg_start = start
    for word in text.split():
        candidate = " ".join([*current, word])
        if current and (
            count_tokens(candidate, embedding_model=embedding_model) > target_tokens
        ):
            seg_text = " ".join(current)
            out.append(
                _TextSegment(
                    seg_text,
                    seg_start,
                    seg_start + len(seg_text),
                    count_tokens(seg_text, embedding_model=embedding_model),
                )
            )
            seg_start += len(seg_text) + 1  # +1 für das trennende Leerzeichen
            current = [word]
        else:
            current.append(word)
    if current:
        seg_text = " ".join(current)
        out.append(
            _TextSegment(
                seg_text,
                seg_start,
                seg_start + len(seg_text),
                count_tokens(seg_text, embedding_model=embedding_model),
            )
        )


def _split_segments(
    body: str,
    *,
    embedding_model: str,
    max_segment_tokens: int,
    overlap_tokens: int,
) -> list[_TextSegment]:
    """Teilt an Absatz-, Satz- und (bei Bedarf) Wortgrenzen.

    Kein Segment überschreitet `max_segment_tokens` (außer ein einzelnes
    überlanges Wort) – das ist Voraussetzung dafür, dass `_pack_body_chunks`
    immer Fortschritt macht und nicht in eine Endlosschleife läuft.
    """
    if not body.strip():
        return []

    segments: list[_TextSegment] = []
    search_from = 0
    for paragraph in _PARAGRAPH_SPLIT.split(body):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        start = body.find(paragraph, search_from)
        if start < 0:
            start = search_from
        end = start + len(paragraph)
        search_from = end
        tokens = count_tokens(paragraph, embedding_model=embedding_model)
        if tokens <= max_segment_tokens:
            segments.append(
                _TextSegment(
                    text=paragraph,
                    char_start=start,
                    char_end=end,
                    token_count=tokens,
                )
            )
            continue
        sentence_from = start
        for sentence in _SENTENCE_SPLIT.split(paragraph):
            sentence = sentence.strip()
            if not sentence:
                continue
            s_start = body.find(sentence, sentence_from)
            if s_start < 0:
                s_start = sentence_from
            sentence_from = s_start + len(sentence)
            _emit_with_hard_split(
                sentence,
                s_start,
                embedding_model=embedding_model,
                max_segment_tokens=max_segment_tokens,
                overlap_tokens=overlap_tokens,
                out=segments,
            )
    return segments


def _join_segments(segments: list[_TextSegment], body: str) -> tuple[str, int, int]:
    if not segments:
        return "", 0, 0
    char_start = segments[0].char_start
    char_end = segments[-1].char_end
    return body[char_start:char_end].strip(), char_start, char_end


def _pack_body_chunks(
    body: str,
    segments: list[_TextSegment],
    *,
    max_body_tokens: int,
    overlap_tokens: int,
    min_chunk_tokens: int,
) -> list[tuple[str, int, int]]:
    """Packt Segmente in überlappende Chunks (nur Body, ohne Prefix)."""
    if not segments:
        return []
    if len(segments) == 1 and segments[0].token_count <= max_body_tokens:
        seg = segments[0]
        return [(seg.text, seg.char_start, seg.char_end)]

    packed: list[tuple[str, int, int, int]] = []
    idx = 0
    while idx < len(segments):
        chunk_start_idx = idx
        chunk_segments: list[_TextSegment] = []
        used_tokens = 0
        while idx < len(segments):
            seg = segments[idx]
            if chunk_segments and used_tokens + seg.token_count > max_body_tokens:
                break
            if not chunk_segments and seg.token_count > max_body_tokens:
                chunk_segments.append(seg)
                idx += 1
                break
            chunk_segments.append(seg)
            used_tokens += seg.token_count
            idx += 1
        body_text, char_start, char_end = _join_segments(chunk_segments, body)
        packed.append((body_text, char_start, char_end, used_tokens))

        if idx >= len(segments):
            break

        # Overlap: einige Tail-Segmente in den nächsten Chunk übernehmen –
        # aber NIEMALS vor (chunk_start_idx + 1) zurück. Der Index muss
        # garantiert vorankommen, sonst Endlosschleife + RAM-Explosion bei
        # einem Segment, das größer als max_body_tokens ist.
        min_next_idx = chunk_start_idx + 1
        overlap_used = 0
        back_idx = idx
        while back_idx > min_next_idx and overlap_used < overlap_tokens:
            back_idx -= 1
            overlap_used += segments[back_idx].token_count
        idx = back_idx

    merged: list[tuple[str, int, int]] = [
        (text, start, end) for text, start, end, _ in packed
    ]
    if len(merged) >= 2 and packed[-1][3] < min_chunk_tokens:
        last_text, last_start, last_end, _ = packed[-1]
        prev_text, prev_start, _prev_end = merged[-2]
        merged[-2] = (f"{prev_text}\n\n{last_text}".strip(), prev_start, last_end)
        merged.pop()
    return merged
