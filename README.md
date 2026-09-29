# BJT ARC — 비즈니스 일본어 리딩 드릴 MVP

JLPT N1 학습자가 한자 표기를 보고 일본어 발음을 바로 입력하는 훈련용, 브라우저 단독 실행 MVP임.

## 포함 기능

- 단어 학습과 문장 학습을 분리한 읽기 퀴즈 및 히라가나 답안 입력
- 답안을 제출한 뒤 정답 읽기와 한국어 뜻을 피드백으로 표시
- 공백·전각 공백·일부 문장부호를 무시하는 답안 정규화
- 완전 정답 / 표기 주의(한 글자, 장음·촉음 등) / 재확인 분리
- 오답 피드백에서 내 입력과 정답을 먼저 비교하고, 수정 구간을 문맥 단위로 요약한 뒤 글자별 상세 비교 제공
- 응답 시간 측정 및 탭 비활성 시간 제외
- 일일 한도·대기 시간 없이, 남은 신규 표현을 원하는 만큼 이어서 학습
- 공통 한자와 같은 카테고리의 연속 노출을 줄이는 분산 셔플 출제
- 단어·문장을 나눠 직접 넣고 빼는 복습 보관함
- 문장 답안 확인 후, 문장 속 핵심 단어를 골라 단어 복습으로 보내는 연결 흐름
- XP, 콤보, 업적, 업무 언어 역량 맵
- 주간 실전 라운드 및 주 1회 완료 보너스
- 브라우저 localStorage 기반 학습 기록 저장

## 실행 방법

index.html을 최신 브라우저에서 열면 됨. 별도 설치나 외부 API가 필요하지 않음.

## MVP 정책

- 히라가나 기준으로 정규화한 뒤, 문항의 허용 읽기(`accepted_readings`)와 완전 일치할 때만 완전 정답으로 처리함. 가타카나 입력은 히라가나로 정규화함
- 뜻 보기를 사용한 뒤 맞힌 답은 힌트 정답으로 분리함: +2 XP만 지급하고, 콤보·무힌트 정확도·숙련도에는 반영하지 않음
- 한 글자 차이, 장음·촉음 차이는 표기 주의로 표시하며 콤보에 반영하지 않음
- 틀린 표현·힌트 정답·정답 모두 답안 피드백에서 사용자가 직접 복습 보관함에 넣거나 뺄 수 있음. 자동 재출제·시간 기반 예약·정답 뒤 자동 제거는 하지 않음
- 문장 자체는 문장 복습에, 문장 속에서 고른 핵심 단어는 단어 복습에 각각 독립적으로 저장함
- 신규 학습과 직접 선택한 복습은 세션 시작 때마다 순서를 다시 섞되, 공통 한자 문항이 바로 이어지지 않도록 우선 분산함. 주간 실전 라운드의 고정 구성은 유지함
- 신규 학습과 복습 세션은 고정 문항 수 제한 없이 이어지며, 사용자가 `학습 마치기`를 선택할 때만 종료함
- 탭을 벗어난 뒤 돌아오면 해당 문항의 속도 보상은 제외함
- 현재 문제은행은 핸드오프에 포함된 예시를 바탕으로 만든 데모 데이터임

## 데이터 파이프라인

현재 41개 수동 승인 문항은 앱 코드에만 의존하지 않으며, 검수 가능한 수동 시드로 관리됨.

```text
data/
  raw/        외부 원본을 수정 없이 보관하는 위치
  manual/     프로젝트에서 검수한 seed·읽기 override·제외 목록
  processed/  빌드 생성물(JSON · SQLite · browser catalog)
scripts/      import · 정규화 · 검증 · 생성 스크립트
```

주요 입력은 다음과 같음.

- `data/manual/business_seed.json`: 기존 33개 데모 문항과 문장 연결용 핵심 단어 8개를 관리하는 수동 승인 데이터. `stable_id`는 브라우저 학습 기록과 연결할 안정적인 식별자임. 문장 레코드의 `word_links`는 문장 속 표기·읽기와 실제 단어 문항 ID를 연결함.
- `data/manual/gloss_reviews/`: OpenJLPT 후보의 한국어 뜻을 AI 2단계 검수한 배치. `ai_approved`이면서 신뢰도 0.85 이상인 항목만 활성 퀴즈가 됨.
- `data/manual/reading_overrides.json`: 특정 표기에서 학습 정답으로 허용할 읽기를 제한하는 override. 명시한 `accepted_readings`는 원본의 문제 읽기보다 우선함.
- `data/manual/excluded_words.json`: raw를 지우지 않고 결과에서만 제외하는 목록.
- `data/raw/README.md`: OpenJLPT·JMdict 원본 파일명과 지원 형식.

