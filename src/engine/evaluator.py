"""Hand evaluation engine for poker hands.

Uses prime-product trick for fast rank-pattern identification
and precomputed C(7,5) indices for best-hand selection.
"""
from __future__ import annotations
from typing import List, Tuple
from src.models.card import Card


# Prime for each rank (2..14). Product of 5 primes uniquely identifies rank pattern.
_RANK_PRIMES = {
    2: 2, 3: 3, 4: 5, 5: 7, 6: 11, 7: 13, 8: 17,
    9: 19, 10: 23, 11: 29, 12: 31, 13: 37, 14: 41,
}

# Precompute all C(7,5) = 21 index combinations
_COMBO_7_5 = (
    (0,1,2,3,4), (0,1,2,3,5), (0,1,2,3,6), (0,1,2,4,5), (0,1,2,4,6),
    (0,1,2,5,6), (0,1,3,4,5), (0,1,3,4,6), (0,1,3,5,6), (0,1,4,5,6),
    (0,2,3,4,5), (0,2,3,4,6), (0,2,3,5,6), (0,2,4,5,6), (0,3,4,5,6),
    (1,2,3,4,5), (1,2,3,4,6), (1,2,3,5,6), (1,2,4,5,6), (1,3,4,5,6),
    (2,3,4,5,6),
)

# Precompute straight detection via prime product -> high card
_STRAIGHTS = {}
for _high in range(5, 15):  # 5-high through 14(A)-high
    if _high == 5:
        _ranks_tuple = (14, 5, 4, 3, 2)  # wheel
    else:
        _ranks_tuple = tuple(range(_high, _high - 5, -1))
    _product = 1
    for _r in _ranks_tuple:
        _product *= _RANK_PRIMES[_r]
    _STRAIGHTS[_product] = 5 if _high == 5 else _high


def _eval5_fast(r0, r1, r2, r3, r4, suits_same, prime_product):
    """Ultra-fast 5-card evaluator.

    Ranks must be sorted descending: r0 >= r1 >= r2 >= r3 >= r4.
    """
    # All 5 unique ranks?
    if r0 != r1 and r1 != r2 and r2 != r3 and r3 != r4:
        # No pairs — check straight flush, flush, straight, high card
        straight_high = _STRAIGHTS.get(prime_product)
        if suits_same:
            if straight_high is not None:
                return 9_000_000 + straight_high  # straight flush
            return 6_000_000 + r0 * 50625 + r1 * 3375 + r2 * 225 + r3 * 15 + r4  # flush
        if straight_high is not None:
            return 5_000_000 + straight_high  # straight
        return 1_000_000 + r0 * 50625 + r1 * 3375 + r2 * 225 + r3 * 15 + r4  # high card

    # Has at least one pair — determine pattern from sorted ranks
    # (can't be flush or straight with duplicate ranks)

    if r0 == r1:
        if r1 == r2:
            if r2 == r3:
                # AAAA x -> quads
                return 8_000_000 + r0 * 100 + r4
            if r3 == r4:
                # AAA BB -> full house
                return 7_000_000 + r0 * 100 + r3
            # AAA x y -> trips
            return 4_000_000 + r0 * 10000 + r3 * 15 + r4
        if r2 == r3:
            if r3 == r4:
                # AA BBB -> full house
                return 7_000_000 + r2 * 100 + r0
            # AA BB x -> two pair
            return 3_000_000 + r0 * 10000 + r2 * 100 + r4
        if r3 == r4:
            # AA x YY -> two pair
            return 3_000_000 + r0 * 10000 + r3 * 100 + r2
        # AA x y z -> one pair
        return 2_000_000 + r0 * 10000 + r2 * 225 + r3 * 15 + r4

    if r1 == r2:
        if r2 == r3:
            if r3 == r4:
                # x BBBB -> quads
                return 8_000_000 + r1 * 100 + r0
            # x BBB y -> trips
            return 4_000_000 + r1 * 10000 + r0 * 15 + r4
        if r3 == r4:
            # x BB YY -> two pair
            return 3_000_000 + r1 * 10000 + r3 * 100 + r0
        # x BB y z -> one pair
        return 2_000_000 + r1 * 10000 + r0 * 225 + r3 * 15 + r4

    if r2 == r3:
        if r3 == r4:
            # x y CCC -> trips
            return 4_000_000 + r2 * 10000 + r0 * 15 + r1
        # x y CC z -> one pair
        return 2_000_000 + r2 * 10000 + r0 * 225 + r1 * 15 + r4

    # r3 == r4 (guaranteed since we have at least one pair and above didn't match)
    # x y z DD -> one pair
    return 2_000_000 + r3 * 10000 + r0 * 225 + r1 * 15 + r2


def _best7_fast(cards) -> int:
    """Find best 5-card hand from 7 (rank, suit_id, prime) tuples."""
    best = 0
    for a, b, c, d, e in _COMBO_7_5:
        ca, cb, cc, cd, ce = cards[a], cards[b], cards[c], cards[d], cards[e]

        # Extract ranks
        ra, rb, rc, rd, re = ca[0], cb[0], cc[0], cd[0], ce[0]

        # Sort 5 elements descending via sorting network (9 comparisons)
        if ra < rb: ra, rb = rb, ra; ca, cb = cb, ca
        if rd < re: rd, re = re, rd; cd, ce = ce, cd
        if ra < rc: ra, rc = rc, ra; ca, cc = cc, ca
        if rb < rc: rb, rc = rc, rb; cb, cc = cc, cb
        if ra < rd: ra, rd = rd, ra; ca, cd = cd, ca
        if rc < rd: rc, rd = rd, rc; cc, cd = cd, cc
        if rb < re: rb, re = re, rb; cb, ce = ce, cb
        if rb < rc: rb, rc = rc, rb; cb, cc = cc, cb
        if rd < re: rd, re = re, rd; cd, ce = ce, cd

        suits_same = (ca[1] == cb[1] == cc[1] == cd[1] == ce[1])
        prime_product = ca[2] * cb[2] * cc[2] * cd[2] * ce[2]

        score = _eval5_fast(ra, rb, rc, rd, re, suits_same, prime_product)
        if score > best:
            best = score

    return best


def card_to_tuple(card: Card) -> Tuple[int, int, int]:
    """Convert Card to (rank, suit_id, prime) tuple for fast evaluation."""
    return (card.rank, card.suit.value, _RANK_PRIMES[card.rank])


def cards_to_tuples(cards: List[Card]) -> Tuple:
    """Convert list of Cards to tuple of (rank, suit_id, prime) tuples."""
    return tuple(card_to_tuple(c) for c in cards)


# --- Public API (Card-based, for tests and external use) ---

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

    tuples = cards_to_tuples(cards)
    ranks_sorted = sorted((t[0] for t in tuples), reverse=True)
    suits_same = len(set(t[1] for t in tuples)) == 1
    prime_product = tuples[0][2] * tuples[1][2] * tuples[2][2] * tuples[3][2] * tuples[4][2]

    return _eval5_fast(
        ranks_sorted[0], ranks_sorted[1], ranks_sorted[2],
        ranks_sorted[3], ranks_sorted[4],
        suits_same, prime_product
    )


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
    return _best7_fast(cards_to_tuples(cards))
