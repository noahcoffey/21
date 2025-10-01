# Terminal Blackjack (Scaffold)

A terminal-based Blackjack game implemented in Python 3.8+ using only the standard library.

This is Step 1/12 of the implementation: project scaffolding and initial code skeletons.

## Features (current step)
- Project structure scaffold
- Core models: Card, Deck, Hand (ace valuation algorithm included)
- Minimal CLI entrypoint stub

## Requirements
- Python 3.8+
- Standard library only (random, argparse, unittest, etc.)

## Setup
1) Create a virtual environment (optional but recommended):
   - macOS/Linux:
     - python3 -m venv .venv
     - source .venv/bin/activate
   - Windows (PowerShell):
     - py -3 -m venv .venv
     - .venv\Scripts\Activate.ps1

2) Upgrade pip (optional):
   - python -m pip install --upgrade pip

No external dependencies are required at this step.

## Run (CLI scaffold)
- Run the CLI scaffold:
  - python -m blackjack.blackjack --help
  - python -m blackjack.blackjack --demo

The demo deals example hands to showcase the deck and hand logic only; full gameplay will be added in subsequent steps.

## Testing
- When tests are added, run using:
  - python -m unittest

## Project Structure (current)
- README.md
- blackjack/
  - blackjack.py   (CLI skeleton)
  - deck.py        (Card, Deck, Hand models)
  - [player.py]    (planned)
  - [tests/test_blackjack.py] (planned)

## Notes
- Ace valuation algorithm is implemented in Hand.total: aces start as 11 and are demoted to 1 as needed to avoid busting.
- Future steps will add Player abstractions, dealer logic, full game loop, and comprehensive tests.
