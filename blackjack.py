from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Tuple, Optional


SUITS = ["\u2660", "\u2665", "\u2666", "\u2663"]  # Spades, Hearts, Diamonds, Clubs
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"


class Deck:
    """Represents a multi-deck shoe with reshuffle support."""

    def __init__(self, num_decks: int = 6, reshuffle_threshold: int = 15) -> None:
        if num_decks <= 0:
            raise ValueError("num_decks must be >= 1")
        if reshuffle_threshold <= 0:
            raise ValueError("reshuffle_threshold must be >= 1")
        self.num_decks = num_decks
        self.reshuffle_threshold = reshuffle_threshold
        self._cards: List[Card] = []
        self.reshuffle()

    def _build_shoe(self) -> List[Card]:
        return [Card(rank, suit) for _ in range(self.num_decks) for suit in SUITS for rank in RANKS]

    def reshuffle(self) -> None:
        self._cards = self._build_shoe()
        random.shuffle(self._cards)

    def draw(self) -> Card:
        if not self._cards:
            # As a safeguard, rebuild the shoe if unexpectedly empty mid-round
            self.reshuffle()
        return self._cards.pop()

    def cards_remaining(self) -> int:
        return len(self._cards)

    def needs_reshuffle(self) -> bool:
        return self.cards_remaining() < self.reshuffle_threshold


class Hand:
    """Represents a blackjack hand and computes totals with soft handling."""

    def __init__(self) -> None:
        self.cards: List[Card] = []

    def add_card(self, card: Card) -> None:
        self.cards.append(card)

    def clear(self) -> None:
        self.cards.clear()

    def values(self) -> Tuple[int, bool]:
        """Return best total <= 21 if possible, and whether it's soft (i.e., an Ace counted as 11)."""
        total_without_aces = 0
        aces = 0
        for c in self.cards:
            if c.rank == "A":
                aces += 1
            elif c.rank in {"J", "Q", "K"}:
                total_without_aces += 10
            else:
                total_without_aces += int(c.rank)

        # Count all aces as 1 initially
        base_total = total_without_aces + aces
        best_total = base_total
        is_soft = False

        # Try to upgrade some aces to 11 (i.e., add 10 for each such ace) while <= 21
        # Choose the largest possible total <= 21
        for elevate in range(aces + 1):
            total = base_total + elevate * 10
            if total <= 21 and total >= best_total:
                best_total = total
                is_soft = elevate > 0
        # If all totals > 21, keep the minimal (all aces as 1)
        if best_total > 21:
            best_total = base_total
            is_soft = False
        return best_total, is_soft

    def total(self) -> int:
        return self.values()[0]

    def is_soft(self) -> bool:
        return self.values()[1]

    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.total() == 21

    def is_bust(self) -> bool:
        return self.total() > 21

    def __str__(self) -> str:
        return " ".join(str(c) for c in self.cards)


