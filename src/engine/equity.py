"""Equity calculation engine for poker hands.

Strategy:
- River (5 board cards): exact enumeration of villain hands
- Turn (4 board cards): exact enumeration of river card + villain hands
- Flop (3 board cards): Monte Carlo (exact is too slow in pure Python)
- Preflop (0 board cards): Monte Carlo
"""
from __future__ import annotations
from typing import List, Dict, Optional, Tuple
from itertools import combinations
import random
from src.models.card import Card
from src.models.deck import Deck
from src.engine.evaluator import _best7_fast, card_to_tuple


def equity_vs_random(
    hero_cards: List[Card],
    board_cards: List[Card],
    mc_iters: Optional[int] = None,
    seed: Optional[int] = None
) -> Dict[str, float]:
    """Calculate hero's equity against a random villain hand.

    Uses exact enumeration for river/turn and Monte Carlo for flop/preflop.

    Args:
        hero_cards: Hero's 2 hole cards
        board_cards: 0-5 community cards
        mc_iters: Monte Carlo iterations (default: 10000 preflop, 30000 flop).
                  Ignored for river/turn (exact enumeration).
        seed: Random seed for Monte Carlo (for reproducibility)

    Returns:
        Dictionary with keys 'win', 'tie', 'lose' (values sum to ~1.0)

    Raises:
        ValueError: If hero_cards is not 2 cards or board_cards is invalid
    """
    if len(hero_cards) != 2:
        raise ValueError(f"hero_cards must be exactly 2 cards, got {len(hero_cards)}")
    if len(board_cards) > 5:
        raise ValueError(f"board_cards cannot exceed 5 cards, got {len(board_cards)}")

    num_board = len(board_cards)

    if num_board == 5:
        return _equity_river_exact(hero_cards, board_cards)
    elif num_board == 4:
        return _equity_turn_exact(hero_cards, board_cards)
    elif num_board == 3:
        return _equity_mc(hero_cards, board_cards, mc_iters or 30_000, seed)
    elif num_board == 0:
        return _equity_mc(hero_cards, board_cards, mc_iters or 10_000, seed)
    else:
        raise ValueError(f"Invalid board state: {num_board} cards. Expected 0, 3, 4, or 5.")


def _to_tuples(cards: List[Card]) -> List[Tuple[int, int, int]]:
    """Convert Card list to list of (rank, suit_id, prime) tuples."""
    return [card_to_tuple(c) for c in cards]


def _equity_river_exact(hero_cards: List[Card], board_cards: List[Card]) -> Dict[str, float]:
    """Exact equity on river. Enumerate all C(45,2) villain combos."""
    deck = Deck()
    remaining = deck.remove(hero_cards + board_cards)

    hero_t = tuple(_to_tuples(hero_cards))
    board_t = tuple(_to_tuples(board_cards))
    remaining_t = [card_to_tuple(c) for c in remaining]

    hero_score = _best7_fast(hero_t + board_t)

    wins = 0
    ties = 0
    losses = 0

    for v1, v2 in combinations(remaining_t, 2):
        villain_score = _best7_fast((v1, v2) + board_t)
        if hero_score > villain_score:
            wins += 1
        elif hero_score == villain_score:
            ties += 1
        else:
            losses += 1

    total = wins + ties + losses
    return {'win': wins / total, 'tie': ties / total, 'lose': losses / total}


def _equity_turn_exact(hero_cards: List[Card], board_cards: List[Card]) -> Dict[str, float]:
    """Exact equity on turn. Enumerate river card x villain combos."""
    deck = Deck()
    known = hero_cards + board_cards
    remaining = deck.remove(known)

    hero_t = tuple(_to_tuples(hero_cards))
    board_t = tuple(_to_tuples(board_cards))
    remaining_t = [card_to_tuple(c) for c in remaining]

    wins = 0
    ties = 0
    losses = 0

    for i, river_t in enumerate(remaining_t):
        full_board_t = board_t + (river_t,)
        hero_score = _best7_fast(hero_t + full_board_t)

        villain_pool = remaining_t[:i] + remaining_t[i+1:]
        for v1, v2 in combinations(villain_pool, 2):
            villain_score = _best7_fast((v1, v2) + full_board_t)
            if hero_score > villain_score:
                wins += 1
            elif hero_score == villain_score:
                ties += 1
            else:
                losses += 1

    total = wins + ties + losses
    return {'win': wins / total, 'tie': ties / total, 'lose': losses / total}


def _equity_mc(
    hero_cards: List[Card],
    board_cards: List[Card],
    iterations: int,
    seed: Optional[int],
) -> Dict[str, float]:
    """Monte Carlo equity for flop and preflop.

    Samples random completions of the board + random villain hands.
    """
    rng = random.Random(seed)

    deck = Deck()
    known = hero_cards + board_cards
    remaining = deck.remove(known)
    remaining_t = [card_to_tuple(c) for c in remaining]
    hero_t = tuple(_to_tuples(hero_cards))
    board_t = tuple(_to_tuples(board_cards))
    cards_to_come = 5 - len(board_cards)
    # We need: cards_to_come board cards + 2 villain cards
    sample_size = cards_to_come + 2

    wins = 0
    ties = 0
    losses = 0

    for _ in range(iterations):
        sample = rng.sample(remaining_t, sample_size)
        full_board_t = board_t + tuple(sample[:cards_to_come])
        villain_t = (sample[cards_to_come], sample[cards_to_come + 1])

        hero_score = _best7_fast(hero_t + full_board_t)
        villain_score = _best7_fast(villain_t + full_board_t)

        if hero_score > villain_score:
            wins += 1
        elif hero_score == villain_score:
            ties += 1
        else:
            losses += 1

    return {'win': wins / iterations, 'tie': ties / iterations, 'lose': losses / iterations}
