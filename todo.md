# Poker Companion - TODO

> Living document. Update as tasks are completed or new ones emerge.

## Status marks
- `[x]` done
- `[ ]` pending
- `[~]` in progress — **must include**: `branch`, `session`, `started`

## In-progress format
When marking a task `[~]`, use this format:
```
- [~] Task description
  - branch: `feature/xxx`
  - session: `<who or session-id>`
  - started: `YYYY-MM-DD HH:MM`
```
This prevents two sessions from working on the same task, and lets anyone see who's doing what.

---

## POC-1: Calculation Engine

### Data Models
- [x] Card class (rank + suit, validation, string parsing)
- [x] Hand class (2 cards, no duplicates)
- [x] Board class (0-5 cards, no duplicates, street detection)
- [x] Deck class (generate 52 cards, deal, remove known cards)
- [x] Unit tests: 23 tests all passing

### Hand Evaluator
- [x] 5-card hand ranking (map to comparable integer)
- [x] 7-card best hand selection (C(7,5) = 21 combos)
- [x] Wheel straight bug fix (A-5 now scores as 5-high)
- [x] Unit tests: all hand types, tie-breaking, edge cases (30 tests)

### Equity Calculator
- [x] River equity (exact enumeration of villain hands)
- [x] Turn equity (exact: enumerate river card × villain hands)
- [x] Flop equity (Monte Carlo, 30k default — exact too slow in pure Python)
- [x] Preflop Monte Carlo (configurable iterations + seed)
- [x] Performance check: flop < 1 second (MC approach)
- [x] Unit tests: 20 tests (validation, known spots, sum to 1.0, seeded consistency)

### CLI Verification
- [x] Simple CLI script: input cards, print equity/win/tie/lose
- [ ] Cross-check 5+ scenarios against known poker calculators

---

## POC-2: Outs & Odds

- [x] Flush draw detection + out count (9 outs, hero participation check)
- [x] Straight draw detection (OESD vs gutshot) + out count
- [x] Combined draw deduplication (flush+straight outs merged)
- [x] Hand type distribution across all runouts (exact turn, MC flop/preflop)
- [x] Pot odds calculation (callAmount / (pot + callAmount))
- [x] EV(call) calculation + should_call decision helper
- [x] Unit tests: 46 tests (outs, odds, distribution)

---

## POC-3: UI + Advice

- [ ] Streamlit app: card input (text-based)
- [ ] Display: equity, outs, distribution
- [ ] Optional input: pot, villain bet, call amount, effective stack
- [ ] Advice engine v1: rule-based action suggestion
- [ ] Advice output: action + 3-5 bullet point rationale
- [ ] Bet sizing suggestions (% of pot)

---

## Parallel Work Plan

### Dependency graph
```
Data Models ✅
  ├── Hand Evaluator        ← 關鍵路徑, 必須先做
  │     └── Equity Calculator
  │           └── CLI Verification
  │
  ├── Outs detection (POC-2) ← 只依賴 models + evaluator, 可在 evaluator 完成後立即開始
  │
  └── Streamlit UI 骨架 (POC-3) ← 純 UI, 不依賴 engine, 可提前搭
```

### What can run in parallel (by session/branch)

| Branch | Work | Depends on | Can start |
|--------|------|------------|-----------|
| `feature/evaluator` | Hand Evaluator + tests | Data Models ✅ | **NOW** |
| `feature/ui-skeleton` | Streamlit 空殼 (card input UI, placeholder output) | Data Models ✅ | **NOW** |
| `feature/equity` | Equity Calculator + tests | evaluator merged | After evaluator |
| `feature/outs` | Outs detection + tests | evaluator merged | After evaluator |
| `feature/cli` | CLI script | equity merged | After equity |
| `feature/advice` | Advice engine | equity + outs merged | After both |

### Rules
1. **One task per session** — each session claims a task by marking `[~]` with branch/session/started
2. **Check todo.md before starting** — if someone else is `[~]` on it, pick another task
3. **Branch per feature** — never work directly on `main`
4. **Merge to main after tests pass** — PR or local merge, then mark `[x]`
5. **Update todo.md in your branch** — merge conflicts in todo.md are expected, resolve manually

---

## Discovered / Deferred
<!-- Add items here as they come up during development -->
