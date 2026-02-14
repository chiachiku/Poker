# Poker Companion

## What is this

A Texas Hold'em poker analysis tool. Core purpose: input your hole cards + community cards, get equity, outs, and actionable advice.

## Current phase: POC

We are building in 3 incremental POC steps. Each step must be **working and tested** before moving on.

### POC-1: Calculation engine (CLI)
- Card / Hand / Board data models
- Hand evaluator: 7 cards -> best 5-card hand ranking
- Equity calculation: exact enumeration (flop/turn/river), Monte Carlo (preflop)
- Validation: unit tests + CLI spot checks against known answers
- Performance target: flop/turn exact enumeration < 1 second

### POC-2: Outs, distribution, pot odds
- Outs calculation (flush draws, straight draws, OESD vs gutshot)
- Hand type distribution across all runouts
- Pot odds / EV(call) calculation (pure math, no UI)
- Validation: CLI scripts, manual cross-check

### POC-3: Minimal UI + advice engine v1
- Simple web interface (Streamlit or similar, NOT React)
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
  CLAUDE.md          # This file - project context for AI assistants
  todo.md            # Living task tracker, update as we go
  src/
    models/          # Card, Hand, Board data types
    engine/          # Evaluator, equity calculator, outs
    advisor/         # Advice engine (POC-3)
  tests/             # pytest tests, mirrors src/ structure
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
- Hand evaluator: rank each 5-card combo as a single comparable integer for fast comparison
- Equity: enumerate all remaining board cards, evaluate hero vs random villain hand
- Preflop: Monte Carlo with configurable iterations + optional seed for reproducibility
