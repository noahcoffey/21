import argparse
import random
from dataclasses import dataclass, field
from typing import List, Optional


SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
RANK_VALUES = {
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


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str

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

    def values(self) -> int:
        total = 0
        aces = 0
        for c in self.cards:
            v = c.value()
            total += v
            if c.rank == "A":
                aces += 1
        # Adjust Aces from 11 to 1 as needed
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.values() == 21

    def is_bust(self) -> bool:
        return self.values() > 21

    def is_soft(self) -> bool:
        # Soft hand if an Ace is counted as 11 in best total
        total = 0
        aces = 0
        for c in self.cards:
            total += c.value()
            if c.rank == "A":
                aces += 1
        # Reduce while bust
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        # If there remains an Ace counted as 11, it's soft
        return any(card.rank == "A" for card in self.cards) and total <= 21 and any(
            # Recompute if making one Ace 1 reduces total by 10 but still keeps <= 21
            # If after reductions, if there was at least one Ace not reduced, that's soft
            True for _ in ()
        ) and self._has_ace_counted_as_11()

    def _has_ace_counted_as_11(self) -> bool:
        total = 0
        aces = 0
        for c in self.cards:
            total += c.value()
            if c.rank == "A":
                aces += 1
        # Reduce as needed
        reduced = 0
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
            reduced += 1
        # If there are remaining aces not reduced, one is 11
        return any(card.rank == "A" for card in self.cards) and aces > 0

    def __str__(self) -> str:
        return ", ".join(str(c) for c in self.cards)


class Deck:
    def __init__(self, num_decks: int = 6) -> None:
        if num_decks <= 0:
            raise ValueError("num_decks must be positive")
        self.num_decks = num_decks
        self.cards: List[Card] = []
        self._reset()

    def _reset(self) -> None:
        self.cards = [Card(rank, suit) for _ in range(self.num_decks) for suit in SUITS for rank in RANKS]
        random.shuffle(self.cards)

    def need_reshuffle(self) -> bool:
        return len(self.cards) < 15

    def reshuffle(self) -> None:
        print("[Deck] Reshuffling shoe...")
        self._reset()

    def deal(self) -> Card:
        if self.need_reshuffle():
            self.reshuffle()
        return self.cards.pop()


@dataclass
class Player:
    name: str
    chips: int
    hand: Hand = field(default_factory=Hand)
    bet: int = 0

    def place_bet(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Bet must be positive")
        if amount > self.chips:
            raise ValueError("Bet cannot exceed available chips")
        self.bet = amount
        self.chips -= amount

    def win(self) -> None:
        # Regular win: pay 1:1, return bet + winnings
        self.chips += self.bet * 2
        self.bet = 0

    def push(self) -> None:
        # Return bet
        self.chips += self.bet
        self.bet = 0

    def lose(self) -> None:
        # Bet already deducted
        self.bet = 0

    def blackjack_payout(self) -> None:
        # Pay 3:2 for blackjack
        winnings = int(self.bet * 1.5)
        self.chips += self.bet + winnings
        self.bet = 0


class Game:
    def __init__(self, chips: int, decks: int, min_bet: int) -> None:
        if chips <= 0:
            raise ValueError("Starting chips must be positive")
        if decks <= 0:
            raise ValueError("Number of decks must be positive")
        if min_bet <= 0:
            raise ValueError("Minimum bet must be positive")
        self.deck = Deck(num_decks=decks)
        self.player = Player(name="Player", chips=chips)
        self.dealer_hand = Hand()
        self.min_bet = min_bet

    def print_state(self, hide_dealer_hole: bool = True) -> None:
        if hide_dealer_hole and len(self.dealer_hand.cards) > 0:
            if len(self.dealer_hand.cards) >= 2:
                upcard = str(self.dealer_hand.cards[0])
                print(f"Dealer: {upcard}, [hidden]")
            else:
                print(f"Dealer: {self.dealer_hand}")
        else:
            print(f"Dealer: {self.dealer_hand} (total: {self.dealer_hand.values()})")
        print(f"You: {self.player.hand} (total: {self.player.hand.values()})")
        print(f"Chips: {self.player.chips}")

    def prompt_bet(self) -> Optional[int]:
        while True:
            raw = input(f"Place your bet (min {self.min_bet}, 'q' to quit): ").strip().lower()
            if raw in ("q", "quit", "exit"):
                return None
            try:
                amt = int(raw)
            except ValueError:
                print("Enter a valid integer amount.")
                continue
            if amt < self.min_bet:
                print(f"Bet must be at least {self.min_bet}.")
                continue
            if amt > self.player.chips:
                print("You cannot bet more than your available chips.")
                continue
            return amt

    def initial_deal(self) -> None:
        self.player.hand.clear()
        self.dealer_hand.clear()
        # Deal two cards each, player first
        self.player.hand.add_card(self.deck.deal())
        self.dealer_hand.add_card(self.deck.deal())
        self.player.hand.add_card(self.deck.deal())
        self.dealer_hand.add_card(self.deck.deal())

    def player_turn(self) -> str:
        # Returns outcome: 'bust', 'stand', 'blackjack-stand'
        if self.player.hand.is_blackjack():
            return 'blackjack-stand'
        while True:
            self.print_state(hide_dealer_hole=True)
            choice = input("Hit or Stand? [h/s]: ").strip().lower()
            if choice in ("s", "stand"):
                return 'stand'
            if choice in ("h", "hit"):
                self.player.hand.add_card(self.deck.deal())
                if self.player.hand.is_bust():
                    self.print_state(hide_dealer_hole=True)
                    print("You busted!")
                    return 'bust'
                continue
            if choice in ("q", "quit", "exit"):
                print("Finishing current hand then exiting...")
                return 'stand'
            print("Please enter 'h' or 's'.")

    def dealer_turn(self) -> None:
        # Dealer stands on all 17 (including soft 17)
        while self.dealer_hand.values() < 17:
            self.dealer_hand.add_card(self.deck.deal())

    def settle(self) -> None:
        player_val = self.player.hand.values()
        dealer_val = self.dealer_hand.values()
        print(f"Dealer reveals: {self.dealer_hand} (total: {dealer_val})")
        print(f"Your hand: {self.player.hand} (total: {player_val})")

        if self.player.hand.is_bust():
            print("You lose.")
            self.player.lose()
            return

        if self.dealer_hand.is_bust():
            print("Dealer busts. You win!")
            self.player.win()
            return

        if player_val > dealer_val:
            if self.player.hand.is_blackjack():
                print("Blackjack! You win 3:2.")
                self.player.blackjack_payout()
            else:
                print("You win!")
                self.player.win()
        elif player_val < dealer_val:
            print("You lose.")
            self.player.lose()
        else:
            print("Push.")
            self.player.push()

    def play_round(self) -> bool:
        if self.deck.need_reshuffle():
            self.deck.reshuffle()
        if self.player.chips < self.min_bet:
            print("You do not have enough chips to continue.")
            return False
        bet = self.prompt_bet()
        if bet is None:
            return False
        try:
            self.player.place_bet(bet)
        except ValueError as e:
            print(f"Bet error: {e}")
            return True

        self.initial_deal()

        # Check for immediate blackjacks
        if self.player.hand.is_blackjack():
            if self.dealer_hand.is_blackjack():
                print("Both you and the dealer have blackjack. Push.")
                self.player.push()
            else:
                print("Blackjack! You win 3:2.")
                self.player.blackjack_payout()
            return True

        outcome = self.player_turn()
        if outcome == 'bust':
            self.player.lose()
            return True

        # Dealer plays
        self.dealer_turn()
        self.settle()
        return True

    def loop(self) -> None:
        print("Welcome to Blackjack!")
        print(f"Starting chips: {self.player.chips}. Minimum bet: {self.min_bet}. Decks: {self.deck.num_decks}.")
        try:
            while True:
                if not self.play_round():
                    break
                if self.player.chips <= 0:
                    print("You are out of chips. Game over.")
                    break
                # Ask to continue
                ans = input("Play another hand? [Y/n]: ").strip().lower()
                if ans in ("n", "no", "q", "quit", "exit"):
                    break
        except KeyboardInterrupt:
            print("\nGoodbye!")
        finally:
            print(f"Thanks for playing. You leave with {self.player.chips} chips.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Terminal-based Blackjack")
    parser.add_argument("--chips", type=int, default=100, help="Starting chips (default: 100)")
    parser.add_argument("--decks", type=int, default=6, help="Number of decks in shoe (default: 6)")
    parser.add_argument("--min-bet", type=int, default=10, help="Minimum bet per hand (default: 10)")
    args = parser.parse_args()

    if args.chips <= 0:
        parser.error("--chips must be positive")
    if args.decks <= 0:
        parser.error("--decks must be positive")
    if args.min_bet <= 0:
        parser.error("--min-bet must be positive")
    if args.min_bet > args.chips:
        parser.error("--min-bet cannot exceed starting chips")

    return args


def main() -> None:
    args = parse_args()
    game = Game(chips=args.chips, decks=args.decks, min_bet=args.min_bet)
    game.loop()


if __name__ == "__main__":
    main()
