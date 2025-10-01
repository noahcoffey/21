from dataclasses import dataclass, field
from typing import List
import random

SUITS = ("S", "H", "D", "C")  # Spades, Hearts, Diamonds, Clubs
RANKS = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A")

RANK_VALUES = {
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
    "A": 11,  # Ace handled as 11 or 1 in Hand
}


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str

    @property
    def value(self) -> int:
        return RANK_VALUES[self.rank]

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"


@dataclass
class Hand:
    cards: List[Card] = field(default_factory=list)

    def add_card(self, card: Card) -> None:
        self.cards.append(card)

    def clear(self) -> None:
        self.cards.clear()

    @property
    def value(self) -> int:
        total = sum(c.value for c in self.cards)
        aces = sum(1 for c in self.cards if c.rank == "A")
        # Reduce Ace(s) from 11 to 1 as needed
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    @property
    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.value == 21

    @property
    def is_bust(self) -> bool:
        return self.value > 21

    def __str__(self) -> str:
        return " ".join(str(c) for c in self.cards)


class Deck:
    """
    Manages a multi-deck shoe. Reshuffles automatically when remaining < reshuffle_threshold.
    """

    def __init__(
        self,
        num_decks: int = 1,
        *,
        seed: int = None,
        reshuffle_threshold: int = 15,
    ) -> None:
        if num_decks < 1:
            raise ValueError("num_decks must be >= 1")
        if reshuffle_threshold < 1:
            raise ValueError("reshuffle_threshold must be >= 1")
        self.num_decks = num_decks
        self.reshuffle_threshold = reshuffle_threshold
        self._rng = random.Random(seed)
        self._shoe: List[Card] = []
        self._build_and_shuffle_shoe()

    def _build_and_shuffle_shoe(self) -> None:
        self._shoe = [
            Card(rank, suit)
            for _ in range(self.num_decks)
            for suit in SUITS
            for rank in RANKS
        ]
        self._rng.shuffle(self._shoe)

    @property
    def remaining(self) -> int:
        return len(self._shoe)

    def _maybe_reshuffle(self) -> None:
        if self.remaining < self.reshuffle_threshold:
            # Prepare a fresh shoe for next deals
            self._build_and_shuffle_shoe()

    def deal_one(self) -> Card:
        if not self._shoe:
            self._build_and_shuffle_shoe()
        card = self._shoe.pop()
        # After dealing, ensure we have enough cards for continued play
        self._maybe_reshuffle()
        return card
