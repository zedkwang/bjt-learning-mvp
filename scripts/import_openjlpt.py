#!/usr/bin/env python3
"""OpenJLPT N1 원본을 검증 가능한 중간 JSON으로 확인한다.

이 파일은 원본을 바꾸지 않으며, 실제 SQLite 생성은 build_database.py가 수행한다.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pipeline_core import PROCESSED_DIR, PipelineError, load_openjlpt_records, record_export, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenJLPT N1 JSON/CSV 입력을 점검합니다.")
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="기본값: data/raw/openjlpt/n1.json 또는 n1.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_DIR / "openjlpt_normalized.json",
        help="정규화 확인용 출력 경로",
    )
    args = parser.parse_args()
    try:
        records, notes = load_openjlpt_records(args.input, required=True)
    except PipelineError as error:
        print(f"OpenJLPT import 실패\n{error}", file=sys.stderr)
        return 2
    write_json(args.output, {"schema_version": 1, "records": [record_export(record) for record in records]})
    print(f"OpenJLPT N1 후보 {len(records)}개를 {args.output}에 기록했습니다.")
    for note in notes:
        print(f"[안내] {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
