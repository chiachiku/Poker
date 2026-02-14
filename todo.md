# Poker Companion - TODO

> Living document. Update as tasks are completed or new ones emerge.
> Mark: `[x]` done, `[ ]` pending, `[~]` in progress

---

## POC-1: Calculation Engine

### Data Models
- [ ] Card class (rank + suit, validation, string parsing)
- [ ] Hand class (2 cards, no duplicates)
- [ ] Board class (0-5 cards, no duplicates, street detection)
- [ ] Deck class (generate 52 cards, deal, remove known cards)

### Hand Evaluator
- [ ] 5-card hand ranking (map to comparable integer)
- [ ] 7-card best hand selection (C(7,5) = 21 combos)
- [ ] Unit tests: all hand types, tie-breaking, edge cases

### Equity Calculator
- [ ] River equity (hero vs random villain, full deck enumeration)
- [ ] Turn equity (enumerate 1 remaining card + villain hands)
- [ ] Flop equity (enumerate 2 remaining cards + villain hands)
- [ ] Preflop Monte Carlo (configurable iterations + seed)
- [ ] Performance check: flop exact < 1 second
- [ ] Unit tests: known equity spots, sum to 1.0

### CLI Verification
- [ ] Simple CLI script: input cards, print equity/win/tie/lose
- [ ] Cross-check 5+ scenarios against known poker calculators

---

## POC-2: Outs & Odds

- [ ] Flush draw detection + out count
- [ ] Straight draw detection (OESD vs gutshot) + out count
- [ ] Hand type distribution across all runouts
- [ ] Pot odds calculation (callAmount / (pot + callAmount))
- [ ] EV(call) calculation
- [ ] Unit tests for all above

---

## POC-3: UI + Advice

- [ ] Streamlit app: card input (text-based)
- [ ] Display: equity, outs, distribution
- [ ] Optional input: pot, villain bet, call amount, effective stack
- [ ] Advice engine v1: rule-based action suggestion
- [ ] Advice output: action + 3-5 bullet point rationale
- [ ] Bet sizing suggestions (% of pot)

---

## Discovered / Deferred
<!-- Add items here as they come up during development -->
