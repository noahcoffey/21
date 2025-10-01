from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional

# Suits and ranks used to build a standard 52-card deck
SUITS = ("Hearts", "Diamonds", "Clubs", "Spades")
RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")


@dataclass(frozen=True)
class Card:
    """A playing card with rank and suit.

    Points are derived from rank as follows:
    - Aces are treated as 11 by default (Hand will adjust down to 1 as needed)
    - Face cards (J, Q, K) are 10
    - Number cards are their numeric value
    """

    rank: str
    suit: str

    @property
    def points(self) -> int:
        if self.rank == "A":
            return 11
        if self.rank in {"K", "Q", "J"}:
            return 10
        return int(self.rank)

    def __str__(self) -> str:
        return f"{self.rank} of {self.suit}"

    def __repr__(self) -> str:
        return f"Card(rank={self.rank!r}, suit={self.suit!r})"


class Deck:
    """A standard deck of playing cards.

    Supports one or more combined decks (e.g., 6- or 8-deck shoes).
    """

    def __init__(self, num_decks: int = 1, rng: Optional[random.Random] = None) -> None:
        if num_decks < 1:
            raise ValueError("num_decks must be >= 1")
        self._rng = rng if rng is not None else random.Random()
        self._num_decks = num_decks
        self.cards: List[Card] = []
        self.reset()

    def reset(self) -> None:
        """Reset the shoe to a freshly shuffled set of cards."""
        self.cards = [
            Card(rank=r, suit=s)
            for _ in range(self._num_decks)
            for s in SUITS
            for r in RANKS
        ]
        self.shuffle()

    def shuffle(self) -> None:
        self._rng.shuffle(self.cards)

    def draw(self) -> Card:
        """Draw a single card from the top of the deck.

        Raises IndexError if the deck is empty.
        """
        if not self.cards:
            raise IndexError("The deck is empty.")
        return self.cards.pop()

    def __len__(self) -> int:  # allows len(deck)
        return len(self.cards)


class Hand:
    """A Blackjack hand with ace valuation that avoids busting when possible."""

    def __init__(self) -> None:
        self.cards: List[Card] = []

    def add_card(self, card: Card) -> None:
        self.cards.append(card)

    def clear(self) -> None:
        self.cards.clear()

    @property
    def total(self) -> int:
        """Compute the best total not exceeding 21 using ace demotion.

        Aces count as 11 initially; demote to 1 as needed while total > 21.
        """
        total = sum(c.points for c in self.cards)
        aces = sum(1 for c in self.cards if c.rank == "A")
        # Demote aces from 11 to 1 (subtract 10) while over 21
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    @property
    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.total == 21

    @property
    def is_bust(self) -> bool:
        return self.total > 21

    def __str__(self) -> str:
        cards_s = ", ".join(str(c) for c in self.cards)
        return f"[{cards_s}] (total={self.total})"
