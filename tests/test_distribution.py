"""Tests for hand type distribution."""
import pytest
from src.models.card import Card
from src.engine.distribution import hand_distribution


def _parse_cards(card_strings: str) -> list:
    return [Card.from_string(s) for s in card_strings.split()]


class TestDistributionRiver:
    """On river, distribution is deterministic."""

    def test_river_flush(self):
        hero = _parse_cards("Ah Kh")
        board = _parse_cards("Qh Jh 9h 2d 3c")
        dist = hand_distribution(hero, board)
        assert dist == {'flush': 1.0}

    def test_river_straight(self):
        hero = _parse_cards("Ah Kd")
        board = _parse_cards("Qh Jc Tc 2d 3h")
        dist = hand_distribution(hero, board)
        assert dist == {'straight': 1.0}

    def test_river_pair(self):
        hero = _parse_cards("Ah 2d")
        board = _parse_cards("Ac 9s 7h 4d 3c")
        dist = hand_distribution(hero, board)
        assert dist == {'one_pair': 1.0}


class TestDistributionTurn:
    """On turn, exact enumeration of river cards."""

    def test_turn_probabilities_sum_to_one(self):
        hero = _parse_cards("Ah Kh")
        board = _parse_cards("Qh 7h 3d 2c")
        dist = hand_distribution(hero, board)
        total = sum(dist.values())
        assert abs(total - 1.0) < 1e-9

    def test_turn_flush_draw_probability(self):
        """With 4 hearts, ~19.6% chance of making flush on river (9/46)."""
        hero = _parse_cards("Ah Kh")
        board = _parse_cards("Qh 7h 3d 2c")
        dist = hand_distribution(hero, board)
        # Should have some flush probability
        assert 'flush' in dist
        assert abs(dist['flush'] - 9/46) < 1e-9

    def test_turn_has_multiple_outcomes(self):
        hero = _parse_cards("Ah Kd")
        board = _parse_cards("Qh Jc 9s 2d")
        dist = hand_distribution(hero, board)
        # Should have multiple hand types
        assert len(dist) > 1


class TestDistributionFlop:
    """On flop, uses Monte Carlo."""

    def test_flop_probabilities_sum_to_one(self):
        hero = _parse_cards("Ah Kh")
        board = _parse_cards("Qh 7h 3d")
        dist = hand_distribution(hero, board, seed=42)
        total = sum(dist.values())
        assert abs(total - 1.0) < 1e-9

    def test_flop_seeded_consistency(self):
        hero = _parse_cards("Ah Kd")
        board = _parse_cards("Qh Jc Tc")
        d1 = hand_distribution(hero, board, seed=42)
        d2 = hand_distribution(hero, board, seed=42)
        assert d1 == d2

    def test_flop_set_distribution(self):
        """Flopped set should show mostly full_house / trips / quads paths."""
        hero = _parse_cards("Kh Kd")
        board = _parse_cards("Kc 7h 2d")
        dist = hand_distribution(hero, board, mc_iters=10000, seed=42)
        # Set can improve to full house or quads, or stay as trips
        assert 'three_of_a_kind' in dist or 'full_house' in dist


class TestDistributionPreflop:
    """Preflop uses Monte Carlo."""

    def test_preflop_probabilities_sum_to_one(self):
        hero = _parse_cards("Ah Kd")
        dist = hand_distribution(hero, [], seed=42)
        total = sum(dist.values())
        assert abs(total - 1.0) < 1e-9

    def test_preflop_has_variety(self):
        hero = _parse_cards("Ah Kd")
        dist = hand_distribution(hero, [], seed=42)
        # Preflop should have many possible hand types
        assert len(dist) >= 4