class Player:
    def __init__(self, name: str, bankroll: float) -> None:
        if bankroll < 0:
            raise ValueError("bankroll must be non-negative")
        self.name = name
        self.bankroll: float = bankroll
        self.hand = Hand()
        self.current_bet: float = 0.0

    def clear_hand(self) -> None:
        self.hand.clear()
        self.current_bet = 0.0

    def place_bet(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Bet must be greater than zero")
        if amount > self.bankroll:
            raise ValueError("Bet cannot exceed bankroll")
        self.bankroll -= amount
        self.current_bet = amount

    def settle_win(self) -> None:
        # Payout 1:1 (return bet + win equal to bet)
        self.bankroll += self.current_bet * 2.0
        self.current_bet = 0.0

    def settle_blackjack(self) -> None:
        # Payout 3:2 (return bet + 1.5x profit)
        self.bankroll += self.current_bet * 2.5
        self.current_bet = 0.0

    def settle_push(self) -> None:
        # Return bet only
        self.bankroll += self.current_bet
        self.current_bet = 0.0

    def settle_loss(self) -> None:
        # Bet already removed
        self.current_bet = 0.0


class Dealer:
    def __init__(self) -> None:
        self.hand = Hand()

    def clear_hand(self) -> None:
        self.hand.clear()


class Game:
    """Blackjack game controller implementing round flow (Step 7)."""

    def __init__(self, num_decks: int = 6, bankroll: float = 100.0, min_bet: float = 1.0) -> None:
        self.deck = Deck(num_decks=num_decks)
        self.player = Player(name="Player", bankroll=bankroll)
        self.dealer = Dealer()
        self.min_bet = min_bet

    def _format_hand(self, hand: Hand, hide_second_card: bool = False) -> str:
        if not hide_second_card or len(hand.cards) <= 1:
            return str(hand)
        return f"{hand.cards[0]} [Hidden]"

    def display_table(self, hide_dealer_hole: bool = True) -> None:
        print("\n=== Current Table ===")
        dealer_hand_str = self._format_hand(self.dealer.hand, hide_second_card=hide_dealer_hole)
        if hide_dealer_hole:
            # Show partial total for dealer (only upcard value if it's not an Ace properly? Keep simple: show '?')
            print(f"Dealer: {dealer_hand_str}")
        else:
            print(f"Dealer: {dealer_hand_str} (Total: {self.dealer.hand.total()})")
        print(f"{self.player.name}: {self.player.hand} (Total: {self.player.hand.total()})")
        print("====================\n")

    def prompt_bet(self) -> Optional[float]:
        while True:
            raw = input(f"Enter bet (min {self.min_bet}, bankroll {self.player.bankroll:.2f}) or 'q' to quit: ").strip().lower()
            if raw in {"q", "quit", "exit"}:
                return None
            try:
                amt = float(raw)
            except ValueError:
                print("Invalid amount. Please enter a number.")
                continue
            if amt < self.min_bet:
                print(f"Bet must be at least {self.min_bet}.")
                continue
            if amt > self.player.bankroll:
                print("Bet cannot exceed current bankroll.")
                continue
            return amt

    def initial_deal(self) -> None:
        # Player gets 2 up, Dealer gets 1 up + 1 down (represented by hide flag in display)
        self.player.hand.add_card(self.deck.draw())
        self.dealer.hand.add_card(self.deck.draw())  # upcard
        self.player.hand.add_card(self.deck.draw())
        self.dealer.hand.add_card(self.deck.draw())  # hole card

    def check_naturals(self) -> bool:
        player_bj = self.player.hand.is_blackjack()
        dealer_bj = self.dealer.hand.is_blackjack()
        if player_bj or dealer_bj:
            # Reveal dealer hole card
            self.display_table(hide_dealer_hole=False)
            if player_bj and dealer_bj:
                print("Both have Blackjack. Push.")
                self.player.settle_push()
            elif player_bj:
                print("Blackjack! You win 3:2.")
                self.player.settle_blackjack()
            else:
                print("Dealer has Blackjack. You lose.")
                self.player.settle_loss()
            return True
        return False

    def player_turn(self) -> None:
        while True:
            self.display_table(hide_dealer_hole=True)
            if self.player.hand.is_bust():
                print("You busted!")
                return
            choice = input("Hit or Stand? [h/s]: ").strip().lower()
            if choice in {"h", "hit"}:
                self.player.hand.add_card(self.deck.draw())
                continue
            elif choice in {"s", "stand"}:
                print("You stand.")
                return
            else:
                print("Please enter 'h' to hit or 's' to stand.")

    def dealer_turn(self) -> None:
        print("Dealer reveals hole card...")
        self.display_table(hide_dealer_hole=False)
        while True:
            total, is_soft = self.dealer.hand.values()
            if total <= 16:
                print("Dealer hits.")
                self.dealer.hand.add_card(self.deck.draw())
                self.display_table(hide_dealer_hole=False)
                if self.dealer.hand.is_bust():
                    print("Dealer busts!")
                    return
            else:
                # Stand on all 17s including soft 17 (S17), and naturally >=18
                print("Dealer stands.")
                return

    def settle_outcome(self) -> None:
        player_total = self.player.hand.total()
        dealer_total = self.dealer.hand.total()
        if self.player.hand.is_bust():
            print("You busted. You lose.")
            self.player.settle_loss()
            return
        if self.dealer.hand.is_bust():
            print("Dealer busted. You win!")
            self.player.settle_win()
            return
        if player_total > dealer_total:
            print("You win!")
            self.player.settle_win()
        elif player_total < dealer_total:
            print("Dealer wins. You lose.")
            self.player.settle_loss()
        else:
            print("Push.")
            self.player.settle_push()

    def play_round(self) -> bool:
        # Ensure deck is ready
        if self.deck.needs_reshuffle():
            print("Reshuffling shoe...")
            self.deck.reshuffle()

        bet = self.prompt_bet()
        if bet is None:
            return False  # Quit
        try:
            self.player.place_bet(bet)
        except ValueError as e:
            print(f"Bet error: {e}")
            return True

        # Clear hands and deal
        self.player.hand.clear()
        self.dealer.hand.clear()
        self.initial_deal()

        # Naturals check
        if self.check_naturals():
            return True

        # Player action loop
        self.player_turn()

        # Dealer logic if player hasn't busted
        if not self.player.hand.is_bust():
            self.dealer_turn()

        # Settle results
        self.display_table(hide_dealer_hole=False)
        self.settle_outcome()
        return True

    def run(self) -> None:
        print("Welcome to Terminal Blackjack! Dealer stands on all 17s. No splits/doubles/insurance.")
        while True:
            if self.player.bankroll <= 0:
                print("You're out of funds. Game over.")
                break
            keep_playing = self.play_round()
            if not keep_playing:
                break
            print(f"Bankroll: {self.player.bankroll:.2f}")
            # Ask to continue
            cont = input("Play another round? [y/n]: ").strip().lower()
            if cont not in {"y", "yes", ""}:
                break
        print(f"Thanks for playing! Final bankroll: {self.player.bankroll:.2f}")


if __name__ == "__main__":
    game = Game(num_decks=6, bankroll=100.0, min_bet=1.0)
    game.run()
