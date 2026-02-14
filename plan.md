# POC-1 Implementation Plan

## Overview
Build the core calculation engine: data models + hand evaluator + equity calculator. All validated via pytest, no UI.

## Step 1: Data Models (`src/models/`)

### `src/models/card.py`
- `Card` dataclass: `rank` (int 2-14), `suit` (enum h/d/c/s)
- Parse from string notation: `"Ah"` → Card(14, hearts)
- `__eq__`, `__hash__`, `__repr__` for comparison and display
- Validation: reject invalid rank/suit

### `src/models/deck.py`
- `Deck` class: generates all 52 cards
- `remove(cards)` → return remaining cards (for enumeration)
- No shuffle needed (we enumerate, not deal randomly)

### `src/models/hand.py`
- `Hand`: holds 2 hole cards, validates no duplicates
- `Board`: holds 0-5 community cards, validates no duplicates, detects street (preflop/flop/turn/river)

### `src/__init__.py`, `src/models/__init__.py`
- Package init files for imports

### Tests: `tests/test_models.py`
- Card parsing, invalid input rejection
- Hand/Board duplicate detection
- Board street detection
- Deck card removal

## Step 2: Hand Evaluator (`src/engine/evaluator.py`)

### Core logic
- `evaluate_5(cards) -> int`: rank a 5-card hand as a single integer
  - Encoding: `category * 10^6 + tiebreaker`
  - Categories: 1=high card, 2=pair, 3=two pair, 4=trips, 5=straight, 6=flush, 7=full house, 8=quads, 9=straight flush
  - Tiebreaker: kicker values packed into remaining digits
- `best_hand_7(cards) -> int`: try all C(7,5)=21 combos, return max score

### Tests: `tests/test_evaluator.py`
- One test per hand type (royal flush down to high card)
- Tie-breaking tests (e.g. higher pair wins)
- 7-card selection tests (correct 5 picked from 7)

## Step 3: Equity Calculator (`src/engine/equity.py`)

### Core logic
- `equity_vs_random(hero_cards, board_cards, mc_iters=None, seed=None) -> dict`
  - Returns `{"win": float, "tie": float, "lose": float}`
  - If board has 5 cards (river): enumerate all villain 2-card combos from remaining deck
  - If board has 4 cards (turn): enumerate 1 river card × all villain combos
  - If board has 3 cards (flop): enumerate 2 cards (turn+river) × all villain combos
  - If board has 0 cards (preflop): Monte Carlo sampling
- Internal: for each scenario, compare `best_hand_7(hero)` vs `best_hand_7(villain)`

### Tests: `tests/test_equity.py`
- River: known matchup spot checks
- Flop/Turn: verify win+tie+lose ≈ 1.0, check against known equity values
- Performance: flop enumeration < 1 second
- Monte Carlo: seeded run produces consistent results

## Step 4: CLI Verification Script

### `cli.py` (project root)
- Simple argparse script: `python cli.py --hero "Ah Ks" --board "2d 7d Jc"`
- Prints equity results formatted nicely
- Used for manual spot checks, not production code

## File creation order
1. `src/__init__.py`, `src/models/__init__.py`, `src/engine/__init__.py`
2. `src/models/card.py` + `tests/test_models.py` → run tests
3. `src/models/deck.py` + `src/models/hand.py` → extend tests → run tests
4. `src/engine/evaluator.py` + `tests/test_evaluator.py` → run tests
5. `src/engine/equity.py` + `tests/test_equity.py` → run tests
6. `cli.py` → manual verification
