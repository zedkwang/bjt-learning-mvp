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

## Project-authored data

`data/manual/business_seed.json` and the Korean post-answer glosses in this
repository are project-authored learning data. They remain separate from the
upstream raw data and are recorded with their own provenance in the build output.
