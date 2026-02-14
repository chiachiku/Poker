# Module Interface Contracts（模組介面契約）

> **用途：** 記錄所有模組的公開 API，讓平行工作的 session 知道可以依賴什麼、不能隨便改什麼。
>
> **規則：** 修改任何已列出的 function signature 或回傳格式前，先在這裡標 `⚠️ BREAKING`，更新所有呼叫端，跑全部測試。
>
> 最後更新：2026-02-14

---

## models.card

### Class: `Suit` (Enum)
```python
class Suit(Enum):
    HEARTS = 'h'
    DIAMONDS = 'd'
    CLUBS = 'c'
    SPADES = 's'
```

### Class: `Card`
```python
Card(rank: int, suit: Suit)
```
- `rank`: 2-14（2=2, ..., 10=T, 11=J, 12=Q, 13=K, 14=A）
- `suit`: Suit enum

| Method | Signature | 說明 |
|--------|-----------|------|
| `from_string` | `(card_str: str) -> Card` | 解析字串，如 `"Ah"` → Card(14, HEARTS) |
| `__repr__` | `() -> str` | 標準記法，如 `"Ah"` |
| `__eq__`, `__hash__` | — | 支援比較與集合操作 |

**使用方：** evaluator, equity, outs, odds, distribution, advisor, streamlit UI

---

## models.hand

### Class: `Hand`
```python
Hand(cards: List[Card])
```
- 必須恰好 2 張牌，不可重複
- Raises `ValueError` if invalid

### Class: `Board`
```python
Board(cards: List[Card])
```
- 0-5 張牌，不可重複
- Raises `ValueError` if invalid

| Property/Method | Signature | 說明 |
|----------------|-----------|------|
| `street` | `@property -> str` | `'preflop'` / `'flop'` / `'turn'` / `'river'` |

**使用方：** streamlit UI (input validation)

---

## models.deck

### Class: `Deck`
```python
Deck()
```

| Method | Signature | 說明 |
|--------|-----------|------|
| `remove` | `(cards_to_remove: List[Card]) -> List[Card]` | 回傳移除後的剩餘牌（不改變原 deck） |
| `__len__` | `() -> int` | 牌數 |

**使用方：** equity, outs, distribution

---

## engine.evaluator

### `evaluate_5(cards: List[Card]) -> int`
- 將 5 張牌評為一個整數分數（越高越好）
- 編碼：`category * 10^6 + tiebreaker`
- Categories: 9=Straight Flush, 8=Quads, 7=Full House, 6=Flush, 5=Straight, 4=Trips, 3=Two Pair, 2=One Pair, 1=High Card
- Raises `ValueError` if not exactly 5 cards

### `best_hand_7(cards: List[Card]) -> int`
- 從 7 張牌中找最佳 5 張的分數
- C(7,5)=21 種組合取最大值
- Raises `ValueError` if not exactly 7 cards

### `card_to_tuple(card: Card) -> Tuple[int, int, int]`
- 轉換為 `(rank, suit_id, prime)` tuple（供 fast path 使用）

### `cards_to_tuples(cards: List[Card]) -> Tuple`
- 批次轉換

**使用方：** equity, outs, distribution

---

## engine.equity

### `equity_vs_random(hero_cards, board_cards, mc_iters=None, seed=None) -> Dict[str, float]`

```python
def equity_vs_random(
    hero_cards: List[Card],     # 恰好 2 張
    board_cards: List[Card],    # 0, 3, 4, 或 5 張
    mc_iters: Optional[int],    # MC 迭代次數（preflop 預設 10k, flop 預設 30k）
    seed: Optional[int],        # 亂數種子（reproducibility）
) -> Dict[str, float]
```

**Output format:**
```python
{"win": float, "tie": float, "lose": float}
# 三者加總 ≈ 1.0
```

**策略：**
| Board cards | Method |
|-------------|--------|
| 5 (river) | Exact enumeration |
| 4 (turn) | Exact enumeration |
| 3 (flop) | Monte Carlo (30k default) |
| 0 (preflop) | Monte Carlo (10k default) |

**使用方：** odds (should_call), distribution, advisor, streamlit UI

---

## engine.outs

### `detect_draws(hero_cards: List[Card], board_cards: List[Card]) -> Dict`

**Output format:**
```python
{
    "flush_draw": {                    # or None if no flush draw
        "suit": str,                   # e.g. "h"
        "outs": int,                   # e.g. 9
        "hero_cards_in_suit": int,     # hero 有幾張是這個花色
        "out_cards_rs": List[str],     # e.g. ["Ah", "9h", ...]
    },
    "straight_draws": [                # list, 可能多個 or 空
        {
            "type": str,               # "oesd" or "gutshot"
            "outs": int,               # 8 (oesd) or 4 (gutshot)
            "target_ranks": List[int],  # 可以完成順子的 rank
        }
    ],
    "total_outs": int,                 # 去重後的總 outs 數
    "out_cards": List[Tuple[int, str]], # (rank, suit) sorted by rank desc
}
```

