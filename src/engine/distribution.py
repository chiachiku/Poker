"""Hand type distribution across all runouts.

Given hero cards + board, enumerate or sample possible runouts
and count how often hero ends up with each hand type.
"""
from __future__ import annotations
from typing import List, Dict, Optional
from itertools import combinations
import random
from src.models.card import Card
from src.models.deck import Deck
from src.engine.evaluator import _best7_fast, card_to_tuple


# Hand categories by score range
_HAND_TYPES = [
    (9_000_000, 'straight_flush'),
    (8_000_000, 'four_of_a_kind'),
    (7_000_000, 'full_house'),
    (6_000_000, 'flush'),
    (5_000_000, 'straight'),
    (4_000_000, 'three_of_a_kind'),
    (3_000_000, 'two_pair'),
    (2_000_000, 'one_pair'),
    (1_000_000, 'high_card'),
]


def _score_to_hand_type(score: int) -> str:
    """Convert a hand score to its hand type name."""
    for threshold, name in _HAND_TYPES:
        if score >= threshold:
            return name
    return 'high_card'


def hand_distribution(
    hero_cards: List[Card],
    board_cards: List[Card],
    mc_iters: Optional[int] = None,
    seed: Optional[int] = None,
) -> Dict[str, float]:
    """Calculate probability of hero ending up with each hand type.

    On river (5 board cards): exact — just evaluate hero's hand.
    On turn (4 board cards): enumerate all 46 river cards.
    On flop (3 board cards): Monte Carlo sampling.
    Preflop: Monte Carlo sampling.

    Args:
        hero_cards: Hero's 2 hole cards
        board_cards: 0-5 community cards
        mc_iters: MC iterations for flop/preflop (default 10000)
        seed: Random seed for reproducibility

    Returns:
        Dict mapping hand type names to probabilities (sum to 1.0).
        Only includes hand types with non-zero probability.
    """
    num_board = len(board_cards)

    if num_board == 5:
        return _distribution_river(hero_cards, board_cards)
    elif num_board == 4:
        return _distribution_turn(hero_cards, board_cards)
    else:
        return _distribution_mc(hero_cards, board_cards, mc_iters or 10_000, seed)


def _distribution_river(hero_cards: List[Card], board_cards: List[Card]) -> Dict[str, float]:
    """On river, hero's hand type is fixed."""
    hero_t = tuple(card_to_tuple(c) for c in hero_cards)
    board_t = tuple(card_to_tuple(c) for c in board_cards)
    score = _best7_fast(hero_t + board_t)
    hand_type = _score_to_hand_type(score)
    return {hand_type: 1.0}


def _distribution_turn(hero_cards: List[Card], board_cards: List[Card]) -> Dict[str, float]:
    """Enumerate all 46 river cards."""
    deck = Deck()
    remaining = deck.remove(hero_cards + board_cards)

    hero_t = tuple(card_to_tuple(c) for c in hero_cards)
    board_t = tuple(card_to_tuple(c) for c in board_cards)

    counts: Dict[str, int] = {}
    total = 0

    for river_card in remaining:
        river_t = card_to_tuple(river_card)
        full_board_t = board_t + (river_t,)
        score = _best7_fast(hero_t + full_board_t)
        hand_type = _score_to_hand_type(score)
        counts[hand_type] = counts.get(hand_type, 0) + 1
        total += 1

    return {ht: c / total for ht, c in sorted(counts.items(), key=lambda x: -x[1])}


def _distribution_mc(
    hero_cards: List[Card],
    board_cards: List[Card],
    iterations: int,
    seed: Optional[int],
) -> Dict[str, float]:
    """Monte Carlo distribution for flop/preflop."""
    rng = random.Random(seed)

    deck = Deck()
    remaining = deck.remove(hero_cards + board_cards)
    remaining_t = [card_to_tuple(c) for c in remaining]
    hero_t = tuple(card_to_tuple(c) for c in hero_cards)
    board_t = tuple(card_to_tuple(c) for c in board_cards)
    cards_to_come = 5 - len(board_cards)

    counts: Dict[str, int] = {}

    for _ in range(iterations):
        sample = rng.sample(remaining_t, cards_to_come)
        full_board_t = board_t + tuple(sample)
        score = _best7_fast(hero_t + full_board_t)
        hand_type = _score_to_hand_type(score)
        counts[hand_type] = counts.get(hand_type, 0) + 1

    return {ht: c / iterations for ht, c in sorted(counts.items(), key=lambda x: -x[1])}
