"""Deck model for generating and managing cards."""
from typing import List
from .card import Card, Suit


class Deck:
    """Represents a standard 52-card deck.

    Used primarily for generating all possible cards and removing known cards
    for equity enumeration (not for shuffling/dealing).
    """

    def __init__(self):
        """Initialize a full 52-card deck."""
        self.cards: List[Card] = []
        for suit in Suit:
            for rank in range(2, 15):  # 2-14 (A)
                self.cards.append(Card(rank=rank, suit=suit))

    def remove(self, cards_to_remove: List[Card]) -> List[Card]:
        """Return a new list of cards with specified cards removed.

        Args:
            cards_to_remove: Cards to exclude from the deck

        Returns:
            List of remaining cards (does not modify original deck)

        Raises:
            ValueError: If any card to remove is not in the deck
        """
        remaining = self.cards.copy()
        for card in cards_to_remove:
            try:
                remaining.remove(card)
            except ValueError:
                raise ValueError(f"Card {card} not found in deck (may already be removed).")
        return remaining

    def __len__(self) -> int:
        """Return number of cards in deck."""
        return len(self.cards)

    def __repr__(self) -> str:
        """String representation."""
        return f"Deck({len(self.cards)} cards)"
