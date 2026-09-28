#!/usr/bin/env python3
"""manual/raw 입력을 검증하고 SQLite 및 브라우저 카탈로그를 함께 생성한다."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pipeline_core import PipelineError, build_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="BJT 읽기 학습용 canonical SQLite와 browser catalog.js를 생성합니다."
    )
    parser.add_argument("--openjlpt", type=Path, help="선택: OpenJLPT N1 JSON 또는 CSV 경로")
    parser.add_argument("--jmdict", type=Path, help="선택: JMdict XML 또는 XML.GZ 경로")
    parser.add_argument(
        "--require-openjlpt",
        action="store_true",
        help="OpenJLPT 원본이 없으면 실패합니다. 운영 빌드에서 사용합니다.",
    )
    parser.add_argument(
        "--require-jmdict",
        action="store_true",
        help="JMdict 원본이 없으면 실패합니다. 운영 빌드에서 사용합니다.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = build_pipeline(
            openjlpt_path=args.openjlpt,
            jmdict_path=args.jmdict,
            require_openjlpt=args.require_openjlpt,
            require_jmdict=args.require_jmdict,
        )
    except PipelineError as error:
        print(f"빌드 실패\n{error}", file=sys.stderr)
        return 2

    print("=== Vocabulary Build Complete ===")
    print(f"Canonical vocabulary: {len(result['records'])}")
    print(f"Manual demo seed: {result['manual_count']}")
    print(f"OpenJLPT N1 candidates: {result['openjlpt_count']}")
    print(f"JMdict expression matches: {result['jmdict_matched_count']}")
    print(f"Quiz catalog (meaning_ko required): {result['quiz_count']}")
    print("Validation errors: 0")
    for note in result["notes"]:
        print(f"[안내] {note}")
    for warning in result["warnings"]:
        print(f"[주의] {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
