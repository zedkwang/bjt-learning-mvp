# claude_bjt 이관 원본

동일 사용자의 별도 프로젝트인 `https://github.com/zedkwang/claude_bjt`의 `main` 브랜치에서 2026-09-29에 이관한 원본입니다.

- `p3_n1_vocab.json`: 일반 N1 어휘 200개
  - SHA-256: `e82dd875ceba2186ebe3d7f33e19557e47f7df6f32a3a3233c13c345b419a719`
- `sentences.json`: 문장 100개
  - SHA-256: `85268b0e6bff9e1246f0acd1ee25b6b206a61552f4f86828242d33b7ec4e8376`

원본은 수정하지 않으며, `scripts/pipeline_core.py`가 기존 OpenJLPT·JMdict 및 활성 단어 데이터와 병합합니다. 같은 표기의 기존 항목은 안정적인 ID를 유지하고 `general_n1` 학습 트랙만 추가합니다.
