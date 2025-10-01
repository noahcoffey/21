from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Dict, Mapping, Tuple, Union

__all__ = [
    "Card",
    "SUITS",
    "RANKS",
    "SUIT_SYMBOLS",
]

# Canonical order/constants for a standard 52-card deck
SUITS: Tuple[str, ...] = ("Spades", "Hearts", "Diamonds", "Clubs")
RANKS: Tuple[str, ...] = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")

# Suit to Unicode symbol mapping (for compact display)
SUIT_SYMBOLS: Mapping[str, str] = {
    "Spades": "\u2660",   # ♠
    "Hearts": "\u2665",   # ♥
    "Diamonds": "\u2666", # ♦
    "Clubs": "\u2663",    # ♣
}

# Internal: suit normalization helpers
_SUIT_ALIASES: Dict[str, str] = {
    "s": "Spades",
    "spade": "Spades",
    "spades": "Spades",
    "\u2660": "Spades",
    "h": "Hearts",
    "heart": "Hearts",
    "hearts": "Hearts",
    "\u2665": "Hearts",
    "d": "Diamonds",
    "diamond": "Diamonds",
    "diamonds": "Diamonds",
    "\u2666": "Diamonds",
    "c": "Clubs",
    "club": "Clubs",
    "clubs": "Clubs",
    "\u2663": "Clubs",
}

# Internal: rank normalization helpers
_RANK_ALIASES: Dict[str, str] = {
    "a": "A",
    "ace": "A",
    "1": "A",  # accept 1 as Ace for input flexibility
    "t": "10",
    "10": "10",
    "j": "J",
    "jack": "J",
    "q": "Q",
    "queen": "Q",
    "k": "K",
    "king": "K",
    "2": "2",
    "3": "3",
    "4": "4",
    "5": "5",
    "6": "6",
    "7": "7",
    "8": "8",
    "9": "9",
}

# Base blackjack values; Ace handled specially in Hand (may be 11 or 1)
_RANK_BASE_VALUES: Mapping[str, int] = {
    "A": 11,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 10,
    "Q": 10,
    "K": 10,
}


def _normalize_suit(suit: Union[str, "Card"]) -> str:
    """Normalize a suit input to one of the canonical SUITS values.

    Accepts common aliases and symbols. Raises ValueError on invalid suit.
    """
    if isinstance(suit, Card):  # defensive; not expected typical usage
        suit = suit.suit
    if not isinstance(suit, str):
        raise ValueError(f"Invalid suit type: {type(suit)!r}")
    s = suit.strip()
    # Direct canonical
    if s in SUITS:
        return s
    # Case-insensitive alias lookup
    key = s.lower()
    if key in _SUIT_ALIASES:
        return _SUIT_ALIASES[key]
    # Try direct match of a symbol
    if s in SUIT_SYMBOLS.values():
        for canonical, sym in SUIT_SYMBOLS.items():
            if sym == s:
                return canonical
    raise ValueError(f"Invalid suit: {s!r}")


def _normalize_rank(rank: Union[str, int]) -> str:
    """Normalize rank to one of RANKS. Accepts int 2-10, 'A', 'K', etc.

    Raises ValueError on invalid rank.
    """
    if isinstance(rank, int):
        if 2 <= rank <= 10:
            return str(rank)
        if rank == 1:  # treat 1 as Ace for convenience
            return "A"
        raise ValueError(f"Invalid numeric rank: {rank}")
    if not isinstance(rank, str):
        raise ValueError(f"Invalid rank type: {type(rank)!r}")
    r = rank.strip()
    if r in RANKS:
        return r
    key = r.lower()
    if key in _RANK_ALIASES:
        normalized = _RANK_ALIASES[key]
        if normalized in RANKS:
            return normalized
    raise ValueError(f"Invalid rank: {rank!r}")


@dataclass(frozen=True, slots=True)
class Card:
    """Represents a single playing card.

    - rank: one of RANKS (A, 2-10, J, Q, K)
    - suit: one of SUITS (Spades, Hearts, Diamonds, Clubs)

    The base_value property returns the base blackjack value for the rank
    (Ace=11 by default). Hand evaluation is responsible for converting
    some Aces from 11 to 1 to avoid busting.
    """

    rank: str
    suit: str

    # Class-level references for consumers
    VALID_RANKS: ClassVar[Tuple[str, ...]] = RANKS
    VALID_SUITS: ClassVar[Tuple[str, ...]] = SUITS
    SUIT_SYMBOLS: ClassVar[Mapping[str, str]] = SUIT_SYMBOLS

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_rank(self.rank))
        object.__setattr__(self, "suit", _normalize_suit(self.suit))

    @property
    def symbol(self) -> str:
        """Unicode suit symbol for display (e.g., '♠')."""
        return SUIT_SYMBOLS[self.suit]

    @property
    def base_value(self) -> int:
        """Base blackjack value for this card's rank.

        Ace returns 11 here; the Hand logic should demote to 1 as needed.
        """
        return _RANK_BASE_VALUES[self.rank]

    @property
    def is_ace(self) -> bool:
        return self.rank == "A"

    @property
    def is_face(self) -> bool:
        return self.rank in {"J", "Q", "K"}

    def __str__(self) -> str:  # human-friendly
        # e.g., 'A♠' or '10♥'
        return f"{self.rank}{self.symbol}"

    def __repr__(self) -> str:  # unambiguous, evaluable-style representation
        return f"Card(rank={self.rank!r}, suit={self.suit!r})"


# Backwards/utility aliases for convenience in other modules
get_base_value = lambda rank: _RANK_BASE_VALUES[_normalize_rank(rank)]
