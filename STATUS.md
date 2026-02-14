# Poker Companion — 進度報告

> 最後更新：2026-02-14

---

## 整體進度

| 階段 | 狀態 | 完成度 |
|------|------|--------|
| POC-1：計算引擎 | 完成 | 100% |
| POC-2：Outs & Odds | 完成 | 100% |
| POC-3：UI + 建議引擎 | 接近完成 | ~90% |

---

## 已完成項目

### POC-1：計算引擎

#### Data Models（資料模型）

| 項目 | 說明 |
|------|------|
| Card class | rank + suit、驗證、字串解析（如 `Ah`、`Ks`） |
| Hand class | 2 張牌、防重複 |
| Board class | 0-5 張牌、street 偵測 |
| Deck class | 52 張牌產生、發牌、移除已知牌 |
| 單元測試 | 23 個測試全部通過 |

#### Hand Evaluator（手牌評估器）

| 項目 | 說明 |
|------|------|
| 5-card 評分 | `evaluate_5()` — 將 5 張牌映射為可比較整數 |
| 7-card 最佳手牌 | `best_hand_7()` — C(7,5)=21 種組合取最佳 |
| Prime-product 優化 | `_eval5_fast()` / `_best7_fast()` — 質數乘積做 O(1) 順子偵測，sorting network 排序 |
| Wheel straight | A-2-3-4-5 正確判定為 5-high |
| 單元測試 | 32 個測試全部通過 |

#### Equity Calculator（勝率計算器）

| 項目 | 說明 |
|------|------|
| River 精確計算 | 列舉 C(45,2) villain hands |
| Turn 精確計算 | 列舉 46 river cards x villain hands |
| Flop Monte Carlo | 30k 預設迭代（exact 在純 Python 太慢 ~45s） |
| Preflop Monte Carlo | 10k 預設迭代，獨立 `random.Random(seed)` 確保可重現 |
| 效能達標 | Flop MC < 1 秒 |
| 單元測試 | 20 個測試全部通過 |

#### CLI 驗證

| 項目 | 說明 |
|------|------|
| CLI 腳本 (`cli.py`) | 輸入牌面 → 印出 win/tie/lose 勝率 |
| 交叉驗證 | 待完成（5+ 情境 vs 已知 poker calculator） |

### POC-2：Outs & Odds

#### Outs 偵測（`src/engine/outs.py`）

| 項目 | 說明 |
|------|------|
| Flush draw 偵測 | 9 outs，含 hero 參與度檢查 |
| Straight draw 偵測 | OESD (8 outs) vs gutshot (4 outs) |
| Combined draw 去重 | flush + straight outs 合併計算，避免重複 |
| 單元測試 | 17 個測試 |

#### Hand Distribution（`src/engine/distribution.py`）

| 項目 | 說明 |
|------|------|
| 牌型分佈 | 所有 runout 的牌型出現機率 |
| Turn exact / Flop+Preflop MC | 精確列舉或 Monte Carlo |
| 單元測試 | 11 個測試 |

#### Pot Odds & EV（`src/engine/odds.py`）

| 項目 | 說明 |
|------|------|
| Pot odds | callAmount / (pot + callAmount) |
| EV(call) | 期望值計算 |
| should_call | 決策輔助函數 |
| 單元測試 | 18 個測試 |

### POC-3：UI + 建議引擎

#### Advice Engine（`src/advisor/advisor.py`）

| 項目 | 說明 |
|------|------|
| `get_advice()` | 輸入牌面 + pot/call → 回傳 action/confidence/rationale/bet_sizing |
| Decision rules v1 | 基於 equity 門檻 + outs + pot odds 的規則表 |
| Bet sizing | equity ≥80% → pot-sized, 70-80% → 3/4 pot, 60-70% → 2/3 pot, <60% → 1/2 pot |
| 單元測試 | 38 個測試全部通過 |

#### Streamlit UI（`app.py`）

| 項目 | 說明 |
|------|------|
| Card input | 文字輸入 hero cards + board cards |
| 分析顯示 | Equity、outs、hand distribution、advice 全部整合 |
| 選填欄位 | pot、call amount |
| Advice 整合 | 直接調用 `get_advice()` 顯示建議 |

---

## 未完成項目

| 項目 | 說明 | 優先序 |
|------|------|--------|
| End-to-end 測試 | Streamlit UI 整合測試 | 高 |
| CLI 交叉驗證 | 5+ 情境 vs 已知 poker calculator | 中 |

---

## 測試狀態

```
159 passed in 11.79s
```

