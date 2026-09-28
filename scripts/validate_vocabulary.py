#!/usr/bin/env python3
"""생성된 vocabulary.json과 client catalog의 운영 전 검증을 수행한다."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pipeline_core import (
    PROCESSED_DIR,
    PipelineError,
    client_items,
    format_validation_errors,
    load_categories,
    read_json,
    validate_records,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="생성된 BJT vocabulary.json을 다시 검증합니다.")
    parser.add_argument(
        "--input",
        type=Path,
        default=PROCESSED_DIR / "vocabulary.json",
        help="기본값: data/processed/vocabulary.json",
    )
    args = parser.parse_args()
    try:
        payload = read_json(args.input)
        records = payload.get("records") if isinstance(payload, dict) else None
        if not isinstance(records, list):
            raise PipelineError("vocabulary.json은 records 배열을 포함해야 합니다. 먼저 build_database.py를 실행하세요.")
        categories = load_categories()
        errors, warnings = validate_records(records, {category["code"] for category in categories})
        if errors:
            raise PipelineError(format_validation_errors(errors))
        items = client_items(records)
        if len(items) != sum(bool(record.get("is_active") and record.get("meaning_ko")) for record in records):
            raise PipelineError("client catalog 후보 필터가 활성·뜻 보유 정책과 일치하지 않습니다.")
    except PipelineError as error:
        print(f"검증 실패\n{error}", file=sys.stderr)
        return 2
    print("=== Vocabulary Validation Complete ===")
    print(f"Canonical vocabulary: {len(records)}")
    print(f"Quiz catalog (meaning_ko required): {len(items)}")
    print("Validation errors: 0")
    for warning in warnings:
        print(f"[주의] {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
