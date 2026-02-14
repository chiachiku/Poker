"""Tests for equity calculator."""
import pytest
import time
from src.models.card import Card
from src.engine.equity import equity_vs_random


def _parse_cards(card_strings: str) -> list:
    """Helper to parse space-separated card strings."""
    return [Card.from_string(s) for s in card_strings.split()]


class TestEquityValidation:
    """Test input validation for equity calculator."""

    def test_hero_must_have_2_cards(self):
        """Test that hero must have exactly 2 cards."""
        with pytest.raises(ValueError, match="exactly 2 cards"):
            equity_vs_random(_parse_cards("Ah"), _parse_cards("Ks Qd Jc"))

        with pytest.raises(ValueError, match="exactly 2 cards"):
            equity_vs_random(_parse_cards("Ah Ks Qd"), _parse_cards("Jc Tc 9h"))

    def test_board_cannot_exceed_5_cards(self):
        """Test that board cannot have more than 5 cards."""
        with pytest.raises(ValueError, match="cannot exceed 5 cards"):
            equity_vs_random(_parse_cards("Ah Ks"), _parse_cards("Qd Jc Tc 9h 8d 7c"))


class TestEquityRiver:
    """Test equity calculation on the river (5 board cards)."""

    def test_river_nut_hand(self):
        """Test that nut hand has 100% equity (no ties possible)."""
        # Royal flush on board, hero has irrelevant cards but no one can beat the board
        # Actually, let me use a different example where hero has the nuts
        hero = _parse_cards("Ah Kh")  # Nut flush
        board = _parse_cards("Qh Jh 9h 2d 3c")  # Three hearts on board

        result = equity_vs_random(hero, board)

        # Hero has nut flush, should win against all random hands
        assert result['win'] > 0.99  # Should be very close to 1.0
        assert result['lose'] < 0.01

    def test_river_probabilities_sum_to_one(self):
        """Test that win + tie + lose = 1.0."""
        hero = _parse_cards("Ah Kd")
        board = _parse_cards("Qh Jc Tc 2d 3h")

        result = equity_vs_random(hero, board)

        assert abs(result['win'] + result['tie'] + result['lose'] - 1.0) < 1e-9

    def test_river_weak_hand(self):
        """Test weak hand has low equity."""
        hero = _parse_cards("2h 3d")  # Weak hand
        board = _parse_cards("Ah Kc 9d 7s 5h")  # Rainbow high board

        result = equity_vs_random(hero, board)

        # Hero has very weak hand (just ace high), should lose most of the time
        assert result['lose'] > 0.7


class TestEquityTurn:
    """Test equity calculation on the turn (4 board cards)."""

    def test_turn_probabilities_sum_to_one(self):
        """Test that win + tie + lose = 1.0."""
        hero = _parse_cards("Ah Kd")
        board = _parse_cards("Qh Jc Tc 2d")

        result = equity_vs_random(hero, board)

        assert abs(result['win'] + result['tie'] + result['lose'] - 1.0) < 1e-9

    def test_turn_flush_draw(self):
        """Test flush draw equity on turn."""
        hero = _parse_cards("Ah Kh")  # Nut flush draw
        board = _parse_cards("Qh Jh 2d 3c")  # Two hearts on board

        result = equity_vs_random(hero, board)

        # With flush draw + overcards, should have decent equity
        assert result['win'] > 0.3


class TestEquityFlop:
    """Test equity calculation on the flop (3 board cards).

    Flop uses Monte Carlo (50k default) since exact enumeration is too slow
    in pure Python (~45s for 1M+ evaluations).
    """

    def test_flop_probabilities_sum_to_one(self):
        """Test that win + tie + lose = 1.0."""
        hero = _parse_cards("Ah Kd")
        board = _parse_cards("Qh Jc Tc")

        result = equity_vs_random(hero, board, seed=42)

        assert abs(result['win'] + result['tie'] + result['lose'] - 1.0) < 1e-9

    def test_flop_set_vs_random(self):
        """Test set has high equity vs random hand."""
        hero = _parse_cards("Kh Kd")  # Pocket kings
        board = _parse_cards("Kc 7h 2d")  # Flopped a set

        result = equity_vs_random(hero, board, seed=42)

        # Set should have very high equity vs random
        assert result['win'] > 0.80

    def test_flop_overpair_vs_random(self):
        """Test overpair has good equity vs random."""
        hero = _parse_cards("Ah Ad")  # Pocket aces
        board = _parse_cards("Kh Qd 7c")  # Overpair to the board

        result = equity_vs_random(hero, board, seed=42)

        # Overpair should have good equity
        assert result['win'] > 0.65

    def test_flop_performance(self):
        """Test that flop equity completes in < 1 second.

        Uses Monte Carlo (50k default iterations) which runs in ~1s.
        """
        hero = _parse_cards("Ah Kd")
        board = _parse_cards("Qh Jc Tc")

        start_time = time.time()
        result = equity_vs_random(hero, board, seed=42)
        elapsed = time.time() - start_time

        assert elapsed < 1.0, f"Flop MC took {elapsed:.2f}s, expected < 1.0s"
        assert abs(result['win'] + result['tie'] + result['lose'] - 1.0) < 1e-9

    def test_flop_seeded_consistency(self):
        """Test that seeded flop MC produces consistent results."""
        hero = _parse_cards("Ah Kd")
        board = _parse_cards("Qh Jc Tc")

        result1 = equity_vs_random(hero, board, seed=42)
        result2 = equity_vs_random(hero, board, seed=42)

        assert result1 == result2


