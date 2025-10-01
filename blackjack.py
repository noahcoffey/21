import random
import curses
from dataclasses import dataclass, field
from typing import List, Iterable, Optional


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

    def get_suit_symbol(self) -> str:
        """Get Unicode symbol for suit"""
        symbols = {
            "Hearts": "♥",
            "Diamonds": "♦",
            "Clubs": "♣",
            "Spades": "♠"
        }
        return symbols.get(self.suit, "?")

    def to_visual(self) -> List[str]:
        """Return card as visual ASCII art (5 lines)"""
        suit_symbol = self.get_suit_symbol()
        rank_str = self.rank.ljust(2)

        return [
            "┌─────────┐",
            f"│{rank_str}       │",
            f"│    {suit_symbol}    │",
            f"│       {rank_str}│",
            "└─────────┘"
        ]


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


class VisualUI:
    """Visual terminal UI using curses"""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)  # Hide cursor
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)

    def draw_cards(self, cards: List[Card], y: int, x: int, hide_first: bool = False) -> None:
        """Draw cards horizontally at position"""
        if not cards:
            return

        for i, card in enumerate(cards):
            if i == 0 and hide_first:
                # Show card back
                card_lines = [
                    "┌─────────┐",
                    "│░░░░░░░░░│",
                    "│░░░░░░░░░│",
                    "│░░░░░░░░░│",
                    "└─────────┘"
                ]
            else:
                card_lines = card.to_visual()

            # Determine color based on suit
            color = curses.COLOR_WHITE
            if card.suit in ("Hearts", "Diamonds"):
                color = curses.color_pair(1)  # Red

            for line_idx, line in enumerate(card_lines):
                try:
                    if i == 0 and hide_first:
                        self.stdscr.addstr(y + line_idx, x + (i * 12), line)
                    else:
                        self.stdscr.addstr(y + line_idx, x + (i * 12), line, color)
                except curses.error:
                    pass  # Ignore if out of bounds

    def draw_hand_value(self, hand: Hand, y: int, x: int, show: bool = True) -> None:
        """Draw hand value at position"""
        if show:
            value_str = f"Value: {hand.value()}"
            if hand.is_blackjack():
                value_str += " - BLACKJACK!"
            elif hand.is_bust():
                value_str += " - BUST!"
            try:
                color = curses.color_pair(2) if not hand.is_bust() else curses.color_pair(1)
                self.stdscr.addstr(y, x, value_str, color | curses.A_BOLD)
            except curses.error:
                pass

    def draw_title(self, title: str, y: int) -> None:
        """Draw centered title"""
        max_y, max_x = self.stdscr.getmaxyx()
        x = max(0, (max_x - len(title)) // 2)
        try:
            self.stdscr.addstr(y, x, title, curses.color_pair(3) | curses.A_BOLD)
        except curses.error:
            pass

    def draw_message(self, message: str, y: int, color_pair: int = 0) -> None:
        """Draw centered message"""
        max_y, max_x = self.stdscr.getmaxyx()
        x = max(0, (max_x - len(message)) // 2)
        try:
            self.stdscr.addstr(y, x, message, curses.color_pair(color_pair) | curses.A_BOLD)
        except curses.error:
            pass

    def draw_prompt(self, prompt: str, y: int) -> None:
        """Draw centered prompt"""
        max_y, max_x = self.stdscr.getmaxyx()
        x = max(0, (max_x - len(prompt)) // 2)
        try:
            self.stdscr.addstr(y, x, prompt, curses.color_pair(4))
        except curses.error:
            pass

    def get_input(self, y: int, x: int) -> str:
        """Get single character input"""
        curses.echo()
        curses.curs_set(1)
        try:
            self.stdscr.move(y, x)
            ch = self.stdscr.getch()
            result = chr(ch).lower()
        except:
            result = ''
        finally:
            curses.noecho()
            curses.curs_set(0)
        return result


class Game:
    def __init__(self, num_decks: int = 6, reshuffle_threshold: int = 15) -> None:
        self.deck = Deck(num_decks=num_decks, reshuffle_threshold=reshuffle_threshold)
        self.player = Player(name="Player")
        self.dealer = Player(name="Dealer")
        self.ui: Optional[VisualUI] = None

    def deal_initial(self) -> None:
        # Each gets two cards, player first
        for _ in range(2):
            self.player.hand.add_card(self.deck.draw(1)[0])
            self.dealer.hand.add_card(self.deck.draw(1)[0])

    def player_turn(self, interactive: bool = True) -> None:
        if not interactive:
            # Simple strategy placeholder: hit until 16 or more
            while self.player.hand.value() < 16:
                self.player.hand.add_card(self.deck.draw(1)[0])
                if self.player.hand.is_bust():
                    break
            return

        # Visual interactive mode
        if self.ui:
            while not self.player.hand.is_bust():
                self._draw_game_state(show_dealer_value=False)
                self.ui.draw_prompt("(H)it or (S)tand?", 20)
                self.ui.stdscr.refresh()

                action = self.ui.get_input(20, self.ui.stdscr.getmaxyx()[1] // 2 + 20)

                if action in ('s',):
                    break
                elif action in ('h',):
                    card = self.deck.draw(1)[0]
                    self.player.hand.add_card(card)
                    if self.player.hand.is_bust():
                        self._draw_game_state(show_dealer_value=False)
                        self.ui.draw_message("BUST! You lose!", 22, 1)
                        self.ui.stdscr.refresh()
                        curses.napms(2000)
                        break
        else:
            # Fallback text mode
            while not self.player.hand.is_bust():
                action = input("Choose action: (h)it, (s)tand: ").strip().lower()
                if action in ('s', 'stand'):
                    break
                elif action in ('h', 'hit'):
                    card = self.deck.draw(1)[0]
                    self.player.hand.add_card(card)
                    print(f"You drew: {card}")
                    print(f"Your hand: {self.player.hand}")
                    if self.player.hand.is_bust():
                        print("Bust!")
                        break
                else:
                    print("Invalid action. Please choose (h)it or (s)tand.")

    def dealer_turn(self) -> None:
        # Dealer stands on 17 or more (typical rule)
        while self.dealer.hand.value() < 17:
            self.dealer.hand.add_card(self.deck.draw(1)[0])
            if self.dealer.hand.is_bust():
                break

    def _draw_game_state(self, show_dealer_value: bool = True) -> None:
        """Draw complete game state on screen"""
        if not self.ui:
            return

        self.ui.stdscr.clear()

        # Title
        self.ui.draw_title("♠ ♥ BLACKJACK ♦ ♣", 0)

        # Dealer section
        self.ui.stdscr.addstr(2, 2, "DEALER:", curses.A_BOLD)
        self.ui.draw_cards(self.dealer.hand.cards, 3, 2, hide_first=not show_dealer_value)
        if show_dealer_value:
            self.ui.draw_hand_value(self.dealer.hand, 9, 2, show=True)
        else:
            try:
                self.ui.stdscr.addstr(9, 2, "Value: ??", curses.color_pair(2))
            except curses.error:
                pass

        # Player section
        self.ui.stdscr.addstr(12, 2, "PLAYER:", curses.A_BOLD)
        self.ui.draw_cards(self.player.hand.cards, 13, 2)
        self.ui.draw_hand_value(self.player.hand, 19, 2, show=True)

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

    def play_round(self, verbose: bool = False, interactive: bool = True) -> str:
        # Ensure deck is healthy before dealing
        self.deck.reshuffle_if_needed()

        self.deal_initial()

        if self.ui:
            # Visual mode
            self._draw_game_state(show_dealer_value=False)
            self.ui.stdscr.refresh()
            curses.napms(1000)

            # Check for blackjack
            if self.player.hand.is_blackjack():
                self._draw_game_state(show_dealer_value=True)
                self.ui.draw_message("BLACKJACK! You win!", 22, 2)
                self.ui.stdscr.refresh()
                curses.napms(2000)
            else:
                self.player_turn(interactive=interactive)

            # Dealer's turn if player didn't bust
            if not self.player.hand.is_bust():
                self._draw_game_state(show_dealer_value=True)
                self.ui.draw_message("Dealer's turn...", 22, 3)
                self.ui.stdscr.refresh()
                curses.napms(1500)

                self.dealer_turn()

                # Show dealer cards being drawn
                self._draw_game_state(show_dealer_value=True)
                self.ui.stdscr.refresh()
                curses.napms(1500)

            # Show result
            result = self.settle()
            self._draw_game_state(show_dealer_value=True)

            color = 2 if "Player wins" in result else 1 if "Dealer wins" in result else 3
            self.ui.draw_message(result.upper(), 22, color)
            self.ui.stdscr.refresh()
            curses.napms(2000)

        else:
            # Text mode fallback
            if verbose:
                print(f"Your hand: {self.player.hand}")
                print(f"Dealer shows: {self.dealer.hand.cards[0]}")

            if not self.player.hand.is_blackjack():
                self.player_turn(interactive=interactive)
            elif verbose:
                print("Blackjack!")

            if not self.player.hand.is_bust():
                if verbose:
                    print("\nDealer's turn...")
                self.dealer_turn()

            result = self.settle()

            if verbose:
                print(f"Dealer: {self.dealer.hand}")
                print(result)
                if not interactive:
                    print(f"Draw pile remaining before cleanup: {self.deck.cards_remaining()}")
                    print(f"Discard pile before cleanup: {self.deck.discard_pile_size()}")

        # Return all cards to discard and possibly reshuffle
        self.cleanup_round()

        if verbose and not interactive and not self.ui:
            print(f"Draw pile after cleanup/reshuffle: {self.deck.cards_remaining()}")
            print(f"Discard pile after cleanup/reshuffle: {self.deck.discard_pile_size()}\n")

        return result

    def run(self, num_rounds: int = 5, verbose: bool = True, interactive: bool = True) -> None:
        if self.ui:
            # Visual mode
            round_num = 1
            while round_num <= num_rounds:
                self.play_round(verbose=verbose, interactive=interactive)

                if interactive and round_num < num_rounds:
                    self.ui.stdscr.clear()
                    self.ui.draw_title("♠ ♥ BLACKJACK ♦ ♣", 0)
                    self.ui.draw_prompt("Play another round? (Y)es or (N)o", 10)
                    self.ui.stdscr.refresh()

                    max_y, max_x = self.ui.stdscr.getmaxyx()
                    choice = self.ui.get_input(10, max_x // 2 + 20)

                    if choice not in ('y',):
                        self.ui.stdscr.clear()
                        self.ui.draw_message("Thanks for playing!", 10, 2)
                        self.ui.stdscr.refresh()
                        curses.napms(2000)
                        break

                round_num += 1
        else:
            # Text mode fallback
            for i in range(1, num_rounds + 1):
                if verbose:
                    print(f"--- Round {i} ---")
                self.play_round(verbose=verbose, interactive=interactive)
                if interactive and i < num_rounds:
                    continue_game = input("\nPlay another round? (y/n): ").strip().lower()
                    if continue_game not in ('y', 'yes'):
                        print("Thanks for playing!")
                        break


def main_visual(stdscr) -> None:
    """Main entry point for visual curses mode"""
    game = Game(num_decks=6, reshuffle_threshold=15)
    game.ui = VisualUI(stdscr)

    # Welcome screen
    stdscr.clear()
    game.ui.draw_title("♠ ♥ BLACKJACK ♦ ♣", 5)
    game.ui.draw_message("Welcome to Blackjack!", 8, 2)
    game.ui.draw_prompt("Press any key to start...", 10)
    stdscr.refresh()
    stdscr.getch()

    game.run(num_rounds=100, verbose=True, interactive=True)


if __name__ == "__main__":
    # Run in visual curses mode
    try:
        curses.wrapper(main_visual)
    except KeyboardInterrupt:
        print("\nThanks for playing!")
    except Exception as e:
        print(f"Error: {e}")
        print("Falling back to text mode...")
        game = Game(num_decks=6, reshuffle_threshold=15)
        game.run(num_rounds=100, verbose=True, interactive=True)
