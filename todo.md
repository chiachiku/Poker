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

### Streamlit UI (`feature/streamlit-ui`)
- [ ] Streamlit app 骨架: card input (text-based)
- [ ] Display: equity, outs, distribution (接 engine)
- [ ] Optional input: pot, villain bet, call amount, effective stack

### Advice Engine (`feature/advice-engine`)
- [x] Advice engine v1: rule-based action suggestion
  - branch: `feature/advice-engine`
  - session: `claude-opus-session-2`
  - completed: `2026-02-14`
- [x] Advice output: action + 3-5 bullet point rationale
- [x] Bet sizing suggestions (% of pot)
- [x] Unit tests for advice engine (38 tests)

### Integration (`feature/streamlit-integration`)
- [ ] 把 advice engine 接進 Streamlit UI
- [ ] End-to-end 測試

### Remaining POC-1
- [ ] Cross-check 5+ scenarios against known poker calculators (`feature/cli-verify`)

---

## Parallel Work Plan (POC-3)

> 完整規則見 `CLAUDE.md` → Parallel Work Protocol
> 模組介面見 `docs/interfaces.md`

### Dependency graph
```
POC-1 ✅  POC-2 ✅
  │         │
  ├─────────┤
  │         │
  ▼         ▼
Streamlit UI ◄──────── 不依賴 advisor，可以先用 placeholder
  │
  │    Advice Engine ◄─ 依賴 equity + outs（已完成）
  │         │
  ▼         ▼
Streamlit Integration ◄── 需要 UI + advice 都完成
```

### What can run in parallel NOW

| Branch | Work | Depends on | Can start |
|--------|------|------------|-----------|
| `feature/streamlit-ui` | Streamlit 骨架 + card input + 顯示 | models + engine ✅ | **NOW** |
| `feature/advice-engine` | Advice engine v1 (rule-based) | equity + outs ✅ | **NOW** |
| `feature/cli-verify` | CLI cross-check vs known calculators | CLI script ✅ | **NOW** |
| `feature/streamlit-integration` | 把 advice engine 接進 UI | ui + advice merged | After both |

### Rules
1. **One task per session** — 認領時在 todo.md 標 `[~]` + branch/session/started
2. **Check todo.md first** — 有人 `[~]` 就換一個做
3. **Branch per feature** — 不直接改 `main`
4. **Merge after tests pass** — 測試通過才 merge，然後標 `[x]`
5. **Update interfaces** — 改了公開 API → 更新 `docs/interfaces.md`
6. **Breaking change** — 在 `docs/interfaces.md` 標 `⚠️ BREAKING`，commit message 加 `BREAKING:`

---

## Discovered / Deferred
<!-- Add items here as they come up during development -->
