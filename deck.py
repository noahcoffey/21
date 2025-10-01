from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple


RANKS: Tuple[str, ...] = (
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "J",
    "Q",
    "K",
    "A",
)
SUITS: Tuple[str, ...] = ("♠", "♥", "♦", "♣")


@dataclass(frozen=True)
class Card:
    """Represents a single playing card.

    Attributes:
        rank: One of RANKS (e.g., '2'..'10', 'J', 'Q', 'K', 'A').
        suit: One of SUITS (e.g., '♠', '♥', '♦', '♣').
    """

    rank: str
    suit: str

    def __post_init__(self) -> None:
        if self.rank not in RANKS:
            raise ValueError(f"Invalid rank: {self.rank}")
        if self.suit not in SUITS:
            raise ValueError(f"Invalid suit: {self.suit}")

    @property
    def is_ace(self) -> bool:
        return self.rank == "A"

    @property
    def face_value(self) -> int:
        """Returns the nominal face value for Blackjack base calculation.
        Aces are treated as 1 by default; face cards are 10; numeric ranks as ints.
        """
        if self.is_ace:
            return 1
        if self.rank in ("J", "Q", "K"):
            return 10
        return int(self.rank)

    def __str__(self) -> str:  # pragma: no cover - convenience representation
        return f"{self.rank}{self.suit}"

    def __repr__(self) -> str:  # pragma: no cover - convenience representation
        return f"Card(rank={self.rank!r}, suit={self.suit!r})"


class Hand:
    """Represents a player's hand in Blackjack.

    Features:
      - add_card(card)
      - total() that optimally handles multiple aces
      - is_blackjack(): exactly two cards totaling 21
      - is_bust(): total exceeds 21
      - is_soft()/is_hard() detection
    """

    __slots__ = ("_cards",)

    def __init__(self, cards: Iterable[Card] = ()) -> None:
        self._cards: List[Card] = []
        for c in cards:
            self.add_card(c)

    def add_card(self, card: Card) -> None:
        """Add a single Card to the hand.

        Raises:
            TypeError: If the provided object is not a Card.
        """
        if not isinstance(card, Card):
            raise TypeError("add_card expects a Card instance")
        self._cards.append(card)

    def clear(self) -> None:
        """Remove all cards from the hand."""
        self._cards.clear()

    @property
    def cards(self) -> Sequence[Card]:
        """A read-only view of the cards in the hand."""
        return tuple(self._cards)

    def _compute_total_and_softness(self) -> Tuple[int, bool]:
        """Compute the best total (<=21 if possible) and whether it's soft.

        Algorithm:
          - Sum all non-ace values and count aces as 1 initially.
          - While upgrading an ace from 1 to 11 (i.e., +10) keeps total <= 21,
            do so for as many aces as possible; this yields the optimal total.
          - Hand is soft if any ace is counted as 11 in the optimal total.
        """
        total = 0
        aces = 0
        for card in self._cards:
            if card.is_ace:
                aces += 1
                total += 1  # count all aces as 1 initially
            else:
                total += card.face_value

        soft = False
        # Try to upgrade as many aces from 1 to 11 as possible without busting
        # Each upgrade adds +10 (since already counted as 1)
        while aces > 0 and total + 10 <= 21:
            total += 10
            aces -= 1
            soft = True
        # Remaining aces (if any) stay counted as 1
        return total, soft

    def total(self) -> int:
        """Return the optimal blackjack total for the hand.

        Returns the highest total <= 21 if possible, else the minimal total > 21.
        """
        total, _ = self._compute_total_and_softness()
        return total

    def is_soft(self) -> bool:
        """Return True if the hand is soft (i.e., an ace counted as 11)."""
        _, soft = self._compute_total_and_softness()
        return soft

    def is_hard(self) -> bool:
        """Return True if the hand is hard (i.e., no ace counted as 11) and not bust."""
        total, soft = self._compute_total_and_softness()
        return (not soft) and total <= 21

    def is_blackjack(self) -> bool:
        """Return True if the hand is a natural blackjack (two-card 21)."""
        return len(self._cards) == 2 and self.total() == 21

    def is_bust(self) -> bool:
        """Return True if the hand total exceeds 21."""
        return self.total() > 21

    def __len__(self) -> int:
        return len(self._cards)

    def __iter__(self):  # pragma: no cover - convenience
        return iter(self._cards)

    def __repr__(self) -> str:  # pragma: no cover - convenience representation
        return f"Hand(cards={list(map(str, self._cards))}, total={self.total()}, soft={self.is_soft()})"