외부 원본은 빌드 과정에서 자동 다운로드하지 않음. 현재 저장소에는 2026-09-28에 확인·수집한 OpenJLPT N1 JSON과 JMdict 원본이 포함되어 있으며, URL·SHA-256·표기 사항은 [NOTICE.md](NOTICE.md)에 기록함. 이후 원본을 갱신할 때도 현재 라이선스·표시 조건을 재확인해야 함. OpenJLPT의 레벨은 `openjlpt` 출처의 학습 레벨로만 저장하며, 공식 JLPT 출제 목록으로 표현하지 않음.

### 빌드와 검증

프로젝트 폴더에서 실행함.

```bash
python3 scripts/build_database.py
python3 scripts/validate_vocabulary.py
```

빌드하면 아래 생성물이 함께 갱신됨.

- `data/processed/vocabulary.json`: 검수·디버깅용 canonical export
- `data/processed/vocabulary.sqlite`: source provenance, 복수 읽기, 카테고리, 한자 연결 정보를 가진 SQLite DB
- `data/processed/catalog.js`: 브라우저 앱이 읽을 `window.BJT_CATALOG` 전역 데이터

`catalog.js` 항목은 기존 UI 호환 필드(`id`, `display`, `reading`, `meaning`, `category`, `level`, `related`, `type`)와 canonical 필드(`expression`, `primary_reading`, `accepted_readings`, `meaning_ko`, `categories`)를 함께 제공함. 문장에는 검수된 `word_links`도 포함되어 문장 피드백에서 실제 단어 문항을 복습에 넣을 수 있음. AI 검수 상태·신뢰도·검수 메모는 canonical JSON과 SQLite에 보관하며, 학습 화면에는 노출하지 않음.

한국어 뜻은 문제를 보기 전 기본 노출하는 정보가 아니라 답안 제출 후 피드백에 쓰는 보조 필드임. 따라서 활성 퀴즈 항목은 반드시 `meaning_ko`와 승인 상태를 가져야 하며, 뜻이 없거나 `needs_review`/`rejected`인 OpenJLPT 후보는 canonical DB에는 보관하되 퀴즈 카탈로그에서는 제외됨. OpenJLPT가 지정한 `primary_reading`만 정답으로 허용하고, JMdict의 다른 읽기는 근거 metadata로만 보관함. 다른 읽기를 정답으로 허용해야 할 때만 `reading_overrides.json`에 명시함.

원본 파일이 아직 없으면 기본 빌드는 수동 41개 문항만 생성하고, OpenJLPT·JMdict를 건너뛴다는 안내를 출력함. 운영용으로 원본이 반드시 있어야 할 때는 아래처럼 명시적으로 실패하게 만들 수 있음.

```bash
python3 scripts/build_database.py --require-openjlpt --require-jmdict
```

원본 형식 자체를 먼저 점검하려면 다음을 사용함. 입력 파일이 없거나 형식이 맞지 않으면 실패 이유와 필요한 경로를 출력함.

```bash
python3 scripts/import_openjlpt.py
python3 scripts/import_jmdict.py
```

### 현재 범위와 한계

- OpenJLPT N1 JSON과 JMdict `JMdict_e.gz`를 현재 `data/raw/`에 포함함. 이번 빌드에서는 한자→읽기 훈련 대상 3,183개를 OpenJLPT에서 가져와 canonical DB 총 3,215개 항목을 생성함.
- JMdict는 표기·읽기·우선순위 태그 대조용이며, OpenJLPT 문제 읽기를 사전의 복수 읽기로 자동 확장하지 않음.
- KANJIDIC2와 BCCWJ는 DB 스키마 확장 여지는 준비했지만 이 1차 빌드에서는 가져오지 않음. 특히 BCCWJ는 이용 조건 검토 전 비활성임.
- Business Seed 41개와 AI 2단계 검수를 마친 초기 100개 후보를 함께 관리함. 2026-09-28 기준 활성 퀴즈는 단어 135개·문장 3개이며, 초기 AI 검수 배치 3개는 다의성 또는 추가 확인 사유로 비활성 보류함.
- AI 검수는 인적 사전 편집 감수가 아니므로, 이후 외부 검수 근거가 생기면 해당 배치를 `needs_review`에서 다시 판정해야 함. 검수 근거·신뢰도·보류 사유는 `data/manual/gloss_reviews/`와 canonical DB에 남김.

## 다음 단계

운영용 확장에는 로그인·다기기 동기화·문제은행 CMS·실제 16주 콘텐츠 배정표·권리 검수된 청해/청독해 자료가 필요함.
