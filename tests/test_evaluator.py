"""Tests for hand evaluator."""
import pytest
from src.models.card import Card
from src.engine.evaluator import evaluate_5, best_hand_7


def _parse_cards(card_strings: str) -> list:
    """Helper to parse space-separated card strings."""
    return [Card.from_string(s) for s in card_strings.split()]


class TestEvaluate5:
    """Test 5-card hand evaluation."""

    def test_royal_flush(self):
        """Test royal flush (highest straight flush)."""
        cards = _parse_cards("Ah Kh Qh Jh Th")
        score = evaluate_5(cards)
        assert score > 9_000_000  # Straight flush category
        assert score == 9_000_014  # Max rank is 14 (Ace)

    def test_straight_flush(self):
        """Test straight flush."""
        cards = _parse_cards("9h 8h 7h 6h 5h")
        score = evaluate_5(cards)
        assert score > 9_000_000
        assert score == 9_000_009  # High card is 9

    def test_wheel_straight_flush(self):
        """Test wheel straight flush (A-2-3-4-5 suited)."""
        cards = _parse_cards("5d 4d 3d 2d Ad")
        score = evaluate_5(cards)
        assert score > 9_000_000
        # Wheel straight flush is 5-high (lowest straight flush)
        assert score == 9_000_005

    def test_wheel_straight_flush_loses_to_6_high(self):
        """Wheel SF (A-5) should lose to 6-high SF."""
        wheel_sf = _parse_cards("5d 4d 3d 2d Ad")
        six_high_sf = _parse_cards("6h 5h 4h 3h 2h")
        assert evaluate_5(six_high_sf) > evaluate_5(wheel_sf)

    def test_four_of_a_kind(self):
        """Test four of a kind (quads)."""
        cards = _parse_cards("Kh Kd Kc Ks 2h")
        score = evaluate_5(cards)
        assert 8_000_000 < score < 9_000_000  # Quads category

    def test_four_of_a_kind_tiebreaker(self):
        """Test that higher quads beat lower quads."""
        aces = _parse_cards("Ah Ad Ac As 2h")
        kings = _parse_cards("Kh Kd Kc Ks 2h")
        assert evaluate_5(aces) > evaluate_5(kings)

    def test_four_of_a_kind_kicker(self):
        """Test that kicker matters in quads."""
        quad_kings_ace = _parse_cards("Kh Kd Kc Ks Ah")
        quad_kings_two = _parse_cards("Kh Kd Kc Ks 2h")
        assert evaluate_5(quad_kings_ace) > evaluate_5(quad_kings_two)

    def test_full_house(self):
        """Test full house."""
        cards = _parse_cards("Kh Kd Kc 2s 2h")
        score = evaluate_5(cards)
        assert 7_000_000 < score < 8_000_000  # Full house category

    def test_full_house_tiebreaker(self):
        """Test that trips rank determines winner in full house."""
        aces_over_kings = _parse_cards("Ah Ad Ac Ks Kh")
        kings_over_aces = _parse_cards("Kh Kd Kc As Ah")
        assert evaluate_5(aces_over_kings) > evaluate_5(kings_over_aces)

    def test_flush(self):
        """Test flush."""
        cards = _parse_cards("Ah Kh 9h 5h 2h")
        score = evaluate_5(cards)
        assert 6_000_000 < score < 7_000_000  # Flush category

    def test_flush_tiebreaker(self):
        """Test that high cards matter in flush."""
        flush_high = _parse_cards("Ah Kh Qh Jh 9h")
        flush_low = _parse_cards("Ah Kh Qh Jh 8h")
        assert evaluate_5(flush_high) > evaluate_5(flush_low)

    def test_straight(self):
        """Test straight."""
        cards = _parse_cards("9h 8d 7c 6s 5h")
        score = evaluate_5(cards)
        assert 5_000_000 < score < 6_000_000  # Straight category

    def test_wheel_straight(self):
        """Test wheel straight (A-2-3-4-5 unsuited)."""
        cards = _parse_cards("5h 4d 3c 2s Ah")
        score = evaluate_5(cards)
        assert score == 5_000_005  # 5-high straight

    def test_wheel_straight_loses_to_6_high(self):
        """Wheel (A-5) should lose to 6-high straight."""
        wheel = _parse_cards("5h 4d 3c 2s Ah")
        six_high = _parse_cards("6h 5d 4c 3s 2d")
        assert evaluate_5(six_high) > evaluate_5(wheel)

    def test_straight_tiebreaker(self):
        """Test that higher straight beats lower straight."""
        high_straight = _parse_cards("Ah Kd Qc Js Th")
        low_straight = _parse_cards("9h 8d 7c 6s 5h")
        assert evaluate_5(high_straight) > evaluate_5(low_straight)

    def test_three_of_a_kind(self):
        """Test three of a kind (trips)."""
        cards = _parse_cards("Kh Kd Kc 9s 2h")
        score = evaluate_5(cards)
        assert 4_000_000 < score < 5_000_000  # Trips category

    def test_three_of_a_kind_tiebreaker(self):
        """Test that trips rank determines winner."""
        trip_aces = _parse_cards("Ah Ad Ac 9s 2h")
        trip_kings = _parse_cards("Kh Kd Kc 9s 2h")
        assert evaluate_5(trip_aces) > evaluate_5(trip_kings)

    def test_two_pair(self):
        """Test two pair."""
        cards = _parse_cards("Kh Kd 9c 9s 2h")
        score = evaluate_5(cards)
        assert 3_000_000 < score < 4_000_000  # Two pair category

    def test_two_pair_tiebreaker(self):
        """Test that higher pair wins in two pair."""
        aces_kings = _parse_cards("Ah Ad Kc Ks 2h")
        kings_queens = _parse_cards("Kh Kd Qc Qs 2h")
        assert evaluate_5(aces_kings) > evaluate_5(kings_queens)

    def test_two_pair_kicker(self):
        """Test that kicker matters in two pair."""
        two_pair_ace = _parse_cards("Kh Kd 9c 9s Ah")
        two_pair_two = _parse_cards("Kh Kd 9c 9s 2h")
        assert evaluate_5(two_pair_ace) > evaluate_5(two_pair_two)

    def test_one_pair(self):
        """Test one pair."""
        cards = _parse_cards("Kh Kd 9c 7s 2h")
        score = evaluate_5(cards)
        assert 2_000_000 < score < 3_000_000  # One pair category

    def test_one_pair_tiebreaker(self):
        """Test that pair rank determines winner."""
        pair_aces = _parse_cards("Ah Ad 9c 7s 2h")
        pair_kings = _parse_cards("Kh Kd 9c 7s 2h")
        assert evaluate_5(pair_aces) > evaluate_5(pair_kings)

    def test_one_pair_kicker(self):
        """Test that kickers matter in one pair."""
        pair_high_kicker = _parse_cards("Kh Kd Ac Qs Jh")
        pair_low_kicker = _parse_cards("Kh Kd 9c 7s 2h")
        assert evaluate_5(pair_high_kicker) > evaluate_5(pair_low_kicker)

    def test_high_card(self):
        """Test high card."""
        cards = _parse_cards("Ah Kd 9c 7s 2h")
        score = evaluate_5(cards)
        assert 1_000_000 < score < 2_000_000  # High card category

    def test_high_card_tiebreaker(self):
        """Test that kickers matter in high card."""
        high_card_better = _parse_cards("Ah Kd Qc Js 9h")
        high_card_worse = _parse_cards("Ah Kd Qc Js 8h")
        assert evaluate_5(high_card_better) > evaluate_5(high_card_worse)

    def test_category_ordering(self):
        """Test that hand categories are correctly ordered."""
        straight_flush = _parse_cards("9h 8h 7h 6h 5h")
        quads = _parse_cards("Ah Ad Ac As Kh")
        full_house = _parse_cards("Ah Ad Ac Ks Kh")
        flush = _parse_cards("Ah Kh 9h 5h 2h")
        straight = _parse_cards("9h 8d 7c 6s 5h")
        trips = _parse_cards("Ah Ad Ac Ks Qh")
        two_pair = _parse_cards("Ah Ad Kc Ks Qh")
        one_pair = _parse_cards("Ah Ad Kc Qs Jh")
        high_card = _parse_cards("Ah Kd Qc Js 9h")

        hands = [
            (straight_flush, "straight_flush"),
            (quads, "quads"),
            (full_house, "full_house"),
            (flush, "flush"),
            (straight, "straight"),
            (trips, "trips"),
            (two_pair, "two_pair"),
            (one_pair, "one_pair"),
            (high_card, "high_card"),
        ]

        scores = [evaluate_5(h) for h, _ in hands]

        # Verify descending order
        for i in range(len(scores) - 1):
            assert scores[i] > scores[i + 1], f"{hands[i][1]} should beat {hands[i+1][1]}"

    def test_invalid_card_count(self):
        """Test that evaluate_5 requires exactly 5 cards."""
        with pytest.raises(ValueError, match="exactly 5 cards"):
            evaluate_5(_parse_cards("Ah Kh Qh Jh"))

        with pytest.raises(ValueError, match="exactly 5 cards"):
            evaluate_5(_parse_cards("Ah Kh Qh Jh Th 9h"))