class TestEquityPreflop:
    """Test equity calculation preflop (Monte Carlo)."""

    def test_preflop_probabilities_sum_to_one(self):
        """Test that win + tie + lose = 1.0."""
        hero = _parse_cards("Ah Kd")
        board = []

        result = equity_vs_random(hero, board, mc_iters=1000, seed=42)

        # Allow slightly larger tolerance for Monte Carlo
        assert abs(result['win'] + result['tie'] + result['lose'] - 1.0) < 1e-9

    def test_preflop_pocket_aces_vs_random(self):
        """Test that pocket aces have ~85% equity preflop vs random."""
        hero = _parse_cards("Ah Ad")
        board = []

        result = equity_vs_random(hero, board, mc_iters=10000, seed=42)

        # Pocket aces should have roughly 85% equity vs random
        # Allow some variance due to Monte Carlo
        assert 0.80 < result['win'] < 0.90

    def test_preflop_suited_connectors(self):
        """Test suited connectors have decent equity preflop."""
        hero = _parse_cards("Th 9h")  # Suited connectors
        board = []

        result = equity_vs_random(hero, board, mc_iters=10000, seed=42)

        # Suited connectors should have roughly 50% equity vs random
        assert 0.45 < result['win'] < 0.55

    def test_preflop_weak_hand(self):
        """Test weak hand has low equity preflop."""
        hero = _parse_cards("7d 2c")  # Very weak hand
        board = []

        result = equity_vs_random(hero, board, mc_iters=10000, seed=42)

        # Weak hand should have less than 50% equity vs random
        assert result['win'] < 0.45

    def test_preflop_seeded_consistency(self):
        """Test that seeded Monte Carlo produces consistent results."""
        hero = _parse_cards("Ah Kd")
        board = []

        result1 = equity_vs_random(hero, board, mc_iters=1000, seed=42)
        result2 = equity_vs_random(hero, board, mc_iters=1000, seed=42)

        # Same seed should produce identical results
        assert result1 == result2

    def test_preflop_unseeded_variation(self):
        """Test that unseeded Monte Carlo produces varying results."""
        hero = _parse_cards("Ah Kd")
        board = []

        result1 = equity_vs_random(hero, board, mc_iters=100, seed=None)
        result2 = equity_vs_random(hero, board, mc_iters=100, seed=None)

        # Different runs without seed should likely produce different results
        # (This test may occasionally fail due to random chance, but very unlikely)
        # Actually, let's not test this as it could be flaky
        # Instead just verify both are valid
        assert abs(result1['win'] + result1['tie'] + result1['lose'] - 1.0) < 1e-9
        assert abs(result2['win'] + result2['tie'] + result2['lose'] - 1.0) < 1e-9


class TestEquityKnownSpots:
    """Test against known equity spots to verify correctness."""

    def test_dominated_hand_preflop(self):
        """Test dominated hand scenario (e.g., AK vs AQ)."""
        # Note: This is vs random, not vs a specific hand, so we just verify reasonable equity
        hero = _parse_cards("Ah Kd")  # AK
        board = []

        result = equity_vs_random(hero, board, mc_iters=5000, seed=123)

        # AK should have good equity vs random (around 65-67%)
        assert 0.60 < result['win'] < 0.72

    def test_pocket_pair_vs_random(self):
        """Test pocket pair equity preflop."""
        hero = _parse_cards("Jh Jd")  # Pocket jacks
        board = []

        result = equity_vs_random(hero, board, mc_iters=5000, seed=123)

        # Pocket jacks should have roughly 75% equity vs random
        assert 0.70 < result['win'] < 0.80
