"""Outs detection and counting for poker draws.

Analyzes hero's hole cards + board to identify:
- Flush draws (4 to a flush)
- Straight draws (OESD and gutshot)
- Combined draw outs (deduplicated)
"""
from __future__ import annotations
from typing import List, Dict
from collections import Counter
from src.models.card import Card, Suit


def detect_draws(hero_cards: List[Card], board_cards: List[Card]) -> Dict:
    """Detect all draws for hero given current board.

    Only meaningful on flop (3 cards) or turn (4 cards).
    On river or preflop, returns empty draws.

    Args:
        hero_cards: Hero's 2 hole cards
        board_cards: 0-5 community cards

    Returns:
        Dict with keys:
            'flush_draw': dict or None — {suit, outs, cards_held}
            'straight_draws': list of dicts — [{type, outs, target_ranks, ...}]
            'total_outs': int — deduplicated count of all out cards
            'out_cards': list of Card descriptions that improve the hand
    """
    all_cards = hero_cards + board_cards
    num_board = len(board_cards)

    result = {
        'flush_draw': None,
        'straight_draws': [],
        'total_outs': 0,
        'out_cards': [],
    }

    # Only detect draws on flop/turn
    if num_board not in (3, 4):
        return result

    out_ranks_and_suits = set()  # track (rank, suit) to deduplicate

    # --- Flush draw detection ---
    flush_info = _detect_flush_draw(hero_cards, board_cards)
    if flush_info:
        result['flush_draw'] = flush_info
        for rank, suit in flush_info['out_cards_rs']:
            out_ranks_and_suits.add((rank, suit))

    # --- Straight draw detection ---
    straight_draws = _detect_straight_draws(hero_cards, board_cards)
    if straight_draws:
        result['straight_draws'] = straight_draws
        for draw in straight_draws:
            for rank in draw['target_ranks']:
                # Straight outs: any suit that isn't already in known cards
                for suit in Suit:
                    card = (rank, suit)
                    if card not in {(c.rank, c.suit) for c in all_cards}:
                        out_ranks_and_suits.add(card)

    result['total_outs'] = len(out_ranks_and_suits)
    result['out_cards'] = sorted(out_ranks_and_suits, key=lambda x: (-x[0], x[1].value))

    return result


def _detect_flush_draw(hero_cards: List[Card], board_cards: List[Card]) -> dict | None:
    """Detect flush draw (exactly 4 cards to a flush).

    Returns None if no flush draw, or dict with draw info.
    """
    all_cards = hero_cards + board_cards
    suit_counts = Counter(c.suit for c in all_cards)

    for suit, count in suit_counts.items():
        if count == 4:
            # 4 to a flush — need 1 more
            # How many cards of that suit held by hero?
            hero_suited = sum(1 for c in hero_cards if c.suit == suit)
            if hero_suited == 0:
                continue  # board-only flush draw, hero doesn't benefit

            # Count remaining cards of that suit in deck
            known_ranks = {c.rank for c in all_cards if c.suit == suit}
            out_cards = []
            for rank in range(2, 15):
                if rank not in known_ranks:
                    out_cards.append((rank, suit))

            return {
                'suit': suit,
                'outs': len(out_cards),
                'hero_cards_in_suit': hero_suited,
                'out_cards_rs': out_cards,
            }

    return None


def _detect_straight_draws(hero_cards: List[Card], board_cards: List[Card]) -> List[dict]:
    """Detect straight draws (OESD and gutshot).

    Looks at all 7 possible 5-card straight windows (A-5 through T-A)
    and checks if hero+board have exactly 4 of the 5 ranks needed.

    Only counts draws where at least one hero card participates.

    Returns list of draw dicts, each with:
        type: 'oesd' or 'gutshot'
        target_ranks: list of ranks that complete the straight
        outs: number of outs for this draw (target_ranks * 4 minus known cards)
    """
    all_cards = hero_cards + board_cards
    all_ranks = {c.rank for c in all_cards}
    hero_ranks = {c.rank for c in hero_cards}
    known_cards = {(c.rank, c.suit) for c in all_cards}

    draws = []
    seen_targets = set()  # avoid duplicate draw reports

    # All possible 5-rank straight windows
    windows = []
    # Wheel: A-2-3-4-5
    windows.append((14, 2, 3, 4, 5))
    # Regular: 2-6 through T-A
    for low in range(2, 11):
        windows.append(tuple(range(low, low + 5)))

    for window in windows:
        window_set = set(window)
        held = window_set & all_ranks
        missing = window_set - all_ranks

        if len(held) != 4 or len(missing) != 1:
            continue

        # At least one hero card must participate in the straight
        if not (hero_ranks & window_set):
            continue

        target_rank = missing.pop()

        # Avoid reporting same target rank twice
        if target_rank in seen_targets:
            continue
        seen_targets.add(target_rank)

        # Count actual outs (4 suits minus any known cards of that rank)
        outs = sum(1 for s in Suit if (target_rank, s) not in known_cards)

        draws.append({
            'target_ranks': [target_rank],
            'outs': outs,
        })

    # Classify draws: check if hero has OESD
    # OESD = two different single-card completions on both ends of a run
    # Simpler approach: if we have 2+ straight draw targets, it's likely OESD
    # But the correct way: look for 4 consecutive ranks in held cards
    _classify_draws(draws, all_ranks, hero_ranks)

    return draws


def _classify_draws(draws: List[dict], all_ranks: set, hero_ranks: set):
    """Classify each draw as 'oesd' or 'gutshot'.

    OESD (Open-Ended Straight Draw): 4 consecutive ranks, missing either end.
    Gutshot: missing an interior rank.
    """
    for draw in draws:
        target = draw['target_ranks'][0]

        # Check if the 4 held ranks form a consecutive sequence
        # For each window containing the target, check if the other 4 are consecutive
        is_oesd = False

        # A draw is OESD if the target is at either end of the straight window
        # Check all windows that contain the target rank
        windows = []
        windows.append((14, 2, 3, 4, 5))
        for low in range(2, 11):
            windows.append(tuple(range(low, low + 5)))

        for window in windows:
            if target not in window:
                continue
            window_list = list(window)
            held_in_window = [r for r in window_list if r in all_ranks]
            if len(held_in_window) != 4:
                continue
            # target is at position 0 or 4 (ends) → OESD
            idx = window_list.index(target)
            if idx == 0 or idx == 4:
                is_oesd = True
                break

        draw['type'] = 'oesd' if is_oesd else 'gutshot'


def count_outs(hero_cards: List[Card], board_cards: List[Card]) -> int:
    """Simple API: return total deduplicated out count.

    Args:
        hero_cards: Hero's 2 hole cards
        board_cards: Community cards (3 or 4)

    Returns:
        Number of unique out cards
    """
    return detect_draws(hero_cards, board_cards)['total_outs']
