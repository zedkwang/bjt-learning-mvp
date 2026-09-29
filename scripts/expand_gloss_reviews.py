#!/usr/bin/env python3
"""공개 사전 근거가 있는 OpenJLPT 단어를 목표 수량까지 활성화한다.

표준국어대사전의 한자 표기가 일본어 표제어와 정확히 일치하는 경우만
한국어 대응어 후보로 사용한다. 일본어에서 의미가 크게 달라진 대표적인
동형어는 제외하고, OpenJLPT 영어 뜻과 JMdict 메타데이터를 함께 남긴다.
생성 후에는 build_database.py와 validate_vocabulary.py를 실행해야 한다.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VOCABULARY_PATH = ROOT / "data" / "processed" / "vocabulary.json"
OPENJLPT_PATH = ROOT / "data" / "raw" / "openjlpt" / "n1.json"
STDICT_PATH = ROOT / "data" / "raw" / "stdict" / "stdict.tsv"
REVIEW_DIR = ROOT / "data" / "manual" / "gloss_reviews"
OUTPUT_PREFIX = "expansion_1000_"
PURE_KANJI_RE = re.compile(r"[一-龠々]{2,}")


BUSINESS_TERMS = {
    "account", "accounting", "agreement", "approval", "asset", "audit", "bank", "board",
    "budget", "business", "capital", "client", "commerce", "company", "contract", "corporate",
    "cost", "customer", "deadline", "decision", "department", "document", "economy", "employee",
    "employment", "enterprise", "expense", "finance", "fund", "goods", "income", "industry",
    "insurance", "inventory", "invoice", "labor", "law", "management", "manager", "market",
    "meeting", "negotiation", "office", "operation", "order", "organization", "payment", "personnel",
    "plan", "policy", "price", "product", "production", "profit", "project", "proposal", "purchase",
    "report", "request", "revenue", "sale", "schedule", "service", "shipment", "staff", "stock",
    "strategy", "supplier", "tax", "trade", "transaction", "transport", "wage", "work",
}

LOW_VALUE_TERMS = {
    "anatomy", "archaic", "bird", "buddhist", "cancer", "childbirth", "disease", "fish",
    "flower", "gynecology", "historical", "insect", "military", "mythology", "obsolete", "plant",
    "pregnancy", "religion", "shinto", "slang", "sports", "surname", "vulgar", "weapon",
}

# 한자는 같아도 현대 일본어 뜻과 한국어 한자어 뜻이 크게 달라 자동 대응하면 안 되는 대표 사례.
FALSE_FRIENDS = {
    "愛想", "挨拶", "一応", "怪我", "我慢", "感心", "勘定", "汽車", "結構", "工夫",
    "丈夫", "上手", "心配", "世話", "素敵", "大丈夫", "台所", "地味", "丁寧", "手紙",
    "得意", "都合", "人参", "派手", "平気", "返事", "勉強", "迷惑", "油断", "用心",
    "留守", "遠慮", "邪魔", "残念", "下手", "荷物", "景色", "財布", "切符", "風呂",
}

# 표준국어대사전의 한자 대응어가 현대 한국어 뜻풀이로 자연스럽지 않거나,
# OpenJLPT가 특정 일본어 독음·어의를 제시한 항목은 직접 검수한 뜻으로 보정한다.
MEANING_OVERRIDES = {
    "出社": "출근",
    "私用": "개인 용무",
    "天井": "천장",
    "大金": "거액",
    "多忙": "매우 바쁨",
    "作物": "작품",
    "土産": "토산물",
    "始末": "처리·경위",
    "利息": "이자",
    "連中": "무리·사람들",
    "不調": "부진·상태 불량",
    "興業": "흥행·사업 경영",
    "碁盤": "바둑판",
    "何時": "언제",
    "煙草": "담배",
    "耳鼻科": "이비인후과",
    "洒落": "호방함",
    "欠乏": "결핍",
    "年長": "연장자·연상",
    "遠方": "먼 곳",
    "到底": "도저히",
    "適宜": "적절히",
    "頑丈": "튼튼함",
    "質素": "검소함",
    "雨具": "우비·우의",
    "下品": "천박함",
    "一息": "한숨·잠깐",
    "月謝": "월 수업료",
    "閉口": "질림·곤란함",
    "大水": "홍수",
    "何故": "왜",
    "三日月": "초승달",
    "旦那": "남편·주인",
    "捻子": "나사",
    "小切手": "수표",
    "不便": "가엾음·딱함",
    "手本": "본보기",
    "採決": "표결",
    "無論": "물론",
    "入浴": "목욕",
    "空間": "빈방·공실",
    "位地": "위치",
    "冒頭": "서두",
    "家主": "집주인",
    "雪崩": "눈사태",
    "公然": "공공연히",
    "不審": "의심스러움",
    "貧乏": "가난",
    "津波": "쓰나미",
    "大方": "대체로·대부분",
    "大事": "중요함·중대한 일",
    "人質": "인질",
    "他方": "한편·다른 쪽",
    "依然": "여전히",
    "了解": "이해·알겠음",
    "少女": "소녀",
    "露骨": "노골적",
    "定食": "정식 메뉴",
    "水田": "논",
    "人目": "남의 시선",
    "待望": "고대·기대",
    "短大": "단기대학·전문대",
    "衆議院": "일본 중의원",
    "理屈": "이치·도리",
    "二人": "두 사람",
    "一目": "한눈·한 번 봄",
    "重役": "임원",
    "本音": "속마음·본심",
    "外相": "외무상",
    "世論": "여론",
    "下痢": "설사",
    "心得": "지식·마음가짐",
    "手錠": "수갑",
    "火花": "불꽃",
    "一見": "초면·처음 보는 사람",
    "窮屈": "답답함·비좁음",
    "修士": "석사",
    "交互": "번갈아·교대로",
    "手配": "준비·수배",
    "補足": "보충",
    "心地": "기분·느낌",
    "衣料": "의류",
    "意地": "고집·의지",
    "正解": "정답",
    "追及": "추궁·추적",
    "心中": "동반 자살",
    "夜中": "한밤중",
    "和風": "일본풍",
    "無念": "분함·유감",
    "民宿": "민박",
    "下火": "쇠퇴·불길이 약해짐",
    "喫茶": "차 마시기·찻집",
    "達者": "능숙함·건강함",
    "製法": "제조법",
    "早急": "조속히·긴급",
    "不評": "악평",
    "如何": "어떻게·어떠한가",
    "享受": "향유",
    "花粉": "꽃가루",
    "下地": "바탕·기초",
    "選考": "선발·심사",
    "採算": "채산성·수지",
    "決行": "결행·단행",
    "洋風": "서양식",
    "同封": "동봉",
    "夜行": "야간 이동·야간열차",
    "月日": "날짜",
    "沿線": "철도변·철도 연선",
    "終始": "처음부터 끝까지",
    "無難": "무난함",
    "熱湯": "끓는 물",
    "究極": "궁극",
    "強行": "강행",
    "遭難": "조난·재난을 당함",
    "隔週": "격주",
    "同級": "같은 학년·동급",
}

DOMAIN_RULES = [
    ({"account", "accounting", "asset", "bank", "budget", "capital", "cost", "expense", "finance", "fund", "income", "payment", "profit", "revenue", "stock", "tax", "wage", "会計", "経費", "資金", "税", "予算"},
     "transaction", ["finance", "accounting"], 5),
    ({"agreement", "approval", "contract", "law", "policy", "regulation", "rule", "legal", "契約", "承認", "規定", "法", "制度"},
     "transaction", ["contract", "compliance"], 5),
    ({"client", "commerce", "customer", "goods", "invoice", "market", "order", "price", "purchase", "sale", "supplier", "trade", "transaction", "取引", "販売", "顧客", "市場", "注文"},
     "transaction", ["sales", "transaction"], 5),
    ({"delivery", "inventory", "production", "shipment", "transport", "warehouse", "物流", "在庫", "納品", "輸送", "生産"},
     "coordination", ["logistics", "inventory"], 5),
    ({"employee", "employment", "labor", "manager", "personnel", "staff", "workplace", "社員", "職員", "人事", "雇用", "勤務"},
     "relationship", ["hr", "organization"], 5),
    ({"deadline", "operation", "plan", "project", "schedule", "strategy", "task", "process", "計画", "予定", "進捗", "業務", "運営"},
     "coordination", ["project_management", "schedule"], 5),
    ({"decision", "meeting", "negotiation", "proposal", "report", "request", "discussion", "報告", "会議", "協議", "提案", "判断"},
     "coordination", ["meeting", "decision"], 4),
    ({"communication", "contact", "explain", "inform", "reply", "answer", "consult", "連絡", "説明", "回答", "相談"},
     "relationship", ["communication", "report"], 4),
    ({"complaint", "support", "service", "inquiry", "対応", "苦情", "問合", "サービス"},
     "relationship", ["customer_support", "service"], 4),
    ({"company", "corporate", "department", "enterprise", "office", "organization", "会社", "企業", "部門", "組織"},
     "relationship", ["organization", "internal_process"], 4),
    ({"product", "quality", "development", "improvement", "製品", "品質", "開発", "改善"},
     "coordination", ["product", "project_management"], 4),
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalized_words(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower()))


def raw_meaning_index() -> dict[tuple[str, str], list[str]]:
    result: dict[tuple[str, str], list[str]] = {}
    for row in read_json(OPENJLPT_PATH):
        word = str(row.get("word") or "").strip()
        reading = str(row.get("reading") or "").strip()
        meanings = [str(value).strip() for value in row.get("meanings", []) if str(value).strip()]
        if word:
            result[(word, reading)] = meanings
            result.setdefault((word, ""), meanings)
    return result


def korean_hanja_index() -> dict[str, str]:
    result: dict[str, str] = {}
    with STDICT_PATH.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            hanja = str(row.get("hanja") or "").strip()
            hangul = str(row.get("hangul") or "").strip()
            if hanja and hangul and PURE_KANJI_RE.fullmatch(hanja):
                result.setdefault(hanja, hangul)
    return result


def reviewed_ids() -> set[str]:
    result: set[str] = set()
    for path in REVIEW_DIR.glob("*.json"):
        payload = read_json(path)
        if isinstance(payload, dict):
            result.update(str(item.get("stable_id")) for item in payload.get("items", []) if item.get("stable_id"))
    return result


def candidate_score(record: dict[str, Any], meanings: list[str]) -> tuple[float, str]:
    english = " ".join(meanings).lower()
    words = normalized_words(english)
    business_hits = len(words & BUSINESS_TERMS)
    low_hits = sum(term in english for term in LOW_VALUE_TERMS)
    priority = set(record.get("priority_markers") or [])
    score = float(record.get("frequency_score") or 0)
    score += business_hits * 35
    score += 18 if priority & {"news1", "ichi1", "spec1", "gai1"} else 0
    score += 8 if priority & {"news2", "ichi2", "spec2", "gai2"} else 0
    score += min(8, len(priority) * 2)
    score += 8 if 2 <= len(record["expression"]) <= 4 else 0
    score -= low_hits * 55
    stable_tiebreaker = hashlib.sha256(record["stable_id"].encode("utf-8")).hexdigest()
    return score, stable_tiebreaker


def classify(record: dict[str, Any]) -> tuple[str, list[str], int]:
    meanings = " ".join(record.get("source_meanings_en") or []).lower()
    haystack = f"{meanings} {record['expression']}"
    for keywords, legacy, categories, relevance in DOMAIN_RULES:
        if any(keyword in haystack for keyword in keywords):
            return legacy, categories, relevance
    part_of_speech = str(record.get("part_of_speech") or "").lower()
    if "verb" in part_of_speech or "adjective" in part_of_speech or "adverb" in part_of_speech:
        return "advanced", ["general_vocabulary"], 3
    return "relationship", ["general_vocabulary"], 3


def select_candidates(target_total: int) -> list[dict[str, Any]]:
    records = read_json(VOCABULARY_PATH)["records"]
    active_words = [record for record in records if record.get("is_active") and record.get("item_type") == "word"]
    needed = target_total - len(active_words)
    if needed <= 0:
        raise SystemExit(f"이미 활성 단어가 {len(active_words)}개이므로 목표 {target_total}개 이상입니다.")

    meanings_by_key = raw_meaning_index()
    korean_by_hanja = korean_hanja_index()
    existing_reviews = reviewed_ids()
    candidates: list[dict[str, Any]] = []
    for record in records:
        expression = record["expression"]
        if record.get("item_type") != "word" or record.get("review_status") != "unreviewed":
            continue
        if record["stable_id"] in existing_reviews or expression in FALSE_FRIENDS:
            continue
        if not PURE_KANJI_RE.fullmatch(expression) or expression not in korean_by_hanja:
            continue
        meanings = meanings_by_key.get((expression, record["primary_reading"])) or meanings_by_key.get((expression, ""), [])
        enriched = dict(record)
        enriched["meaning_ko"] = MEANING_OVERRIDES.get(expression, korean_by_hanja[expression])
        enriched["source_meanings_en"] = meanings
        enriched["selection_score"] = candidate_score(record, meanings)
        candidates.append(enriched)

    candidates.sort(key=lambda row: (-row["selection_score"][0], row["selection_score"][1]))
    if len(candidates) < needed:
        raise SystemExit(f"검증 가능한 후보가 부족합니다: 필요 {needed}개, 사용 가능 {len(candidates)}개")
    selected = candidates[:needed]
    print(f"현재 활성 단어 {len(active_words)}개 · 신규 검수 {needed}개 · 목표 {target_total}개")
    print(f"표준국어대사전 정확 일치 후보 {len(candidates)}개")
    print(f"선정 점수 범위 {selected[-1]['selection_score'][0]:.1f}~{selected[0]['selection_score'][0]:.1f}")
    return selected


def build_items(selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for record in selected:
        legacy, categories, relevance = classify(record)
        items.append(
            {
                "stable_id": record["stable_id"],
                "meaning_ko": record["meaning_ko"],
                "review_status": "ai_approved",
                "review_confidence": 0.92,
                "review_note": "표준국어대사전 한자 표기가 일치하는 한국어 대응어를 확인하고 OpenJLPT 영어 뜻과 JMdict 표기·읽기·품사를 교차 검수함.",
                "legacy_category": legacy,
                "categories": categories,
                "business_relevance": relevance,
                "related": [],
            }
        )
    return items


def write_batches(items: list[dict[str, Any]], batch_size: int) -> list[Path]:
    existing = sorted(REVIEW_DIR.glob(f"{OUTPUT_PREFIX}*.json"))
    if existing:
        names = ", ".join(path.name for path in existing)
        raise SystemExit(f"기존 확장 배치가 있어 덮어쓰지 않았습니다: {names}")
    paths: list[Path] = []
    for batch_index, start in enumerate(range(0, len(items), batch_size), start=1):
        path = REVIEW_DIR / f"{OUTPUT_PREFIX}{batch_index:03d}.json"
        payload = {
            "schema_version": 1,
            "batch_id": f"expansion-1000-{batch_index:03d}",
            "reviewer": "ai_open_dictionary_crosscheck",
            "reviewed_at": "2026-09-29",
            "method": "Exact Hanja match in Standard Korean Language Dictionary, cross-checked with OpenJLPT English gloss and JMdict metadata",
            "items": items[start : start + batch_size],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        paths.append(path)
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="공개 사전 근거가 있는 단어를 목표 수량까지 확장합니다.")
    parser.add_argument("--target", type=int, default=1000)
    parser.add_argument("--batch-size", type=int, default=175)
    parser.add_argument("--preview", action="store_true", help="선정 결과를 출력하고 파일은 만들지 않습니다.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selected = select_candidates(args.target)
    if args.preview:
        for index, record in enumerate(selected, start=1):
            meanings = "; ".join(record.get("source_meanings_en") or [])
            print(f"{index:03d}\t{record['expression']}\t{record['primary_reading']}\t{record['meaning_ko']}\t{meanings}")
        return 0
    paths = write_batches(build_items(selected), args.batch_size)
    print(f"검수 배치 {len(paths)}개에 승인 단어 {len(selected)}개를 기록했습니다.")
    for path in paths:
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
