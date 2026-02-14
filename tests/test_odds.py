"""Tests for pot odds and EV calculation."""
import pytest
from src.engine.odds import pot_odds, ev_call, should_call


class TestPotOdds:
    """Test pot odds calculation."""

    def test_basic_pot_odds(self):
        """Standard pot odds: $50 call into $100 pot."""
        result = pot_odds(100, 50)
        # 50 / (100 + 50) = 0.3333
        assert abs(result - 1/3) < 1e-9

    def test_small_bet_into_big_pot(self):
        """Good pot odds: small call into big pot."""
        result = pot_odds(200, 20)
        # 20 / 220 ≈ 0.0909
        assert abs(result - 20/220) < 1e-9

    def test_overbet(self):
        """Bad pot odds: big call into small pot."""
        result = pot_odds(50, 100)
        # 100 / 150 ≈ 0.6667
        assert abs(result - 2/3) < 1e-9

    def test_half_pot_bet(self):
        """Half pot bet: common scenario."""
        result = pot_odds(100, 50)
        assert abs(result - 1/3) < 1e-9

    def test_pot_size_bet(self):
        """Pot-sized bet."""
        result = pot_odds(100, 100)
        # 100 / 200 = 0.5
        assert result == 0.5

    def test_negative_pot_raises(self):
        with pytest.raises(ValueError, match="negative"):
            pot_odds(-10, 50)

    def test_zero_call_raises(self):
        with pytest.raises(ValueError, match="positive"):
            pot_odds(100, 0)

    def test_negative_call_raises(self):
        with pytest.raises(ValueError, match="positive"):
            pot_odds(100, -10)


class TestEvCall:
    """Test expected value calculation."""

    def test_positive_ev(self):
        """Calling with enough equity is +EV."""
        # Pot $100, call $50, hero has 50% equity
        ev = ev_call(100, 50, 0.50)
        # EV = 0.50 * 150 - 50 = 75 - 50 = 25
        assert abs(ev - 25.0) < 1e-9

    def test_negative_ev(self):
        """Calling without enough equity is -EV."""
        # Pot $100, call $50, hero has 20% equity
        ev = ev_call(100, 50, 0.20)
        # EV = 0.20 * 150 - 50 = 30 - 50 = -20
        assert abs(ev - (-20.0)) < 1e-9

    def test_breakeven_ev(self):
        """Calling at exact pot odds is 0 EV."""
        # Pot $100, call $50, need 33.3% to break even
        po = pot_odds(100, 50)
        ev = ev_call(100, 50, po)
        assert abs(ev) < 1e-9

    def test_certain_win(self):
        """100% equity = always profitable."""
        ev = ev_call(100, 50, 1.0)
        # EV = 1.0 * 150 - 50 = 100
        assert abs(ev - 100.0) < 1e-9

    def test_certain_lose(self):
        """0% equity = always lose the call amount."""
        ev = ev_call(100, 50, 0.0)
        # EV = 0 * 150 - 50 = -50
        assert abs(ev - (-50.0)) < 1e-9

    def test_invalid_equity_high(self):
        with pytest.raises(ValueError, match="between 0 and 1"):
            ev_call(100, 50, 1.5)

    def test_invalid_equity_low(self):
        with pytest.raises(ValueError, match="between 0 and 1"):
            ev_call(100, 50, -0.1)


class TestShouldCall:
    """Test the combined should_call decision helper."""

    def test_good_call(self):
        """Hero has enough equity to call."""
        result = should_call(100, 50, 0.50)

        assert result['profitable'] is True
        assert result['ev'] > 0
        assert result['edge'] > 0
        assert abs(result['pot_odds'] - 1/3) < 1e-9

    def test_bad_call(self):
        """Hero doesn't have enough equity to call."""
        result = should_call(100, 50, 0.20)

        assert result['profitable'] is False
        assert result['ev'] < 0
        assert result['edge'] < 0

    def test_breakeven_call(self):
        """Exactly at breakeven equity."""
        po = pot_odds(100, 50)
        result = should_call(100, 50, po)

        assert abs(result['ev']) < 1e-9
        assert abs(result['edge']) < 1e-9
