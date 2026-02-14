# Poker Companion

## What is this

A Texas Hold'em poker analysis tool. Core purpose: input your hole cards + community cards, get equity, outs, and actionable advice.

## Current phase: POC-3

POC-1 (calculation engine) and POC-2 (outs & odds) are **complete**. We are now building POC-3.

### POC-1: Calculation engine (CLI) — COMPLETE
- Card / Hand / Board data models
- Hand evaluator: 7 cards -> best 5-card hand ranking
- Equity calculation: exact (river/turn), Monte Carlo (flop/preflop)
- Validation: unit tests + CLI spot checks
- Performance: flop MC < 1 second

### POC-2: Outs, distribution, pot odds — COMPLETE
- Outs calculation (flush draws, straight draws, OESD vs gutshot)
- Hand type distribution across all runouts
- Pot odds / EV(call) calculation
- 46 tests all passing

### POC-3: Minimal UI + advice engine v1 — IN PROGRESS
- Simple web interface (Streamlit, NOT React)
- Input: hole cards, community cards, pot/bet amounts (optional)
- Output: equity, outs, distribution, rule-based action advice
- Advice engine v1: heuristic rules based on equity + outs + pot odds

## Not doing yet (post-POC)
- Opponent hand / range input
- Full REST API (FastAPI)
- React frontend
- OCR / screen reading
- GTO solver
- Multi-player / cloud

## Tech stack
- Language: Python 3.12+
- No framework needed for POC-1/2, Streamlit for POC-3
- Testing: pytest
- No frontend/backend split until post-POC

## Project structure

```
Poker/
  CLAUDE.md              # This file — project context + parallel work rules (權威來源)
  todo.md                # Living task tracker (誰在做什麼)
  STATUS.md              # 中文進度報告
  docs/
    interfaces.md        # 模組介面契約 (interface contracts)
  src/
    models/              # Card, Hand, Board data types
    engine/              # Evaluator, equity, outs, odds, distribution
    advisor/             # Advice engine (POC-3)
  tests/                 # pytest tests, mirrors src/ structure
```

## Conventions
- All card notation: rank + suit lowercase, e.g. `Ah`, `Ks`, `2d`, `Tc`
  - Ranks: 2,3,4,5,6,7,8,9,T,J,Q,K,A
  - Suits: h(hearts), d(diamonds), c(clubs), s(spades)
- Keep modules small and focused, one responsibility per file
- Every piece of logic gets a test before moving on
- Use type hints throughout
- Commit after each meaningful milestone

## Key design decisions
- Hand evaluator: prime-product trick for O(1) straight detection, sorting network for 5-element sort
- Cards converted to `(rank, suit_id, prime)` tuples at boundaries for speed
- Equity: river/turn exact enumeration, flop/preflop Monte Carlo (30k/10k default)
- `_best7_fast` ~10.5μs/call in pure Python — bottleneck for equity
- Independent `random.Random(seed)` for reproducibility without polluting global RNG

---

## Parallel Work Protocol（平行協作規範）

> **所有 session（人或 AI）開始工作前，必須讀這一段。**

### 核心原則

1. **不重複做** — 開工前先讀 `todo.md`，確認沒有人在做同一件事
2. **有介面就寫文件** — 模組之間的介面契約寫在 `docs/interfaces.md`
3. **人人知道文件在哪** — 所有共用文件的位置寫在下面的「文件地圖」

### 文件地圖

| 文件 | 用途 | 什麼時候更新 |
|------|------|-------------|
| `CLAUDE.md` | 專案上下文 + 平行協作規範 | 規則或架構改變時 |
| `todo.md` | 任務追蹤：誰在做什麼、哪些完成了 | 認領/完成任務時 |
| `docs/interfaces.md` | 模組介面契約：function signature、input/output 格式 | 新增或修改模組公開 API 時 |
| `STATUS.md` | 中文進度報告 | 里程碑完成時 |

### 認領任務流程

```
1. 讀 todo.md → 找到一個 [ ] (pending) 的任務
2. 確認沒有人標 [~]（in-progress）在做同一個
3. 將該任務改為 [~]，填入 metadata：
   - [~] Task description
     - branch: `feature/xxx`
     - session: `<你的 session id 或名字>`
     - started: `YYYY-MM-DD HH:MM`
4. 建立 feature branch，開始工作
5. 完成後：
   a. 所有測試通過
   b. 如果改了公開 API → 更新 docs/interfaces.md
   c. 標記 [x]
   d. Merge 到 main
```

### 介面契約規則

**什麼時候要寫介面文件：**
- 新增一個其他模組會 import 的 function
- 修改已有 function 的 signature（參數名稱、型別、回傳值）
- 修改回傳資料的 format（例如 dict 的 key 改名）

**寫在哪裡：** `docs/interfaces.md`

**格式範例：**
```markdown
## engine.equity

### equity_vs_random(hero_cards, board_cards, mc_iters=None, seed=None) -> dict
- Input: hero_cards: List[Card] (2張), board_cards: List[Card] (0/3/4/5張)
- Output: {"win": float, "tie": float, "lose": float}  (sum ≈ 1.0)
- 使用方: advisor, streamlit UI
```

**破壞性變更（breaking change）的處理：**
1. 先在 `docs/interfaces.md` 標注 `⚠️ BREAKING` 並說明變了什麼
2. 更新所有呼叫端的程式碼
3. 跑全部測試確認沒壞
4. Commit message 中標注 `BREAKING:`

### 分支規則

| 規則 | 說明 |
|------|------|
| 一人一分支 | 每個 session 在自己的 `feature/xxx` branch 上工作 |
| 不直接改 main | 所有變更透過 merge（測試通過後） |
| 衝突自己解 | `todo.md` 的 merge conflict 是預期行為，手動解決 |
| Commit 訊息要清楚 | 格式：`Add/Fix/Update <what> (<scope>)` |

### 如何溝通（沒有 Slack 的情況下）

所有溝通透過 **檔案**，不透過口頭約定：

| 我要說什麼 | 寫在哪裡 |
|------------|---------|
| 「我正在做 X」 | `todo.md` → 標 `[~]` |
| 「X 完成了」 | `todo.md` → 標 `[x]` |
| 「這個 function 的 API 長這樣」 | `docs/interfaces.md` |
| 「我發現了一個問題 / 新需求」 | `todo.md` → Discovered / Deferred 區 |
| 「我做了一個架構決策」 | `CLAUDE.md` → Key design decisions |
| 「這個變更會影響你」 | `docs/interfaces.md` → 標 `⚠️ BREAKING` |

### POC-3 平行工作表

```
Streamlit UI ←──── 不依賴 advisor，可以先用 placeholder
     │
     ├── feature/streamlit-ui     可以馬上開始
     │
Advice Engine ←── 依賴 equity + outs（已完成）
     │
     ├── feature/advice-engine    可以馬上開始
     │
CLI 交叉驗證 ←── 獨立工作
     │
     └── feature/cli-verify       可以馬上開始
```

| Branch | Work | Depends on | Can start |
|--------|------|------------|-----------|
| `feature/streamlit-ui` | Streamlit app 骨架 + card input + 顯示 | models + engine (done) | **NOW** |
| `feature/advice-engine` | Advice engine v1 (rule-based) | equity + outs (done) | **NOW** |
| `feature/cli-verify` | CLI cross-check vs known calculators | CLI script (done) | **NOW** |
| `feature/streamlit-integration` | 把 advice engine 接進 UI | ui + advice merged | After both |
