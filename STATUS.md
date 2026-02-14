# Poker Companion — 進度報告

> 最後更新：2026-02-14

---

## 整體進度

| 階段 | 狀態 | 完成度 |
|------|------|--------|
| POC-1：計算引擎 (Calculation Engine) | 完成 | 100% |
| POC-2：Outs & Odds | 完成 | 100% |
| POC-3：UI + 建議引擎 | 未開始 | 0% |

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
| 單元測試 | 30 個測試全部通過（涵蓋全部牌型、tiebreaker、edge cases） |

#### Equity Calculator（勝率計算器）

| 項目 | 說明 |
|------|------|
| River 精確計算 | 列舉 C(45,2) villain hands |
| Turn 精確計算 | 列舉 46 river cards x villain hands |
| Flop Monte Carlo | 30k 預設迭代（exact 在純 Python 太慢 ~45s） |
| Preflop Monte Carlo | 10k 預設迭代，可設定 seed 確保可重現 |
| 效能達標 | Flop MC < 1 秒 |
| 單元測試 | 21 個測試全部通過（驗證、已知勝率、機率總和=1.0、seed 一致性） |

#### CLI 驗證

| 項目 | 說明 |
|------|------|
| CLI 腳本 | 輸入牌面 → 印出 win/tie/lose 勝率 |
| 交叉驗證 | 待完成（5+ 情境 vs 已知 poker calculator） |

### POC-2：Outs & Odds

#### Outs 偵測（`src/engine/outs.py`）

| 項目 | 說明 |
|------|------|
| Flush draw 偵測 | 9 outs，含 hero 參與度檢查 |
| Straight draw 偵測 | OESD (8 outs) vs gutshot (4 outs) |
| Combined draw 去重 | flush + straight outs 合併計算，避免重複 |

#### Hand Distribution（`src/engine/distribution.py`）

| 項目 | 說明 |
|------|------|
| 牌型分佈 | 所有 runout 的牌型出現機率 |
| Turn exact | 精確列舉 |
| Flop / Preflop MC | Monte Carlo 模擬 |

#### Pot Odds & EV（`src/engine/odds.py`）

| 項目 | 說明 |
|------|------|
| Pot odds | callAmount / (pot + callAmount) |
| EV(call) | 期望值計算 |
| should_call | 決策輔助函數 |

#### 單元測試

| 項目 | 說明 |
|------|------|
| test_outs.py | outs 偵測相關測試 |
| test_odds.py | pot odds / EV 測試 |
| test_distribution.py | 牌型分佈測試 |
| 合計 | 46 個測試全部通過 |

---

## 測試狀態

```
121 passed in 6.73s
```

| 測試檔案 | 測試數 | 狀態 |
|----------|--------|------|
| test_models.py | 23 | 全部通過 |
| test_evaluator.py | 30 | 全部通過 |
| test_equity.py | 22 | 全部通過 |
| test_outs.py | — | 全部通過 |
| test_odds.py | — | 全部通過 |
| test_distribution.py | — | 全部通過 |
| **合計** | **121** | **全部通過** |

---

## 接下來：POC-3

| 優先序 | 任務 | 預估工作量 | 備註 |
|--------|------|-----------|------|
| 1 | Streamlit UI 骨架 | 中 | card input（文字輸入）、placeholder output |
| 2 | 顯示：equity、outs、distribution | 中 | 接上已完成的 engine |
| 3 | 選填欄位：pot、villain bet、call amount、effective stack | 小 | |
| 4 | Advice engine v1 | 中 | 規則式建議（基於 equity + outs + pot odds） |
| 5 | 建議輸出格式 | 小 | action + 3-5 bullet point 理由 |
| 6 | Bet sizing 建議 | 小 | % of pot |

### 剩餘 POC-1 收尾

| 任務 | 說明 |
|------|------|
| CLI 交叉驗證 | 5+ 情境 vs 已知 poker calculator |

---

## 人員與分支

### 目前分工

目前 todo.md 中無任何 `[~]` 進行中任務，所有工作已 commit 到 `main`。

### 可立即認領的任務

| 分支 | 工作項目 | 前置條件 |
|------|----------|----------|
| `feature/ui-skeleton` | Streamlit UI 骨架 | 無（models + engine 已完成） |
| `feature/advice` | Advice engine v1 | 無（equity + outs 已完成） |
| `feature/cli-verify` | CLI 交叉驗證 | 無（CLI 腳本已完成） |

---

## Git 歷史

```
00c7218  Add POC-2: outs detection, pot odds, hand distribution (46 tests)
e605f92  Add POC-1 completion documentation
f7dac61  Add CLI verification script for equity calculation
bb43585  Add equity calculator + optimize evaluator with prime-product trick
37985ed  Add hand evaluator with wheel straight fix and 55 passing tests
4bea236  Add POC-1 data models (Card, Deck, Hand, Board) with full test coverage
a391f60  Initial commit: Poker Companion project structure
```

**未 push 的 commit**：1 個（`main` 領先 `origin/main` 1 個 commit）

---

## 專案架構

```
Poker/
  CLAUDE.md              # AI 助理上下文
  todo.md                # 任務追蹤（即時更新）
  STATUS.md              # 本進度報告
  src/
    models/
      card.py            # Card class
      hand.py            # Hand class（2 張底牌）
      deck.py            # Deck class（52 張牌）
    engine/
      evaluator.py       # 手牌評估器（5-card / 7-card + fast tuple 版本）
      equity.py          # 勝率計算器（river/turn exact, flop/preflop MC）
      outs.py            # Outs 偵測（flush draw, straight draw, combined）
      odds.py            # Pot odds / EV(call) / should_call
      distribution.py    # 牌型分佈（exact + MC）
    advisor/             #（POC-3 才會用到）
  tests/
    test_models.py       # 23 tests
    test_evaluator.py    # 30 tests
    test_equity.py       # 22 tests
    test_outs.py         # outs 測試
    test_odds.py         # odds 測試
    test_distribution.py # distribution 測試
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