### `count_outs(hero_cards: List[Card], board_cards: List[Card]) -> int`
- 簡化 API：只回傳去重後的 out 總數

**使用方：** advisor, streamlit UI

---

## engine.odds

### `pot_odds(pot: float, call_amount: float) -> float`
- 公式：`call_amount / (pot + call_amount)`
- 回傳值在 [0, 1]，代表需要的最低 equity
- Raises `ValueError` if pot < 0 or call_amount <= 0

### `ev_call(pot: float, call_amount: float, equity: float) -> float`
- 公式：`equity * (pot + call_amount) - call_amount`
- 正值 = 有利可圖
- Raises `ValueError` if inputs invalid

### `should_call(pot: float, call_amount: float, equity: float) -> Dict`

**Output format:**
```python
{
    "pot_odds": float,     # 需要的最低 equity
    "equity": float,       # hero 的 equity
    "ev": float,           # 期望值
    "profitable": bool,    # True if EV > 0
    "edge": float,         # equity - pot_odds（正 = 好 call）
}
```

**使用方：** advisor, streamlit UI

---

## engine.distribution

### `hand_distribution(hero_cards, board_cards, mc_iters=None, seed=None) -> Dict[str, float]`

```python
def hand_distribution(
    hero_cards: List[Card],
    board_cards: List[Card],
    mc_iters: Optional[int],    # 預設 10000
    seed: Optional[int],
) -> Dict[str, float]
```

**Output format:**
```python
{
    "straight_flush": float,     # 只包含機率 > 0 的牌型
    "four_of_a_kind": float,
    "full_house": float,
    "flush": float,
    "straight": float,
    "three_of_a_kind": float,
    "two_pair": float,
    "one_pair": float,
    "high_card": float,
}
# 所有值加總 = 1.0
```

**使用方：** advisor, streamlit UI

---

## advisor

### `get_advice(hero_cards, board_cards, pot=None, call_amount=None, mc_iters=None, seed=None) -> Dict`

```python
def get_advice(
    hero_cards: List[Card],     # 恰好 2 張
    board_cards: List[Card],    # 0, 3, 4, 或 5 張
    pot: Optional[float],       # 底池大小（可選）
    call_amount: Optional[float], # 跟注金額（可選）
    mc_iters: Optional[int],    # MC 迭代次數（傳給 equity_vs_random）
    seed: Optional[int],        # 亂數種子（reproducibility）
) -> Dict
```

> **與預計介面的差異：** 新增了 `mc_iters` 和 `seed` 參數，用於控制 equity 計算的精度和重現性。非 breaking change（新增可選參數）。

**Output format:**
```python
{
    "action": str,             # "fold" / "call" / "raise"
    "confidence": str,         # "strong" / "moderate" / "marginal"
    "rationale": List[str],    # 2-5 bullet points（equity summary + draw info + pot odds + decision reason）
    "bet_sizing": Optional[float],  # raise 時建議的 bet size（pot 的比例，0.50-1.0）；fold/call 時為 None
}
```

**Decision rules（v1 heuristic）：**

| Rule | Condition | Action | Confidence |
|------|-----------|--------|------------|
| 1 | equity ≥ 70% | raise | strong |
| 2 | equity 55-70% | raise | moderate |
| 3 | equity 35-55%, outs ≥ 4, +EV | call | moderate |
| 3b | equity 35-55%, outs ≥ 4, −EV | fold | marginal |
| 4 | equity 35-55%, no draws, +EV | call | marginal |
| 4b | equity 35-55%, no draws, −EV | fold | marginal |
| 5 | equity < 35%, outs ≥ 8, +EV | call | marginal |
| 5b | equity < 35%, otherwise | fold | strong |

**Bet sizing（raise 時）：**

| Equity | Sizing (fraction of pot) |
|--------|--------------------------|
| ≥ 80% | 1.0 (pot-sized) |
| 70-80% | 0.75 (3/4 pot) |
| 60-70% | 0.66 (2/3 pot) |
| < 60% | 0.50 (1/2 pot) |

**使用方：** streamlit UI

---

## Changelog

| 日期 | 模組 | 變更 | Breaking? |
|------|------|------|-----------|
| 2026-02-14 | all | 初始版本：記錄所有已完成模組的公開 API | — |
| 2026-02-14 | advisor | 實作 get_advice v1：新增 mc_iters/seed 參數（相對預計介面） | No（新增可選參數） |
