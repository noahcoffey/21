from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Sequence, Optional, Union

__all__ = ["Card", "Deck", "RANKS", "SUITS"]

# Standard 52-card deck definitions (Ace high by convention; hand logic evaluates value)
RANKS: Sequence[str] = (
    "A",
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
)

SUITS: Sequence[str] = ("S", "H", "D", "C")  # Spades, Hearts, Diamonds, Clubs


@dataclass(frozen=True)
class Card:
    """Immutable representation of a playing card.

    Attributes:
        rank: Rank label (e.g., "A", "10", "K").
        suit: Suit label ("S", "H", "D", "C").
    """

    rank: str
    suit: str

    def __str__(self) -> str:  # e.g., "AS" for Ace of Spades
        return f"{self.rank}{self.suit}"

    def __repr__(self) -> str:
        return f"Card(rank={self.rank!r}, suit={self.suit!r})"


class Deck:
    """A shoe of one or more standard 52-card decks.

    - Supports building N decks, shuffling (random.shuffle), drawing cards, checking remaining count,
      and resetting/rebuilding.
    - The deck does not reshuffle automatically; call reset()/rebuild() explicitly between hands.

    Args:
        num_decks: Number of standard 52-card decks to include.
        rng: Optional random.Random instance for deterministic shuffling in tests.
        shuffle_on_init: Shuffle immediately after building at initialization.
    """

    def __init__(
        self,
        num_decks: int = 1,
        rng: Optional[random.Random] = None,
        shuffle_on_init: bool = True,
    ) -> None:
        if not isinstance(num_decks, int) or num_decks < 1:
            raise ValueError("num_decks must be a positive integer")
        self.num_decks: int = num_decks
        self._rng: random.Random = rng if rng is not None else random.Random()
        self._cards: List[Card] = []
        self._discards: List[Card] = []
        self.rebuild(shuffle=shuffle_on_init)

    def __len__(self) -> int:
        return self.remaining()

    def __repr__(self) -> str:
        return f"Deck(num_decks={self.num_decks}, remaining={self.remaining()})"

    @property
    def cards(self) -> Sequence[Card]:
        """A read-only snapshot of the remaining cards (top of deck is the end of the sequence)."""
        return tuple(self._cards)

    def remaining(self) -> int:
        """Number of cards left to draw."""
        return len(self._cards)

    def shuffle(self) -> None:
        """Shuffle the remaining cards using the configured RNG.

        Note: This does not automatically occur during play; call explicitly between hands.
        """
        self._rng.shuffle(self._cards)

    def rebuild(self, shuffle: bool = True) -> "Deck":
        """Rebuild the shoe to a full set of cards and optionally shuffle.

        Args:
            shuffle: If True, shuffle after rebuilding.

        Returns:
            self (for method chaining).
        """
        cards: List[Card] = []
        for _ in range(self.num_decks):
            for suit in SUITS:
                for rank in RANKS:
                    cards.append(Card(rank=rank, suit=suit))
        self._cards = cards
        self._discards.clear()
        if shuffle:
            self.shuffle()
        return self

    def reset(self) -> "Deck":
        """Reset the deck to a full, shuffled state.

        Equivalent to rebuild(shuffle=True).
        """
        return self.rebuild(shuffle=True)

    def draw(self, n: int = 1) -> Union[Card, List[Card]]:
        """Draw card(s) from the top of the deck.

        Args:
            n: Number of cards to draw (default 1).

        Returns:
            A single Card if n == 1, otherwise a list of Cards of length n.

        Raises:
            ValueError: If n < 1 or if there are not enough cards remaining.
        """
        if not isinstance(n, int) or n < 1:
            raise ValueError("n must be a positive integer")
        if n > len(self._cards):
            raise ValueError("Not enough cards remaining to draw the requested amount")

        if n == 1:
            card = self._cards.pop()  # top of deck is end of list
            self._discards.append(card)
            return card

        drawn: List[Card] = [self._cards.pop() for _ in range(n)]
        self._discards.extend(drawn)
        return drawn

    def discard_pile_size(self) -> int:
        """Number of cards in the discard pile (useful for diagnostics/tests)."""
        return len(self._discards)
