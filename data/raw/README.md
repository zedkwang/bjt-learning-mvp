# 원본 데이터 입력 규약

이 폴더의 파일은 원본 그대로 보관합니다. 빌드 스크립트는 이 폴더를 수정하지 않습니다.

현재 저장소에는 OpenJLPT N1 JSON, JMdict 원본과 한국어 뜻 교차 검수용 표준국어대사전 정규화 TSV가 포함되어 있습니다. 빌드 스크립트가 외부 원본을 자동으로 내려받지는 않으며, 갱신 시에는 라이선스와 배포 조건을 해당 원본의 현재 공식 배포처에서 다시 확인해야 합니다. 수집 URL·SHA-256·표기 사항은 루트의 `NOTICE.md`에 기록합니다.

## OpenJLPT

다음 중 하나를 넣습니다.

- `openjlpt/n1.json`: JSON 배열 또는 `words` / `vocabulary` 배열을 가진 JSON 객체
- `openjlpt/n1.csv`: UTF-8 CSV. 헤더는 `word` 또는 `expression`, `reading` 또는 `kana`, `level`을 사용합니다.

JSON 항목 예시입니다.

```json
{"word":"促す","reading":"うながす","level":"N1"}
```

`level`이 비어 있으면 이 파일이 N1 전용임을 전제로 `N1`을 부여합니다. 이 값은 `openjlpt` 출처의 학습 레벨이며 공식 JLPT 출제 목록을 뜻하지 않습니다.

이 앱은 한자 표기에서 읽기를 꺼내는 훈련이므로, 가나·가타카나만으로 된 OpenJLPT 항목은 오류 없이 건너뜁니다. 한자가 있는데 `reading`이 비어 있는 항목은 검수해야 하므로 import를 중단합니다.

## JMdict

`jmdict/JMdict_e`, `jmdict/JMdict_e.gz`, `jmdict/JMdict_e.xml` 또는 `jmdict/JMdict_e.xml.gz`를 둡니다. 표준 JMdict XML의 `entry`, `k_ele/keb`, `r_ele/reb`, `r_ele/re_restr`, `ke_pri`, `re_pri`, `sense/pos` 구조를 읽습니다.

현재 후보 표현과 일치하는 항목만 메모리에 남기므로 대형 XML도 전체 JSON으로 변환하지 않습니다.

## 표준국어대사전

`stdict/stdict.tsv`는 국립국어원 표준국어대사전 전체 내려받기 데이터를 Gukhanmun 프로젝트가 한자→한글 대응표로 정규화한 스냅샷입니다. 한국어 뜻 확장 스크립트는 일본어 표제어와 한자 표기가 정확히 일치하는 항목만 후보로 사용하며, 대표적인 한일 동형이의어를 제외하고 OpenJLPT 영어 뜻과 JMdict 메타데이터로 교차 검수합니다.

이 데이터는 CC BY-SA 2.0 KR 조건으로 제공됩니다. 스냅샷 날짜와 원출처, 정규화 프로젝트, 체크섬은 루트의 `NOTICE.md`에 기록합니다.

## 선택 소스

`kanjidic/`, `bccwj/`는 이 1차 빌드에서 읽지 않습니다. BCCWJ는 라이선스 검토 전 비활성 상태로 유지합니다.
