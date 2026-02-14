"""Hand and Board models for poker game state."""
from typing import List
from .card import Card


class Hand:
    """Represents a player's 2 hole cards.

    Attributes:
        cards: Exactly 2 cards
    """

    def __init__(self, cards: List[Card]):
        """Initialize a hand with 2 hole cards.

        Args:
            cards: List of exactly 2 Card objects

        Raises:
            ValueError: If not exactly 2 cards or if cards are duplicates
        """
        if len(cards) != 2:
            raise ValueError(f"Hand must have exactly 2 cards, got {len(cards)}.")

        if cards[0] == cards[1]:
            raise ValueError(f"Hand cannot contain duplicate cards: {cards[0]}.")

        self.cards = cards

    def __repr__(self) -> str:
        """String representation."""
        return f"Hand({self.cards[0]} {self.cards[1]})"


class Board:
    """Represents community cards (0-5 cards).

    Attributes:
        cards: 0-5 community cards
    """

    def __init__(self, cards: List[Card]):
        """Initialize a board with 0-5 community cards.

        Args:
            cards: List of 0-5 Card objects

        Raises:
            ValueError: If more than 5 cards or if duplicates exist
        """
        if len(cards) > 5:
            raise ValueError(f"Board cannot have more than 5 cards, got {len(cards)}.")

        if len(cards) != len(set(cards)):
            raise ValueError("Board cannot contain duplicate cards.")

        self.cards = cards

    @property
    def street(self) -> str:
        """Detect current street based on number of cards.

        Returns:
            'preflop', 'flop', 'turn', or 'river'
        """
        num_cards = len(self.cards)
        if num_cards == 0:
            return 'preflop'
        elif num_cards == 3:
            return 'flop'
        elif num_cards == 4:
            return 'turn'
        elif num_cards == 5:
            return 'river'
        else:
            raise ValueError(f"Invalid board state: {num_cards} cards. Expected 0, 3, 4, or 5.")

    def __repr__(self) -> str:
        """String representation."""
        if not self.cards:
            return "Board(preflop)"
        cards_str = ' '.join(str(c) for c in self.cards)
        return f"Board({cards_str})"
