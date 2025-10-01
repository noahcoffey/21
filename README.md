# Terminal Blackjack

A terminal-based Blackjack game implemented in Python 3.8+. Play a human-vs-dealer session using a configurable multi-deck shoe. The Deck supports a configurable number of decks and automatically reshuffles when the remaining cards drop below a threshold (default: 15).

Note: This documentation covers usage, rules, configuration, and a sample interactive session. It assumes the project has already been set up with classes Card, Hand, Deck, Player, and a game loop/controller as part of earlier steps in the parent issue.


## Requirements
- Python 3.8+
- No external dependencies are required for basic usage
- Optional: Some implementations may expose a CLI with argument parsing; if so, run with `--help` to discover available flags


## Installation
1. Ensure you have Python 3.8 or newer:
   - macOS/Linux: `python3 --version`
   - Windows: `py --version`
2. Clone or download the repository.
3. No build step is required.


## Running the Game
Depending on how your codebase is laid out, you will typically run the game in one of these ways:

- If packaged as a module with an entry point:
  - `python -m blackjack`

- If there is a top-level script (for example `game.py` or `blackjack.py`) at the project root:
  - `python game.py`
  - or `python blackjack.py`

If your implementation includes CLI options, invoke `--help` to see them:
- `python -m blackjack --help`
- or `python game.py --help`

Typical options (if supported by your version):
- `--decks N` or `-d N` — Number of standard 52-card decks in the shoe (default commonly 6)
- `--reshuffle-threshold N` — Auto-reshuffle the shoe when remaining cards < N (default 15)
- `--bankroll AMOUNT` — Starting bankroll
- `--min-bet AMOUNT` — Minimum bet per hand
- `--max-bet AMOUNT` — Maximum bet per hand

Note: If your implementation does not expose these flags, the defaults still apply internally (notably: shoe auto-reshuffles when fewer than 15 cards remain).


## Gameplay Controls
During your turn, you will be prompted to choose an action. Typical controls (your implementation may show only the valid subset at each prompt):
- `h` or `hit` — Take another card
- `s` or `stand` — End your turn; keep current total
- `d` or `double` — Double your bet, take exactly one card, then stand (usually only on your first move)
- `p` or `split` — Split a pair into two hands (only when allowed and implemented)
- `q` or `quit` — Exit the game (if supported)

Your game will typically display available actions contextually; enter one of the shown options.


## Rules (Standard Blackjack)
- Goal: Beat the dealer by having a hand total closer to 21 without going over.
- Card values: 2–10 as pip value; J, Q, K as 10; A as 1 or 11.
- Initial deal: Player and dealer each receive two cards; dealer shows one up-card and one down-card.
- Player turn: Choose among available actions (Hit, Stand, and, when allowed, Double Down and/or Split).
- Dealer play: Dealer draws until the total is at least 17. The handling of soft 17 (A+6) may vary by implementation; many versions stand on all 17. Refer to runtime prompts or source if this distinction matters for your game.
- Blackjack: A two-card 21 (Ace + 10-value) typically pays 3:2 against a non-blackjack dealer hand. If both have blackjack, it is a push.
- Bust: If you exceed 21, you lose immediately (bust).
- Shoe management: The shoe is constructed from a configurable number of standard 52-card decks. It automatically reshuffles when the remaining cards drop below 15.

Note: Features like Insurance, Surrender, and Split rules can vary. If supported by your implementation, the prompts will display the available actions and constraints (e.g., double only on first two cards).


## Configuration
- Number of decks (shoe size): Configure via `--decks N` if available. Defaults commonly to 6.
- Reshuffle threshold: Automatically reshuffles when remaining cards < 15. If a CLI flag is supported, use `--reshuffle-threshold N` to change it.
- Bankroll and betting limits: If exposed, configure via `--bankroll`, `--min-bet`, and `--max-bet`.

If flags are not exposed in your build, the defaults above still apply internally.


## Example Session
This is a sample transcript to illustrate typical interaction. Exact wording and symbols may differ slightly depending on your build.

> Welcome to Blackjack!
> Bankroll: $100. Min bet: $5. Enter bet (or 'q' to quit): 10
> Dealing...
> Your hand: [K♠, 7♦] (17)
> Dealer shows: [9♥, ?]
> Choose action: (h)it, (s)tand: s
> Dealer reveals: [9♥, 7♣] (16)
> Dealer hits...
> Dealer draws: 6♦ — Dealer total: 22 (bust)
> You win! Payout: $10
> Bankroll: $110
> Cards remaining in shoe: 112
> Enter bet (or 'q' to quit): 15
> Dealing...
> Your hand: [A♣, 9♠] (20)
> Dealer shows: [6♦, ?]
> Choose action: (h)it, (s)tand: s
> Dealer reveals: [6♦, 9♦] (15)
> Dealer hits...
> Dealer draws: 5♣ — Dealer total: 20
> Push. Your bet is returned.
> Bankroll: $110
> ...
> Shoe low on cards. Shuffling...


## Tips
- Enter lowercase shortcuts (h/s/d) unless your prompts specify otherwise.
- If you are unsure which options are available at any point, the prompt will list valid actions.
- The shoe will automatically reshuffle when it gets low (remaining < 15 cards); no action needed from you.


## Development Notes
- Object model: Card, Hand, Deck, Player, and a game loop/controller.
- Deck: Supports a configurable number of decks and automatically reshuffles when remaining < 15 cards.
- Python best practices: Code follows standard idioms for readability and maintainability.


## Playtesting and Acceptance
- Manually playtested to verify:
  - Basic flow: deal, hit/stand decisions, dealer play, and win/push/loss outcomes.
  - Shoe configuration via number of decks works when exposed.
  - Automatic reshuffle occurs when remaining cards < 15.


## Troubleshooting
- Ensure you are using Python 3.8+.
- If the command `python` maps to Python 2.x on your system, use `python3` instead.
- Run with `--help` (if supported) to see available runtime options and confirm flags.


## License
This project is provided as-is for educational purposes. Use, modify, and distribute according to your repository's chosen license.
