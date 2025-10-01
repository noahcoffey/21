import argparse
from typing import Optional

try:
    # Package-relative imports (preferred)
    from .deck import Deck
    from .player import Player
except ImportError:  # pragma: no cover - allows running as a script
    # Fallback to local imports when executed directly as a script
    from deck import Deck  # type: ignore
    from player import Player  # type: ignore


class Game:
    """
    Minimal game controller to bootstrap the project and provide a simple CLI demo.
    """

    def __init__(self, num_decks: int = 1, seed: Optional[int] = None) -> None:
        self.deck = Deck(num_decks=num_decks, seed=seed)
        self.dealer = Player(name="Dealer", is_dealer=True)
        self.player = Player(name="You")

    def new_round(self) -> None:
        self.dealer.new_round()
        self.player.new_round()

    def initial_deal(self) -> None:
        # Two cards each, player first
        for _ in range(2):
            self.player.hit(self.deck)
            self.dealer.hit(self.deck)

    def render_opening(self) -> str:
        # Show one dealer card hidden for typical blackjack presentation
        dealer_up = str(self.dealer.hand.cards[0]) if self.dealer.hand.cards else "??"
        dealer_hidden = "??"
        player_hand = str(self.player.hand)
        player_val = self.player.hand.value
        lines = [
            "=== Blackjack ===",
            f"Dealer shows: {dealer_up} {dealer_hidden}",
            f"Your hand:    {player_hand}  [= {player_val}]",
        ]
        return "\n".join(lines)

    def demo_round(self) -> str:
        self.new_round()
        self.initial_deal()
        return self.render_opening()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="blackjack",
        description="Terminal-based Blackjack (scaffold demo)",
    )
    parser.add_argument(
        "--decks",
        type=int,
        default=1,
        help="Number of decks to use in the shoe (default: 1)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional RNG seed for reproducible deals",
    )
    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    game = Game(num_decks=args.decks, seed=args.seed)
    screen = game.demo_round()
    print(screen)
    # Exit success
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
