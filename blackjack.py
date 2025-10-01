import random
from dataclasses import dataclass, field
from typing import List, Iterable


SUITS = ("Hearts", "Diamonds", "Clubs", "Spades")
RANKS = (
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


def rank_value(rank: str) -> int:
    if rank in ("J", "Q", "K"):
        return 10
    if rank == "A":
        return 11
    return int(rank)


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str

    @property
    def value(self) -> int:
        return rank_value(self.rank)

    def __str__(self) -> str:
        return f"{self.rank} of {self.suit}"


@dataclass
class Hand:
    cards: List[Card] = field(default_factory=list)

    def add_card(self, card: Card) -> None:
        self.cards.append(card)

    def add_cards(self, cards: Iterable[Card]) -> None:
        self.cards.extend(cards)

    def value(self) -> int:
        total = sum(c.value for c in self.cards)
        # Adjust for Aces
        aces = sum(1 for c in self.cards if c.rank == "A")
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.value() == 21

    def is_bust(self) -> bool:
        return self.value() > 21

    def discard_all(self) -> List[Card]:
        discarded = list(self.cards)
        self.cards.clear()
        return discarded

    def __str__(self) -> str:
        joined = ", ".join(str(c) for c in self.cards)
        return f"[{joined}] (value={self.value()})"


class Deck:
    def __init__(self, num_decks: int = 1, reshuffle_threshold: int = 15) -> None:
        if num_decks < 1:
            raise ValueError("num_decks must be >= 1")
        if reshuffle_threshold < 1:
            raise ValueError("reshuffle_threshold must be >= 1")
        self.num_decks = num_decks
        self.reshuffle_threshold = reshuffle_threshold
        self._draw_pile: List[Card] = []
        self._discard_pile: List[Card] = []
        self._build_shoe()
        self._shuffle_draw_pile()

    def _build_shoe(self) -> None:
        self._draw_pile.clear()
        for _ in range(self.num_decks):
            for suit in SUITS:
                for rank in RANKS:
                    self._draw_pile.append(Card(rank=rank, suit=suit))

    def _shuffle_draw_pile(self) -> None:
        random.shuffle(self._draw_pile)

    def cards_remaining(self) -> int:
        return len(self._draw_pile)

    def discard_pile_size(self) -> int:
        return len(self._discard_pile)

    def draw(self, n: int = 1) -> List[Card]:
        if n < 1:
            return []
        drawn: List[Card] = []
        for _ in range(n):
            if not self._draw_pile:
                # If draw pile is empty, attempt to reshuffle discards
                self._reshuffle_from_discards()
                if not self._draw_pile:
                    raise RuntimeError("Cannot draw a card: both draw pile and discard pile are empty.")
            drawn.append(self._draw_pile.pop())
        return drawn

    def discard(self, cards: Iterable[Card]) -> None:
        # Add cards to discard pile; input order doesn't matter
        for c in cards:
            self._discard_pile.append(c)

    def reshuffle_if_needed(self) -> None:
        if self.cards_remaining() < self.reshuffle_threshold:
            self._reshuffle_from_discards()

    def _reshuffle_from_discards(self) -> None:
        if not self._discard_pile:
            return
        # Move all discards to draw pile and shuffle
        self._draw_pile.extend(self._discard_pile)
        self._discard_pile.clear()
        self._shuffle_draw_pile()


@dataclass
class Player:
    name: str
    hand: Hand = field(default_factory=Hand)

    def reset_hand(self) -> List[Card]:
        return self.hand.discard_all()


class Game:
    def __init__(self, num_decks: int = 6, reshuffle_threshold: int = 15) -> None:
        self.deck = Deck(num_decks=num_decks, reshuffle_threshold=reshuffle_threshold)
        self.player = Player(name="Player")
        self.dealer = Player(name="Dealer")

    def deal_initial(self) -> None:
        # Each gets two cards, player first
        for _ in range(2):
            self.player.hand.add_card(self.deck.draw(1)[0])
            self.dealer.hand.add_card(self.deck.draw(1)[0])

    def player_turn(self) -> None:
        # Simple strategy placeholder: hit until 16 or more
        while self.player.hand.value() < 16:
            self.player.hand.add_card(self.deck.draw(1)[0])
            if self.player.hand.is_bust():
                break

    def dealer_turn(self) -> None:
        # Dealer stands on 17 or more (typical rule)
        while self.dealer.hand.value() < 17:
            self.dealer.hand.add_card(self.deck.draw(1)[0])
            if self.dealer.hand.is_bust():
                break

    def settle(self) -> str:
        p_val = self.player.hand.value()
        d_val = self.dealer.hand.value()
        if self.player.hand.is_bust():
            return "Dealer wins (player busts)"
        if self.dealer.hand.is_bust():
            return "Player wins (dealer busts)"
        if p_val > d_val:
            return "Player wins"
        if d_val > p_val:
            return "Dealer wins"
        return "Push"

    def cleanup_round(self) -> None:
        # Return all cards to discard, then reshuffle if threshold reached
        player_discards = self.player.reset_hand()
        dealer_discards = self.dealer.reset_hand()
        self.deck.discard(player_discards)
        self.deck.discard(dealer_discards)
        # Trigger reshuffle conditionally based on remaining draw pile size
        self.deck.reshuffle_if_needed()

    def play_round(self, verbose: bool = False) -> str:
        # Ensure deck is healthy before dealing
        self.deck.reshuffle_if_needed()

        self.deal_initial()

        if verbose:
            print(f"Player: {self.player.hand}")
            print(f"Dealer shows: {self.dealer.hand.cards[0]}")

        # Player and Dealer turns
        if not self.player.hand.is_blackjack():
            self.player_turn()
        if not self.player.hand.is_bust():
            self.dealer_turn()

        result = self.settle()

        if verbose:
            print(f"Dealer: {self.dealer.hand}")
            print(result)
            print(f"Draw pile remaining before cleanup: {self.deck.cards_remaining()}")
            print(f"Discard pile before cleanup: {self.deck.discard_pile_size()}")

        # Return all cards to discard and possibly reshuffle
        self.cleanup_round()

        if verbose:
            print(f"Draw pile after cleanup/reshuffle: {self.deck.cards_remaining()}")
            print(f"Discard pile after cleanup/reshuffle: {self.deck.discard_pile_size()}\n")

        return result

    def run(self, num_rounds: int = 5, verbose: bool = True) -> None:
        for i in range(1, num_rounds + 1):
            if verbose:
                print(f"--- Round {i} ---")
            self.play_round(verbose=verbose)


if __name__ == "__main__":
    # Example CLI run demonstrating deck lifecycle and reshuffling
    game = Game(num_decks=6, reshuffle_threshold=15)
    game.run(num_rounds=10, verbose=True)
