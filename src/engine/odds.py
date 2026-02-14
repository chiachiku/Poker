"""Pot odds and EV calculation for poker decisions."""
from __future__ import annotations
from typing import Dict, Optional


def pot_odds(pot: float, call_amount: float) -> float:
    """Calculate pot odds as a ratio.

    Pot odds = call_amount / (pot + call_amount)
    This is the minimum equity needed to break even on a call.

    Args:
        pot: Current pot size (before hero's call)
        call_amount: Amount hero needs to call

    Returns:
        Pot odds as a float in [0, 1]

    Raises:
        ValueError: If pot or call_amount is negative, or call_amount is 0
    """
    if pot < 0:
        raise ValueError(f"Pot cannot be negative, got {pot}")
    if call_amount <= 0:
        raise ValueError(f"Call amount must be positive, got {call_amount}")

    return call_amount / (pot + call_amount)


def ev_call(pot: float, call_amount: float, equity: float) -> float:
    """Calculate expected value of calling.

    EV(call) = equity * (pot + call_amount) - call_amount
             = equity * pot_after_call - call_amount

    Positive EV means calling is profitable in the long run.

    Args:
        pot: Current pot size (before hero's call)
        call_amount: Amount hero needs to call
        equity: Hero's win probability (0-1). Ties are typically counted as
                half a win: equity = win_rate + tie_rate/2

    Returns:
        Expected value of calling (positive = profitable)

    Raises:
        ValueError: If inputs are invalid
    """
    if pot < 0:
        raise ValueError(f"Pot cannot be negative, got {pot}")
    if call_amount <= 0:
        raise ValueError(f"Call amount must be positive, got {call_amount}")
    if not 0 <= equity <= 1:
        raise ValueError(f"Equity must be between 0 and 1, got {equity}")

    return equity * (pot + call_amount) - call_amount


def should_call(pot: float, call_amount: float, equity: float) -> Dict:
    """Determine if calling is profitable and by how much.

    Args:
        pot: Current pot size
        call_amount: Amount to call
        equity: Hero's equity (win + tie/2)

    Returns:
        Dict with:
            'pot_odds': float — minimum equity needed
            'equity': float — hero's equity
            'ev': float — expected value of calling
            'profitable': bool — True if EV > 0
            'edge': float — equity minus pot odds (positive = good call)
    """
    po = pot_odds(pot, call_amount)
    ev = ev_call(pot, call_amount, equity)

    return {
        'pot_odds': po,
        'equity': equity,
        'ev': ev,
        'profitable': ev > 0,
        'edge': equity - po,
    }
