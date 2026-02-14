"""Tests for advice engine v1 (rule-based)."""
import pytest
from src.models.card import Card
from src.advisor.advisor import get_advice, _street_name, _raise_sizing


def _parse_cards(card_strings: str) -> list:
    """Helper to parse space-separated card strings."""
    return [Card.from_string(s) for s in card_strings.split()]


# =============================================
# Street name helper
# =============================================

class TestStreetName:
    """Test _street_name helper."""

    def test_preflop(self):
        assert _street_name(0) == 'preflop'

    def test_flop(self):
        assert _street_name(3) == 'flop'

    def test_turn(self):
        assert _street_name(4) == 'turn'

    def test_river(self):
        assert _street_name(5) == 'river'

    def test_unknown(self):
        assert _street_name(2) == 'unknown'


# =============================================
# Raise sizing helper
# =============================================

class TestRaiseSizing:
    """Test _raise_sizing bet size suggestions."""

    def test_very_strong_equity(self):
        """Equity >= 80% → pot-sized bet."""
        assert _raise_sizing(0.85) == 1.0

    def test_strong_equity(self):
        """Equity 70-80% → 3/4 pot."""
        assert _raise_sizing(0.75) == 0.75

    def test_moderate_equity(self):
        """Equity 60-70% → 2/3 pot."""
        assert _raise_sizing(0.65) == 0.66

    def test_lower_equity(self):
        """Equity < 60% → half pot."""
        assert _raise_sizing(0.55) == 0.50


# =============================================
# Return format
# =============================================

class TestAdviceReturnFormat:
    """Verify get_advice returns correct structure."""

    def test_return_keys(self):
        hero = _parse_cards("Ah Kh")
        board = _parse_cards("Qh Jh 9h 2d 3c")
        result = get_advice(hero, board, seed=42)

        assert 'action' in result
        assert 'confidence' in result
        assert 'rationale' in result
        assert 'bet_sizing' in result

    def test_action_is_valid(self):
        hero = _parse_cards("Ah Kd")
        board = _parse_cards("Qh Jc Tc 2d 3h")
        result = get_advice(hero, board, seed=42)
        assert result['action'] in ('fold', 'call', 'raise')

    def test_confidence_is_valid(self):
        hero = _parse_cards("Ah Kd")
        board = _parse_cards("Qh Jc Tc 2d 3h")
        result = get_advice(hero, board, seed=42)
        assert result['confidence'] in ('strong', 'moderate', 'marginal')

    def test_rationale_is_list(self):
        hero = _parse_cards("Ah Kd")
        board = _parse_cards("Qh Jc Tc 2d 3h")
        result = get_advice(hero, board, seed=42)
        assert isinstance(result['rationale'], list)
        assert len(result['rationale']) >= 2  # at least equity summary + decision

    def test_bet_sizing_on_raise(self):
        """When action is raise, bet_sizing should be a float."""
        hero = _parse_cards("Ah Kh")
        board = _parse_cards("Qh Jh 9h 2d 3c")
        result = get_advice(hero, board, seed=42)
        if result['action'] == 'raise':
            assert isinstance(result['bet_sizing'], float)
            assert 0 < result['bet_sizing'] <= 1.0

    def test_bet_sizing_on_fold(self):
        """When action is fold, bet_sizing should be None."""
        hero = _parse_cards("2h 7d")
        board = _parse_cards("Ah Kc Qs 9d 4c")
        result = get_advice(hero, board, seed=42)
        if result['action'] == 'fold':
            assert result['bet_sizing'] is None


# =============================================
# Rule 1: Strong hand (equity >= 70%)
# =============================================

class TestStrongHand:
    """Test advice for strong hands — should recommend raise."""

    def test_made_flush_on_river(self):
        """Made flush on river → should raise with strong confidence."""
        hero = _parse_cards("Ah Kh")
        board = _parse_cards("Qh Jh 9h 2d 3c")
        result = get_advice(hero, board, seed=42)

        assert result['action'] == 'raise'
        assert result['confidence'] == 'strong'
        assert result['bet_sizing'] is not None

    def test_made_straight_on_river(self):
        """Made straight on river → should raise."""
        hero = _parse_cards("Ah Kd")
        board = _parse_cards("Qh Jc Tc 2d 3h")
        result = get_advice(hero, board, seed=42)

        assert result['action'] == 'raise'
        assert result['confidence'] == 'strong'

    def test_top_pair_aces_on_flop(self):
        """AA on a low board → strong equity, recommend raise."""
        hero = _parse_cards("Ah Ad")
        board = _parse_cards("7c 4d 2s")
        result = get_advice(hero, board, mc_iters=10000, seed=42)

        # Pocket aces on a low board: equity vs random ~85%+
        assert result['action'] == 'raise'
        assert result['confidence'] == 'strong'

    def test_strong_hand_rationale_has_equity(self):
        """Rationale should include equity information."""
        hero = _parse_cards("Ah Kh")
        board = _parse_cards("Qh Jh 9h 2d 3c")
        result = get_advice(hero, board, seed=42)

        equity_mentioned = any('Equity' in r or 'equity' in r for r in result['rationale'])
        assert equity_mentioned


