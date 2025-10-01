from __future__ import annotations

import random
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import List, Optional

# Configure Decimal for currency operations
getcontext().prec = 28

SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
RANKS = [
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
]


class Card:
    def __init__(self, rank: str, suit: str) -> None:
        self.rank = rank
        self.suit = suit

    @property
    def value(self) -> int:
        if self.rank in ("J", "Q", "K"):
            return 10
        if self.rank == "A":
            return 11  # Ace initially as 11; Hand will adjust as needed
        return int(self.rank)

    def __repr__(self) -> str:
        return f"{self.rank} of {self.suit}"


class Hand:
    def __init__(self) -> None:
        self.cards: List[Card] = []

    def add_card(self, card: Card) -> None:
        self.cards.append(card)

    def values(self) -> int:
        # Return best total <= 21, else smallest total
        total = 0
        aces = 0
        for c in self.cards:
            total += c.value
            if c.rank == "A":
                aces += 1
        # Adjust aces from 11 to 1 as needed
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.values() == 21

    def is_bust(self) -> bool:
        return self.values() > 21

    def is_soft(self) -> bool:
        # Soft if contains an Ace counted as 11
        total = 0
        aces = 0
        for c in self.cards:
            total += c.value
            if c.rank == "A":
                aces += 1
        # If we can reduce by 10 and still <=21, that ace counted as 11
        return aces > 0 and total <= 21

    def __repr__(self) -> str:
        return f"Hand({self.cards}, total={self.values()})"


class Deck:
    def __init__(self, num_decks: int = 1, reshuffle_threshold: int = 15) -> None:
        self.num_decks = max(1, num_decks)
        self.reshuffle_threshold = reshuffle_threshold
        self._cards: List[Card] = []
        self._build_and_shuffle()

    def _build_and_shuffle(self) -> None:
        self._cards = [
            Card(rank, suit)
            for _ in range(self.num_decks)
            for suit in SUITS
            for rank in RANKS
        ]
        random.shuffle(self._cards)

    def draw(self) -> Card:
        if len(self._cards) == 0:
            self._build_and_shuffle()
        return self._cards.pop()

    def remaining(self) -> int:
        return len(self._cards)

    def needs_reshuffle(self) -> bool:
        return self.remaining() < self.reshuffle_threshold

    def reshuffle(self) -> None:
        self._build_and_shuffle()


@dataclass
class Stats:
    rounds: int = 0
    wins: int = 0
    losses: int = 0
    pushes: int = 0
    blackjacks: int = 0
    total_bet: Decimal = Decimal("0.00")
    net_won: Decimal = Decimal("0.00")  # positive means player profit


