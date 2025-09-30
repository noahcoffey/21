# Implementation for Issue #1

## Title
Project Brief

## Plan
{
  "summary": "Implement a terminal-based single-player Blackjack game in Python with deck management, betting, standard rules, clear CLI, basic stats, configuration, and unit tests.",
  "implementation_plan": [
    "Step 1: Scaffold project structure (blackjack/, README.md, blackjack.py, deck.py, player.py, tests/test_blackjack.py) and initialize a git repo.",
    "Step 2: Implement Card and Deck in deck.py (Card dataclass, Unicode suit symbols, multi-deck support, shuffle, draw, remaining, reset/reshuffle logic with threshold check).",
    "Step 3: Implement Hand logic in a dedicated class (either in blackjack.py or deck.py): add_card, total calculation with flexible Ace valuation, is_blackjack (only first two cards), is_bust.",
    "Step 4: Implement Player and Dealer classes in player.py: Player with chips (stored in cents), place_bet validation, apply_win/lose/push, and basic stats (hands, wins, losses, pushes, net). Dealer with hand and play_turn(deck) logic (hit <=16, stand >=17, treating soft 17 as stand).",
    "Step 5: Implement game engine in blackjack.py: argument parsing for starting chips, number of decks, min bet; game loop orchestrating betting, dealing, natural blackjack checks, player turn (hit/stand), dealer turn, outcome resolution, and payouts (1:1, 3:2 for blackjack).",
    "Step 6: Build CLI rendering helpers: clear, readable printing of hands with card symbols, hide dealer hole card until reveal, show totals and chip balances, and display round results and stats.",
    "Step 7: Implement input validation and prompts: numeric bet within chips and >= min bet, action choices (h/s), replay (y/n), with graceful error messages and retry loops.",
    "Step 8: Add reshuffle policy: after each round, if deck.remaining() < threshold (default 15), recreate and shuffle multi-deck shoe and announce reshuffle.",
    "Step 9: Write unit tests in tests/test_blackjack.py using unittest: card/hand totals (especially multiple Aces), blackjack detection, dealer behavior at 16/17, deck shuffling/drawing and reshuffle threshold, betting constraints, and payout scenarios (win/loss/push/blackjack). Seed RNG for deterministic tests.",
    "Step 10: Update README with instructions, configuration options, rules implemented, and testing commands; verify acceptance criteria via a manual run-through."
  ],
  "complexity": "medium",
  "priority": "high",
  "estimated_subtasks": 10,
  "technical_requirements": [
    "Python 3.8+; prefer standard library only (random, dataclasses, typing, argparse, unittest)",
    "Represent currency as integer cents to correctly handle 3:2 blackjack payouts and avoid float rounding issues",
    "Card/Deck implementation supporting 52-card deck, multiple decks, and proper shuffling",
    "Hand evaluation with dynamic Ace valuation (11 or 1) to avoid busting when possible",
    "Dealer AI: must hit on 16 or less and stand on 17 or more (treat soft 17 as stand per spec)",
    "Configurable parameters: starting chips, number of decks, minimum bet",
    "Clear terminal I/O with input validation and Unicode suit symbols (with fallback if needed)",
    "Stats tracking: hands played, wins, losses, pushes, net amount won/lost",
    "Reshuffle logic when remaining cards < 15 (performed between rounds, not mid-hand)",
    "Unit tests using unittest framework; deterministic behavior via seeding random"
  ],
  "dependencies": [
    "Python standard library modules: random, dataclasses, typing, argparse, sys, itertools, unittest",
    "Terminal capable of displaying Unicode (\u2660 \u2665 \u2666 \u2663); consider ASCII fallback for incompatible environments"
  ],
  "risks": [
    "Ace handling edge cases: Multiple Aces must be valued correctly to avoid premature busts.",
    "Blackjack detection: Ensure only a two-card 21 is treated as natural blackjack (not a 3+ card 21).",
    "Soft 17 interpretation: Spec says stand on 17; ensure dealer stands on soft 17 to avoid rule ambiguity.",
    "Currency rounding: 3:2 payouts can cause rounding issues if using floats; mitigate by using integer cents.",
    "Unicode rendering: Some terminals (especially on Windows) may not render suit symbols; implement safe fallback.",
    "Reshuffle timing: Avoid reshuffling mid-hand; ensure reshuffle checks only occur between rounds.",
    "Input validation robustness: Prevent crashes from invalid inputs and handle EOF/interrupts gracefully."
  ],
  "testing_requirements": [
    "Card/Hand totals: Verify correct totals with combinations including multiple Aces (e.g., A+A+9 = 21; A+9+A = 21; A+K = blackjack).",
    "Blackjack detection and payout: Two-card 21 pays 3:2 and ends round immediately unless dealer also has blackjack (push).",
    "Dealer behavior: Dealer hits on 16 and stands on 17 (including soft 17); test boundary conditions.",
    "Bust logic: Player busts lose bet; dealer busts pay 1:1 if player not bust.",
    "Push handling: Equal totals result in return of bet.",
    "Betting validation: Cannot bet more than available chips, below minimum, zero, or negative; chips decrement/increment correctly.",
    "Deck operations: Shuffling produces varied order (seeded for test), drawing reduces count, multi-deck size correct.",
    "Reshuffle threshold: After a round, if remaining < 15, deck is recreated/shuffled for next hand.",
    "Stats tracking: Hands played, wins, losses, pushes, and net amount won/lost update correctly.",
    "CLI I/O: Basic prompts and outputs are formatted and error messages appear on invalid input (can be validated via functions where feasible)."
  ]
}

## Status
Implementation completed by Coding Agent

This is a marker file for the MVP. In production, actual code changes would be made here.
