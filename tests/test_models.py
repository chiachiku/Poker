"""Tests for data models (Card, Deck, Hand, Board)."""
import pytest
from src.models.card import Card, Suit
from src.models.deck import Deck
from src.models.hand import Hand, Board


class TestCard:
    """Test Card model."""

    def test_card_creation(self):
        """Test basic card creation."""
        card = Card(rank=14, suit=Suit.HEARTS)
        assert card.rank == 14
        assert card.suit == Suit.HEARTS

    def test_card_parsing(self):
        """Test parsing cards from string notation."""
        # Test all ranks
        assert Card.from_string("2h") == Card(2, Suit.HEARTS)
        assert Card.from_string("9d") == Card(9, Suit.DIAMONDS)
        assert Card.from_string("Tc") == Card(10, Suit.CLUBS)
        assert Card.from_string("Js") == Card(11, Suit.SPADES)
        assert Card.from_string("Qh") == Card(12, Suit.HEARTS)
        assert Card.from_string("Kd") == Card(13, Suit.DIAMONDS)
        assert Card.from_string("Ah") == Card(14, Suit.HEARTS)

        # Test lowercase
        assert Card.from_string("as") == Card(14, Suit.SPADES)
        assert Card.from_string("kc") == Card(13, Suit.CLUBS)

    def test_card_invalid_rank(self):
        """Test that invalid ranks are rejected."""
        with pytest.raises(ValueError, match="Invalid rank"):
            Card(rank=1, suit=Suit.HEARTS)
        with pytest.raises(ValueError, match="Invalid rank"):
            Card(rank=15, suit=Suit.HEARTS)
        with pytest.raises(ValueError, match="Invalid rank"):
            Card.from_string("Xh")

    def test_card_invalid_suit(self):
        """Test that invalid suits are rejected."""
        with pytest.raises(ValueError, match="Invalid suit"):
            Card.from_string("Ax")

    def test_card_invalid_string_format(self):
        """Test that invalid string formats are rejected."""
        with pytest.raises(ValueError, match="Must be 2 characters"):
            Card.from_string("A")
        with pytest.raises(ValueError, match="Must be 2 characters"):
            Card.from_string("Ahh")

    def test_card_repr(self):
        """Test card string representation."""
        assert str(Card(14, Suit.HEARTS)) == "Ah"
        assert str(Card(13, Suit.SPADES)) == "Ks"
        assert str(Card(10, Suit.CLUBS)) == "Tc"
        assert str(Card(2, Suit.DIAMONDS)) == "2d"

    def test_card_equality_and_hash(self):
        """Test card equality and hashing."""
        card1 = Card.from_string("Ah")
        card2 = Card.from_string("Ah")
        card3 = Card.from_string("Kh")

        assert card1 == card2
        assert card1 != card3
        assert hash(card1) == hash(card2)
        assert hash(card1) != hash(card3)

        # Test set operations
        card_set = {card1, card2, card3}
        assert len(card_set) == 2  # card1 and card2 are the same


class TestDeck:
    """Test Deck model."""

    def test_deck_initialization(self):
        """Test that deck has 52 cards."""
        deck = Deck()
        assert len(deck) == 52

    def test_deck_contains_all_cards(self):
        """Test that deck contains one of each card."""
        deck = Deck()
        # Should have 4 suits × 13 ranks = 52 unique cards
        assert len(set(deck.cards)) == 52

    def test_deck_remove_cards(self):
        """Test removing cards from deck."""
        deck = Deck()
        cards_to_remove = [Card.from_string("Ah"), Card.from_string("Ks")]

        remaining = deck.remove(cards_to_remove)

        assert len(remaining) == 50
        assert Card.from_string("Ah") not in remaining
        assert Card.from_string("Ks") not in remaining
        # Original deck unchanged
        assert len(deck) == 52

    def test_deck_remove_duplicate_card(self):
        """Test that removing the same card twice raises error."""
        deck = Deck()
        cards_to_remove = [Card.from_string("Ah"), Card.from_string("Ah")]

        with pytest.raises(ValueError, match="not found in deck"):
            deck.remove(cards_to_remove)


class TestHand:
    """Test Hand model."""

    def test_hand_creation(self):
        """Test creating a valid hand."""
        cards = [Card.from_string("Ah"), Card.from_string("Ks")]
        hand = Hand(cards)
        assert hand.cards == cards

    def test_hand_not_two_cards(self):
        """Test that hand must have exactly 2 cards."""
        with pytest.raises(ValueError, match="exactly 2 cards"):
            Hand([Card.from_string("Ah")])

        with pytest.raises(ValueError, match="exactly 2 cards"):
            Hand([Card.from_string("Ah"), Card.from_string("Ks"), Card.from_string("Qd")])

    def test_hand_duplicate_cards(self):
        """Test that hand cannot have duplicate cards."""
        with pytest.raises(ValueError, match="duplicate"):
            Hand([Card.from_string("Ah"), Card.from_string("Ah")])

    def test_hand_repr(self):
        """Test hand string representation."""
        hand = Hand([Card.from_string("Ah"), Card.from_string("Ks")])
        assert "Ah" in str(hand)
        assert "Ks" in str(hand)


class TestBoard:
    """Test Board model."""

    def test_board_empty(self):
        """Test creating an empty board (preflop)."""
        board = Board([])
        assert len(board.cards) == 0
        assert board.street == 'preflop'

    def test_board_flop(self):
        """Test creating a flop board."""
        cards = [Card.from_string("Ah"), Card.from_string("Ks"), Card.from_string("Qd")]
        board = Board(cards)
        assert len(board.cards) == 3
        assert board.street == 'flop'

    def test_board_turn(self):
        """Test creating a turn board."""
        cards = [Card.from_string("Ah"), Card.from_string("Ks"),
                Card.from_string("Qd"), Card.from_string("Jc")]
        board = Board(cards)
        assert len(board.cards) == 4
        assert board.street == 'turn'

    def test_board_river(self):
        """Test creating a river board."""
        cards = [Card.from_string("Ah"), Card.from_string("Ks"),
                Card.from_string("Qd"), Card.from_string("Jc"),
                Card.from_string("Tc")]
        board = Board(cards)
        assert len(board.cards) == 5
        assert board.street == 'river'

    def test_board_too_many_cards(self):
        """Test that board cannot have more than 5 cards."""
        cards = [Card.from_string(c) for c in ["Ah", "Ks", "Qd", "Jc", "Tc", "9h"]]
        with pytest.raises(ValueError, match="more than 5 cards"):
            Board(cards)

    def test_board_duplicate_cards(self):
        """Test that board cannot have duplicate cards."""
        with pytest.raises(ValueError, match="duplicate"):
            Board([Card.from_string("Ah"), Card.from_string("Ah")])

    def test_board_invalid_street(self):
        """Test that boards with 1 or 2 cards raise error when checking street."""
        board_one = Board([Card.from_string("Ah")])
        with pytest.raises(ValueError, match="Invalid board state"):
            _ = board_one.street

        board_two = Board([Card.from_string("Ah"), Card.from_string("Ks")])
        with pytest.raises(ValueError, match="Invalid board state"):
            _ = board_two.street

    def test_board_repr(self):
        """Test board string representation."""
        board = Board([Card.from_string("Ah"), Card.from_string("Ks"), Card.from_string("Qd")])
        board_str = str(board)
        assert "Ah" in board_str
        assert "Ks" in board_str
        assert "Qd" in board_str
