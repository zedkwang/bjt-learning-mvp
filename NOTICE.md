# Third-party data notices

This repository includes source data used to build the BJT ARC learning catalog.
The original source files remain in `data/raw/`; generated data is in
`data/processed/`.

## OpenJLPT

- Source: `data/raw/openjlpt/n1.json`
- Download URL: https://raw.githubusercontent.com/evanclan/OpenJLPT/main/data/json/vocab/n1.json
- Downloaded: 2026-09-28
- SHA-256: `e9662df1dba34c2f566a128f203c8a78296c1c2c1a337b8ef036ca516ea8430e`
- License: CC BY-SA 4.0
- Attribution and upstream NOTICE: https://github.com/evanclan/OpenJLPT/blob/main/NOTICE.md

OpenJLPT level data is stored as an `openjlpt`-sourced learning-level
candidate. It must not be presented as an official JLPT vocabulary list.

## JMdict

- Source: `data/raw/jmdict/JMdict_e.gz`
- Download URL: https://www.edrdg.org/pub/Nihongo/JMdict_e.gz
- Downloaded: 2026-09-28
- SHA-256: `07c9aa6d4c8b477096ca5c2a02f960b1e354b6d8f27626b478c54e8c95d3753a`
- Copyright holder: Electronic Dictionary Research and Development Group
- Licence statement: https://www.edrdg.org/edrdg/licence.html
- Suggested acknowledgement: https://www.edrdg.org/edrdg/sample.html

JMdict is used for spelling, reading, reading restriction, part-of-speech, and
priority-marker validation. It is not presented as project-owned dictionary data.

## Standard Korean Language Dictionary

- Source: `data/raw/stdict/stdict.tsv`
- Original data: National Institute of Korean Language, Standard Korean Language Dictionary
- Normalized snapshot: https://github.com/dahlia/gukhanmun/blob/main/crates/gukhanmun-stdict/data/stdict.tsv
- Snapshot: `전체 내려받기_표준국어대사전_JSON_20260606.zip`
- Included: 2026-09-29
- SHA-256: `4e3796dfc85a16345b7c4395d89f68e23a5606fd03f62da5d197c77dc75c438a`
- Data license: CC BY-SA 2.0 KR
- Copyright policy: https://stdict.korean.go.kr/join/copyrightPolicy.do

The normalized Hanja-to-Hangul table is used to cross-check Korean glosses.
Exact Hanja matches are further reviewed against OpenJLPT meanings and JMdict
metadata; known Japanese-Korean false friends are excluded or corrected.
The redistributed normalized table and Korean glosses derived from it remain
available under CC BY-SA 2.0 KR; project-authored corrections are distributed
under the same terms when included in those derived review batches.

## Project-authored data

`data/manual/business_seed.json` and the Korean post-answer glosses in this
repository are project-authored learning data. They remain separate from the
upstream raw data and are recorded with their own provenance in the build output.
