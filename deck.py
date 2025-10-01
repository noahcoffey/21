"""
Deck implementation for a Blackjack game.

Features:
- Supports N standard 52-card decks (shoe)
- shuffle(), draw(), discard() with discard pile management
- Auto-reshuffle when remaining < auto_reshuffle_threshold (default: 15)
- Allow injecting a predefined shoe for tests (keeps order; not shuffled on init)
- Optional card_factory to create Card objects compatible with a separate Card model

Python 3.8+
"""
from __future__ import annotations

import random
from typing import Any, Callable, Iterable, List, Optional, Sequence, Union


CardFactory = Callable[[str, str], Any]
CardLike = Any


class Deck:
    """A shoe of one or more 52-card decks with discard management.

    Notes:
    - If predefined_shoe is provided, its order is preserved on initialization
      (no automatic shuffle). This is useful for deterministic tests.
    - Auto-reshuffle occurs when remaining cards < auto_reshuffle_threshold
      and there are cards in the discard pile. The reshuffle combines the
      remaining draw pile and the discard pile and shuffles them together.

    Parameters
    - num_decks: number of standard 52-card decks to include in the shoe if
      no predefined_shoe is provided. Must be >= 1.
    - predefined_shoe: an explicit sequence/iterable of cards to use as the
      initial draw pile (top of deck is the right/end of the list). If provided,
      num_decks is ignored for the initial content.
    - auto_reshuffle_threshold: when remaining < threshold and there are
      discarded cards, the deck will auto-reshuffle before the next draw.
    - rng: an instance of random.Random to allow deterministic shuffles in tests.
      If None, a new random.Random() is created.
    - card_factory: optional callable rank, suit -> card object. Used only when
      building a standard shoe (i.e., when predefined_shoe is not provided).
    - shuffle_on_init: if True and no predefined_shoe, shuffle the initial shoe.
    """

    RANKS: Sequence[str] = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
    SUITS: Sequence[str] = ("S", "H", "D", "C")  # Spades, Hearts, Diamonds, Clubs

    def __init__(
        self,
        num_decks: int = 1,
        *,
        predefined_shoe: Optional[Union[Sequence[CardLike], Iterable[CardLike]]] = None,
        auto_reshuffle_threshold: int = 15,
        rng: Optional[random.Random] = None,
        card_factory: Optional[CardFactory] = None,
        shuffle_on_init: bool = True,
    ) -> None:
        if num_decks < 1:
            raise ValueError("num_decks must be >= 1")
        if auto_reshuffle_threshold < 0:
            raise ValueError("auto_reshuffle_threshold must be >= 0")

        self._num_decks: int = num_decks
        self._rng: random.Random = rng if rng is not None else random.Random()
        self._auto_reshuffle_threshold: int = auto_reshuffle_threshold
        self._discard: List[CardLike] = []
        self._card_factory: CardFactory = card_factory if card_factory is not None else self._default_card_factory

        if predefined_shoe is not None:
            # Preserve provided order; top of deck is end of list
            self._draw: List[CardLike] = list(predefined_shoe)
            if shuffle_on_init:
                # Respect tests that explicitly want a shuffled predefined shoe
                self.shuffle(full=False)
        else:
            self._draw = self._build_standard_shoe(self._num_decks, self._card_factory)
            if shuffle_on_init:
                self.shuffle(full=True)

    # ---------------------- Public API ----------------------
    @property
    def remaining(self) -> int:
        """Number of cards remaining in the draw pile."""
        return len(self._draw)

    @property
    def discard_count(self) -> int:
        """Number of cards currently in the discard pile."""
        return len(self._discard)

    @property
    def total_count(self) -> int:
        """Total number of cards across draw and discard piles."""
        return len(self._draw) + len(self._discard)

    @property
    def auto_reshuffle_threshold(self) -> int:
        return self._auto_reshuffle_threshold

    @auto_reshuffle_threshold.setter
    def auto_reshuffle_threshold(self, value: int) -> None:
        if value < 0:
            raise ValueError("auto_reshuffle_threshold must be >= 0")
        self._auto_reshuffle_threshold = value

    def shuffle(self, *, full: bool = True) -> None:
        """Shuffle the deck.

        - If full is True (default), combine draw and discard piles and shuffle
          them together, clearing the discard pile.
        - If full is False, shuffle only the remaining draw pile in place.
        """
        if full:
            if self._discard:
                self._draw.extend(self._discard)
                self._discard.clear()
        # Shuffle draw pile in place
        self._rng.shuffle(self._draw)

    def draw(self, count: int = 1) -> Union[CardLike, List[CardLike]]:
        """Draw card(s) from the top of the deck.

        - Auto-reshuffles if remaining < auto_reshuffle_threshold and there are
          cards in the discard pile.
        - If insufficient cards remain to satisfy the draw, it will attempt a
          full reshuffle (combining discard + draw). If still insufficient
          (i.e., total_count < count), raises IndexError.

        Returns a single card if count == 1, otherwise a list of cards.
        """
        if count < 1:
            return []  # type: ignore[return-value]

        # Auto-reshuffle if below threshold and there are discards
        self._maybe_auto_reshuffle()

        if self.remaining < count:
            # Attempt a full reshuffle if possible
            if self._discard:
                self.shuffle(full=True)
            if self.remaining < count:
                raise IndexError("Not enough cards remaining in the shoe to draw the requested amount")

        if count == 1:
            return self._draw.pop()  # top of deck is end of list
        else:
            # Slice from end for efficiency
            out = self._draw[-count:]
            del self._draw[-count:]
            return out

    def discard(self, cards: Union[CardLike, Iterable[CardLike]]) -> None:
        """Add card(s) to the discard pile.

        Accepts a single card or an iterable of cards.
        """
        if cards is None:
            return
        if isinstance(cards, (list, tuple, set)):
            self._discard.extend(cards)  # type: ignore[arg-type]
        else:
            # Single card
            self._discard.append(cards)

    def needs_reshuffle(self) -> bool:
        """Return True if the deck should auto-reshuffle on next draw."""
        return self.remaining < self._auto_reshuffle_threshold and bool(self._discard)

    def reset(self, *, predefined_shoe: Optional[Union[Sequence[CardLike], Iterable[CardLike]]] = None, shuffle_on_init: bool = True) -> None:
        """Reset the deck to a fresh shoe.

        If predefined_shoe is provided, it is used (order preserved unless
        shuffle_on_init=True). Otherwise a standard shoe based on num_decks is
        built. Discard pile is cleared.
        """
        self._discard.clear()
        if predefined_shoe is not None:
            self._draw = list(predefined_shoe)
            if shuffle_on_init:
                self.shuffle(full=False)
        else:
            self._draw = self._build_standard_shoe(self._num_decks, self._card_factory)
            if shuffle_on_init:
                self.shuffle(full=True)

    def __len__(self) -> int:
        return self.remaining

    def __repr__(self) -> str:
        return (
            f"Deck(num_decks={self._num_decks}, remaining={self.remaining}, "
            f"discard={self.discard_count}, threshold={self._auto_reshuffle_threshold})"
        )

    # ---------------------- Internal helpers ----------------------
    def _maybe_auto_reshuffle(self) -> None:
        if self.needs_reshuffle():
            self.shuffle(full=True)

    @staticmethod
    def _default_card_factory(rank: str, suit: str) -> dict:
        """Default card representation used when no card_factory is provided.

        Returns a simple dict with rank and suit keys to avoid coupling to any
        specific Card class. Games can provide a custom card_factory to create
        their own Card objects.
        """
        return {"rank": rank, "suit": suit}

    @classmethod
    def _build_standard_shoe(cls, num_decks: int, card_factory: CardFactory) -> List[CardLike]:
        shoe: List[CardLike] = []
        for _ in range(num_decks):
            for suit in cls.SUITS:
                for rank in cls.RANKS:
                    shoe.append(card_factory(rank, suit))
        return shoe


__all__ = ["Deck"]
