from __future__ import annotations

import argparse
from typing import Optional

from .deck import Deck, Hand

__version__ = "0.1.0"


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="blackjack",
        description="Terminal Blackjack (scaffold). Full gameplay will be added in later steps.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--decks", type=int, default=1, help="Number of decks to use (default: 1)")
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional RNG seed for deterministic shuffles",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a minimal demo that deals example hands (for development)",
    )
    return parser.parse_args(argv)


def demo(decks: int, seed: Optional[int]) -> int:
    """Deal example hands to demonstrate Deck/Hand behavior."""
    rng = None
    if seed is not None:
        import random

        rng = random.Random(seed)

    deck = Deck(num_decks=decks, rng=rng)

    player = Hand()
    dealer = Hand()

    # Initial deal: two cards each
    player.add_card(deck.draw())
    dealer.add_card(deck.draw())
    player.add_card(deck.draw())
    dealer.add_card(deck.draw())

    print("-- Demo Hand --")
    print(f"Player: {player}")
    print(f"Dealer: [{dealer.cards[0]}, Hidden]")
    print("(Note: This is a scaffold demo, not full gameplay.)")

    return 0


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    if args.demo:
        return demo(args.decks, args.seed)

    print("Blackjack CLI scaffold.")
    print("- Use --help for options.")
    print("- Full gameplay will be implemented in subsequent steps.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