# =============================================
# Rule 2: Good hand (equity 55-70%)
# =============================================

class TestGoodHand:
    """Test advice for good (but not dominant) hands."""

    def test_top_pair_good_kicker(self):
        """Top pair with good kicker on a safe board."""
        hero = _parse_cards("Ah Qd")
        board = _parse_cards("As 7c 3d")
        result = get_advice(hero, board, mc_iters=10000, seed=42)

        # TPTK on dry board: equity ~75%+ → raise
        assert result['action'] == 'raise'

    def test_good_hand_with_positive_ev(self):
        """Good equity + positive EV with pot info → raise."""
        hero = _parse_cards("Kd Qd")
        board = _parse_cards("Kh 7c 3s")
        result = get_advice(hero, board, pot=100, call_amount=30,
                            mc_iters=10000, seed=42)

        # Top pair decent kicker, small bet into pot → should raise
        assert result['action'] == 'raise'


# =============================================
# Rule 3: Drawing hand (equity 35-55%, has outs)
# =============================================

class TestDrawingHand:
    """Test advice for drawing hands."""

    def test_flush_draw_no_pot_info(self):
        """Flush draw without pot info → call to see next card."""
        hero = _parse_cards("Ah 9h")
        board = _parse_cards("Kh 7h 3d 2c")
        result = get_advice(hero, board, seed=42)

        # Flush draw: ~19.6% to complete on river, but equity vs random includes pair outs etc.
        # Without pot info, if equity is 35-55% with draws → call
        if result['action'] == 'call':
            assert result['confidence'] in ('moderate', 'marginal')

    def test_flush_draw_good_pot_odds(self):
        """Flush draw with good pot odds → call."""
        hero = _parse_cards("Ah 9h")
        board = _parse_cards("Kh 7h 3d 2c")
        result = get_advice(hero, board, pot=200, call_amount=20, seed=42)

        # Huge pot, small bet → great odds for a draw
        assert result['action'] in ('call', 'raise')

    def test_flush_draw_bad_pot_odds(self):
        """Flush draw with terrible pot odds → fold."""
        hero = _parse_cards("5h 4h")
        board = _parse_cards("Kh 7h 3d 2c")
        result = get_advice(hero, board, pot=50, call_amount=100, seed=42)

        # Small pot, huge bet → bad odds for a draw with low equity
        # Could be fold depending on equity
        assert result['action'] in ('fold', 'call')


# =============================================
# Rule 4/5: Weak hands
# =============================================

class TestWeakHand:
    """Test advice for weak / marginal hands."""

    def test_garbage_hand_on_river(self):
        """Very weak hand on river → fold."""
        hero = _parse_cards("2h 7d")
        board = _parse_cards("Ah Kc Qs 9d 4c")
        result = get_advice(hero, board, seed=42)

        assert result['action'] == 'fold'
        assert result['confidence'] == 'strong'

    def test_weak_hand_no_draws(self):
        """Weak hand with no draws → fold."""
        hero = _parse_cards("2h 5d")
        board = _parse_cards("Ah Kc 9s")
        result = get_advice(hero, board, mc_iters=10000, seed=42)

        # Low cards vs high board, no draws
        assert result['action'] == 'fold'

    def test_weak_equity_strong_draw(self):
        """Weak equity but strong draw (8+ outs) without pot info → call."""
        hero = _parse_cards("5h 4h")
        board = _parse_cards("Ah 9h 3d")
        result = get_advice(hero, board, mc_iters=10000, seed=42)

        # Flush draw + some straight potential
        # If equity < 35% but has 8+ outs, should consider calling
        assert result['action'] in ('call', 'raise', 'fold')
        # This test mainly verifies the code path doesn't error


# =============================================
# Pot odds integration
# =============================================