| 測試檔案 | 測試數 | 狀態 |
|----------|--------|------|
| test_models.py | 23 | 全部通過 |
| test_evaluator.py | 32 | 全部通過 |
| test_equity.py | 20 | 全部通過 |
| test_outs.py | 17 | 全部通過 |
| test_odds.py | 18 | 全部通過 |
| test_distribution.py | 11 | 全部通過 |
| test_advisor.py | 38 | 全部通過 |
| **合計** | **159** | **全部通過** |

---

## 人員與分支

### 歷史分工紀錄

| Session | 工作項目 | 分支 | 狀態 |
|---------|----------|------|------|
| `claude-opus-session-2` | Advice engine v1 | `feature/advice-engine` | 完成 |
| `claude-opus-session-2` | Streamlit UI + integration | `feature/streamlit-ui` | 完成 |

### 可立即認領的任務

| 分支 | 工作項目 | 前置條件 |
|------|----------|----------|
| `feature/cli-verify` | CLI 交叉驗證（5+ 情境） | CLI 腳本已完成 |
| — | End-to-end 測試 | UI + advisor 已完成 |

---

## Git 歷史

```
07364bf  Add Streamlit UI with full analysis pipeline (equity, outs, distribution, advice)
52b9d15  Add advice engine v1: rule-based action suggestions (38 tests)
9ffef47  Add parallel work protocol and interface contracts
b5b9cb6  Add Chinese status report (STATUS.md)
00c7218  Add POC-2: outs detection, pot odds, hand distribution (46 tests)
e605f92  Add POC-1 completion documentation
f7dac61  Add CLI verification script for equity calculation
bb43585  Add equity calculator + optimize evaluator with prime-product trick
37985ed  Add hand evaluator with wheel straight fix and 55 passing tests
4bea236  Add POC-1 data models (Card, Deck, Hand, Board) with full test coverage
a391f60  Initial commit: Poker Companion project structure
```

Local 與 remote 同步（`origin/main` up to date）。

---

## 專案架構

```
Poker/
  CLAUDE.md              # 專案上下文 + 平行協作規範（權威來源）
  todo.md                # 任務追蹤（誰在做什麼）
  STATUS.md              # 本進度報告
  docs/
    interfaces.md        # 模組介面契約（function signature、input/output 格式）
  app.py                 # Streamlit UI 入口
  cli.py                 # CLI 驗證腳本
  src/
    models/
      card.py            # Card, Suit
      hand.py            # Hand（2 張底牌）、Board（0-5 張公牌）
      deck.py            # Deck（52 張牌）
    engine/
      evaluator.py       # 手牌評估器（evaluate_5, best_hand_7, _best7_fast）
      equity.py          # 勝率計算器（river/turn exact, flop/preflop MC）
      outs.py            # Outs 偵測（flush draw, straight draw, combined）
      odds.py            # Pot odds / EV(call) / should_call
      distribution.py    # 牌型分佈（exact + MC）
    advisor/
      advisor.py         # Advice engine v1（get_advice: rule-based）
  tests/
    test_models.py       # 23 tests
    test_evaluator.py    # 32 tests
    test_equity.py       # 20 tests
    test_outs.py         # 17 tests
    test_odds.py         # 18 tests
    test_distribution.py # 11 tests
    test_advisor.py      # 38 tests
```

---

## 關鍵架構決策

| 決策 | 說明 |
|------|------|
| Evaluator 用質數乘積 | 每個 rank 對應一個質數，5 張牌乘積可唯一辨識 rank pattern，O(1) 偵測順子 |
| Fast tuple 路徑 | `(rank, suit_id, prime)` tuple 取代 Card 物件，避免重複轉換開銷 |
| Sorting network | 9 次比較排序 5 個元素，比 Python sorted() 快 |
| Flop/Preflop 用 MC | 純 Python exact enumeration 太慢（~45s），改用 Monte Carlo（30k/10k 迭代） |
| River/Turn 用 exact | 計算量夠小（~1k / ~46k combos），精確列舉 |
| 獨立 RNG | `random.Random(seed)` 不影響全域亂數狀態 |
| Advisor v1 純規則 | equity 門檻 + outs + pot odds 的 heuristic，不用 ML |

---

## 文件地圖

> 平行工作時，所有溝通透過檔案。詳見 `CLAUDE.md` → Parallel Work Protocol。

| 文件 | 用途 | 什麼時候更新 |
|------|------|-------------|
| `CLAUDE.md` | 專案上下文 + 平行協作規範 | 規則或架構改變時 |
| `todo.md` | 任務追蹤：誰在做什麼、哪些完成了 | 認領/完成任務時 |
| `docs/interfaces.md` | 模組介面契約：function signature、input/output 格式 | 新增或修改模組公開 API 時 |
| `STATUS.md` | 本進度報告 | 里程碑完成時 |
