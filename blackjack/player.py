from dataclasses import dataclass, field
from typing import Optional

try:
    # When used as a package/module
    from .deck import Hand, Card, Deck
except ImportError:  # pragma: no cover - support running as a script
    # When run as a loose script without package context
    from deck import Hand, Card, Deck  # type: ignore


@dataclass
class Player:
    name: str
    is_dealer: bool = False
    hand: Hand = field(default_factory=Hand)
    _has_stood: bool = field(default=False, init=False, repr=False)

    def new_round(self) -> None:
        self.hand.clear()
        self._has_stood = False

    def hit(self, deck: Deck) -> Card:
        card = deck.deal_one()
        self.hand.add_card(card)
        return card

    def stand(self) -> None:
        self._has_stood = True

    @property
    def has_stood(self) -> bool:
        return self._has_stood

    def __str__(self) -> str:
        role = "Dealer" if self.is_dealer else "Player"
        return f"{role}({self.name}): {self.hand} [{self.hand.value}]"
