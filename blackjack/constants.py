from typing import Final, Dict, Mapping, Any

"""
Core constants and default configuration for a terminal-based Blackjack game.

This module centralizes values that are shared across the game implementation,
including suits, ranks, payout rates, and default behavior flags.
"""

# Suits and ranks
SUITS: Final = [
    "Clubs",
    "Diamonds",
    "Hearts",
    "Spades",
]

# Human-friendly representations for suits (safe ASCII by default)
SUIT_SYMBOLS: Final[Dict[str, str]] = {
    "Clubs": "C",
    "Diamonds": "D",
    "Hearts": "H",
    "Spades": "S",
}

# Game ranks ordered from lowest to highest (Ace high with special handling)
RANKS: Final = [
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

# Rank values used for initial tally; Aces are treated as 11 and demoted to 1 as needed
RANK_VALUES: Final[Dict[str, int]] = {
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
    "A": 11,
}

# Game constants
MAX_HAND_TOTAL: Final[int] = 21
DEALER_STAND_VALUE: Final[int] = 17  # Dealer stands on 17+ (soft/hard depends on config)

# Payout rates as multipliers on the original bet
# Positive values pay the player; negative values cost the player.
PAYOUT_RATES: Final[Dict[str, float]] = {
    "blackjack": 1.5,     # Natural blackjack 3:2
    "win": 1.0,           # Regular win pays 1:1
    "push": 0.0,          # Tie returns the bet
    "loss": -1.0,         # Player loses their bet
    "surrender": -0.5,    # Late surrender (player loses half the bet)
    "insurance": 2.0,     # Insurance pays 2:1 on the insurance side bet
}

# Reshuffle when the remaining card ratio falls at or below this threshold
RESHUFFLE_AT_REMAINING_RATIO: Final[float] = 0.25  # e.g., with 312-card shoe, reshuffle at <= 78 cards left

# Default configuration for a standard shoe game
DEFAULT_CONFIG: Final[Dict[str, Any]] = {
    "num_decks": 6,
    "starting_bankroll": 1000,     # Starting chips/money for the player (integer currency units)
    "min_bet": 10,
    "max_bet": 500,
    "dealer_hits_soft_17": True,   # If True, dealer hits on soft 17
    "allow_surrender": True,       # Late surrender allowed
    "allow_insurance": True,       # Insurance allowed when dealer shows Ace
    "blackjack_payout": PAYOUT_RATES["blackjack"],
    "reshuffle_at_remaining_ratio": RESHUFFLE_AT_REMAINING_RATIO,
}


def get_default_config(overrides: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    """Return a shallow copy of the default config, optionally applying overrides.

    Parameters:
        overrides: Optional mapping of configuration keys to override.

    Returns:
        A new dict with defaults merged with any overrides provided.
    """
    cfg = dict(DEFAULT_CONFIG)
    if overrides:
        cfg.update(overrides)
    return cfg


__all__ = [
    "SUITS",
    "SUIT_SYMBOLS",
    "RANKS",
    "RANK_VALUES",
    "MAX_HAND_TOTAL",
    "DEALER_STAND_VALUE",
    "PAYOUT_RATES",
    "RESHUFFLE_AT_REMAINING_RATIO",
    "DEFAULT_CONFIG",
    "get_default_config",
]