class Player:
    def __init__(self, name: str, chips: Decimal) -> None:
        self.name = name
        self.chips: Decimal = Player._to_money(chips)
        self.stats = Stats()

    @staticmethod
    def _to_money(amount: Decimal) -> Decimal:
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def can_bet(self, amount: Decimal) -> bool:
        amount = Player._to_money(amount)
        return amount > 0 and self.chips >= amount

    def place_bet(self, amount: Decimal) -> Decimal:
        amount = Player._to_money(amount)
        if amount <= 0:
            raise ValueError("Bet must be positive")
        if amount > self.chips:
            raise ValueError("Insufficient chips for bet")
        self.chips -= amount
        self.stats.total_bet += amount
        return amount

    def settle(self, bet: Decimal, outcome: str) -> Decimal:
        # outcome in {"blackjack", "win", "push", "loss"}
        bet = Player._to_money(bet)
        profit = Decimal("0.00")
        self.stats.rounds += 1
        if outcome == "blackjack":
            # 3:2 payout + return bet
            profit = (bet * Decimal(3) / Decimal(2)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            self.chips += bet + profit
            self.stats.wins += 1
            self.stats.blackjacks += 1
            self.stats.net_won += profit
        elif outcome == "win":
            # 1:1 payout + return bet
            profit = bet
            self.chips += bet + profit
            self.stats.wins += 1
            self.stats.net_won += profit
        elif outcome == "push":
            # Return bet only
            self.chips += bet
            self.stats.pushes += 1
            # net_won unchanged
        elif outcome == "loss":
            # Player already paid bet when placing it; nothing returned
            self.stats.losses += 1
            self.stats.net_won -= bet
        else:
            raise ValueError(f"Unknown outcome: {outcome}")
        return profit


class BlackjackGame:
    def __init__(self, num_decks: int = 6, starting_chips: Decimal = Decimal("1000.00")) -> None:
        self.deck = Deck(num_decks=num_decks)
        self.player = Player(name="Player", chips=starting_chips)
        self.dealer_hand: Optional[Hand] = None
        self.player_hand: Optional[Hand] = None

    def _deal_initial(self) -> None:
        self.player_hand = Hand()
        self.dealer_hand = Hand()
        # Two to player, two to dealer
        self.player_hand.add_card(self.deck.draw())
        self.dealer_hand.add_card(self.deck.draw())
        self.player_hand.add_card(self.deck.draw())
        self.dealer_hand.add_card(self.deck.draw())

    def _dealer_play(self) -> None:
        assert self.dealer_hand is not None
        # Dealer stands on all 17 (including soft)
        while self.dealer_hand.values() < 17:
            self.dealer_hand.add_card(self.deck.draw())

    def _resolve_outcome(self, bet: Decimal) -> str:
        assert self.player_hand is not None and self.dealer_hand is not None
        player_total = self.player_hand.values()
        dealer_total = self.dealer_hand.values()

        # Player busts
        if self.player_hand.is_bust():
            return "loss"
        # Dealer busts
        if self.dealer_hand.is_bust():
            return "win"
        # Compare totals
        if player_total > dealer_total:
            # Note: Only two-card 21 is blackjack. If player reaches 21 with >2 cards, it's a standard win.
            if self.player_hand.is_blackjack():
                return "blackjack"
            return "win"
        if player_total < dealer_total:
            return "loss"
        # Push
        return "push"

    def _check_natural_blackjack_phase(self, bet: Decimal) -> Optional[str]:
        # Returns outcome if round ends immediately due to naturals, else None
        assert self.player_hand is not None and self.dealer_hand is not None
        player_bj = self.player_hand.is_blackjack()
        dealer_bj = self.dealer_hand.is_blackjack()
        if player_bj and dealer_bj:
            self.player.settle(bet, "push")
            return "push"
        if player_bj and not dealer_bj:
            self.player.settle(bet, "blackjack")
            return "blackjack"
        if dealer_bj and not player_bj:
            self.player.settle(bet, "loss")
            return "loss"
        return None

    def run_round(self, bet: Decimal) -> dict:
        # Reshuffle if deck running low
        if self.deck.needs_reshuffle():
            self.deck.reshuffle()

        # Place bet
        bet = Player._to_money(bet)
        if not self.player.can_bet(bet):
            raise ValueError("Cannot place bet: insufficient chips or invalid amount")
        placed = self.player.place_bet(bet)

        # Deal
        self._deal_initial()

        # Check naturals
        immediate = self._check_natural_blackjack_phase(placed)
        if immediate is not None:
            return self._round_state(outcome=immediate, bet=bet)

        # Player decision loop (simple terminal prompt)
        while True:
            # Auto-stand on 21 (but not blackjack since already handled)
            if self.player_hand.values() >= 21:
                break
            action = self._prompt_action()
            if action == "h":
                self.player_hand.add_card(self.deck.draw())
                if self.player_hand.is_bust():
                    break
            elif action == "s":
                break

        # Dealer plays if player didn't bust
        if not self.player_hand.is_bust():
            self._dealer_play()

        # Resolve
        outcome = self._resolve_outcome(placed)
        self.player.settle(placed, outcome)
        return self._round_state(outcome=outcome, bet=bet)

    def _prompt_action(self) -> str:
        # Minimal terminal prompt for hit/stand
        while True:
            raw = input("Hit or Stand? [h/s]: ").strip().lower()
            if raw in ("h", "s"):
                return raw
            print("Please enter 'h' to hit or 's' to stand.")

    def _round_state(self, outcome: str, bet: Decimal) -> dict:
        assert self.player_hand is not None and self.dealer_hand is not None
        return {
            "outcome": outcome,
            "bet": str(bet),
            "player_hand": [str(c) for c in self.player_hand.cards],
            "player_total": self.player_hand.values(),
            "dealer_hand": [str(c) for c in self.dealer_hand.cards],
            "dealer_total": self.dealer_hand.values(),
            "player_chips": str(self.player.chips),
            "stats": {
                "rounds": self.player.stats.rounds,
                "wins": self.player.stats.wins,
                "losses": self.player.stats.losses,
                "pushes": self.player.stats.pushes,
                "blackjacks": self.player.stats.blackjacks,
                "total_bet": str(self.player.stats.total_bet),
                "net_won": str(self.player.stats.net_won),
            },
        }


def _choose_bet(player: Player) -> Decimal:
    while True:
        try:
            raw = input(f"Enter bet (available {player.chips}): ").strip()
            amt = Decimal(raw)
            if amt <= 0:
                print("Bet must be positive.")
                continue
            if amt > player.chips:
                print("Insufficient chips.")
                continue
            return amt.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except Exception:
            print("Invalid amount. Try again.")


def main() -> None:
    print("Welcome to Terminal Blackjack! Payouts: Blackjack 3:2, Wins 1:1, Push returns bet.")
    game = BlackjackGame(num_decks=6, starting_chips=Decimal("1000.00"))
    while True:
        if game.player.chips <= 0:
            print("You are out of chips. Game over.")
            break
        try:
            bet = _choose_bet(game.player)
            result = game.run_round(bet)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue

        print("--- Round Result ---")
        print(f"Player hand ({result['player_total']}): {', '.join(result['player_hand'])}")
        print(f"Dealer hand ({result['dealer_total']}): {', '.join(result['dealer_hand'])}")
        print(f"Outcome: {result['outcome'].upper()} | Chips: {result['player_chips']}")
        print(
            f"Stats -> Rounds: {result['stats']['rounds']}, W: {result['stats']['wins']}, L: {result['stats']['losses']}, P: {result['stats']['pushes']}, BJ: {result['stats']['blackjacks']}"
        )
        again = input("Play another round? [y/n]: ").strip().lower()
        if again != "y":
            break

    print("Thanks for playing!")


if __name__ == "__main__":
    main()
