"""Rule-based advice engine for poker decisions (v1).

Heuristic rules based on:
- Equity vs random opponent
- Outs (flush/straight draws)
- Pot odds / EV (when pot and bet amounts are provided)

Outputs an action recommendation with rationale.
"""
from __future__ import annotations
from typing import List, Dict, Optional

from src.models.card import Card
from src.engine.equity import equity_vs_random
from src.engine.outs import detect_draws
from src.engine.odds import pot_odds, ev_call


def get_advice(
    hero_cards: List[Card],
    board_cards: List[Card],
    pot: Optional[float] = None,
    call_amount: Optional[float] = None,
    mc_iters: Optional[int] = None,
    seed: Optional[int] = None,
) -> Dict:
    """Generate rule-based action advice.

    Args:
        hero_cards: Hero's 2 hole cards.
        board_cards: 0-5 community cards.
        pot: Current pot size (optional).
        call_amount: Amount to call (optional).
        mc_iters: MC iterations for equity calc.
        seed: Random seed for reproducibility.

    Returns:
        Dict with keys:
            action: "fold" / "call" / "raise"
            confidence: "strong" / "moderate" / "marginal"
            rationale: List[str] — 3-5 bullet points
            bet_sizing: Optional[float] — suggested raise as fraction of pot (e.g. 0.75)
    """
    # --- Gather data ---
    equity_result = equity_vs_random(hero_cards, board_cards, mc_iters=mc_iters, seed=seed)
    equity = equity_result['win'] + equity_result['tie'] / 2

    draws = detect_draws(hero_cards, board_cards)
    total_outs = draws['total_outs']
    flush_draw = draws['flush_draw']
    straight_draws = draws['straight_draws']

    num_board = len(board_cards)
    street = _street_name(num_board)

    # --- Pot odds analysis (if available) ---
    has_pot_info = pot is not None and call_amount is not None and call_amount > 0
    po = None
    ev = None
    if has_pot_info:
        po = pot_odds(pot, call_amount)
        ev = ev_call(pot, call_amount, equity)

    # --- Rule engine ---
    rationale = []
    action, confidence, bet_sizing = _decide(
        equity=equity,
        total_outs=total_outs,
        flush_draw=flush_draw,
        straight_draws=straight_draws,
        street=street,
        pot_odds_val=po,
        ev_val=ev,
        has_pot_info=has_pot_info,
        rationale=rationale,
    )

    return {
        'action': action,
        'confidence': confidence,
        'rationale': rationale,
        'bet_sizing': bet_sizing,
    }


def _street_name(num_board: int) -> str:
    """Map board card count to street name."""
    return {0: 'preflop', 3: 'flop', 4: 'turn', 5: 'river'}.get(num_board, 'unknown')


def _decide(
    equity: float,
    total_outs: int,
    flush_draw,
    straight_draws: list,
    street: str,
    pot_odds_val: Optional[float],
    ev_val: Optional[float],
    has_pot_info: bool,
    rationale: list,
) -> tuple:
    """Core decision logic. Returns (action, confidence, bet_sizing).

    Mutates `rationale` list in-place to add bullet points.
    """
    eq_pct = equity * 100

    # --- Rationale: equity summary ---
    rationale.append(f"Equity vs random: {eq_pct:.1f}%")

    # --- Rationale: draws ---
    if flush_draw:
        rationale.append(f"Flush draw ({flush_draw['outs']} outs)")
    for sd in straight_draws:
        label = "OESD" if sd['type'] == 'oesd' else "Gutshot"
        rationale.append(f"{label} straight draw ({sd['outs']} outs)")
    if total_outs > 0 and not flush_draw and not straight_draws:
        rationale.append(f"{total_outs} draw outs")

    # --- Rationale: pot odds ---
    if has_pot_info:
        rationale.append(f"Pot odds: need {pot_odds_val * 100:.1f}%, have {eq_pct:.1f}% → EV = {ev_val:+.1f}")

    # ========================================
    # RULE 1: Strong hand (equity >= 70%)
    # ========================================
    if equity >= 0.70:
        bet_sizing = _raise_sizing(equity)
        rationale.append("Strong hand — raise for value")
        return ('raise', 'strong', bet_sizing)

    # ========================================
    # RULE 2: Good hand (equity 55-70%)
    # ========================================
    if equity >= 0.55:
        if has_pot_info and ev_val is not None and ev_val > 0:
            bet_sizing = _raise_sizing(equity)
            rationale.append("Good equity + positive EV — raise")
            return ('raise', 'moderate', bet_sizing)
        else:
            rationale.append("Good equity — raise or call")
            return ('raise', 'moderate', _raise_sizing(equity))

    # ========================================
    # RULE 3: Drawing hand (equity 35-55%, has outs)
    # ========================================
    if equity >= 0.35 and total_outs >= 4:
        if has_pot_info:
            if ev_val is not None and ev_val > 0:
                rationale.append("Drawing hand with good pot odds — call")
                return ('call', 'moderate', None)
            else:
                rationale.append("Drawing hand but pot odds unfavorable — fold or call small")
                return ('fold', 'marginal', None)
        else:
            rationale.append("Drawing hand with outs — call to see next card")
            return ('call', 'moderate', None)

    # ========================================
    # RULE 4: Decent equity but no draws (35-55%)
    # ========================================
    if equity >= 0.35:
        if has_pot_info and ev_val is not None and ev_val > 0:
            rationale.append("Decent equity + positive EV — call")
            return ('call', 'marginal', None)
        elif has_pot_info:
            rationale.append("Decent equity but negative EV — fold")
            return ('fold', 'marginal', None)
        else:
            rationale.append("Marginal hand — proceed with caution")
            return ('call', 'marginal', None)

    # ========================================
    # RULE 5: Weak hand (equity < 35%)
    # ========================================
    if total_outs >= 8:
        # Strong draw (e.g. flush draw) even with low equity
        if has_pot_info and ev_val is not None and ev_val > 0:
            rationale.append("Weak equity but strong draw with good odds — call")
            return ('call', 'marginal', None)
        elif not has_pot_info:
            rationale.append("Weak equity but strong draw — consider calling")
            return ('call', 'marginal', None)

    rationale.append("Weak hand — fold")
    return ('fold', 'strong', None)


def _raise_sizing(equity: float) -> float:
    """Suggest raise size as fraction of pot based on equity.

    Higher equity → larger bet for value.
    """
    if equity >= 0.80:
        return 1.0    # pot-sized bet
    elif equity >= 0.70:
        return 0.75   # 3/4 pot
    elif equity >= 0.60:
        return 0.66   # 2/3 pot
    else:
        return 0.50   # half pot
