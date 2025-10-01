from typing import Iterable, Mapping, Sequence, Tuple, Union

from .constants import (
    RANK_VALUES,
    RANKS,
    SUITS,
    PAYOUT_RATES,
    MAX_HAND_TOTAL,
    RESHUFFLE_AT_REMAINING_RATIO,
)

"""
Utility functions for Blackjack logic and shared helpers.

Includes:
- Ace valuation algorithm (maximize hand total without busting)
- Blackjack/bust detection helpers
- Reshuffle threshold logic
- Payout computation helpers
"""

RankLike = Union[str, int]


def rank_to_value(rank: RankLike) -> int:
    """Convert a card rank into its nominal value.

    Aces are treated as 11 initially and may be demoted to 1 later by the
    best_total function to avoid busting.

    Accepts ranks as strings ("2".."10", "J", "Q", "K", "A") or ints.
    For integers, 2..10 map to themselves. Values 1 or 11 are treated as
    Ace (11) and will be demoted if necessary during total calculation.

    Raises ValueError for invalid inputs.
    """
    if isinstance(rank, int):
        if 2 <= rank <= 10:
            return rank
        if rank in (1, 11):
            return 11  # Ace nominal value
        raise ValueError(f"Invalid integer rank: {rank}")

    if isinstance(rank, str):
        if rank in RANK_VALUES:
            return RANK_VALUES[rank]
        # tolerate numeric strings like "2".."10" (already covered), others invalid
        raise ValueError(f"Invalid rank string: {rank}")

    raise ValueError(f"Unsupported rank type: {type(rank)!r}")


def best_total(ranks: Sequence[RankLike]) -> Tuple[int, bool]:
    """Compute the best total for a hand using Blackjack rules.

    The algorithm counts all Aces as 11 initially, then demotes them to 1
    one by one until the total is <= 21 or no more Aces can be demoted.

    Parameters:
        ranks: Sequence of rank-like values.

    Returns:
        (total, is_soft)
        - total: best achievable total without busting (or the raw sum if busts)
        - is_soft: True if at least one Ace is counted as 11 in the final total
    """
    total = 0
    aces_as_eleven = 0

    for r in ranks:
        v = rank_to_value(r)
        total += v
        if v == 11:
            aces_as_eleven += 1

    # Demote Aces (11 -> 1) until we don't bust or run out
    while total > MAX_HAND_TOTAL and aces_as_eleven > 0:
        total -= 10  # demote one Ace from 11 to 1
        aces_as_eleven -= 1

    is_soft = aces_as_eleven > 0
    return total, is_soft


def is_blackjack(ranks: Sequence[RankLike]) -> bool:
    """Return True if the hand is a natural blackjack (two-card 21)."""
    if len(ranks) != 2:
        return False
    total, _ = best_total(ranks)
    return total == 21


def is_bust(ranks: Sequence[RankLike]) -> bool:
    """Return True if the hand value exceeds 21."""
    total, _ = best_total(ranks)
    return total > MAX_HAND_TOTAL


def should_reshuffle(cards_remaining: int, total_cards: int, *, threshold_ratio: float = RESHUFFLE_AT_REMAINING_RATIO) -> bool:
    """Determine if the shoe should be reshuffled based on remaining cards.

    Reshuffle when remaining cards are at or below threshold_ratio * total_cards.
    """
    if total_cards <= 0:
        raise ValueError("total_cards must be positive")
    if cards_remaining < 0:
        raise ValueError("cards_remaining cannot be negative")
    if not (0.0 < threshold_ratio <= 1.0):
        raise ValueError("threshold_ratio must be in (0, 1]")

    threshold_count = int(total_cards * threshold_ratio)
    if threshold_count < 1:
        threshold_count = 1
    return cards_remaining <= threshold_count


def payout_multiplier(outcome: str, payout_rates: Mapping[str, float] = PAYOUT_RATES) -> float:
    """Return the payout multiplier for a given outcome.

    Known outcomes: "blackjack", "win", "push", "loss", "surrender", "insurance".
    """
    if outcome not in payout_rates:
        raise KeyError(f"Unknown outcome '{outcome}'. Known: {sorted(payout_rates.keys())}")
    return payout_rates[outcome]


def compute_payout(bet: float, outcome: str, payout_rates: Mapping[str, float] = PAYOUT_RATES) -> float:
    """Compute the payout for a bet given the outcome using the configured rates.

    Returns a signed float amount relative to the original bet size. For example:
    - outcome="win" on bet 10 => 10.0
    - outcome="loss" on bet 10 => -10.0
    - outcome="blackjack" on bet 10 => 15.0
    - outcome="push" on bet 10 => 0.0
    """
    if bet < 0:
        raise ValueError("bet must be non-negative")
    return bet * payout_multiplier(outcome, payout_rates)


def build_shoe(num_decks: int, *, suits: Iterable[str] = SUITS, ranks: Iterable[str] = RANKS) -> list[tuple[str, str]]:
    """Build a standard shoe as a list of (rank, suit) tuples.

    This utility does not shuffle; shuffling should be handled by the Deck logic.
    """
    if num_decks <= 0:
        raise ValueError("num_decks must be positive")

    shoe: list[tuple[str, str]] = []
    for _ in range(num_decks):
        for s in suits:
            for r in ranks:
                shoe.append((r, s))
    return shoe


__all__ = [
    "RankLike",
    "rank_to_value",
    "best_total",
    "is_blackjack",
    "is_bust",
    "should_reshuffle",
    "payout_multiplier",
    "compute_payout",
    "build_shoe",
]
