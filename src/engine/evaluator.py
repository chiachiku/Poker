"""Hand evaluation engine for poker hands."""
from __future__ import annotations
from typing import List
from itertools import combinations
from collections import Counter
from src.models.card import Card


def evaluate_5(cards: List[Card]) -> int:
    """Evaluate a 5-card hand and return a numerical score.

    Higher scores beat lower scores. Encoding: category * 10^6 + tiebreaker

    Categories:
        9 = Straight Flush
        8 = Four of a Kind (Quads)
        7 = Full House
        6 = Flush
        5 = Straight
        4 = Three of a Kind (Trips/Set)
        3 = Two Pair
        2 = One Pair
        1 = High Card

    Args:
        cards: Exactly 5 Card objects

    Returns:
        Integer score (higher is better)

    Raises:
        ValueError: If not exactly 5 cards
    """
    if len(cards) != 5:
        raise ValueError(f"evaluate_5 requires exactly 5 cards, got {len(cards)}")

    ranks = sorted([c.rank for c in cards], reverse=True)
    suits = [c.suit for c in cards]
    rank_counts = Counter(ranks)
    count_values = sorted(rank_counts.values(), reverse=True)

    is_flush = len(set(suits)) == 1
    is_straight = _is_straight(ranks)

    # Straight Flush (including Royal Flush)
    if is_flush and is_straight:
        return 9_000_000 + _straight_high(ranks)

    # Four of a Kind
    if count_values == [4, 1]:
        quad_rank = [r for r, c in rank_counts.items() if c == 4][0]
        kicker = [r for r, c in rank_counts.items() if c == 1][0]
        return 8_000_000 + quad_rank * 100 + kicker

    # Full House
    if count_values == [3, 2]:
        trips_rank = [r for r, c in rank_counts.items() if c == 3][0]
        pair_rank = [r for r, c in rank_counts.items() if c == 2][0]
        return 7_000_000 + trips_rank * 100 + pair_rank

    # Flush
    if is_flush:
        return 6_000_000 + _encode_kickers(ranks)

    # Straight
    if is_straight:
        return 5_000_000 + _straight_high(ranks)

    # Three of a Kind
    if count_values == [3, 1, 1]:
        trips_rank = [r for r, c in rank_counts.items() if c == 3][0]
        kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)
        return 4_000_000 + trips_rank * 10000 + _encode_kickers(kickers)

    # Two Pair
    if count_values == [2, 2, 1]:
        pairs = sorted([r for r, c in rank_counts.items() if c == 2], reverse=True)
        kicker = [r for r, c in rank_counts.items() if c == 1][0]
        return 3_000_000 + pairs[0] * 10000 + pairs[1] * 100 + kicker

    # One Pair
    if count_values == [2, 1, 1, 1]:
        pair_rank = [r for r, c in rank_counts.items() if c == 2][0]
        kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)
        return 2_000_000 + pair_rank * 10000 + _encode_kickers(kickers)

    # High Card
    return 1_000_000 + _encode_kickers(ranks)


def best_hand_7(cards: List[Card]) -> int:
    """Evaluate best 5-card hand from 7 cards.

    Tries all C(7,5) = 21 combinations and returns the best score.

    Args:
        cards: Exactly 7 Card objects

    Returns:
        Best hand score

    Raises:
        ValueError: If not exactly 7 cards
    """
    if len(cards) != 7:
        raise ValueError(f"best_hand_7 requires exactly 7 cards, got {len(cards)}")

    max_score = 0
    for combo in combinations(cards, 5):
        score = evaluate_5(list(combo))
        max_score = max(max_score, score)

    return max_score


def _straight_high(ranks: List[int]) -> int:
    """Return the high card of a straight.

    For wheel (A-2-3-4-5), the high card is 5, not Ace.

    Args:
        ranks: List of 5 ranks, sorted descending. Must be a valid straight.

    Returns:
        The high card rank of the straight.
    """
    if ranks == [14, 5, 4, 3, 2]:
        return 5
    return ranks[0]


def _is_straight(ranks: List[int]) -> bool:
    """Check if sorted ranks form a straight.

    Handles both regular straights and the wheel (A-2-3-4-5).

    Args:
        ranks: List of 5 ranks, sorted in descending order

    Returns:
        True if straight, False otherwise
    """
    # Regular straight: consecutive ranks
    if ranks[0] - ranks[4] == 4 and len(set(ranks)) == 5:
        return True

    # Wheel (A-2-3-4-5): special case
    if ranks == [14, 5, 4, 3, 2]:
        return True

    return False


def _encode_kickers(kickers: List[int]) -> int:
    """Encode kicker ranks into a single integer for tie-breaking.

    Uses base-15 encoding since ranks go from 2-14.

    Args:
        kickers: List of kicker ranks (sorted high to low)

    Returns:
        Encoded integer
    """
    result = 0
    for kicker in kickers:
        result = result * 15 + kicker
    return result
