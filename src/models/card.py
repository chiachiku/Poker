"""Card model for poker hands."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class Suit(Enum):
    """Card suits."""
    HEARTS = 'h'
    DIAMONDS = 'd'
    CLUBS = 'c'
    SPADES = 's'


@dataclass(frozen=True)
class Card:
    """Represents a single playing card.

    Attributes:
        rank: Integer rank (2-14, where 11=J, 12=Q, 13=K, 14=A)
        suit: Suit enum (h/d/c/s)
    """
    rank: int
    suit: Suit

    def __post_init__(self):
        """Validate rank is in valid range."""
        if not 2 <= self.rank <= 14:
            raise ValueError(f"Invalid rank: {self.rank}. Must be 2-14.")

    @classmethod
    def from_string(cls, card_str: str) -> Card:
        """Parse card from string notation like 'Ah', 'Ks', '2d', 'Tc'.

        Args:
            card_str: Two-character string (rank + suit)

        Returns:
            Card instance

        Raises:
            ValueError: If string format is invalid
        """
        if len(card_str) != 2:
            raise ValueError(f"Invalid card string: '{card_str}'. Must be 2 characters (rank+suit).")

        rank_char, suit_char = card_str[0], card_str[1].lower()

        # Parse rank
        rank_map = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
            'T': 10, 't': 10,
            'J': 11, 'j': 11,
            'Q': 12, 'q': 12,
            'K': 13, 'k': 13,
            'A': 14, 'a': 14
        }

        if rank_char not in rank_map:
            raise ValueError(f"Invalid rank: '{rank_char}'. Must be 2-9, T, J, Q, K, or A.")

        rank = rank_map[rank_char]

        # Parse suit
        try:
            suit = Suit(suit_char)
        except ValueError:
            raise ValueError(f"Invalid suit: '{suit_char}'. Must be h, d, c, or s.")

        return cls(rank=rank, suit=suit)

    def __repr__(self) -> str:
        """String representation in standard notation."""
        rank_chars = {2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9',
                     10: 'T', 11: 'J', 12: 'Q', 13: 'K', 14: 'A'}
        return f"{rank_chars[self.rank]}{self.suit.value}"

    def __str__(self) -> str:
        """String representation in standard notation."""
        return self.__repr__()
