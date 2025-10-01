from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Dict, Set, Tuple

__all__ = ["Suit", "Card"]


class Suit(Enum):
    """Enumeration of card suits with Unicode symbols.

    str() and repr() of Suit return the Unicode symbol.
    """

    SPADES = ("Spades", "\u2660")   # ♠
    HEARTS = ("Hearts", "\u2665")   # ♥
    DIAMONDS = ("Diamonds", "\u2666") # ♦
    CLUBS = ("Clubs", "\u2663")     # ♣

    @property
    def fullname(self) -> str:
        return self.value[0]

    @property
    def symbol(self) -> str:
        return self.value[1]

    @property
    def is_red(self) -> bool:
        return self in (Suit.HEARTS, Suit.DIAMONDS)

    @property
    def is_black(self) -> bool:
        return self in (Suit.SPADES, Suit.CLUBS)

    def __str__(self) -> str:
        return self.symbol

    def __repr__(self) -> str:
        return self.symbol

    @classmethod
    def from_symbol(cls, symbol: str) -> "Suit":
        """Create a Suit from its Unicode symbol.

        Args:
            symbol: One of "♠", "♥", "♦", "♣".

        Raises:
            ValueError: If the symbol does not map to a Suit.
        """
        mapping = {s.symbol: s for s in cls}
        try:
            return mapping[symbol]
        except KeyError as exc:
            raise ValueError(f"Unknown suit symbol: {symbol!r}") from exc


@dataclass(frozen=True)
class Card:
    """A standard playing card used for Blackjack.

    - rank: 1..13 (Ace=1, Jack=11, Queen=12, King=13)
    - suit: Suit enum

    str() and repr() render as a compact glyph, e.g. "[A♠]", "[10♦]".
    """

    rank: int
    suit: Suit

    # Class-level maps/constants
    RANK_LABELS: ClassVar[Dict[int, str]] = {
        1: "A",
        2: "2",
        3: "3",
        4: "4",
        5: "5",
        6: "6",
        7: "7",
        8: "8",
        9: "9",
        10: "10",
        11: "J",
        12: "Q",
        13: "K",
    }
    FACE_RANKS: ClassVar[Set[int]] = {11, 12, 13}

    def __post_init__(self) -> None:
        if not isinstance(self.suit, Suit):
            raise TypeError(f"suit must be a Suit, got {type(self.suit).__name__}")
        if not isinstance(self.rank, int):
            raise TypeError(f"rank must be an int, got {type(self.rank).__name__}")
        if not 1 <= self.rank <= 13:
            raise ValueError("rank must be between 1 (Ace) and 13 (King)")

    @property
    def label(self) -> str:
        """Short string label for rank (e.g., 'A', '10', 'K')."""
        return self.RANK_LABELS[self.rank]

    @property
    def is_ace(self) -> bool:
        return self.rank == 1

    @property
    def is_face(self) -> bool:
        return self.rank in self.FACE_RANKS

    @property
    def blackjack_values(self) -> Tuple[int, ...]:
        """Potential Blackjack values for this card.

        - Ace: (1, 11)
        - Face cards (J, Q, K): (10,)
        - Number cards: (rank,)
        """
        if self.is_ace:
            return (1, 11)
        if self.is_face:
            return (10,)
        return (self.rank,)

    def __str__(self) -> str:
        return f"[{self.label}{self.suit}]"

    def __repr__(self) -> str:
        return f"[{self.label}{self.suit}]"