class TestBestHand7:
    """Test 7-card hand evaluation."""

    def test_best_hand_from_7(self):
        """Test selecting best 5 cards from 7."""
        # 7 cards that contain a flush (5 hearts)
        cards = _parse_cards("Ah Kh Qh Jh 9h 8d 7c")
        score = best_hand_7(cards)

        # Should recognize the flush
        assert 6_000_000 < score < 7_000_000

    def test_best_hand_ignores_worse_cards(self):
        """Test that worst 2 cards are correctly ignored."""
        # Aces full of kings + two low cards
        cards = _parse_cards("Ah Ad Ac Ks Kh 3d 2c")
        score = best_hand_7(cards)

        # Should recognize the full house (not trips)
        assert 7_000_000 < score < 8_000_000

    def test_best_hand_straight_from_7(self):
        """Test finding a straight in 7 cards."""
        # Contains 9-high straight
        cards = _parse_cards("9h 8d 7c 6s 5h Ah 2d")
        score = best_hand_7(cards)

        # Should recognize the straight
        assert 5_000_000 < score < 6_000_000

    def test_best_hand_two_pair_from_7(self):
        """Test selecting best two pair from 7 cards."""
        # Three pairs available: AA, KK, QQ
        cards = _parse_cards("Ah Ad Kc Ks Qh Qd 2c")
        score = best_hand_7(cards)

        # Should select AA and KK (best two pairs)
        assert 3_000_000 < score < 4_000_000
        # Verify it's aces and kings, not queens
        expected = evaluate_5(_parse_cards("Ah Ad Kc Ks Qd"))
        assert score == expected

    def test_invalid_card_count_7(self):
        """Test that best_hand_7 requires exactly 7 cards."""
        with pytest.raises(ValueError, match="exactly 7 cards"):
            best_hand_7(_parse_cards("Ah Kh Qh Jh Th 9h"))

        with pytest.raises(ValueError, match="exactly 7 cards"):
            best_hand_7(_parse_cards("Ah Kh Qh Jh Th 9h 8h 7h"))
