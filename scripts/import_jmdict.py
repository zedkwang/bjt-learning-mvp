#!/usr/bin/env python3
"""JMdict에서 현재 manual seed 표현의 읽기 후보를 추출한다."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pipeline_core import PROCESSED_DIR, PipelineError, load_jmdict_matches, load_manual_seed, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="JMdict XML에서 manual seed의 표기·읽기 후보를 대조합니다.")
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="기본값: data/raw/jmdict/JMdict_e.xml 또는 .xml.gz",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_DIR / "jmdict_matches.json",
        help="대조 결과 출력 경로",
    )
    args = parser.parse_args()
    try:
        manual = load_manual_seed()
        matches, notes = load_jmdict_matches(
            {record["expression"] for record in manual}, args.input, required=True
        )
    except PipelineError as error:
        print(f"JMdict import 실패\n{error}", file=sys.stderr)
        return 2
    write_json(args.output, {"schema_version": 1, "matches": matches})
    print(f"JMdict 매칭 표현 {len(matches)}개를 {args.output}에 기록했습니다.")
    for note in notes:
        print(f"[안내] {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
