"""BJT 읽기 학습 데이터의 로컬 빌드 공용 모듈.

외부 원본을 내려받지 않으며 Python 표준 라이브러리만 사용한다.
raw는 원본 보관용, manual은 검수된 운영 입력용, processed는 생성물이다.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import os
import re
import sqlite3
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
MANUAL_DIR = DATA_DIR / "manual"
PROCESSED_DIR = DATA_DIR / "processed"
GLOSS_REVIEW_DIR = MANUAL_DIR / "gloss_reviews"

VALID_JLPT_LEVELS = {"N1", "N2", "N3", "N4", "N5"}
VALID_ITEM_TYPES = {"word", "sentence"}
VALID_READING_TYPES = {"onyomi", "kunyomi", "mixed", "compound", "sentence", "unknown"}
VALID_REVIEW_STATUSES = {"unreviewed", "manual_approved", "ai_approved", "needs_review", "rejected"}
VALID_GLOSS_REVIEW_STATUSES = {"ai_approved", "needs_review", "rejected"}
VALID_LEGACY_CATEGORIES = {"transaction", "coordination", "relationship", "advanced"}
AI_APPROVAL_MIN_CONFIDENCE = 0.85
KANA_RE = re.compile(r"^[\u3041-\u3096ー]+$")
KANJI_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


class PipelineError(RuntimeError):
    """입력 또는 빌드 계약이 지켜지지 않았을 때 발생하는 오류."""


class ValidationError(PipelineError):
    """학습 카탈로그를 생성하면 안 되는 데이터 검증 오류."""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise PipelineError(f"필수 JSON 파일을 찾을 수 없습니다: {relative_path(path)}") from error
    except json.JSONDecodeError as error:
        raise PipelineError(f"JSON 형식이 올바르지 않습니다: {relative_path(path)} ({error})") from error


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_text(value: Any) -> str:
    return unicodedata.normalize("NFC", unicodedata.normalize("NFKC", str(value or "").strip()))


def katakana_to_hiragana(value: str) -> str:
    converted: list[str] = []
    for character in value:
        codepoint = ord(character)
        if 0x30A1 <= codepoint <= 0x30F6:
            converted.append(chr(codepoint - 0x60))
        else:
            converted.append(character)
    return "".join(converted)


def normalize_reading(value: Any) -> str:
    normalized = normalize_text(value)
    normalized = re.sub(r"[\s\u3000]+", "", normalized)
    # 앱 답안 정규화와 맞춘다. 문장 표기에는 문장부호를 남기되, 읽기 정답에는 저장하지 않는다.
    normalized = re.sub(r"[、。！？・]", "", normalized)
    return unicodedata.normalize("NFC", katakana_to_hiragana(normalized))


def dedupe(values: Iterable[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = normalize_reading(value)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def contains_kanji(value: str) -> bool:
    return bool(KANJI_RE.search(value))


def stable_generated_id(expression: str, reading: str) -> str:
    digest = hashlib.sha256(f"{expression}\0{reading}".encode("utf-8")).hexdigest()[:14]
    return f"auto-{digest}"


def source_list(raw_sources: Any, fallback_name: str, reference: str = "") -> list[dict[str, str]]:
    values = raw_sources if isinstance(raw_sources, list) else [raw_sources]
    sources: list[dict[str, str]] = []
    for value in values:
        if isinstance(value, str):
            name = normalize_text(value)
            item = {"name": name, "reference": "", "version": ""}
        elif isinstance(value, dict):
            name = normalize_text(value.get("name"))
            item = {
                "name": name,
                "reference": normalize_text(value.get("reference")),
                "version": normalize_text(value.get("version")),
            }
        else:
            continue
        if item["name"]:
            sources.append(item)
    if not sources:
        sources.append({"name": fallback_name, "reference": reference, "version": ""})
    return merge_sources([], sources)


def merge_sources(first: list[dict[str, str]], second: list[dict[str, str]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for source in [*first, *second]:
        item = {
            "name": normalize_text(source.get("name")),
            "reference": normalize_text(source.get("reference")),
            "version": normalize_text(source.get("version")),
        }
        key = (item["name"], item["reference"], item["version"])
        if item["name"] and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def first_present(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return value
    return None


def normalize_categories(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    result: list[str] = []
    for value in values:
        code = normalize_text(value).lower().replace(" ", "_")
        if code and code not in result:
            result.append(code)
    return result


def normalize_text_list(values: Any) -> list[str]:
    """UI 보조 목록은 배열만 허용해 문자열을 글자 단위로 오해하지 않게 한다."""
    if not isinstance(values, list):
        return []
    result: list[str] = []
    for value in values:
        normalized = normalize_text(value)
        if normalized and normalized not in result:
            result.append(normalized)
    return result


def normalize_confidence(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return None
    return confidence if math.isfinite(confidence) else None


def normalize_record(raw: dict[str, Any], *, origin: str, index: int = 0) -> dict[str, Any]:
    expression = normalize_text(first_present(raw, "expression", "word", "display", "kanji", "term"))
    primary_reading = normalize_reading(first_present(raw, "primary_reading", "reading", "kana", "furigana"))
    accepted_raw = raw.get("accepted_readings")
    accepted_readings = dedupe(accepted_raw if isinstance(accepted_raw, list) else [primary_reading])
    if primary_reading and primary_reading not in accepted_readings:
        accepted_readings.insert(0, primary_reading)

    stable_id = normalize_text(first_present(raw, "stable_id", "id")) or stable_generated_id(expression, primary_reading)
    item_type = normalize_text(raw.get("item_type") or raw.get("type") or "word").lower()
    reading_type = normalize_text(raw.get("reading_type") or "unknown").lower()
    jlpt_level = normalize_text(raw.get("jlpt_level") or raw.get("level_jlpt")).upper() or None
    relevance_raw = raw.get("business_relevance", 0)
    difficulty_raw = raw.get("reading_difficulty", 3)
    try:
        relevance = int(relevance_raw)
    except (TypeError, ValueError):
        relevance = -1
    try:
        difficulty = int(difficulty_raw)
    except (TypeError, ValueError):
        difficulty = -1

    meaning_ko = normalize_text(first_present(raw, "meaning_ko", "korean_meaning", "ko_meaning"))
    review_status = normalize_text(raw.get("review_status")).lower()
    if not review_status:
        review_status = "manual_approved" if origin == "manual" and meaning_ko else "unreviewed"
    review_confidence = normalize_confidence(raw.get("review_confidence"))
    if review_confidence is None and review_status == "manual_approved":
        review_confidence = 1.0
    reviewer = normalize_text(raw.get("reviewer"))
    if not reviewer and review_status == "manual_approved":
        reviewer = "manual_seed"

    source_reference = f"{origin} #{index + 1}" if origin else ""
    return {
        "stable_id": stable_id,
        "expression": expression,
        "primary_reading": primary_reading,
        "accepted_readings": accepted_readings,
        "meaning_ko": meaning_ko,
        "legacy_category": normalize_text(raw.get("legacy_category") or raw.get("category")) or None,
        "categories": normalize_categories(raw.get("categories")),
        "level": normalize_text(raw.get("level")) or "uncategorized",
        "item_type": item_type,
        "reading_type": reading_type,
        "reading_difficulty": difficulty,
        "business_relevance": relevance,
        "frequency_score": raw.get("frequency_score"),
        "frequency_source": normalize_text(raw.get("frequency_source")),
        "priority_markers": normalize_text_list(raw.get("priority_markers")),
        "learning_priority": raw.get("learning_priority"),
        "jlpt_level": jlpt_level,
        "jlpt_level_source": normalize_text(raw.get("jlpt_level_source")) or None,
        "jlpt_official": False,
        "part_of_speech": normalize_text(raw.get("part_of_speech")) or None,
        "related": normalize_text_list(raw.get("related")),
        "aliases": normalize_text_list(raw.get("aliases")),
        "example": normalize_text(raw.get("example")) or None,
        "sources": source_list(raw.get("sources"), origin or "manual", source_reference),
        "is_active": bool(raw.get("is_active", True)),
        "inactive_reason": normalize_text(raw.get("inactive_reason")) or None,
        "review_status": review_status,
        "review_confidence": review_confidence,
        "review_note": normalize_text(raw.get("review_note")) or None,
        "reviewer": reviewer or None,
        "reviewed_at": normalize_text(raw.get("reviewed_at")) or None,
        "dictionary_readings": [],
        "manual_readings_locked": origin == "manual",
        "origin": origin,
    }


def load_manual_seed(path: Path = MANUAL_DIR / "business_seed.json") -> list[dict[str, Any]]:
    payload = read_json(path)
    if not isinstance(payload, list):
        raise PipelineError(f"manual business_seed는 JSON 배열이어야 합니다: {relative_path(path)}")
    if not payload:
        raise PipelineError(f"manual business_seed가 비어 있습니다: {relative_path(path)}")
    records: list[dict[str, Any]] = []
    for index, raw in enumerate(payload):
        if not isinstance(raw, dict):
            raise PipelineError(f"manual business_seed의 {index + 1}번째 항목이 객체가 아닙니다.")
        records.append(normalize_record(raw, origin="manual", index=index))
    return records


def load_gloss_reviews(path: Path = GLOSS_REVIEW_DIR) -> tuple[list[dict[str, Any]], list[str]]:
    """AI가 검수한 한국어 뜻 배치를 읽는다.

    리뷰 원문은 별도 파일로 보관해 원본 어휘와 번역·검수 이력을 분리한다.
    `ai_approved`만 활성 퀴즈 후보로 승격할 수 있으며, 애매한 항목은
    `needs_review`로 남겨 카탈로그에 내보내지 않는다.
    """
    if not path.exists():
        return [], []

    reviews: list[dict[str, Any]] = []
    notes: list[str] = []
    seen_ids: set[str] = set()
    for review_file in sorted(path.glob("*.json")):
        payload = read_json(review_file)
        if not isinstance(payload, dict):
            raise PipelineError(f"한국어 뜻 검수 배치는 JSON 객체여야 합니다: {relative_path(review_file)}")
        if payload.get("schema_version") != 1:
            raise PipelineError(f"한국어 뜻 검수 배치 schema_version은 1이어야 합니다: {relative_path(review_file)}")
        batch_id = normalize_text(payload.get("batch_id"))
        reviewer = normalize_text(payload.get("reviewer"))
        reviewed_at = normalize_text(payload.get("reviewed_at"))
        items = payload.get("items")
        if not batch_id or not reviewer or not reviewed_at or not isinstance(items, list) or not items:
            raise PipelineError(
                f"한국어 뜻 검수 배치에는 batch_id, reviewer, reviewed_at, 비어 있지 않은 items가 필요합니다: {relative_path(review_file)}"
            )

        approved_count = 0
        for index, raw in enumerate(items):
            if not isinstance(raw, dict):
                raise PipelineError(f"{relative_path(review_file)} {index + 1}번째 items가 객체가 아닙니다")
            stable_id = normalize_text(raw.get("stable_id"))
            if not stable_id:
                raise PipelineError(f"{relative_path(review_file)} {index + 1}번째 items에 stable_id가 없습니다")
            if stable_id in seen_ids:
                raise PipelineError(f"한국어 뜻 검수 배치에서 stable_id가 중복됩니다: {stable_id}")
            seen_ids.add(stable_id)

            review_status = normalize_text(raw.get("review_status")).lower()
            raw_confidence = raw.get("review_confidence")
            confidence = normalize_confidence(raw_confidence)
            meaning_ko = normalize_text(raw.get("meaning_ko"))
            review_note = normalize_text(raw.get("review_note"))
            legacy_category = normalize_text(raw.get("legacy_category"))
            raw_categories = raw.get("categories")
            categories = normalize_categories(raw_categories)
            raw_relevance = raw.get("business_relevance")
            raw_related = raw.get("related")

            if review_status not in VALID_GLOSS_REVIEW_STATUSES:
                raise PipelineError(
                    f"{relative_path(review_file)} {stable_id}: review_status가 허용값이 아닙니다 ({review_status or '비어 있음'})"
                )
            if isinstance(raw_confidence, bool) or not isinstance(raw_confidence, (int, float)) or confidence is None:
                raise PipelineError(f"{relative_path(review_file)} {stable_id}: review_confidence는 0~1 숫자여야 합니다")
            if not 0 <= confidence <= 1:
                raise PipelineError(f"{relative_path(review_file)} {stable_id}: review_confidence는 0~1이어야 합니다")
            if (
                not isinstance(raw_categories, list)
                or not categories
                or any(not isinstance(category, str) or not normalize_text(category) for category in raw_categories)
            ):
                raise PipelineError(f"{relative_path(review_file)} {stable_id}: categories는 비어 있지 않은 문자열 배열이어야 합니다")
            if legacy_category not in VALID_LEGACY_CATEGORIES:
                raise PipelineError(
                    f"{relative_path(review_file)} {stable_id}: legacy_category는 허용값이어야 합니다 "
                    f"({', '.join(sorted(VALID_LEGACY_CATEGORIES))})"
                )
            if isinstance(raw_relevance, bool) or not isinstance(raw_relevance, int) or not 0 <= raw_relevance <= 5:
                raise PipelineError(f"{relative_path(review_file)} {stable_id}: business_relevance는 0~5 정수여야 합니다")
            if "related" in raw and not isinstance(raw_related, list):
                raise PipelineError(f"{relative_path(review_file)} {stable_id}: related는 배열이어야 합니다")
            if not review_note:
                raise PipelineError(f"{relative_path(review_file)} {stable_id}: review_note가 필요합니다")
            if review_status == "ai_approved":
                if not meaning_ko:
                    raise PipelineError(f"{relative_path(review_file)} {stable_id}: ai_approved에는 meaning_ko가 필요합니다")
                if confidence < AI_APPROVAL_MIN_CONFIDENCE:
                    raise PipelineError(
                        f"{relative_path(review_file)} {stable_id}: ai_approved에는 {AI_APPROVAL_MIN_CONFIDENCE:.2f} 이상의 review_confidence가 필요합니다"
                    )
                approved_count += 1

            reviews.append(
                {
                    "stable_id": stable_id,
                    "meaning_ko": meaning_ko,
                    "review_status": review_status,
                    "review_confidence": confidence,
                    "review_note": review_note,
                    "legacy_category": legacy_category,
                    "categories": categories,
                    "business_relevance": raw_relevance,
                    "related": normalize_text_list(raw_related),
                    "has_related": "related" in raw,
                    "reviewer": normalize_text(raw.get("reviewer")) or reviewer,
                    "reviewed_at": normalize_text(raw.get("reviewed_at")) or reviewed_at,
                    "source": {
                        "name": "ai_gloss_review",
                        "reference": relative_path(review_file),
                        "version": batch_id,
                    },
                }
            )
        notes.append(f"AI 한국어 뜻 검수 배치 {batch_id}: 승인 {approved_count}/{len(items)}개를 읽었습니다.")
    return reviews, notes


def apply_gloss_reviews(records: list[dict[str, Any]], reviews: list[dict[str, Any]]) -> list[str]:
    """검수 결과를 canonical record에 병합하고 활성화 정책을 적용한다."""
    index = {record["stable_id"]: record for record in records}
    status_counts: dict[str, int] = {}
    for review in reviews:
        stable_id = review["stable_id"]
        record = index.get(stable_id)
        if record is None:
            raise PipelineError(f"한국어 뜻 검수 대상 stable_id가 canonical 후보에 없습니다: {stable_id}")
        if record.get("origin") != "openjlpt" or record.get("review_status") != "unreviewed":
            raise PipelineError(
                f"한국어 뜻 검수 대상은 아직 검수되지 않은 OpenJLPT 후보여야 합니다: {stable_id}"
            )

        for field in ("meaning_ko", "review_note", "legacy_category", "reviewer", "reviewed_at"):
            value = review.get(field)
            if value not in (None, ""):
                record[field] = value
        if review.get("categories"):
            record["categories"] = review["categories"]
        if review.get("has_related"):
            record["related"] = review["related"]
        record["business_relevance"] = review["business_relevance"]

        status = review["review_status"]
        record["review_status"] = status
        record["review_confidence"] = review["review_confidence"]
        if status == "ai_approved":
            record["is_active"] = True
            record["inactive_reason"] = None
        else:
            record["is_active"] = False
            record["inactive_reason"] = f"gloss_review_{status}"
        record["sources"] = merge_sources(record["sources"], [review["source"]])
        status_counts[status] = status_counts.get(status, 0) + 1

    if not status_counts:
        return []
    labels = ", ".join(f"{status} {count}개" for status, count in sorted(status_counts.items()))
    return [f"AI 한국어 뜻 검수 결과를 병합했습니다: {labels}."]


def pick_openjlpt_input() -> Path | None:
    for candidate in (RAW_DIR / "openjlpt" / "n1.json", RAW_DIR / "openjlpt" / "n1.csv"):
        if candidate.exists():
            return candidate
    return None


def openjlpt_rows(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = read_json(path)
        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict):
            rows = next(
                (payload.get(key) for key in ("words", "vocabulary", "items", "data", "N1", "n1") if isinstance(payload.get(key), list)),
                None,
            )
        else:
            rows = None
        if not isinstance(rows, list):
            raise PipelineError(
                f"OpenJLPT JSON은 배열 또는 words/vocabulary/items/data/N1 배열을 가져야 합니다: {relative_path(path)}"
            )
        return [row for row in rows if isinstance(row, dict)]
    if suffix == ".csv":
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as file:
                return list(csv.DictReader(file))
        except UnicodeDecodeError as error:
            raise PipelineError(f"OpenJLPT CSV는 UTF-8이어야 합니다: {relative_path(path)}") from error
    raise PipelineError(f"OpenJLPT 입력은 .json 또는 .csv만 지원합니다: {relative_path(path)}")


def load_openjlpt_records(path: Path | None = None, *, required: bool = False) -> tuple[list[dict[str, Any]], list[str]]:
    target = path or pick_openjlpt_input()
    if target is None or not target.exists():
        message = "OpenJLPT 원본이 없습니다. data/raw/openjlpt/n1.json 또는 n1.csv를 넣으면 N1 후보를 추가로 가져옵니다."
        if required:
            raise PipelineError(message)
        return [], [message]

    rows = openjlpt_rows(target)
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    skipped_without_kanji = 0
    for index, row in enumerate(rows):
        expression = normalize_text(first_present(row, "word", "expression", "kanji", "term"))
        reading = normalize_reading(first_present(row, "reading", "kana", "furigana"))
        level = normalize_text(first_present(row, "level", "jlpt_level")).upper() or "N1"
        if level != "N1":
            continue
        if not expression:
            errors.append(f"{index + 1}행: word/expression이 필요합니다")
            continue
        # 이 앱의 문제는 한자 표기에서 읽기를 꺼내는 훈련이다. OpenJLPT 원본에는
        # 가나·가타카나 전용 항목의 reading이 비어 있는 경우가 있어, 이를 오류로
        # 취급하면 전체 N1 import가 불필요하게 중단된다.
        if not contains_kanji(expression):
            skipped_without_kanji += 1
            continue
        if not reading:
            errors.append(f"{index + 1}행: 한자 표기에는 reading/kana가 필요합니다 ({expression})")
            continue
        meaning_ko = normalize_text(first_present(row, "meaning_ko", "korean_meaning", "ko_meaning"))
        raw = {
            "stable_id": stable_generated_id(expression, reading),
            "expression": expression,
            "primary_reading": reading,
            "accepted_readings": [reading],
            "meaning_ko": meaning_ko,
            "level": "jlpt_candidate",
            "item_type": "word",
            "reading_type": "unknown",
            "reading_difficulty": 3,
            "business_relevance": 0,
            "jlpt_level": "N1",
            "jlpt_level_source": "openjlpt",
            "is_active": False,
            "inactive_reason": "manual_curation_required",
            "sources": [
                {
                    "name": "OpenJLPT",
                    "reference": relative_path(target),
                    "version": normalize_text(row.get("version")),
                }
            ],
        }
        records.append(normalize_record(raw, origin="openjlpt", index=index))
    if errors:
        examples = "\n".join(f"- {message}" for message in errors[:10])
        suffix = "\n- ..." if len(errors) > 10 else ""
        raise PipelineError(f"OpenJLPT 입력 검증 실패 ({relative_path(target)})\n{examples}{suffix}")
    if not records:
        raise PipelineError(f"N1 후보를 찾지 못했습니다: {relative_path(target)}")
    notes = [f"OpenJLPT N1 한자 읽기 후보 {len(records)}개를 읽었습니다: {relative_path(target)}"]
    if skipped_without_kanji:
        notes.append(
            f"한자 표기가 없는 N1 항목 {skipped_without_kanji}개는 한자→읽기 훈련 대상이 아니어서 건너뛰었습니다."
        )
    return records, notes


def pick_jmdict_input() -> Path | None:
    for candidate in (
        RAW_DIR / "jmdict" / "JMdict_e",
        RAW_DIR / "jmdict" / "JMdict_e.gz",
        RAW_DIR / "jmdict" / "JMdict_e.xml",
        RAW_DIR / "jmdict" / "JMdict_e.xml.gz",
    ):
        if candidate.exists():
            return candidate
    return None


def child_texts(element: ET.Element, tag: str) -> list[str]:
    return [normalize_text(child.text) for child in element.findall(tag) if normalize_text(child.text)]


def load_jmdict_matches(
    target_expressions: set[str], path: Path | None = None, *, required: bool = False
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    target = path or pick_jmdict_input()
    if target is None or not target.exists():
        message = "JMdict 원본이 없습니다. data/raw/jmdict/JMdict_e 또는 JMdict_e.gz를 넣으면 표기·읽기 검증을 추가합니다."
        if required:
            raise PipelineError(message)
        return {}, [message]
    if not target_expressions:
        return {}, ["JMdict 대조 대상 표현이 없어 읽지 않았습니다."]

    matches: dict[str, dict[str, Any]] = {}
    try:
        opener = gzip.open if target.suffix.lower() == ".gz" else open
        with opener(target, "rb") as file:
            for _, entry in ET.iterparse(file, events=("end",)):
                if entry.tag != "entry":
                    continue
                spellings = [text for item in entry.findall("k_ele") for text in child_texts(item, "keb")]
                kana_only = [text for item in entry.findall("r_ele") for text in child_texts(item, "reb")]
                expression_set = set(spellings) | (set(kana_only) & target_expressions)
                matched_expressions = expression_set & target_expressions
                if matched_expressions:
                    pos = [text for sense in entry.findall("sense") for text in child_texts(sense, "pos")]
                    spelling_priority = [text for item in entry.findall("k_ele") for text in child_texts(item, "ke_pri")]
                    reading_rows: list[tuple[str, set[str], list[str]]] = []
                    for reading_element in entry.findall("r_ele"):
                        readings = child_texts(reading_element, "reb")
                        restrictions = set(child_texts(reading_element, "re_restr"))
                        priority = child_texts(reading_element, "re_pri")
                        for reading in readings:
                            reading_rows.append((normalize_reading(reading), restrictions, priority))
                    for expression in matched_expressions:
                        applicable = [
                            reading
                            for reading, restrictions, _ in reading_rows
                            if not restrictions or expression in restrictions
                        ]
                        priorities = [*spelling_priority]
                        priorities.extend(
                            tag
                            for _, restrictions, tags in reading_rows
                            if not restrictions or expression in restrictions
                            for tag in tags
                        )
                        match = matches.setdefault(
                            expression,
                            {
                                "readings": [],
                                "part_of_speech": [],
                                "priority_markers": [],
                                "source": {
                                    "name": "JMdict",
                                    "reference": relative_path(target),
                                    "version": "",
                                },
                            },
                        )
                        match["readings"] = dedupe([*match["readings"], *applicable])
                        match["part_of_speech"] = list(dict.fromkeys([*match["part_of_speech"], *pos]))
                        match["priority_markers"] = list(dict.fromkeys([*match["priority_markers"], *priorities]))
                entry.clear()
    except (ET.ParseError, OSError) as error:
        raise PipelineError(f"JMdict XML을 읽지 못했습니다: {relative_path(target)} ({error})") from error
    return matches, [f"JMdict 대조: {len(matches)}/{len(target_expressions)}개 표현이 매칭되었습니다."]


def merge_manual_and_openjlpt(
    manual_records: list[dict[str, Any]], openjlpt_records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    records = [dict(record) for record in manual_records]
    index_by_key = {(record["expression"], record["primary_reading"]): index for index, record in enumerate(records)}
    for raw in openjlpt_records:
        key = (raw["expression"], raw["primary_reading"])
        if key not in index_by_key:
            index_by_key[key] = len(records)
            records.append(dict(raw))
            continue
        target = records[index_by_key[key]]
        target["sources"] = merge_sources(target["sources"], raw["sources"])
        if not target.get("jlpt_level"):
            target["jlpt_level"] = raw.get("jlpt_level")
            target["jlpt_level_source"] = raw.get("jlpt_level_source")
    return records


def attach_jmdict(records: list[dict[str, Any]], matches: dict[str, dict[str, Any]]) -> None:
    for record in records:
        match = matches.get(record["expression"])
        if not match:
            continue
        dictionary_readings = dedupe(match["readings"])
        # JMdict의 `reb`에는 사전 표기용 물결표 등 실제 답안으로 입력할 수 없는
        # 변형과 동일 표기의 별개 단어 읽기가 함께 들어갈 수 있다. 원본 후보는
        # metadata로 보존하되, 학습 정답 후보는 OpenJLPT의 문제 읽기를 따른다.
        record["dictionary_readings"] = dictionary_readings
        record["sources"] = merge_sources(record["sources"], [match["source"]])
        if not record.get("part_of_speech") and match["part_of_speech"]:
            record["part_of_speech"] = "; ".join(match["part_of_speech"])
        record["priority_markers"] = list(
            dict.fromkeys([*record.get("priority_markers", []), *match["priority_markers"]])
        )
        if not record.get("manual_readings_locked"):
            # 동일 표기의 별개 단어가 JMdict에 함께 들어 있을 수 있다. OpenJLPT가
            # 지정한 문제 읽기를 사전 전체 읽기로 넓히면 오답이 정답 처리될 수 있으므로,
            # 사전 읽기는 metadata로만 보존하고 채점값은 원본 primary_reading으로 고정한다.
            primary_reading = normalize_reading(record.get("primary_reading"))
            if primary_reading:
                record["accepted_readings"] = [primary_reading]


def load_overrides(path: Path = MANUAL_DIR / "reading_overrides.json") -> dict[str, dict[str, Any]]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise PipelineError(f"reading_overrides는 JSON 객체여야 합니다: {relative_path(path)}")
    overrides = payload.get("overrides", payload)
    if not isinstance(overrides, dict):
        raise PipelineError(f"reading_overrides.overrides는 JSON 객체여야 합니다: {relative_path(path)}")
    return {normalize_text(key): value for key, value in overrides.items() if isinstance(value, dict)}


def apply_overrides(records: list[dict[str, Any]], overrides: dict[str, dict[str, Any]]) -> list[str]:
    notices: list[str] = []
    for target, override in overrides.items():
        matched = [record for record in records if record["stable_id"] == target or record["expression"] == target]
        if not matched:
            notices.append(f"override 대상이 없습니다: {target}")
            continue
        for record in matched:
            if "primary_reading" in override:
                record["primary_reading"] = normalize_reading(override["primary_reading"])
            if "accepted_readings" in override:
                values = override["accepted_readings"]
                record["accepted_readings"] = dedupe(values if isinstance(values, list) else [values])
                record["manual_readings_locked"] = True
            if record["primary_reading"] and record["primary_reading"] not in record["accepted_readings"]:
                record["accepted_readings"].insert(0, record["primary_reading"])
            for field in ("meaning_ko", "legacy_category", "reading_type", "level", "part_of_speech", "example"):
                if field in override:
                    record[field] = normalize_text(override[field]) or None
            if "categories" in override:
                record["categories"] = normalize_categories(override["categories"])
            for field in ("business_relevance", "reading_difficulty"):
                if field in override:
                    try:
                        record[field] = int(override[field])
                    except (TypeError, ValueError):
                        record[field] = -1
            if "is_active" in override:
                record["is_active"] = bool(override["is_active"])
            if override.get("exclude") is True:
                record["is_active"] = False
                record["inactive_reason"] = "manual_override_excluded"
            record["sources"] = merge_sources(
                record["sources"], [{"name": "manual_override", "reference": target, "version": ""}]
            )
    return notices


def load_exclusions(path: Path = MANUAL_DIR / "excluded_words.json") -> tuple[set[str], set[str]]:
    payload = read_json(path)
    if isinstance(payload, list):
        return {normalize_text(value) for value in payload}, set()
    if not isinstance(payload, dict):
        raise PipelineError(f"excluded_words는 JSON 객체 또는 배열이어야 합니다: {relative_path(path)}")
    stable_ids = {normalize_text(value) for value in payload.get("stable_ids", []) if normalize_text(value)}
    expressions = {normalize_text(value) for value in payload.get("expressions", []) if normalize_text(value)}
    return stable_ids, expressions


def apply_exclusions(records: list[dict[str, Any]], stable_ids: set[str], expressions: set[str]) -> int:
    count = 0
    for record in records:
        if record["stable_id"] in stable_ids or record["expression"] in expressions:
            record["is_active"] = False
            record["inactive_reason"] = "manual_exclusion"
            count += 1
    return count


def frequency_score(record: dict[str, Any]) -> tuple[float, str]:
    explicit = record.get("frequency_score")
    try:
        if explicit is not None and str(explicit) != "":
            value = float(explicit)
            return max(0.0, min(100.0, value)), record.get("frequency_source") or "manual"
    except (TypeError, ValueError):
        pass
    markers = {marker.lower() for marker in record.get("priority_markers", [])}
    if markers & {"news1", "ichi1", "spec1", "gai1"}:
        return 75.0, "jmdict_priority_proxy"
    if markers & {"news2", "ichi2", "spec2", "gai2"}:
        return 60.0, "jmdict_priority_proxy"
    return 40.0, "default_neutral"


def jlpt_score(level: str | None) -> float:
    return {"N1": 100.0, "N2": 70.0, "N3": 40.0}.get(level or "", 20.0)


def calculate_priorities(records: list[dict[str, Any]]) -> None:
    for record in records:
        frequency, source = frequency_score(record)
        business = max(0, min(5, record.get("business_relevance", 0))) * 20.0
        difficulty = max(0, min(5, record.get("reading_difficulty", 0))) * 20.0
        priority = business * 0.40 + difficulty * 0.25 + frequency * 0.20 + jlpt_score(record.get("jlpt_level")) * 0.15
        record["frequency_score"] = round(frequency, 2)
        record["frequency_source"] = source
        record["learning_priority"] = round(max(0.0, min(100.0, priority)), 2)


def validate_records(records: list[dict[str, Any]], category_codes: set[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    seen_keys: set[tuple[str, str]] = set()
    seen_ids: set[str] = set()
    inactive_without_meaning = 0
    for record in records:
        label = record.get("stable_id") or "(stable_id 없음)"
        expression = record.get("expression", "")
        reading = record.get("primary_reading", "")
        key = (expression, reading)
        if not expression:
            errors.append(f"{label}: expression이 비어 있습니다")
        if not reading:
            errors.append(f"{label}: primary_reading이 비어 있습니다")
        elif not KANA_RE.fullmatch(reading):
            errors.append(f"{label}: primary_reading은 정규화된 히라가나여야 합니다 ({reading})")
        if contains_kanji(expression) and expression == reading:
            errors.append(f"{label}: 한자 표기와 읽기가 동일합니다")
        if key in seen_keys:
            errors.append(f"{label}: expression + primary_reading 중복입니다 ({expression} / {reading})")
        seen_keys.add(key)
        if not label:
            errors.append("stable_id가 비어 있습니다")
        if label in seen_ids:
            errors.append(f"{label}: stable_id가 중복됩니다")
        seen_ids.add(label)
        if record.get("item_type") not in VALID_ITEM_TYPES:
            errors.append(f"{label}: item_type이 word 또는 sentence가 아닙니다")
        if record.get("reading_type") not in VALID_READING_TYPES:
            errors.append(f"{label}: reading_type이 허용값이 아닙니다")
        relevance = record.get("business_relevance")
        if not isinstance(relevance, int) or not 0 <= relevance <= 5:
            errors.append(f"{label}: business_relevance는 0~5 정수여야 합니다")
        difficulty = record.get("reading_difficulty")
        if not isinstance(difficulty, int) or not 0 <= difficulty <= 5:
            errors.append(f"{label}: reading_difficulty는 0~5 정수여야 합니다")
        priority = record.get("learning_priority")
        if not isinstance(priority, (int, float)) or not 0 <= priority <= 100:
            errors.append(f"{label}: learning_priority는 0~100이어야 합니다")
        jlpt = record.get("jlpt_level")
        if jlpt and jlpt not in VALID_JLPT_LEVELS:
            errors.append(f"{label}: jlpt_level이 허용값이 아닙니다 ({jlpt})")
        if record.get("jlpt_official") is not False:
            errors.append(f"{label}: jlpt_official은 항상 false여야 합니다")
        if not record.get("sources"):
            errors.append(f"{label}: source provenance가 없습니다")
        accepted = record.get("accepted_readings", [])
        if not accepted:
            errors.append(f"{label}: accepted_readings가 비어 있습니다")
        if reading and reading not in accepted:
            errors.append(f"{label}: primary_reading이 accepted_readings에 없습니다")
        for alternate in accepted:
            if not KANA_RE.fullmatch(alternate):
                errors.append(f"{label}: accepted_readings에 히라가나가 아닌 값이 있습니다 ({alternate})")
        unknown_categories = [category for category in record.get("categories", []) if category not in category_codes]
        if unknown_categories:
            errors.append(f"{label}: 정의되지 않은 category가 있습니다 ({', '.join(unknown_categories)})")
        review_status = record.get("review_status")
        review_confidence = record.get("review_confidence")
        if review_status not in VALID_REVIEW_STATUSES:
            errors.append(f"{label}: review_status가 허용값이 아닙니다 ({review_status})")
        if review_confidence is not None and (
            isinstance(review_confidence, bool)
            or not isinstance(review_confidence, (int, float))
            or not math.isfinite(review_confidence)
            or not 0 <= review_confidence <= 1
        ):
            errors.append(f"{label}: review_confidence는 0~1 숫자여야 합니다")
        if review_status == "ai_approved":
            if not isinstance(review_confidence, (int, float)) or review_confidence < AI_APPROVAL_MIN_CONFIDENCE:
                errors.append(
                    f"{label}: ai_approved에는 {AI_APPROVAL_MIN_CONFIDENCE:.2f} 이상의 review_confidence가 필요합니다"
                )
            if not record.get("reviewer") or not record.get("reviewed_at"):
                errors.append(f"{label}: ai_approved에는 reviewer와 reviewed_at이 필요합니다")
        if review_status in {"unreviewed", "needs_review", "rejected"} and record.get("is_active"):
            errors.append(f"{label}: {review_status} 항목은 활성 퀴즈가 될 수 없습니다")
        if record.get("is_active"):
            if not record.get("meaning_ko"):
                errors.append(f"{label}: 활성 퀴즈 항목에는 meaning_ko가 필요합니다")
            if not record.get("legacy_category"):
                errors.append(f"{label}: 활성 퀴즈 항목에는 legacy_category가 필요합니다")
        elif not record.get("meaning_ko"):
            inactive_without_meaning += 1
    if inactive_without_meaning:
        warnings.append(
            f"한국어 뜻이 없는 비활성 후보 {inactive_without_meaning}개는 퀴즈 카탈로그에 내보내지 않았습니다."
        )
    return errors, warnings


def load_categories(path: Path = MANUAL_DIR / "categories.json") -> list[dict[str, str]]:
    payload = read_json(path)
    if not isinstance(payload, list):
        raise PipelineError(f"categories는 JSON 배열이어야 합니다: {relative_path(path)}")
    categories: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, raw in enumerate(payload):
        if not isinstance(raw, dict):
            raise PipelineError(f"categories의 {index + 1}번째 항목이 객체가 아닙니다")
        code = normalize_text(raw.get("code")).lower()
        if not code or code in seen:
            raise PipelineError(f"categories의 code가 비었거나 중복됩니다: {code or index + 1}")
        seen.add(code)
        categories.append({"code": code, "name_ko": normalize_text(raw.get("name_ko")), "name_ja": normalize_text(raw.get("name_ja"))})
    return categories


def client_items(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for record in records:
        if not record.get("is_active") or not record.get("meaning_ko"):
            continue
        item: dict[str, Any] = {
            "id": record["stable_id"],
            "display": record["expression"],
            "reading": record["primary_reading"],
            "meaning": record["meaning_ko"],
            "category": record["legacy_category"],
            "level": record["level"],
            "related": record["related"],
            "expression": record["expression"],
            "primary_reading": record["primary_reading"],
            "accepted_readings": record["accepted_readings"],
            "meaning_ko": record["meaning_ko"],
            "categories": record["categories"],
            "item_type": record["item_type"],
            "reading_type": record["reading_type"],
            "learning_priority": record["learning_priority"],
            "sources": [source["name"] for source in record["sources"]],
        }
        if record["item_type"] == "sentence":
            item["type"] = "sentence"
        items.append(item)
    return items


def write_catalog_js(path: Path, records: list[dict[str, Any]], generated_at: str) -> int:
    items = client_items(records)
    if any(not item["meaning_ko"] for item in items):
        raise ValidationError("client catalog에 한국어 뜻이 없는 활성 항목이 포함되어 있습니다")
    payload = {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "quizPolicy": {
            "meaningVisibility": "after_answer_only",
            "requiresMeaningKo": True,
            "note": "한국어 뜻은 문제 전 기본 노출이 아닌 정답 사후 피드백용 보조 정보입니다.",
        },
        "items": items,
    }
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "/* 생성 파일: scripts/build_database.py로 다시 만드세요. */\n"
        f"window.BJT_CATALOG = Object.freeze({serialized});\n",
        encoding="utf-8",
    )
    return len(items)


def record_export(record: dict[str, Any]) -> dict[str, Any]:
    fields = [
        "stable_id",
        "expression",
        "primary_reading",
        "accepted_readings",
        "meaning_ko",
        "legacy_category",
        "categories",
        "level",
        "item_type",
        "reading_type",
        "reading_difficulty",
        "business_relevance",
        "frequency_score",
        "frequency_source",
        "priority_markers",
        "learning_priority",
        "jlpt_level",
        "jlpt_level_source",
        "jlpt_official",
        "part_of_speech",
        "related",
        "aliases",
        "example",
        "sources",
        "is_active",
        "inactive_reason",
        "review_status",
        "review_confidence",
        "review_note",
        "reviewer",
        "reviewed_at",
        "dictionary_readings",
    ]
    return {field: record.get(field) for field in fields}


def create_database(path: Path, records: list[dict[str, Any]], categories: list[dict[str, str]], generated_at: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()
    connection = sqlite3.connect(temporary)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            """
            CREATE TABLE build_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE vocabulary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stable_id TEXT NOT NULL UNIQUE,
                expression TEXT NOT NULL,
                primary_reading TEXT NOT NULL,
                meaning_ko TEXT,
                review_status TEXT NOT NULL DEFAULT 'unreviewed',
                review_confidence REAL,
                review_note TEXT,
                reviewer TEXT,
                reviewed_at TEXT,
                jlpt_level TEXT,
                jlpt_level_source TEXT,
                jlpt_official INTEGER NOT NULL DEFAULT 0 CHECK (jlpt_official = 0),
                part_of_speech TEXT,
                reading_type TEXT,
                reading_difficulty INTEGER,
                business_relevance INTEGER NOT NULL DEFAULT 0 CHECK (business_relevance BETWEEN 0 AND 5),
                frequency_score REAL,
                frequency_source TEXT,
                learning_priority REAL NOT NULL CHECK (learning_priority BETWEEN 0 AND 100),
                item_type TEXT NOT NULL,
                legacy_category TEXT,
                related_json TEXT NOT NULL DEFAULT '[]',
                example TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                inactive_reason TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(expression, primary_reading)
            );
            CREATE TABLE vocabulary_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vocabulary_id INTEGER NOT NULL,
                reading TEXT NOT NULL,
                is_primary INTEGER NOT NULL DEFAULT 0,
                source TEXT,
                UNIQUE(vocabulary_id, reading),
                FOREIGN KEY(vocabulary_id) REFERENCES vocabulary(id) ON DELETE CASCADE
            );
            CREATE TABLE vocabulary_aliases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vocabulary_id INTEGER NOT NULL,
                expression TEXT NOT NULL,
                UNIQUE(vocabulary_id, expression),
                FOREIGN KEY(vocabulary_id) REFERENCES vocabulary(id) ON DELETE CASCADE
            );
            CREATE TABLE categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name_ja TEXT,
                name_ko TEXT
            );
            CREATE TABLE vocabulary_categories (
                vocabulary_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                PRIMARY KEY(vocabulary_id, category_id),
                FOREIGN KEY(vocabulary_id) REFERENCES vocabulary(id) ON DELETE CASCADE,
                FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE
            );
            CREATE TABLE vocabulary_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vocabulary_id INTEGER NOT NULL,
                source_name TEXT NOT NULL,
                source_reference TEXT,
                source_version TEXT,
                imported_at TEXT NOT NULL,
                FOREIGN KEY(vocabulary_id) REFERENCES vocabulary(id) ON DELETE CASCADE
            );
            CREATE TABLE kanji (
                character TEXT PRIMARY KEY,
                jlpt_level TEXT,
                onyomi_json TEXT,
                kunyomi_json TEXT,
                frequency INTEGER,
                source TEXT
            );
            CREATE TABLE vocabulary_kanji (
                vocabulary_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                position INTEGER NOT NULL,
                PRIMARY KEY(vocabulary_id, character, position),
                FOREIGN KEY(vocabulary_id) REFERENCES vocabulary(id) ON DELETE CASCADE,
                FOREIGN KEY(character) REFERENCES kanji(character)
            );
            CREATE INDEX idx_vocabulary_active_priority ON vocabulary(is_active, learning_priority DESC);
            CREATE INDEX idx_vocabulary_stable_id ON vocabulary(stable_id);
            CREATE INDEX idx_vocabulary_sources_vocabulary_id ON vocabulary_sources(vocabulary_id);
            """
        )
        connection.executemany(
            "INSERT INTO categories(code, name_ja, name_ko) VALUES (?, ?, ?)",
            [(category["code"], category["name_ja"], category["name_ko"]) for category in categories],
        )
        category_ids = {code: identifier for identifier, code in connection.execute("SELECT id, code FROM categories")}
        connection.executemany(
            "INSERT INTO build_metadata(key, value) VALUES (?, ?)",
            [
                ("schema_version", "2"),
                ("generated_at", generated_at),
                ("quiz_meaning_policy", "active quiz catalog entries require meaning_ko; reveal after answer only"),
                (
                    "gloss_review_policy",
                    f"ai_approved entries require confidence >= {AI_APPROVAL_MIN_CONFIDENCE:.2f}; needs_review and rejected entries stay inactive",
                ),
            ],
        )
        for record in records:
            cursor = connection.execute(
                """
                INSERT INTO vocabulary(
                    stable_id, expression, primary_reading, meaning_ko, review_status, review_confidence,
                    review_note, reviewer, reviewed_at, jlpt_level, jlpt_level_source,
                    jlpt_official, part_of_speech, reading_type, reading_difficulty, business_relevance,
                    frequency_score, frequency_source, learning_priority, item_type, legacy_category,
                    related_json, example, is_active, inactive_reason, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["stable_id"],
                    record["expression"],
                    record["primary_reading"],
                    record["meaning_ko"],
                    record["review_status"],
                    record["review_confidence"],
                    record["review_note"],
                    record["reviewer"],
                    record["reviewed_at"],
                    record["jlpt_level"],
                    record["jlpt_level_source"],
                    record["part_of_speech"],
                    record["reading_type"],
                    record["reading_difficulty"],
                    record["business_relevance"],
                    record["frequency_score"],
                    record["frequency_source"],
                    record["learning_priority"],
                    record["item_type"],
                    record["legacy_category"],
                    json.dumps(record["related"], ensure_ascii=False),
                    record["example"],
                    int(bool(record["is_active"])),
                    record["inactive_reason"],
                    generated_at,
                    generated_at,
                ),
            )
            vocabulary_id = cursor.lastrowid
            source_name = record["sources"][0]["name"] if record["sources"] else "unknown"
            connection.executemany(
                "INSERT INTO vocabulary_readings(vocabulary_id, reading, is_primary, source) VALUES (?, ?, ?, ?)",
                [
                    (vocabulary_id, reading, int(reading == record["primary_reading"]), source_name)
                    for reading in record["accepted_readings"]
                ],
            )
            connection.executemany(
                "INSERT INTO vocabulary_aliases(vocabulary_id, expression) VALUES (?, ?)",
                [(vocabulary_id, alias) for alias in record["aliases"] if alias != record["expression"]],
            )
            connection.executemany(
                "INSERT INTO vocabulary_categories(vocabulary_id, category_id) VALUES (?, ?)",
                [(vocabulary_id, category_ids[category]) for category in record["categories"]],
            )
            connection.executemany(
                """
                INSERT INTO vocabulary_sources(vocabulary_id, source_name, source_reference, source_version, imported_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (vocabulary_id, source["name"], source["reference"], source["version"], generated_at)
                    for source in record["sources"]
                ],
            )
            for position, character in enumerate(record["expression"]):
                if not contains_kanji(character):
                    continue
                connection.execute(
                    "INSERT OR IGNORE INTO kanji(character, source) VALUES (?, ?)",
                    (character, "derived_from_expression"),
                )
                connection.execute(
                    "INSERT INTO vocabulary_kanji(vocabulary_id, character, position) VALUES (?, ?, ?)",
                    (vocabulary_id, character, position),
                )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    os.replace(temporary, path)


def format_validation_errors(errors: list[str]) -> str:
    return "학습 데이터 검증 실패:\n" + "\n".join(f"- {error}" for error in errors)


def build_pipeline(
    *,
    openjlpt_path: Path | None = None,
    jmdict_path: Path | None = None,
    require_openjlpt: bool = False,
    require_jmdict: bool = False,
) -> dict[str, Any]:
    categories = load_categories()
    manual_records = load_manual_seed()
    openjlpt_records, notes = load_openjlpt_records(openjlpt_path, required=require_openjlpt)
    records = merge_manual_and_openjlpt(manual_records, openjlpt_records)
    matches, jmdict_notes = load_jmdict_matches(
        {record["expression"] for record in records}, jmdict_path, required=require_jmdict
    )
    notes.extend(jmdict_notes)
    attach_jmdict(records, matches)
    gloss_reviews, gloss_review_notes = load_gloss_reviews()
    notes.extend(apply_gloss_reviews(records, gloss_reviews))
    notes.extend(gloss_review_notes)
    # 수동 override는 AI 검수 결과보다 마지막에 적용해 사람의 명시적 결정을 보존한다.
    override_notes = apply_overrides(records, load_overrides())
    excluded_ids, excluded_expressions = load_exclusions()
    excluded_count = apply_exclusions(records, excluded_ids, excluded_expressions)
    if excluded_count:
        notes.append(f"제외 목록으로 {excluded_count}개 항목을 비활성화했습니다.")
    notes.extend(override_notes)
    calculate_priorities(records)
    errors, warnings = validate_records(records, {category["code"] for category in categories})
    if errors:
        raise ValidationError(format_validation_errors(errors))
    generated_at = now_iso()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    write_json(
        PROCESSED_DIR / "vocabulary.json",
        {
            "schema_version": 2,
            "generated_at": generated_at,
            "records": [record_export(record) for record in records],
        },
    )
    create_database(PROCESSED_DIR / "vocabulary.sqlite", records, categories, generated_at)
    quiz_count = write_catalog_js(PROCESSED_DIR / "catalog.js", records, generated_at)
    return {
        "generated_at": generated_at,
        "records": records,
        "manual_count": len(manual_records),
        "openjlpt_count": len(openjlpt_records),
        "jmdict_matched_count": len(matches),
        "gloss_review_count": len(gloss_reviews),
        "ai_approved_gloss_count": sum(1 for review in gloss_reviews if review["review_status"] == "ai_approved"),
        "quiz_count": quiz_count,
        "notes": notes,
        "warnings": warnings,
    }
