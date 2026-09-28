# AI 한국어 뜻 검수 배치

이 폴더에는 OpenJLPT 후보를 앱에 노출하기 전에 검수한 AI 배치를 JSON으로 보관함.
사용자는 이 목록을 학습 전 열람하지 않고, 검수 통과 항목만 브라우저 카탈로그에 반영함.

## 파일 형식

각 `*.json` 파일은 아래 형태를 사용함.

```json
{
  "schema_version": 1,
  "batch_id": "business-communication-001",
  "reviewer": "ai_dual_pass",
  "reviewed_at": "2026-09-28",
  "items": [
    {
      "stable_id": "auto-example",
      "meaning_ko": "간결한 한국어 뜻",
      "review_status": "ai_approved",
      "review_confidence": 0.92,
      "review_note": "업무 문맥과 경어·다의어 확인 결과",
      "legacy_category": "relationship",
      "categories": ["communication"],
      "business_relevance": 4,
      "related": []
    }
  ]
}
```

## 운영 규칙

- `stable_id`는 원본 후보의 식별자이므로 변경하지 않음.
- 이 폴더의 `review_status`는 `ai_approved`, `needs_review`, `rejected`만 허용함. 수동 승인 데이터는 `business_seed.json`과 override로 별도 관리함.
- `review_confidence`는 문자열이 아닌 `0~1` 숫자여야 하며, 모든 항목은 `review_note`, 비어 있지 않은 허용 카테고리, 허용 `legacy_category`, `0~5` 정수형 업무 적합도를 반드시 가짐. `ai_approved`는 여기에 `meaning_ko`와 `0.85` 이상의 신뢰도를 추가로 가짐.
- `ai_approved`만 퀴즈 카탈로그에 활성화함. `needs_review`와 `rejected`는 비활성으로 유지함.
- 뜻은 문제 사전 힌트가 아니라 답안 제출 뒤 보일 짧은 풀이로 작성함.
- 한 배치 안과 배치 간에 동일 `stable_id`를 중복 등록하지 않음.
- 검수 대상은 아직 검수되지 않은 OpenJLPT 후보로 한정함. 수동 시드와 수동 override는 AI 배치가 덮어쓰지 못하며, override가 최종 우선권을 가짐.
- `related`는 생략할 수 있으나, 넣을 때는 문자열 배열이어야 함.
- 원본 의미·읽기 근거는 canonical record의 OpenJLPT·JMdict source provenance를 그대로 유지함. JMdict의 복수 읽기는 metadata이며, 채점 정답은 OpenJLPT의 `primary_reading`을 사용함. 이 파일은 한국어 학습 풀이의 AI 검수 이력이며, 인적 사전 편집 감수와는 구분함.