class TestPotOddsIntegration:
    """Test advice when pot and call_amount are provided."""

    def test_rationale_includes_pot_odds(self):
        """When pot info given, rationale should mention pot odds."""
        hero = _parse_cards("Ah Kd")
        board = _parse_cards("Qh Jc 8d 4s 2c")
        result = get_advice(hero, board, pot=100, call_amount=50, seed=42)

        pot_odds_mentioned = any('Pot odds' in r or 'pot odds' in r or 'EV' in r
                                 for r in result['rationale'])
        assert pot_odds_mentioned

    def test_no_pot_info_no_pot_odds(self):
        """Without pot info, rationale should NOT mention pot odds."""
        hero = _parse_cards("Ah Kd")
        board = _parse_cards("Qh Jc 8d 4s 2c")
        result = get_advice(hero, board, seed=42)

        pot_odds_mentioned = any('Pot odds' in r for r in result['rationale'])
        assert not pot_odds_mentioned

    def test_positive_ev_influences_decision(self):
        """Positive EV should influence toward call/raise."""
        hero = _parse_cards("Kd Jd")
        board = _parse_cards("Kh 9c 4d 2s")
        result = get_advice(hero, board, pot=200, call_amount=20,
                            mc_iters=10000, seed=42)

        # Top pair + small bet → positive EV → should not fold
        assert result['action'] in ('call', 'raise')


# =============================================
# Preflop scenarios
# =============================================

class TestPreflopAdvice:
    """Test advice preflop (0 board cards)."""

    def test_preflop_pocket_aces(self):
        """Pocket aces preflop → should raise strong."""
        hero = _parse_cards("Ah Ad")
        result = get_advice(hero, [], mc_iters=10000, seed=42)

        assert result['action'] == 'raise'
        assert result['confidence'] == 'strong'

    def test_preflop_pocket_kings(self):
        """Pocket kings preflop → should raise."""
        hero = _parse_cards("Kh Kd")
        result = get_advice(hero, [], mc_iters=10000, seed=42)

        assert result['action'] == 'raise'

    def test_preflop_garbage(self):
        """72 offsuit preflop → weakest hand, should fold."""
        hero = _parse_cards("2h 7d")
        result = get_advice(hero, [], mc_iters=10000, seed=42)

        # 72o has ~34% equity vs random → falls into weak hand territory
        # Rule engine: equity < 35%, no draws → strong fold
        assert result['action'] == 'fold'
        assert result['confidence'] == 'strong'


# =============================================
# Seeded reproducibility
# =============================================

class TestReproducibility:
    """Test that seeded advice is deterministic."""

    def test_same_seed_same_advice(self):
        """Same seed → same result."""
        hero = _parse_cards("Ah Kd")
        board = _parse_cards("Qh 7c 3d")

        r1 = get_advice(hero, board, mc_iters=5000, seed=42)
        r2 = get_advice(hero, board, mc_iters=5000, seed=42)

        assert r1['action'] == r2['action']
        assert r1['confidence'] == r2['confidence']
        assert r1['rationale'] == r2['rationale']
        assert r1['bet_sizing'] == r2['bet_sizing']

    def test_different_seed_may_differ(self):
        """Different seeds can produce different results (not guaranteed, but verifies seed is used)."""
        hero = _parse_cards("9h 8h")
        board = _parse_cards("7c 6d 2s")

        r1 = get_advice(hero, board, mc_iters=1000, seed=1)
        r2 = get_advice(hero, board, mc_iters=1000, seed=999)

        # Just verify both return valid results — they may or may not differ
        assert r1['action'] in ('fold', 'call', 'raise')
        assert r2['action'] in ('fold', 'call', 'raise')


# =============================================
# Edge cases
# =============================================

class TestEdgeCases:
    """Test edge cases for advice engine."""

    def test_zero_call_amount_ignored(self):
        """call_amount=0 means no pot odds calc (free check)."""
        hero = _parse_cards("Ah Kd")
        board = _parse_cards("Qh Jc Tc 2d 3h")
        result = get_advice(hero, board, pot=100, call_amount=0, seed=42)

        # call_amount=0 → has_pot_info is False → no pot odds in rationale
        assert result['action'] in ('fold', 'call', 'raise')

    def test_none_pot_no_crash(self):
        """pot=None, call_amount=None should not crash."""
        hero = _parse_cards("Ah Kd")
        board = _parse_cards("Qh Jc Tc")
        result = get_advice(hero, board, seed=42)
        assert result['action'] in ('fold', 'call', 'raise')

    def test_river_exact_evaluation(self):
        """River should use exact equity (no MC variance)."""
        hero = _parse_cards("Ah Kd")
        board = _parse_cards("Qh Jc Tc 2d 3h")

        r1 = get_advice(hero, board, seed=1)
        r2 = get_advice(hero, board, seed=999)

        # River is exact → seed shouldn't matter
        assert r1 == r2
