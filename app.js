(() => {
  "use strict";

  const STORAGE_KEY = "bjt-arc-learning-state-v1";
  const DAY_MS = 24 * 60 * 60 * 1000;
  const MAX_MASTERY_STAGE = 5;

  const CATEGORY_LABELS = {
    transaction: "거래·문서",
    coordination: "조정·진행",
    relationship: "의뢰·경어",
    advanced: "훈독 강화",
  };

  // 카탈로그 파일이 없을 때에도 데모가 깨지지 않도록 남겨 둔 fallback입니다.
  // 운영 데이터는 data/processed/catalog.js에서 주입합니다.
  const DEMO_ITEMS = [
    {
      id: "approval",
      display: "承認",
      reading: "しょうにん",
      meaning: "승인",
      category: "transaction",
      level: "business_core",
      related: ["承知　しょうち", "了承　りょうしょう", "継承　けいしょう"],
    },
    {
      id: "estimate",
      display: "見積",
      reading: "みつもり",
      meaning: "견적",
      category: "transaction",
      level: "business_core",
      related: ["見積書　みつもりしょ", "見積もる　みつもる"],
    },
    {
      id: "delivery-date",
      display: "納期",
      reading: "のうき",
      meaning: "납기",
      category: "coordination",
      level: "business_core",
      related: ["前倒し　まえだおし", "進捗　しんちょく"],
    },
    {
      id: "assignment",
      display: "配属",
      reading: "はいぞく",
      meaning: "배속",
      category: "relationship",
      level: "business_core",
      related: ["採用　さいよう", "面接　めんせつ"],
    },
    {
      id: "reminder",
      display: "催促",
      reading: "さいそく",
      meaning: "독촉",
      category: "relationship",
      level: "business_core",
      related: ["催促する　さいそくする", "確認　かくにん"],
    },
    {
      id: "adjustment",
      display: "調整",
      reading: "ちょうせい",
      meaning: "조정",
      category: "coordination",
      level: "business_core",
      related: ["日程調整　にっていちょうせい", "納期調整　のうきちょうせい"],
    },
    {
      id: "application",
      display: "申請",
      reading: "しんせい",
      meaning: "신청",
      category: "transaction",
      level: "business_core",
      related: ["承認申請　しょうにんしんせい", "提出　ていしゅつ"],
    },
    {
      id: "invoice",
      display: "請求",
      reading: "せいきゅう",
      meaning: "청구",
      category: "transaction",
      level: "business_core",
      related: ["請求書　せいきゅうしょ", "支払い　しはらい"],
    },
    {
      id: "order",
      display: "発注",
      reading: "はっちゅう",
      meaning: "발주",
      category: "transaction",
      level: "business_core",
      related: ["受注　じゅちゅう", "発注書　はっちゅうしょ"],
    },
    {
      id: "receive-order",
      display: "受注",
      reading: "じゅちゅう",
      meaning: "수주",
      category: "transaction",
      level: "business_core",
      related: ["発注　はっちゅう", "納品　のうひん"],
    },
    {
      id: "confirmation",
      display: "確認",
      reading: "かくにん",
      meaning: "확인",
      category: "relationship",
      level: "business_core",
      related: ["再確認　さいかくにん", "ご確認ください　ごかくにんください"],
    },
    {
      id: "consideration",
      display: "検討",
      reading: "けんとう",
      meaning: "검토",
      category: "coordination",
      level: "business_core",
      related: ["再検討　さいけんとう", "社内　しゃない"],
    },
    {
      id: "sharing",
      display: "共有",
      reading: "きょうゆう",
      meaning: "공유",
      category: "coordination",
      level: "business_core",
      related: ["進捗共有　しんちょくきょうゆう", "連絡　れんらく"],
    },
    {
      id: "handling",
      display: "対応",
      reading: "たいおう",
      meaning: "대응",
      category: "relationship",
      level: "business_core",
      related: ["ご対応　ごたいおう", "問題対応　もんだいたいおう"],
    },
    {
      id: "judgment",
      display: "判断",
      reading: "はんだん",
      meaning: "판단",
      category: "coordination",
      level: "business_core",
      related: ["判断する　はんだんする", "方針　ほうしん"],
    },
    {
      id: "submission",
      display: "提出",
      reading: "ていしゅつ",
      meaning: "제출",
      category: "transaction",
      level: "business_core",
      related: ["提出期限　ていしゅつきげん", "申請　しんせい"],
    },
    {
      id: "implementation",
      display: "実施",
      reading: "じっし",
      meaning: "실시",
      category: "coordination",
      level: "business_core",
      related: ["実施する　じっしする", "予定　よてい"],
    },
    {
      id: "acknowledge",
      display: "承知",
      reading: "しょうち",
      meaning: "알겠습니다",
      category: "relationship",
      level: "business_core",
      related: ["承る　うけたまわる", "了承　りょうしょう"],
    },
    {
      id: "consent",
      display: "了承",
      reading: "りょうしょう",
      meaning: "양해",
      category: "relationship",
      level: "business_core",
      related: ["承認　しょうにん", "承知　しょうち"],
    },
    {
      id: "receive-humble",
      display: "承る",
      reading: "うけたまわる",
      meaning: "받들다",
      category: "advanced",
      level: "kunyomi",
      related: ["承知　しょうち", "承認　しょうにん"],
    },
    {
      id: "urge",
      display: "促す",
      reading: "うながす",
      meaning: "재촉하다",
      category: "advanced",
      level: "kunyomi",
      related: ["催促　さいそく", "進める　すすめる"],
    },
    {
      id: "supplement",
      display: "補う",
      reading: "おぎなう",
      meaning: "보충하다",
      category: "advanced",
      level: "kunyomi",
      related: ["不足　ふそく", "補足　ほそく"],
    },
    {
      id: "impair",
      display: "損なう",
      reading: "そこなう",
      meaning: "해치다",
      category: "advanced",
      level: "kunyomi",
      related: ["品質　ひんしつ", "影響　えいきょう"],
    },
    {
      id: "accompany",
      display: "伴う",
      reading: "ともなう",
      meaning: "수반하다",
      category: "advanced",
      level: "kunyomi",
      related: ["変更　へんこう", "影響　えいきょう"],
    },
    {
      id: "estimate-verb",
      display: "見込む",
      reading: "みこむ",
      meaning: "예상하다",
      category: "advanced",
      level: "kunyomi",
      related: ["見込み　みこみ", "判断　はんだん"],
    },
    {
      id: "hinder",
      display: "差し支える",
      reading: "さしつかえる",
      meaning: "지장이 있다",
      category: "advanced",
      level: "kunyomi",
      related: ["問題　もんだい", "支障　ししょう"],
    },
    {
      id: "handle-verb",
      display: "取り扱う",
      reading: "とりあつかう",
      meaning: "취급하다",
      category: "advanced",
      level: "kunyomi",
      related: ["対応　たいおう", "商品　しょうひん"],
    },
    {
      id: "accept-task",
      display: "引き受ける",
      reading: "ひきうける",
      meaning: "맡다",
      category: "advanced",
      level: "kunyomi",
      related: ["担当　たんとう", "依頼　いらい"],
    },
    {
      id: "consider-based-on",
      display: "踏まえる",
      reading: "ふまえる",
      meaning: "바탕으로 하다",
      category: "advanced",
      level: "kunyomi",
      related: ["現状　げんじょう", "進捗　しんちょく"],
    },
    {
      id: "omit",
      display: "省く",
      reading: "はぶく",
      meaning: "생략하다",
      category: "advanced",
      level: "kunyomi",
      related: ["手順　てじゅん", "簡略化　かんりゃくか"],
    },
    {
      id: "sentence-estimate",
      display: "見積書をご確認ください。",
      reading: "みつもりしょをごかくにんください",
      meaning: "견적서를 확인해 주세요.",
      category: "transaction",
      level: "sentence",
      type: "sentence",
      related: ["見積書　みつもりしょ", "確認　かくにん"],
    },
    {
      id: "sentence-review",
      display: "社内で検討したうえで、改めてご回答いたします。",
      reading: "しゃないでけんとうしたうえで、あらためてごかいとういたします",
      meaning: "사내에서 검토한 뒤 다시 답변드리겠습니다.",
      category: "relationship",
      level: "sentence",
      type: "sentence",
      related: ["検討　けんとう", "回答　かいとう"],
    },
    {
      id: "sentence-schedule",
      display: "現状の進捗を踏まえると、前倒しは可能と見込んでおります。",
      reading: "げんじょうのしんちょくをふまえると、まえだおしはかのうとみこんでおります",
      meaning: "현재 진행 상황을 고려하면 앞당기는 것은 가능하다고 예상합니다.",
      category: "coordination",
      level: "sentence",
      type: "sentence",
      related: ["進捗　しんちょく", "踏まえる　ふまえる", "見込む　みこむ"],
    },
  ];

  function mapCatalogCategory(rawCategory, categories, readingType) {
    if (Object.prototype.hasOwnProperty.call(CATEGORY_LABELS, rawCategory)) return rawCategory;

    const codes = Array.isArray(categories) ? categories : [];
    if (readingType === "kunyomi" || readingType === "compound") return "advanced";
    if (
      codes.some((code) =>
        ["sales", "transaction", "contract", "finance", "accounting", "logistics", "inventory"].includes(code)
      )
    ) {
      return "transaction";
    }
    if (
      codes.some((code) =>
        ["project_management", "schedule", "product", "service", "compliance", "policy"].includes(code)
      )
    ) {
      return "coordination";
    }
    return "relationship";
  }

  function normalizeCatalogItem(rawItem) {
    const raw = rawItem && typeof rawItem === "object" ? rawItem : {};
    const primaryReading = String(raw.primary_reading || raw.primaryReading || raw.reading || "").trim();
    const suppliedReadings = Array.isArray(raw.accepted_readings)
      ? raw.accepted_readings
      : Array.isArray(raw.acceptedReadings)
        ? raw.acceptedReadings
        : [];
    const acceptedReadings = Array.from(
      new Set([primaryReading, ...suppliedReadings].map((reading) => String(reading || "").trim()).filter(Boolean))
    );
    const categories = Array.isArray(raw.categories)
      ? raw.categories
      : Array.isArray(raw.business?.categories)
        ? raw.business.categories
        : [];
    const readingType = raw.reading_type || raw.readingType || raw.reading?.type || raw.level || "";
    const category = mapCatalogCategory(raw.category || raw.ui_category || raw.uiCategory, categories, readingType);
    const display = String(raw.display || raw.expression || "").trim();

    return {
      ...raw,
      id: String(raw.id || "").trim(),
      display,
      reading: primaryReading,
      acceptedReadings,
      meaning: String(raw.meaning_ko || raw.meaning || "").trim(),
      category,
      level: raw.level || readingType || "business_core",
      related: Array.isArray(raw.related) ? raw.related : [],
      type: raw.type || raw.item_type || "word",
      learningPriority: Number(raw.learning_priority ?? raw.learningPriority ?? 0),
    };
  }

  function loadCatalogItems() {
    const catalog = window.BJT_CATALOG;
    const candidates = Array.isArray(catalog?.items) ? catalog.items.map(normalizeCatalogItem) : [];
    const usable = candidates.filter(
      (item) => item.id && item.display && item.reading && item.acceptedReadings.length && item.meaning
    );
    if (usable.length) return usable;

    if (catalog) {
      console.warn("학습 카탈로그에 사용할 수 있는 문항이 없어 데모 데이터를 사용합니다.");
    }
    return DEMO_ITEMS.map(normalizeCatalogItem);
  }

  const ITEMS = loadCatalogItems();

  const ACHIEVEMENTS = [
    { id: "first-link", icon: "◌", title: "첫 연결", description: "정확히 1개 읽기", test: () => state.totalCorrect >= 1 },
    { id: "combo-3", icon: "≋", title: "집중 흐름", description: "3콤보 달성", test: () => state.longestCombo >= 3 },
    { id: "combo-10", icon: "≋", title: "읽기 가속", description: "10콤보 달성", test: () => state.longestCombo >= 10 },
    { id: "correct-25", icon: "✦", title: "업무 어휘 25", description: "정확히 25개 읽기", test: () => state.totalCorrect >= 25 },
    { id: "reviewer", icon: "↻", title: "복습 복구자", description: "복습 5개 완료", test: () => state.reviewCorrect >= 5 },
    { id: "boss", icon: "◆", title: "주간 라운드", description: "실전 라운드 완료", test: () => Boolean(state.boss.completedWeek) },
  ];

  const viewRoot = document.getElementById("view-root");
  const toastRegion = document.getElementById("toast-region");
  let state = loadState();
  let activeView = "dashboard";
  let activeSession = null;
  let timerFrame = null;
  let isComposing = false;

  function defaultState() {
    return {
      version: 2,
      xp: 0,
      totalCorrect: 0,
      totalAttempts: 0,
      unhintedAttempts: 0,
      hintedCorrect: 0,
      reviewCorrect: 0,
      longestCombo: 0,
      progress: {},
      manualReview: {},
      logs: [],
      achievements: [],
      boss: { completedWeek: null },
    };
  }

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return defaultState();
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return defaultState();
      const { daily: _legacyDaily, ...currentState } = parsed;
      const hydrated = {
        ...defaultState(),
        ...currentState,
        version: 2,
        progress: parsed.progress || {},
        manualReview:
          parsed.manualReview && typeof parsed.manualReview === "object" && !Array.isArray(parsed.manualReview)
            ? parsed.manualReview
            : {},
        logs: Array.isArray(parsed.logs) ? parsed.logs : [],
        achievements: Array.isArray(parsed.achievements) ? parsed.achievements : [],
        boss: { completedWeek: null, ...(parsed.boss || {}) },
      };
      if (!Number.isFinite(parsed.unhintedAttempts)) {
        hydrated.unhintedAttempts = Number.isFinite(parsed.totalAttempts)
          ? parsed.totalAttempts
          : hydrated.logs.filter((log) => !log.hintUsed).length;
      }
      return hydrated;
    } catch (error) {
      console.warn("학습 기록을 불러오지 못했습니다.", error);
      return defaultState();
    }
  }

  function saveState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (error) {
      showToast("기록을 저장하지 못했습니다. 브라우저 저장소 설정을 확인해 주세요.");
      console.warn("학습 기록 저장 실패", error);
    }
  }

  function getWeekKey(date = new Date()) {
    const yearStart = new Date(date.getFullYear(), 0, 1);
    const day = Math.floor((date - yearStart) / DAY_MS) + 1;
    return `${date.getFullYear()}-W${String(Math.ceil(day / 7)).padStart(2, "0")}`;
  }

  function getProgress(itemId) {
    if (!state.progress[itemId]) {
      state.progress[itemId] = {
        seen: 0,
        correct: 0,
        hinted: 0,
        wrong: 0,
        soft: 0,
        stage: 0,
        firstAttemptCorrect: null,
        bestTime: null,
        lastSeen: null,
      };
    }
    const progress = state.progress[itemId];
    if (!Number.isFinite(progress.hinted)) progress.hinted = 0;
    return progress;
  }

  function isInManualReview(itemId) {
    return Boolean(state.manualReview[itemId]);
  }

  function getManualReviewItems() {
    return ITEMS.filter((item) => isInManualReview(item.id)).sort((first, second) => {
      const firstAddedAt = Number(state.manualReview[first.id]?.addedAt) || 0;
      const secondAddedAt = Number(state.manualReview[second.id]?.addedAt) || 0;
      return secondAddedAt - firstAddedAt;
    });
  }

  function toggleManualReview(item, addedFrom = "manual") {
    if (isInManualReview(item.id)) {
      delete state.manualReview[item.id];
      saveState();
      showToast("복습 보관함에서 뺐습니다.");
      return false;
    }
    const now = Date.now();
    state.manualReview[item.id] = { addedAt: now, addedFrom, updatedAt: now };
    saveState();
    showToast("복습 보관함에 넣었습니다.");
    return true;
  }

  function getUnseenItems() {
    return ITEMS.filter((item) => !(state.progress[item.id] && state.progress[item.id].seen)).sort(
      (first, second) => (second.learningPriority || 0) - (first.learningPriority || 0)
    );
  }

  function escapeHTML(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatSeconds(seconds) {
    if (!Number.isFinite(seconds)) return "—";
    return `${seconds.toFixed(seconds < 10 ? 1 : 0)}초`;
  }

  function normalizeAnswer(value) {
    return String(value || "")
      .normalize("NFKC")
      .normalize("NFC")
      .replace(/[\u30a1-\u30f6]/gu, (character) =>
        String.fromCodePoint(character.codePointAt(0) - 0x60)
      )
      .replace(/[\s\u3000]+/gu, "")
      .replace(/[、。！？・]/gu, "");
  }

  function levenshtein(firstValue, secondValue) {
    const first = Array.from(firstValue);
    const second = Array.from(secondValue);
    const matrix = Array.from({ length: second.length + 1 }, () => []);
    for (let i = 0; i <= second.length; i += 1) matrix[i][0] = i;
    for (let j = 0; j <= first.length; j += 1) matrix[0][j] = j;
    for (let i = 1; i <= second.length; i += 1) {
      for (let j = 1; j <= first.length; j += 1) {
        matrix[i][j] =
          second[i - 1] === first[j - 1]
            ? matrix[i - 1][j - 1]
            : Math.min(matrix[i - 1][j - 1] + 1, matrix[i - 1][j] + 1, matrix[i][j - 1] + 1);
      }
    }
    return matrix[second.length][first.length];
  }

  function gradeAnswer(item, rawAnswer) {
    const answer = normalizeAnswer(rawAnswer);
    const primaryExpected = normalizeAnswer(item.reading);
    const accepted = Array.from(
      new Set(
        [primaryExpected, ...(Array.isArray(item.acceptedReadings) ? item.acceptedReadings : [])]
          .map(normalizeAnswer)
          .filter(Boolean)
      )
    );
    const expected = primaryExpected || accepted[0] || "";
    if (!answer) return { kind: "empty", answer, expected, accepted };
    if (accepted.includes(answer)) {
      return { kind: "correct", answer, expected, accepted, matchedReading: answer };
    }

    const closest = accepted.reduce(
      (best, candidate) => {
        const distance = levenshtein(answer, candidate);
        return !best || distance < best.distance ? { candidate, distance } : best;
      },
      null
    );
    if (closest && closest.distance <= 1) {
      return { kind: "soft", answer, expected: closest.candidate, primaryExpected: expected, accepted };
    }
    return { kind: "wrong", answer, expected, accepted };
  }

  function buildReadingDiff(expectedValue, answerValue) {
    const expected = Array.from(normalizeAnswer(expectedValue));
    const answer = Array.from(normalizeAnswer(answerValue));
    const rows = expected.length + 1;
    const columns = answer.length + 1;
    const distance = Array.from({ length: rows }, () => Array(columns).fill(0));

    for (let row = 0; row < rows; row += 1) distance[row][0] = row;
    for (let column = 0; column < columns; column += 1) distance[0][column] = column;

    for (let row = 1; row < rows; row += 1) {
      for (let column = 1; column < columns; column += 1) {
        const replacementCost = expected[row - 1] === answer[column - 1] ? 0 : 1;
        distance[row][column] = Math.min(
          distance[row - 1][column - 1] + replacementCost,
          distance[row - 1][column] + 1,
          distance[row][column - 1] + 1
        );
      }
    }

    const steps = [];
    let row = expected.length;
    let column = answer.length;

    while (row > 0 || column > 0) {
      const hasDiagonal = row > 0 && column > 0;
      const isSame = hasDiagonal && expected[row - 1] === answer[column - 1];
      const isReplacement =
        hasDiagonal &&
        distance[row][column] ===
          distance[row - 1][column - 1] + (isSame ? 0 : 1);

      if (isReplacement) {
        steps.unshift({
          type: isSame ? "match" : "replace",
          actual: answer[column - 1],
          expected: expected[row - 1],
        });
        row -= 1;
        column -= 1;
      } else if (column > 0 && distance[row][column] === distance[row][column - 1] + 1) {
        steps.unshift({ type: "extra", actual: answer[column - 1], expected: "" });
        column -= 1;
      } else {
        steps.unshift({ type: "missing", actual: "", expected: expected[row - 1] });
        row -= 1;
      }
    }
    return steps;
  }

  function describeReadingDiff(steps) {
    const fixes = steps
      .filter((step) => step.type !== "match")
      .map((step) => {
        if (step.type === "replace") return step.actual + " 대신 " + step.expected;
        if (step.type === "extra") return step.actual + "는 불필요한 입력";
        return step.expected + "가 빠짐";
      });
    return fixes.length ? fixes.join(", ") : "모든 글자가 일치합니다";
  }

  function showToast(message) {
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    toastRegion.append(toast);
    window.setTimeout(() => toast.remove(), 3400);
  }

  function rankForXP(xp) {
    const ranks = [
      { name: "읽기 집중자", min: 0, next: 120 },
      { name: "반응 형성", min: 120, next: 360 },
      { name: "업무 독해자", min: 360, next: 760 },
      { name: "자동화 실무자", min: 760, next: 1400 },
      { name: "정밀 리더", min: 1400, next: 2200 },
      { name: "비즈니스 리딩 마스터", min: 2200, next: null },
    ];
    const rank = [...ranks].reverse().find((entry) => xp >= entry.min) || ranks[0];
    const progress = rank.next
      ? Math.min(100, ((xp - rank.min) / (rank.next - rank.min)) * 100)
      : 100;
    return { ...rank, progress };
  }

  function updateRankUI() {
    const rank = rankForXP(state.xp);
    document.querySelectorAll("[data-rank-name]").forEach((node) => {
      node.textContent = rank.name;
    });
    document.querySelectorAll("[data-rank-progress]").forEach((node) => {
      node.style.width = `${rank.progress}%`;
    });
    document.querySelectorAll("[data-xp-total]").forEach((node) => {
      node.textContent = state.xp.toLocaleString("ko-KR");
    });
    document.querySelectorAll("[data-xp-next]").forEach((node) => {
      node.textContent = rank.next ? (rank.next - state.xp).toLocaleString("ko-KR") : "최고 등급";
    });
  }

  function setActiveNav(view) {
    document.querySelectorAll("[data-view]").forEach((button) => {
      button.classList.toggle("is-active", button.dataset.view === view);
    });
  }

  function evaluateAchievements() {
    ACHIEVEMENTS.forEach((achievement) => {
      if (!state.achievements.includes(achievement.id) && achievement.test()) {
        state.achievements.push(achievement.id);
        window.setTimeout(() => showToast(`업적 해금 · ${achievement.title}`), 80);
      }
    });
  }

  function averageResponseTime() {
    const times = state.logs
      .filter((log) => log.kind === "correct" && !log.focusLost && Number.isFinite(log.seconds))
      .slice(0, 30)
      .map((log) => log.seconds);
    if (!times.length) return null;
    return times.reduce((sum, value) => sum + value, 0) / times.length;
  }

  function itemMastery(item) {
    const progress = state.progress[item.id];
    if (!progress || !progress.seen) return 0;
    const precision = progress.correct / progress.seen;
    const stageWeight = Math.min(progress.stage / MAX_MASTERY_STAGE, 1);
    return Math.round(Math.min(100, precision * 66 + stageWeight * 34));
  }

  function categoryMastery(category) {
    const categoryItems = ITEMS.filter((item) => item.category === category);
    const total = categoryItems.reduce((sum, item) => sum + itemMastery(item), 0);
    return Math.round(total / categoryItems.length);
  }

  function currentSessionLabel() {
    if (!activeSession) return null;
    if (activeSession.mode === "boss") return "주간 실전 라운드";
    if (activeSession.mode === "review") return "복습 보관함";
    return "새 표현 흐름";
  }

  function renderDashboard() {
    stopTimer();
    activeView = "dashboard";
    updateRankUI();
    setActiveNav(activeView);

    const unseen = getUnseenItems();
    const manualReview = getManualReviewItems();
    const learnedCount = ITEMS.length - unseen.length;
    const accuracy = state.unhintedAttempts
      ? Math.round((state.totalCorrect / state.unhintedAttempts) * 100)
      : 0;
    const responseTime = averageResponseTime();
    const continueSession = activeSession && !activeSession.finalized && activeSession.mode === "learn";
    const categoryRows = Object.entries(CATEGORY_LABELS)
      .map(([key, label]) => {
        const percentage = categoryMastery(key);
        return `
          <div class="category-row">
            <span class="category-label">${label}</span>
            <div class="bar-track" aria-label="${label} 숙련도 ${percentage}%"><span style="width: ${percentage}%"></span></div>
            <strong>${percentage}%</strong>
          </div>
        `;
      })
      .join("");
    const achievementRows = ACHIEVEMENTS.slice(0, 4)
      .map((achievement) => {
        const unlocked = state.achievements.includes(achievement.id);
        return `
          <div class="achievement ${unlocked ? "is-unlocked" : ""}">
            <span class="achievement-icon" aria-hidden="true">${achievement.icon}</span>
            <span><b>${achievement.title}</b><small>${achievement.description}</small></span>
          </div>
        `;
      })
      .join("");

    viewRoot.innerHTML = `
      <header class="page-header">
        <div>
          <p class="eyebrow">FLEXIBLE READING FLOW</p>
          <h1 class="page-title">시간 날 때, 원하는 만큼<br />업무 일본어를 읽습니다.</h1>
          <p class="page-lede">하루 목표나 대기 시간 없이, 보이는 한자에서 소리를 바로 꺼내는 흐름입니다.</p>
        </div>
        <span class="date-chip">연결함 ${learnedCount} / ${ITEMS.length}</span>
      </header>

      <div class="dashboard-grid">
        <section class="panel mission-panel" aria-labelledby="mission-title">
          <div class="mission-head"><span class="status-dot" aria-hidden="true"></span><p class="eyebrow">OPEN PRACTICE</p></div>
          <h2 id="mission-title">새 표현 <b>${unseen.length}</b>개,<br />원하는 만큼 계속 읽어 보세요.</h2>
          <p class="page-lede">자동 종료나 일일 한도는 없습니다. 멈추고 싶을 때만 학습을 마치면 됩니다.</p>
          <div class="mission-progress" aria-label="학습 흐름 현황">
            <div><span>새 표현 남음</span><strong>${unseen.length}개</strong></div>
            <div><span>직접 고른 복습</span><strong>${manualReview.length}개</strong></div>
            <div><span>누적 무힌트 정답</span><strong>${state.totalCorrect}개</strong></div>
          </div>
          <button class="primary-button" id="start-learning" type="button" ${unseen.length || continueSession ? "" : "disabled"}>
            ${continueSession ? "학습 이어하기" : unseen.length ? "새 표현 시작" : "새 표현 완료"} <span aria-hidden="true">&nbsp;→</span>
          </button>
        </section>

        <section class="quick-stats" aria-label="학습 현황">
          <article class="panel stat-panel">
            <p>READING XP</p>
            <strong>${state.xp.toLocaleString("ko-KR")}</strong>
            <small>${rankForXP(state.xp).name}</small>
          </article>
          <article class="panel stat-panel">
            <p>무힌트 정확도</p>
            <strong>${state.unhintedAttempts ? accuracy + "%" : "—"}</strong>
            <small>뜻 보기 제외</small>
          </article>
          <article class="panel stat-panel">
            <p>무힌트 평균 반응</p>
            <strong>${responseTime ? formatSeconds(responseTime) : "—"}</strong>
            <small>탭 이탈 시간 제외</small>
          </article>
        </section>
      </div>

      <div class="section-grid">
        <section class="panel section-panel" aria-labelledby="map-title">
          <div class="section-heading">
            <div><h2 id="map-title">업무 언어 역량 맵</h2><p>정확도와 누적 연결 기록이 함께 반영됩니다.</p></div>
            <button class="ghost-button" type="button" data-view="review">복습 보관함 보기</button>
          </div>
          <div class="category-list">${categoryRows}</div>
        </section>
        <section class="panel section-panel" aria-labelledby="achievement-title">
          <div class="section-heading">
            <div><h2 id="achievement-title">최근 업적</h2><p>정답 수보다 자동화를 보상합니다.</p></div>
          </div>
          <div class="achievement-list">${achievementRows}</div>
        </section>
      </div>
    `;

    document.getElementById("start-learning")?.addEventListener("click", () => {
      if (!activeSession || activeSession.finalized || activeSession.mode !== "learn") {
        startSession("learn");
      } else {
        renderQuiz();
      }
    });
    viewRoot.querySelector('[data-view="review"]')?.addEventListener("click", renderReview);
  }

  function renderReview() {
    stopTimer();
    activeView = "review";
    updateRankUI();
    setActiveNav(activeView);
    const manualReview = getManualReviewItems();
    const rows = manualReview
      .map((item) => {
        const progress = state.progress[item.id] || {};
        const retryCount = (progress.wrong || 0) + (progress.soft || 0) + (progress.hinted || 0);
        return `
          <article class="review-row">
            <div><b>${escapeHTML(item.display)}</b><p>${CATEGORY_LABELS[item.category]} · ${item.type === "sentence" ? "문장 읽기" : "단어 읽기"}</p></div>
            <div><p>최근 기록</p><strong>정답 ${progress.correct || 0} · 헷갈림 ${retryCount}</strong></div>
            <div class="review-actions"><span class="pill">직접 선택</span><button class="ghost-button review-remove" type="button" data-remove-review="${escapeHTML(item.id)}">빼기</button></div>
          </article>
        `;
      })
      .join("");

    viewRoot.innerHTML = `
      <header class="page-header">
        <div>
          <p class="eyebrow">REVIEW INBOX</p>
          <h1 class="page-title">내가 다시 읽고 싶은 표현</h1>
          <p class="page-lede">틀렸거나 헷갈렸던 표현만 직접 골라, 원할 때 다시 읽습니다.</p>
        </div>
        <span class="date-chip">보관 ${manualReview.length}개</span>
      </header>
      <div class="review-grid">
        <section class="panel section-panel">
          <div class="section-heading">
            <div><h2>내 복습 목록</h2><p>시간 제한 없이, 직접 넣은 표현만 다시 출제합니다.</p></div>
            <button class="primary-button" id="start-review" type="button" ${manualReview.length ? "" : "disabled"}>복습 시작</button>
          </div>
          ${manualReview.length ? `<div class="review-list">${rows}</div>` : `
            <div class="empty-state">
              <div><strong>아직 직접 넣은 표현이 없습니다</strong>답을 제출한 뒤 헷갈린 표현을 복습 보관함에 넣어 보세요.</div>
            </div>
          `}
        </section>
        <aside class="panel section-panel">
          <p class="eyebrow">REVIEW PRINCIPLE</p>
          <h2>필요할 때 꺼내고,<br />확실해지면 비우기</h2>
          <p class="page-lede">복습을 마쳐도 자동으로 지우지 않습니다. 충분히 익숙해졌을 때 직접 보관함에서 빼면 됩니다.</p>
          <div class="mission-mini-list">
            <div class="mission-mini"><span>완료한 복습</span><b>${state.reviewCorrect}개</b></div>
            <div class="mission-mini"><span>보관함 기준</span><b>내가 선택</b></div>
          </div>
        </aside>
      </div>
    `;

    const startReview = document.getElementById("start-review");
    if (startReview) startReview.addEventListener("click", () => startSession("review"));
    viewRoot.querySelectorAll("[data-remove-review]").forEach((button) => {
      button.addEventListener("click", () => {
        const item = ITEMS.find((candidate) => candidate.id === button.dataset.removeReview);
        if (!item) return;
        toggleManualReview(item);
        renderReview();
      });
    });
  }

  function renderBoss() {
    stopTimer();
    activeView = "boss";
    updateRankUI();
    setActiveNav(activeView);
    const thisWeek = getWeekKey();
    const cleared = state.boss.completedWeek === thisWeek;

    viewRoot.innerHTML = `
      <header class="page-header">
        <div>
          <p class="eyebrow">WEEKLY PRACTICE ROUND</p>
          <h1 class="page-title">주간 실전 라운드</h1>
          <p class="page-lede">업무 상황 속 표현을 연속으로 처리하며, 이번 주의 읽기 리듬을 점검합니다.</p>
        </div>
        <span class="date-chip">이번 주 5문항</span>
      </header>
      <section class="panel boss-stage">
        <p class="eyebrow">SCENARIO 01 · 납기 조정</p>
        <div class="boss-card">
          <h2>거래처의 납기 조정 요청에<br />정확하고 빠르게 반응하세요.</h2>
          <p>조정, 진행, 견적, 훈독 표현이 섞인 5개 문항입니다. 정답 수보다 다음 표현을 바로 읽을 수 있는지를 확인합니다.</p>
          <div class="boss-reward">
            <span class="pill">완료 보너스 40 XP</span>
            <span class="pill">완전 정답 60% 이상</span>
          </div>
          <button class="primary-button" id="start-boss" type="button" ${cleared ? "disabled" : ""}>
            ${cleared ? "이번 주 라운드 완료" : "실전 라운드 시작"} <span aria-hidden="true">&nbsp;→</span>
          </button>
        </div>
      </section>
    `;
    const startBoss = document.getElementById("start-boss");
    if (startBoss) startBoss.addEventListener("click", () => startSession("boss"));
  }

  function buildSessionEntries(mode) {
    const unseen = getUnseenItems();

    if (mode === "boss") {
      const ids = [
        "delivery-date",
        "adjustment",
        "sentence-schedule",
        "consider-based-on",
        "hinder",
      ];
      return ids
        .map((id) => ITEMS.find((item) => item.id === id))
        .filter(Boolean)
        .map((item) => ({
          item,
          source: "boss",
          hintUsed: false,
        }));
    }

    if (mode === "review") {
      return getManualReviewItems().map((item) => ({
        item,
        source: "manual-review",
        hintUsed: false,
      }));
    }

    return unseen.map((item) => ({
      item,
      source: "new",
      hintUsed: false,
    }));
  }

  function startSession(mode) {
    if (mode === "boss" && state.boss.completedWeek === getWeekKey()) {
      showToast("이번 주 실전 라운드는 이미 완료했습니다.");
      return;
    }
    const entries = buildSessionEntries(mode);
    if (!entries.length) {
      showToast("지금 바로 시작할 문항이 없습니다.");
      return;
    }
    activeSession = {
      mode,
      entries,
      index: 0,
      combo: 0,
      highestCombo: 0,
      attempts: 0,
      unhintedAttempts: 0,
      exact: 0,
      hinted: 0,
      soft: 0,
      wrong: 0,
      xpEarned: 0,
      seconds: [],
      feedback: null,
      timer: null,
      finalized: false,
      bonusXP: 0,
    };
    renderQuiz();
  }

  function stopTimer() {
    if (timerFrame) {
      window.cancelAnimationFrame(timerFrame);
      timerFrame = null;
    }
    if (activeSession?.timer && !activeSession.feedback && !activeSession.timer.pausedAt) {
      activeSession.timer.pausedAt = performance.now();
      activeSession.timer.focusLost = true;
    }
  }

  function resumeTimer() {
    const timer = activeSession?.timer;
    if (!timer || !timer.pausedAt) return;
    timer.pausedDuration += performance.now() - timer.pausedAt;
    timer.pausedAt = null;
  }

  function currentSeconds() {
    const timer = activeSession?.timer;
    if (!timer) return 0;
    const now = timer.pausedAt || performance.now();
    return Math.max(0, (now - timer.startedAt - timer.pausedDuration) / 1000);
  }

  function beginQuestionTimer() {
    const session = activeSession;
    if (!session) return;
    if (!session.timer || session.timer.questionIndex !== session.index) {
      session.timer = {
        questionIndex: session.index,
        startedAt: performance.now(),
        pausedAt: null,
        pausedDuration: 0,
        focusLost: false,
      };
    } else {
      resumeTimer();
    }
    updateTimerLoop();
  }

  function updateTimerLoop() {
    if (timerFrame) window.cancelAnimationFrame(timerFrame);
    const tick = () => {
      const timer = document.querySelector("[data-timer]");
      if (timer && activeSession && !activeSession.feedback) {
        timer.textContent = formatSeconds(currentSeconds());
        timerFrame = window.requestAnimationFrame(tick);
      }
    };
    timerFrame = window.requestAnimationFrame(tick);
  }

  function calculateXP(entry, grade, seconds, previousBest, focusLost, hintUsed) {
    if (grade.kind === "correct" && hintUsed) return 2;
    if (grade.kind === "wrong") return 0;
    if (grade.kind === "soft") return 2;

    const defaultTarget = entry.item.type === "sentence" ? 14 : 8;
    const target = Number.isFinite(previousBest) ? Math.max(3, previousBest * 1.15) : defaultTarget;
    const speedBonus = !focusLost && seconds <= target ? 4 : 0;
    const comboBonus = Math.min(Math.max(0, activeSession.combo - 1), 6);
    return 10 + speedBonus + comboBonus;
  }

  function recordAttempt(entry, grade, seconds, focusLost, hintViewed) {
    const progress = getProgress(entry.item.id);
    const previousBest = progress.bestTime;
    const isHintedCorrect = grade.kind === "correct" && hintViewed;
    const isExact = grade.kind === "correct" && !hintViewed;
    const isFirstEncounter = progress.firstAttemptCorrect === null;

    progress.seen += 1;
    progress.lastSeen = Date.now();
    state.totalAttempts += 1;
    if (!hintViewed) state.unhintedAttempts += 1;

    if (isFirstEncounter) progress.firstAttemptCorrect = isExact;

    if (isExact) {
      progress.correct += 1;
      progress.stage = Math.min(progress.stage + 1, MAX_MASTERY_STAGE);
      state.totalCorrect += 1;
      if (entry.source === "manual-review") state.reviewCorrect += 1;
      if (!focusLost && Number.isFinite(seconds)) {
        progress.bestTime = Number.isFinite(previousBest) ? Math.min(previousBest, seconds) : seconds;
      }
    } else if (isHintedCorrect) {
      progress.hinted += 1;
      progress.stage = 0;
      state.hintedCorrect += 1;
    } else {
      if (grade.kind === "soft") progress.soft += 1;
      else progress.wrong += 1;
      progress.stage = 0;
    }

    state.logs.unshift({
      itemId: entry.item.id,
      kind: isHintedCorrect ? "hinted" : grade.kind,
      seconds: Number(seconds.toFixed(2)),
      focusLost,
      hintUsed: Boolean(hintViewed),
      at: Date.now(),
      isReview: entry.source === "manual-review",
    });
    state.logs = state.logs.slice(0, 180);
    return previousBest;
  }

  function feedbackFor(grade, item, seconds, previousBest, focusLost, xp, hintUsed) {
    if (grade.kind === "correct" && hintUsed) {
      return {
        className: "is-hint",
        statusClass: "is-hint",
        label: "뜻 확인 후 정답",
        copy: "힌트 정답은 +2 XP로 기록되며, 콤보와 자동화 숙련도에는 반영하지 않습니다. 헷갈렸다면 아래에서 복습 보관함에 직접 넣어 보세요.",
        xp,
      };
    }
    if (grade.kind === "correct") {
      const faster =
        Number.isFinite(previousBest) &&
        !focusLost &&
        seconds < previousBest - 0.15;
      return {
        className: "is-correct",
        statusClass: "is-correct",
        label: "정확합니다",
        copy: faster
          ? `이전 최고 기록보다 ${(previousBest - seconds).toFixed(1)}초 빨랐습니다. 자동화 단계에 가까워졌습니다.`
          : focusLost
            ? "탭 이탈 시간은 기록에서 제외했습니다. 다음에도 정확하게 연결해 보세요."
            : "정확한 연결을 기록했습니다. 필요하면 이 표현을 직접 복습 보관함에 넣을 수 있습니다.",
        xp,
      };
    }
    if (grade.kind === "soft") {
      return {
        className: "is-wrong",
        statusClass: "is-wrong",
        label: "표기 주의",
        copy: "한 글자 또는 장음·촉음 차이를 확인해 주세요. 필요하면 복습 보관함에 직접 넣어 다시 연습할 수 있습니다.",
        xp,
      };
    }
    return {
      className: "is-wrong",
      statusClass: "is-wrong",
      label: "다시 연결하기",
      copy: "정답과 뜻을 확인했습니다. 같은 표현은 자동으로 다시 나오지 않습니다. 필요하면 복습 보관함에 직접 넣어 주세요.",
      xp,
    };
  }

  function submitAnswer() {
    if (!activeSession || activeSession.feedback || activeSession.submitting) return;
    const input = document.getElementById("answer-input");
    const answer = input?.value || "";
    if (!normalizeAnswer(answer)) {
      showToast("읽은 히라가나를 입력해 주세요.");
      input?.focus();
      return;
    }

    activeSession.submitting = true;
    const entry = activeSession.entries[activeSession.index];
    const seconds = currentSeconds();
    const focusLost = Boolean(activeSession.timer?.focusLost);
    stopTimer();
    const grade = gradeAnswer(entry.item, answer);
    const hintViewed = Boolean(entry.hintUsed);
    const isHintedCorrect = grade.kind === "correct" && hintViewed;

    if (grade.kind === "correct" && !isHintedCorrect) {
      activeSession.combo += 1;
      activeSession.exact += 1;
      activeSession.highestCombo = Math.max(activeSession.highestCombo, activeSession.combo);
      state.longestCombo = Math.max(state.longestCombo, activeSession.highestCombo);
    } else if (isHintedCorrect) {
      activeSession.hinted += 1;
    } else {
      activeSession.combo = 0;
      activeSession[grade.kind] += 1;
    }

    const progressBefore = getProgress(entry.item.id);
    const previousBest = progressBefore.bestTime;
    const xp = calculateXP(entry, grade, seconds, previousBest, focusLost, isHintedCorrect);
    const savedPreviousBest = recordAttempt(entry, grade, seconds, focusLost, hintViewed);
    state.xp += xp;
    activeSession.xpEarned += xp;
    activeSession.attempts += 1;
    if (!hintViewed) activeSession.unhintedAttempts += 1;
    if (grade.kind === "correct" && !hintViewed && !focusLost) {
      activeSession.seconds.push(seconds);
    }

    evaluateAchievements();
    saveState();

    activeSession.feedback = {
      ...feedbackFor(grade, entry.item, seconds, savedPreviousBest, focusLost, xp, isHintedCorrect),
      grade,
      seconds,
      hintUsed: hintViewed,
    };
    activeSession.submitting = false;
    updateRankUI();
    renderQuiz();
  }

  function goToNextQuestion() {
    if (!activeSession) return;
    activeSession.feedback = null;
    activeSession.timer = null;
    activeSession.index += 1;
    if (activeSession.index >= activeSession.entries.length) {
      finalizeSession();
      return;
    }
    renderQuiz();
  }

  function renderQuiz() {
    if (!activeSession) {
      renderDashboard();
      return;
    }
    if (activeSession.index >= activeSession.entries.length) {
      finalizeSession();
      return;
    }

    activeView = "quiz";
    updateRankUI();
    setActiveNav("");
    const session = activeSession;
    const entry = session.entries[session.index];
    const item = entry.item;
    const feedback = session.feedback;
    const isSentence = item.type === "sentence";
    const hintViewed = Boolean(entry.hintUsed);
    const meaningMarkup = hintViewed
      ? `<p class="input-help">뜻: ${escapeHTML(item.meaning)}</p>`
      : "";
    const hintStatusMarkup = hintViewed
      ? `<p class="hint-status" role="status">뜻 확인함 · 정답이어도 +2 XP · 콤보와 숙련도에 반영되지 않음</p>`
      : "";
    const answerArea = feedback
      ? feedbackMarkup(feedback, item)
      : `
        <form id="answer-form" novalidate>
          <div class="input-wrap">
            <input
              class="answer-input"
              id="answer-input"
              type="text"
              lang="ja"
              autocomplete="off"
              autocapitalize="off"
              spellcheck="false"
              maxlength="180"
              enterkeyhint="done"
              placeholder="히라가나로 읽기를 입력"
              aria-label="${escapeHTML(item.display)}의 일본어 읽기"
            />
            <button class="primary-button submit-button" type="submit">확인</button>
          </div>
          <div class="hint-row">
            <p class="input-help">공백·문장부호는 무시합니다.</p>
            <button class="ghost-button" id="toggle-meaning" type="button" ${hintViewed ? "disabled" : ""}>${hintViewed ? "뜻 확인함" : "뜻 보기"}</button>
          </div>
          ${meaningMarkup}
          ${hintStatusMarkup}
        </form>
      `;

    viewRoot.innerHTML = `
      <header class="page-header">
        <div>
          <p class="eyebrow">${session.mode === "boss" ? "WEEKLY PRACTICE ROUND" : "FOCUS MODE"}</p>
          <h1 class="page-title">${currentSessionLabel()}</h1>
          <p class="page-lede">뜻을 떠올리지 말고, 보이는 한자에서 소리를 바로 꺼내 보세요.</p>
        </div>
        <span class="date-chip">${session.mode === "boss" ? "실전 5문항" : session.mode === "review" ? "직접 고른 복습" : "새 표현 흐름"}</span>
      </header>

      <div class="quiz-layout">
        <section class="panel quiz-panel">
          <div class="quiz-topline">
            <span class="question-count">${session.index + 1} / ${session.entries.length}</span>
            <span class="timer" data-timer>0.0초</span>
          </div>
          <div class="question-body">
            <div>
              <p class="question-type">${isSentence ? "문장 전체 읽기" : "한자 읽기"} · ${CATEGORY_LABELS[item.category]}</p>
              <p class="kanji-prompt ${isSentence ? "is-sentence" : ""}">${escapeHTML(item.display)}</p>
              ${answerArea}
            </div>
          </div>
        </section>

        <aside class="quiz-rail" aria-label="현재 세션 현황">
          <section class="panel rail-card">
            <p class="eyebrow">FOCUS COMBO</p>
            <div class="combo-display"><strong>${session.combo}</strong><span>연속 정확</span></div>
            <p>콤보는 보너스만 더합니다. 끊겨도 누적 기록은 사라지지 않습니다.</p>
          </section>
          <section class="panel rail-card">
            <p class="eyebrow">SESSION FLOW</p>
            <div class="mission-mini-list">
              <div class="mission-mini"><span>현재 위치</span><b>${session.index + 1} / ${session.entries.length}</b></div>
              <div class="mission-mini"><span>${session.mode === "review" ? "보관한 표현" : session.mode === "boss" ? "실전 문항" : "새 표현"}</span><b>${session.entries.length}개</b></div>
              <div class="mission-mini"><span>이번 세션 정답</span><b>${session.exact}개</b></div>
            </div>
            ${session.mode === "boss" ? "" : '<button class="ghost-button session-finish" id="finish-session" type="button">학습 마치기</button>'}
          </section>
          <section class="panel rail-card">
            <p class="eyebrow">REVIEW RULE</p>
            <h3>직접 고른 표현만 복습</h3>
            <p>틀렸거나 헷갈린 표현은 답을 확인한 뒤 직접 보관함에 넣습니다. 정답이어도 직접 선택할 수 있습니다.</p>
          </section>
        </aside>
      </div>
    `;

    document.getElementById("finish-session")?.addEventListener("click", finalizeSession);

    if (!feedback) {
      beginQuestionTimer();
      const form = document.getElementById("answer-form");
      const input = document.getElementById("answer-input");
      form?.addEventListener("submit", (event) => {
        event.preventDefault();
        if (!isComposing) submitAnswer();
      });
      input?.addEventListener("compositionstart", () => {
        isComposing = true;
      });
      input?.addEventListener("compositionend", () => {
        isComposing = false;
      });
      input?.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && isComposing) event.preventDefault();
      });
      document.getElementById("toggle-meaning")?.addEventListener("click", () => {
        entry.hintUsed = true;
        showToast("뜻을 확인했습니다. 이 문항의 정답은 힌트 정답으로 기록됩니다.");
        renderQuiz();
      });
      window.setTimeout(() => input?.focus(), 30);
    } else {
      const nextButton = document.getElementById("next-question");
      nextButton?.addEventListener("click", goToNextQuestion);
      document.getElementById("toggle-manual-review")?.addEventListener("click", () => {
        const addedFrom = feedback.hintUsed ? "hinted" : feedback.grade.kind;
        toggleManualReview(item, addedFrom);
        renderQuiz();
        window.setTimeout(() => document.getElementById("toggle-manual-review")?.focus(), 0);
      });
      window.setTimeout(() => nextButton?.focus(), 30);
    }
  }

  function readingDiffMarkup(grade) {
    const steps = buildReadingDiff(grade.expected, grade.answer);
    const inputCharacters = steps
      .map((step) => {
        const className =
          step.type === "match"
            ? "is-match"
            : step.type === "missing"
              ? "is-missing-slot"
              : "is-wrong";
        const character =
          step.type === "missing"
            ? "—"
            : step.type === "match"
              ? step.actual
              : "×" + step.actual;
        const label =
          step.type === "match"
            ? "일치"
            : step.type === "missing"
              ? "입력에서 빠짐"
              : step.type === "extra"
                ? "불필요한 입력"
                : "입력 차이";
        return `<span class="diff-char ${className}" title="${label}">${escapeHTML(character)}</span>`;
      })
      .join("");
    const expectedCharacters = steps
      .map((step) => {
        const className =
          step.type === "match"
            ? "is-match"
            : step.type === "extra"
              ? "is-placeholder"
              : "is-correction";
        const character =
          step.type === "extra"
            ? "—"
            : step.type === "match"
              ? step.expected
              : step.type === "missing"
                ? "+" + step.expected
                : "→" + step.expected;
        const label =
          step.type === "match"
            ? "일치"
            : step.type === "extra"
              ? "정답에는 없음"
              : "정답에서 보완";
        return `<span class="diff-char ${className}" title="${label}">${escapeHTML(character)}</span>`;
      })
      .join("");
    const description = describeReadingDiff(steps);

    return `
      <section class="reading-diff" role="group" aria-label="입력 차이: ${escapeHTML(description)}">
        <p class="diff-heading">어디를 고치면 될까요?</p>
        <div class="diff-row">
          <span class="diff-label">내 입력</span>
          <span class="diff-value" lang="ja" aria-hidden="true">${inputCharacters}</span>
        </div>
        <div class="diff-row">
          <span class="diff-label">정답 기준</span>
          <span class="diff-value" lang="ja" aria-hidden="true">${expectedCharacters}</span>
        </div>
        <p class="sr-only" role="status">입력 차이: ${escapeHTML(description)}</p>
        <p class="diff-legend">
          <span><i class="diff-swatch is-match" aria-hidden="true"></i>일치</span>
          <span><i class="diff-swatch is-wrong" aria-hidden="true"></i>입력 차이</span>
          <span><i class="diff-swatch is-correction" aria-hidden="true"></i>정답에서 보완</span>
        </p>
      </section>
    `;
  }

  function feedbackMarkup(feedback, item) {
    const related = (Array.isArray(item.related) ? item.related : [])
      .map((word) => `<span>${escapeHTML(word)}</span>`)
      .join("");
    const meaning = String(item.meaning || "").trim() || "뜻 정보 준비 중";
    const meaningMarkup = `
      <p class="feedback-meaning">
        <span class="feedback-meaning-label">뜻</span>
        <span>${escapeHTML(meaning)}</span>
      </p>
    `;
    const diffMarkup =
      feedback.grade.kind === "correct" ? "" : readingDiffMarkup(feedback.grade);
    const retryText =
      activeSession.index + 1 >= activeSession.entries.length
        ? "세션 결과 보기"
        : "다음 표현";
    const inManualReview = isInManualReview(item.id);
    const manualReviewText = inManualReview ? "복습에서 빼기" : "복습에 넣기";
    return `
      <section class="feedback-card ${feedback.className}">
        <div class="feedback-meta">
          <span class="feedback-status ${feedback.statusClass}">${feedback.label}</span>
          <span class="answer-tag">${formatSeconds(feedback.seconds)}</span>
        </div>
        <p class="feedback-reading">${escapeHTML(item.reading)}</p>
        ${meaningMarkup}
        <p class="feedback-copy">${feedback.copy}</p>
        ${diffMarkup}
        <div class="related-words">${related}</div>
        <div class="feedback-footer">
          <div class="feedback-actions">
            <span class="xp-gain">${feedback.xp ? "+" + feedback.xp + " XP" : "XP 없음"}</span>
            <button class="ghost-button review-toggle ${inManualReview ? "is-active" : ""}" id="toggle-manual-review" type="button" aria-pressed="${inManualReview}">${manualReviewText}</button>
          </div>
          <button class="primary-button" id="next-question" type="button">${retryText} <span aria-hidden="true">&nbsp;→</span></button>
        </div>
      </section>
    `;
  }

  function finalizeSession() {
    if (!activeSession || activeSession.finalized) {
      if (activeSession) renderSessionResult();
      return;
    }
    stopTimer();
    activeSession.finalized = true;

    if (activeSession.mode === "boss") {
      const accuracy = activeSession.unhintedAttempts
        ? activeSession.exact / activeSession.unhintedAttempts
        : 0;
      if (accuracy >= 0.6 && state.boss.completedWeek !== getWeekKey()) {
        state.boss.completedWeek = getWeekKey();
        activeSession.bonusXP = 40;
        activeSession.xpEarned += 40;
        state.xp += 40;
        showToast("주간 실전 라운드 완료 · 보너스 40 XP");
      }
    }

    evaluateAchievements();
    saveState();
    updateRankUI();
    renderSessionResult();
  }

  function renderSessionResult() {
    if (!activeSession) {
      renderDashboard();
      return;
    }
    stopTimer();
    activeView = "result";
    setActiveNav("");
    const session = activeSession;
    const accuracy = session.unhintedAttempts
      ? Math.round((session.exact / session.unhintedAttempts) * 100)
      : 0;
    const average =
      session.seconds.length > 0
        ? session.seconds.reduce((sum, value) => sum + value, 0) / session.seconds.length
        : null;
    const title =
      session.mode === "boss"
        ? accuracy >= 60
          ? "이번 주 실전 라운드를 통과했습니다."
          : "실전 라운드 기록을 남겼습니다."
        : session.mode === "review"
          ? "복습 기록을 남겼습니다."
          : "학습 흐름을 마쳤습니다.";
    const lede =
      accuracy >= 80
        ? "정확한 연결이 쌓이고 있습니다. 원할 때 다시 이어서 반응 시간을 더 줄여 보세요."
        : "틀린 표현은 자동으로 다시 나오지 않습니다. 다시 보고 싶은 표현은 답안 확인 뒤 직접 복습 보관함에 넣을 수 있습니다.";

    viewRoot.innerHTML = `
      <section class="panel result-panel">
        <p class="eyebrow">SESSION REPORT</p>
        <div class="result-score">${accuracy}<small>%</small></div>
        <h2>${title}</h2>
        <p class="page-lede">${lede}</p>
        <div class="result-stats">
          <div><span>무힌트 정답</span><b>${session.exact}개</b></div>
          <div><span>힌트 정답</span><b>${session.hinted}개</b></div>
          <div><span>무힌트 평균 반응</span><b>${average ? formatSeconds(average) : "—"}</b></div>
          <div><span>획득 XP</span><b>+${session.xpEarned}</b></div>
        </div>
        ${session.bonusXP ? `<p class="xp-gain">주간 라운드 보너스 +${session.bonusXP} XP가 반영되었습니다.</p>` : ""}
        <div class="result-actions">
          <button class="primary-button" id="go-dashboard" type="button">학습 흐름으로 돌아가기</button>
          <button class="secondary-button" id="go-review" type="button">복습 보관함 보기</button>
        </div>
      </section>
    `;
    document.getElementById("go-dashboard")?.addEventListener("click", renderDashboard);
    document.getElementById("go-review")?.addEventListener("click", renderReview);
  }

  function navigate(view) {
    if (view === "dashboard") renderDashboard();
    if (view === "review") renderReview();
    if (view === "boss") renderBoss();
  }

  function handleVisibilityChange() {
    if (!activeSession || activeView !== "quiz" || activeSession.feedback) return;
    const timer = activeSession.timer;
    if (!timer) return;
    if (document.hidden) {
      if (!timer.pausedAt) {
        timer.pausedAt = performance.now();
        timer.focusLost = true;
      }
      if (timerFrame) {
        window.cancelAnimationFrame(timerFrame);
        timerFrame = null;
      }
      return;
    }
    resumeTimer();
    updateTimerLoop();
  }

  function bindGlobalEvents() {
    document.querySelectorAll("[data-view]").forEach((button) => {
      button.addEventListener("click", () => navigate(button.dataset.view));
    });
    document.querySelectorAll("[data-view-link]").forEach((link) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        navigate(link.dataset.viewLink);
      });
    });
    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("storage", (event) => {
      if (event.key !== STORAGE_KEY || !event.newValue) return;
      state = loadState();
      updateRankUI();
    });
    document.getElementById("reset-data")?.addEventListener("click", () => {
      const confirmed = window.confirm("이 브라우저에 저장된 BJT ARC 학습 기록을 초기화할까요?");
      if (!confirmed) return;
      localStorage.removeItem(STORAGE_KEY);
      state = defaultState();
      activeSession = null;
      renderDashboard();
      showToast("학습 기록을 초기화했습니다.");
    });
  }

  bindGlobalEvents();
  renderDashboard();
})();
