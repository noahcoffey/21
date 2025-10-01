# Terminal Blackjack (CLI)

A simple, standards-compliant terminal Blackjack game written in Python 3. Built with the Python standard library only and designed for easy play and straightforward testing.

- Dealer stands on all 17 (S17), including soft 17
- Aces are valued as 11 or 1 to maximize the hand without busting
- Object-oriented design: Card, Deck, Hand, Player; dealer logic encapsulated


## Requirements
- Python 3.8 or newer
- No external dependencies (standard library only)


## Quick Start
From the project root:

```
python -m blackjack  # if the package exposes a module entrypoint
```

If your checkout exposes a script instead, try one of:

```
python main.py
python blackjack.py
python -m src.blackjack  # if a src/ layout is used
```

Tip: The authoritative way to see how to invoke your build is to run `--help` on the main entrypoint you have. For example:

```
python -m blackjack --help
python main.py --help
```


## Command-line options
Your build includes a command-line interface based on `argparse`. The precise set of flags can vary slightly depending on the final module name or layout. Use `--help` for the authoritative list. Typical options supported by this project include:

- --decks N
  - Number of 52-card decks to use in the shoe
  - Default: 1 (or 6 in some builds)
- --bankroll AMOUNT
  - Starting bankroll for the session (integer units)
  - Default: 100
- --bet AMOUNT
  - Default bet size per hand (integer units)
  - Default: 10
- --seed N
  - Seed for the RNG to make runs reproducible
  - Default: None (random)
- --autoplay / --no-autoplay
  - When enabled, plays hands automatically with a simple strategy; otherwise prompts for hit/stand
- --hands N
  - Number of hands to play when autoplay is enabled
- --quiet
  - Reduce output verbosity (useful for testing)

Note: Your build may expose a subset/superset of these flags. Run `--help` to confirm.


## Rules Implemented
- Dealer stands on all 17 (S17), including soft 17
- Aces are automatically "demoted" from 11 to 1 as needed to avoid busting and maximize total
- Standard 52-card ranks and suits; shoe can combine multiple decks
- Player actions: Hit or Stand
- Outcomes: Win, Lose, Push
- Shuffling occurs when a new deck/shoe is created; some builds may reshuffle when the shoe is exhausted

Simplifications (by design):
- No split, double down, surrender, or insurance
- Blackjack payout and betting complexity may be simplified; many builds use even-money payouts for simplicity


## How to Play
Interactive mode (prompts for input):

```
python -m blackjack
```

Autoplay a fixed number of hands (example):

```
python -m blackjack --autoplay --hands 50 --decks 6 --bankroll 1000 --bet 10 --seed 42
```

Run with minimal output (useful for CI/tests):

```
python -m blackjack --autoplay --hands 100 --quiet
```


## Testing
This project uses Python's built-in `unittest` framework.

- Run all tests (auto-discovery):

```
python -m unittest discover -v
```

- Run a specific test module:

```
python -m unittest tests.test_hand -v
```

- Run a specific test case or method:

```
python -m unittest tests.test_hand.TestHandEvaluation.test_ace_valuation -v
```

Deterministic tests: Use `--seed` to ensure deterministic deals when end-to-end testing the CLI.


## Project Layout
Your checkout should resemble the following logical layout. Names may vary slightly depending on earlier steps; the core elements will be present.

```
.
├─ blackjack/               # Package (or src/blackjack if using a src layout)
│  ├─ __init__.py
│  ├─ __main__.py           # Enables `python -m blackjack`
│  ├─ cards.py              # Card and Deck
│  ├─ hand.py               # Hand evaluation (ace valuation logic)
│  ├─ player.py             # Player/Dealer models
│  ├─ game.py               # Game engine and round resolution
│  └─ cli.py                # Argparse-based CLI wiring
├─ tests/
│  ├─ test_cards.py
│  ├─ test_hand.py
│  ├─ test_game.py
│  └─ ...
└─ README.md
```

If your repository uses a different top-level entrypoint (e.g., `main.py` or `blackjack.py` in the root), prefer that file when running the game and use `--help` to inspect available options.


## Implementation Notes
- Python version: 3.8+
- Dependencies: standard library only (random, argparse, sys, typing, dataclasses optional, unittest)
- Ace valuation: The algorithm computes the maximal non-busting total by initially counting all aces as 11, then demoting aces to 1 iteratively until the total is <= 21 or no aces remain.
- Dealer logic: Encapsulated in a function/class that draws until total >= 17 and stands on soft 17.
- I/O: CLI based on argparse; input/print for interactive play.


## Troubleshooting
- Command not found for `python -m blackjack`:
  - Use `python main.py` or `python blackjack.py` if present in the root
  - Ensure you are in the project root directory
  - Check Python version: `python --version` should be 3.8+
- Unicode or font issues: The game uses simple ASCII by default and should work in most terminals.


## Limitations and Future Enhancements
- Additional player options: split, double down, surrender, and insurance
- Configurable dealer rule (H17 vs S17) and configurable blackjack payout (e.g., 3:2)
- Basic strategy hints and card counting aids
- Session statistics and hand history export (JSON/CSV)
- Improved test coverage for edge cases and long-run simulation
- Save/restore bankroll across sessions


## License
This project is distributed for educational purposes. Add your preferred license file if needed.
