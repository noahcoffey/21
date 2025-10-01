from __future__ import annotations

import os
import sys
from typing import IO, Iterable, List, Optional, Sequence, Tuple, Union, Dict


CardLike = object
HandLike = object
PlayerLike = object


class TerminalUI:
    """
    Terminal UI helpers for rendering Blackjack game state and normalizing user input.

    This module is designed to work with a typical Blackjack object model consisting of
    Card, Hand, Player, and a Game controller. It uses duck-typing to interoperate with
    these objects and avoids strict coupling to any specific implementation.

    Key features:
    - Render headers and sections
    - Render hands (with dealer hole card hidden or revealed)
    - Render totals and chip amounts
    - Clear screen and display prompts/errors
    - Normalize user input (y/n, h/s) with retries
    """

    def __init__(
        self,
        in_stream: Optional[IO[str]] = None,
        out_stream: Optional[IO[str]] = None,
        enable_color: Optional[bool] = None,
    ) -> None:
        self._in: IO[str] = in_stream if in_stream is not None else sys.stdin
        self._out: IO[str] = out_stream if out_stream is not None else sys.stdout
        if enable_color is None:
            # Enable color only if output is a TTY
            self._color = hasattr(self._out, "isatty") and self._out.isatty()
        else:
            self._color = bool(enable_color)

        self._suits = {
            "spades": "\u2660",  # ♠
            "hearts": "\u2665",  # ♥
            "diamonds": "\u2666",  # ♦
            "clubs": "\u2663",  # ♣
            "s": "\u2660",
            "h": "\u2665",
            "d": "\u2666",
            "c": "\u2663",
            "♠": "\u2660",
            "♥": "\u2665",
            "♦": "\u2666",
            "♣": "\u2663",
        }

        # ANSI styles (used conservatively)
        if self._color:
            self._style_bold = "\033[1m"
            self._style_dim = "\033[2m"
            self._style_red = "\033[31m"
            self._style_green = "\033[32m"
            self._style_yellow = "\033[33m"
            self._style_reset = "\033[0m"
        else:
            self._style_bold = ""
            self._style_dim = ""
            self._style_red = ""
            self._style_green = ""
            self._style_yellow = ""
            self._style_reset = ""

    # ------------------------------
    # Public rendering helpers
    # ------------------------------

    def clear_screen(self) -> None:
        """Clear the terminal screen and move cursor to home position."""
        try:
            if os.name == "nt":
                os.system("cls")
            else:
                # ANSI clear screen and move cursor home
                self._out.write("\033[2J\033[H")
                self._out.flush()
        except Exception:
            # Fallback: print a few newlines
            self._out.write("\n" * 50)
            self._out.flush()

    def header(self, title: str, subtitle: Optional[str] = None) -> None:
        """Render a header with optional subtitle."""
        bar = "=" * max(8, len(title))
        self._println(bar)
        self._println(f"{self._style_bold}{title}{self._style_reset}")
        if subtitle:
            self._println(subtitle)
        self._println(bar)

    def section(self, title: str) -> None:
        """Render a section header."""
        bar = "-" * max(6, len(title))
        self._println(f"{self._style_bold}{title}{self._style_reset}")
        self._println(bar)

    def format_hand(
        self,
        owner_name: str,
        hand: HandLike,
        hide_hole: bool = False,
        show_total: bool = True,
    ) -> str:
        """
        Return a string representation of a hand.

        - owner_name: Label for the hand owner (e.g., "Dealer", "Alice").
        - hand: Object that provides iterable of cards, typically via `.cards` or iteration.
        - hide_hole: If True and there are >= 2 cards, the second card is hidden (dealer hole).
        - show_total: Show the hand total if not hidden; when hidden, total is shown as '?'.
        """
        cards = self._get_cards(hand)
        rendered_cards: List[str] = []
        for idx, card in enumerate(cards):
            hide = hide_hole and idx == 1  # Hide the second card as dealer's hole card
            rendered_cards.append(self._format_card(card, hide))

        # Compute or mask total
        total_str: str
        if show_total:
            if hide_hole and len(cards) >= 2:
                total_str = "?"
            else:
                total = self._get_hand_total(hand)
                total_str = str(total) if total is not None else "?"
        else:
            total_str = ""

        card_line = " ".join(rendered_cards) if rendered_cards else "(no cards)"
        total_segment = f"  Total: {total_str}" if show_total else ""

        return f"{owner_name}: {card_line}{total_segment}"

    def show_hand(
        self,
        owner_name: str,
        hand: HandLike,
        hide_hole: bool = False,
        show_total: bool = True,
    ) -> None:
        self._println(self.format_hand(owner_name, hand, hide_hole=hide_hole, show_total=show_total))

    def format_game_state(
        self,
        dealer_hand: HandLike,
        player_hands: Sequence[Tuple[str, HandLike]],
        reveal_dealer: bool = False,
    ) -> str:
        """Return a multi-line string of the current game state.

        - dealer_hand: Dealer's hand
        - player_hands: Sequence of (player_name, hand)
        - reveal_dealer: If True, dealer hole card is revealed
        """
        lines: List[str] = []
        lines.append(self.format_hand("Dealer", dealer_hand, hide_hole=not reveal_dealer, show_total=True))
        for name, hand in player_hands:
            lines.append(self.format_hand(name, hand, hide_hole=False, show_total=True))
        return "\n".join(lines)

    def show_game_state(
        self,
        dealer_hand: HandLike,
        player_hands: Sequence[Tuple[str, HandLike]],
        reveal_dealer: bool = False,
    ) -> None:
        self._println(self.format_game_state(dealer_hand, player_hands, reveal_dealer=reveal_dealer))

    def show_chips(self, name: str, chips: Union[int, float], bet: Optional[Union[int, float]] = None, currency: str = "$") -> None:
        """Display chip stack and optional current bet for a player."""
        chips_str = f"{currency}{chips}"
        if bet is not None:
            bet_str = f"{currency}{bet}"
            self._println(f"{name} Chips: {chips_str}  |  Current Bet: {bet_str}")
        else:
            self._println(f"{name} Chips: {chips_str}")

    def print_error(self, message: str) -> None:
        """Print an error message."""
        self._println(f"{self._style_red}Error:{self._style_reset} {message}")

    def print_info(self, message: str) -> None:
        """Print an informational message."""
        self._println(message)

    def wait_for_enter(self, prompt: str = "Press Enter to continue...") -> None:
        """Block until the user presses Enter."""
        self._print(prompt + " ")
        self._readline()

    # ------------------------------
    # Input normalization helpers
    # ------------------------------

    def prompt_yes_no(
        self,
        prompt: str,
        default: Optional[bool] = None,
        max_attempts: Optional[int] = None,
    ) -> bool:
        """
        Prompt the user for a yes/no response with normalization and retries.

        - default: Optional default value (True/False) used when the user submits an empty line.
        - max_attempts: Limit attempts; None means unlimited until valid.
        Returns True for yes, False for no.
        Raises ValueError if attempts exhausted without a valid answer.
        """
        suffix = self._yn_suffix(default)
        attempts = 0
        while True:
            attempts += 1
            self._print(f"{prompt} {suffix} ")
            raw = self._readline()
            if raw is None:
                # Treat EOF like empty input (use default if available)
                raw = ""
            raw = raw.strip().lower()
            if raw == "" and default is not None:
                return bool(default)
            if raw in ("y", "yes", "yeah", "yup", "true", "t"):
                return True
            if raw in ("n", "no", "nope", "false", "f"):
                return False
            self.print_error("Please enter y or n.")
            if max_attempts is not None and attempts >= max_attempts:
                raise ValueError("Maximum attempts exceeded for yes/no prompt")

    def prompt_hit_or_stand(
        self,
        prompt: str = "Hit or Stand?",
        default: Optional[str] = None,
        max_attempts: Optional[int] = None,
    ) -> str:
        """
        Prompt the user to choose Hit or Stand, normalizing to 'hit' or 'stand'.

        - default: Optional default value ('hit'/'stand') used for empty input.
        - max_attempts: Limit attempts; None means unlimited until valid.
        Returns 'hit' or 'stand'.
        Raises ValueError if attempts exhausted without a valid answer.
        """
        default_norm = None
        if default is not None:
            default_norm = self._normalize_hit_stand(default)
        suffix = self._hs_suffix(default_norm)
        attempts = 0
        while True:
            attempts += 1
            self._print(f"{prompt} {suffix} ")
            raw = self._readline()
            if raw is None:
                raw = ""
            raw = raw.strip().lower()
            if raw == "" and default_norm is not None:
                return default_norm
            normalized = self._normalize_hit_stand(raw)
            if normalized:
                return normalized
            self.print_error("Please enter 'h' to hit or 's' to stand.")
            if max_attempts is not None and attempts >= max_attempts:
                raise ValueError("Maximum attempts exceeded for hit/stand prompt")

    def prompt_choice(
        self,
        prompt: str,
        valid: Iterable[str],
        aliases: Optional[Dict[str, str]] = None,
        default: Optional[str] = None,
        max_attempts: Optional[int] = None,
    ) -> str:
        """
        Generic normalized choice prompt with retries. Returns a value from `valid`.

        - valid: Iterable of canonical valid options (case-insensitive)
        - aliases: Optional map of alias -> canonical option (case-insensitive keys)
        - default: Optional default canonical option used for empty input
        - max_attempts: Optional maximum attempts before raising ValueError
        """
        valid_lower = {v.lower(): v for v in valid}
        alias_map: Dict[str, str] = {}
        if aliases:
            for k, v in aliases.items():
                alias_map[k.lower()] = v
        default_norm: Optional[str] = None
        if default is not None:
            d = default.lower()
            default_norm = valid_lower.get(d) or alias_map.get(d)
            if default_norm is None:
                raise ValueError("Default value must be one of valid options or their aliases")
        suffix = self._choice_suffix(valid_lower.values(), default_norm)

        attempts = 0
        while True:
            attempts += 1
            self._print(f"{prompt} {suffix} ")
            raw = self._readline()
            if raw is None:
                raw = ""
            raw_l = raw.strip().lower()
            if raw_l == "" and default_norm is not None:
                return default_norm
            if raw_l in valid_lower:
                return valid_lower[raw_l]
            if raw_l in alias_map:
                canon = alias_map[raw_l]
                # Ensure the canonical is in valid
                canon_l = canon.lower()
                if canon_l in valid_lower:
                    return valid_lower[canon_l]
            self.print_error(f"Please enter one of: {', '.join(valid_lower.values())}.")
            if max_attempts is not None and attempts >= max_attempts:
                raise ValueError("Maximum attempts exceeded for choice prompt")

    # ------------------------------
    # Internal utilities
    # ------------------------------

    def _print(self, s: str) -> None:
        self._out.write(s)
        self._out.flush()

    def _println(self, s: str) -> None:
        self._out.write(s + "\n")
        self._out.flush()

    def _readline(self) -> Optional[str]:
        try:
            return self._in.readline()
        except Exception:
            return None

    def _yn_suffix(self, default: Optional[bool]) -> str:
        if default is True:
            return "[Y/n]"
        if default is False:
            return "[y/N]"
        return "[y/n]"

    def _hs_suffix(self, default: Optional[str]) -> str:
        # default is 'hit' or 'stand'
        if default == "hit":
            return "[H/s]"
        if default == "stand":
            return "[h/S]"
        return "[h/s]"

    def _choice_suffix(self, options: Iterable[str], default: Optional[str]) -> str:
        opts = list(options)
        if default is None:
            return f"[{ '/'.join(opts) }]"
        # Mark default with capitalization convention
        labeled = []
        d_low = default.lower()
        for o in opts:
            if o.lower() == d_low:
                labeled.append(o.upper())
            else:
                labeled.append(o.lower())
        return f"[{ '/'.join(labeled) }]"

    def _normalize_hit_stand(self, s: str) -> Optional[str]:
        s = s.strip().lower()
        if s in ("h", "hit", "+"):
            return "hit"
        if s in ("s", "stand", "stay", "stick", "-"):
            return "stand"
        return None

    # ------------------------------
    # Card/Hand formatting
    # ------------------------------

    def _format_card(self, card: CardLike, hide: bool = False) -> str:
        if hide:
            return "[??]"
        # Try to extract rank and suit with common attribute names or str fallback
        rank = self._get_card_rank(card)
        suit_char = self._get_card_suit_symbol(card)
        if rank and suit_char:
            return f"[{rank}{suit_char}]"
        # Fallback to stringified card trimmed
        return f"[{str(card)}]"

    def _get_cards(self, hand: HandLike) -> List[CardLike]:
        # Common ways to access cards: .cards, .get_cards(), iteration
        cards: List[CardLike]
        if hasattr(hand, "cards"):
            maybe = getattr(hand, "cards")
            if isinstance(maybe, (list, tuple)):
                return list(maybe)
        if hasattr(hand, "get_cards") and callable(getattr(hand, "get_cards")):
            try:
                cards = list(getattr(hand, "get_cards")())
                return cards
            except Exception:
                pass
        # Fallback: attempt to iterate over hand
        try:
            return list(iter(hand))  # type: ignore[arg-type]
        except Exception:
            return []

    def _get_card_rank(self, card: CardLike) -> Optional[str]:
        # Common attributes: .rank, .value, .face
        for attr in ("rank", "face", "value"):
            if hasattr(card, attr):
                val = getattr(card, attr)
                if isinstance(val, str):
                    return self._normalize_rank_str(val)
                try:
                    # numeric values for 2..10
                    if isinstance(val, int):
                        return str(val)
                    # If val has __str__, use it
                    as_str = str(val)
                    return self._normalize_rank_str(as_str)
                except Exception:
                    continue
        # Try parse from str(card)
        try:
            s = str(card)
            # Look for patterns like 'A♠' or 'A of Spades'
            if " of " in s:
                part = s.split(" of ", 1)[0]
                return self._normalize_rank_str(part)
            return self._normalize_rank_str(s[:2].strip())
        except Exception:
            return None

    def _normalize_rank_str(self, r: str) -> str:
        r = r.strip().upper()
        # Map long names
        mapping = {
            "ACE": "A",
            "KING": "K",
            "QUEEN": "Q",
            "JACK": "J",
        }
        if r in mapping:
            return mapping[r]
        # Allow '10' or 'T'
        if r in ("T",):
            return "10"
        # Allow already-valid ranks
        if r in {"A", "K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2"}:
            return r
        # Try if r starts with a number
        for n in ("10", "9", "8", "7", "6", "5", "4", "3", "2"):
            if r.startswith(n):
                return n
        # Last resort: first char
        if r:
            ch = r[0]
            if ch in {"A", "K", "Q", "J"}:
                return ch
        return r

    def _get_card_suit_symbol(self, card: CardLike) -> Optional[str]:
        # Common attributes: .suit
        candidates: List[str] = []
        if hasattr(card, "suit"):
            try:
                suit_val = getattr(card, "suit")
                candidates.append(str(suit_val))
            except Exception:
                pass
        # Parse from string representation
        try:
            s = str(card)
            # If contains unicode suit, return it
            for sym in ("♠", "♥", "♦", "♣"):
                if sym in s:
                    return sym
            # Try formats like "A of Spades"
            if " of " in s:
                suit_name = s.split(" of ", 1)[1].strip()
                candidates.append(suit_name)
        except Exception:
            pass

        for cand in candidates:
            c = cand.strip().lower()
            # Normalize to first letter if word
            if c in self._suits:
                return self._suits[c]
            if c and c[0] in self._suits:
                return self._suits[c[0]]
        return None

    def _get_hand_total(self, hand: HandLike) -> Optional[int]:
        # Try common attributes/methods: .total, .value, .best_total, .score, .get_value()
        for attr in ("total", "value", "best_total", "score"):
            if hasattr(hand, attr):
                val = getattr(hand, attr)
                if isinstance(val, int):
                    return val
                try:
                    if isinstance(val, (str, float)):
                        return int(val)
                except Exception:
                    pass
        for meth in ("total", "value", "best_total", "score", "get_value", "get_total"):
            if hasattr(hand, meth) and callable(getattr(hand, meth)):
                try:
                    v = int(getattr(hand, meth)())
                    return v
                except Exception:
                    pass
        # Fallback: compute from cards (Blackjack rules)
        cards = self._get_cards(hand)
        if not cards:
            return 0
        return self._compute_blackjack_total(cards)

    def _compute_blackjack_total(self, cards: Sequence[CardLike]) -> int:
        total = 0
        aces = 0
        for card in cards:
            r = self._get_card_rank(card)
            if not r:
                continue
            if r == "A":
                aces += 1
                total += 11
            elif r in {"K", "Q", "J", "10"}:
                total += 10
            else:
                try:
                    total += int(r)
                except Exception:
                    # Unknown, ignore or treat as 0
                    pass
        # Adjust for aces
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total


# Convenience factory for default TTY-aware UI
_default_ui: Optional[TerminalUI] = None


def get_ui() -> TerminalUI:
    global _default_ui
    if _default_ui is None:
        _default_ui = TerminalUI()
    return _default_ui


__all__ = [
    "TerminalUI",
    "get_ui",
]
