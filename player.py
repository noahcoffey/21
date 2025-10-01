from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, Optional, Union


def dollars_to_cents(amount: Union[int, float, str]) -> int:
    '''
    Convert a dollar amount to integer cents.
    Accepts int, float, or numeric string.
    Rounds to nearest cent using bankers rounding for floats/strings.
    '''
    if isinstance(amount, int):
        # Interpreted as dollars
        return amount * 100
    if isinstance(amount, float):
        return int(round(amount * 100))
    if isinstance(amount, str):
        if not amount.strip():
            raise ValueError('amount string is empty')
        return int(round(float(amount) * 100))
    raise TypeError('amount must be int, float, or str')


def cents_to_dollars_str(cents: int) -> str:
    '''Format integer cents to a human-readable dollar string.'''
    sign = '-' if cents < 0 else ''
    cents_abs = abs(cents)
    dollars = cents_abs // 100
    rem = cents_abs % 100
    return f'{sign}${dollars}.{rem:02d}'


@dataclass
class Player:
    '''
    Blackjack player tracking chips (stored in cents), bets, and statistics.

    - Chips are stored in integer cents to support precise 3:2 blackjack payouts.
    - Bets are debited from the chip stack when placed.
    - Settlement methods credit chips appropriately and update lifetime stats.

    Stats:
      - hands_played: total settled hands (wins + losses + pushes)
      - wins: number of winning hands
      - losses: number of losing hands
      - pushes: number of pushes
      - net_cents: cumulative profit/loss across settled hands
        (sum of outcomes: +1x bet for normal win, +1.5x for blackjack, -1x for loss, 0 for push)
    '''

    name: str
    _chips_cents: int = field(default=0, repr=False)
    min_bet_cents: int = 1
    max_bet_cents: Optional[int] = None

    # Stats
    hands_played: int = 0
    wins: int = 0
    losses: int = 0
    pushes: int = 0
    net_cents: int = 0

    # Internal state
    _next_bet_id: int = field(default=1, init=False, repr=False)
    _active_bets: Dict[int, int] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError('name must be a non-empty string')
        if not isinstance(self._chips_cents, int) or self._chips_cents < 0:
            raise ValueError('chips must be a non-negative integer number of cents')
        if not isinstance(self.min_bet_cents, int) or self.min_bet_cents <= 0:
            raise ValueError('min_bet_cents must be a positive integer')
        if self.max_bet_cents is not None:
            if not isinstance(self.max_bet_cents, int) or self.max_bet_cents <= 0:
                raise ValueError('max_bet_cents must be a positive integer when provided')
            if self.max_bet_cents < self.min_bet_cents:
                raise ValueError('max_bet_cents must be >= min_bet_cents')

    # -------------------- Properties --------------------
    @property
    def chips_cents(self) -> int:
        '''Return current chip count in cents.'''
        return self._chips_cents

    @property
    def chips_str(self) -> str:
        '''Return current chip count formatted as dollars.'''
        return cents_to_dollars_str(self._chips_cents)

    @property
    def active_bets_count(self) -> int:
        return len(self._active_bets)

    # -------------------- Bankroll management --------------------
    def deposit_cents(self, amount_cents: int) -> None:
        '''Add chips to the player's stack (in cents).'''
        if not isinstance(amount_cents, int) or amount_cents <= 0:
            raise ValueError('deposit amount must be a positive integer (cents)')
        self._chips_cents += amount_cents

    def withdraw_cents(self, amount_cents: int) -> None:
        '''Remove chips from the player's stack (in cents).'''
        if not isinstance(amount_cents, int) or amount_cents <= 0:
            raise ValueError('withdraw amount must be a positive integer (cents)')
        if amount_cents > self._chips_cents:
            raise ValueError('cannot withdraw more chips than available')
        self._chips_cents -= amount_cents

    # -------------------- Betting --------------------
    def can_bet(self, amount_cents: int) -> bool:
        '''Return True if a bet of amount_cents is currently allowed.'''
        try:
            self._validate_bet_amount(amount_cents)
            return True
        except ValueError:
            return False

    def _validate_bet_amount(self, amount_cents: int) -> None:
        if not isinstance(amount_cents, int):
            raise ValueError('bet amount must be an integer number of cents')
        if amount_cents <= 0:
            raise ValueError('bet amount must be greater than zero')
        if amount_cents < self.min_bet_cents:
            raise ValueError(f'minimum bet is {cents_to_dollars_str(self.min_bet_cents)}')
        if self.max_bet_cents is not None and amount_cents > self.max_bet_cents:
            raise ValueError(f'maximum bet is {cents_to_dollars_str(self.max_bet_cents)}')
        if amount_cents > self._chips_cents:
            raise ValueError('insufficient chips for this bet')

    def place_bet(self, amount_cents: int) -> int:
        '''
        Place a bet and debit chips immediately.

        Returns a bet_id int for later settlement.
        '''
        self._validate_bet_amount(amount_cents)
        self._chips_cents -= amount_cents
        bet_id = self._next_bet_id
        self._next_bet_id += 1
        self._active_bets[bet_id] = amount_cents
        return bet_id

    def cancel_bet(self, bet_id: int) -> int:
        '''Cancel an active bet before the hand starts; returns funds to chips.'''
        bet = self._pop_bet(bet_id)
        self._chips_cents += bet
        return bet

    def _pop_bet(self, bet_id: int) -> int:
        if not isinstance(bet_id, int):
            raise ValueError('bet_id must be an int')
        try:
            return self._active_bets.pop(bet_id)
        except KeyError as exc:
            raise KeyError(f'unknown bet_id: {bet_id}') from exc

    # -------------------- Settlement --------------------
    def settle_win(self, bet_id: int, payout_ratio: Union[float, Fraction] = Fraction(1, 1)) -> int:
        '''
        Settle a winning hand. Credits back the original bet plus the payout.

        payout_ratio examples:
          - 1 (or Fraction(1,1)) for even-money win
          - 3/2 (Fraction(3,2)) for blackjack

        Returns the total amount credited to chips (bet + payout) in cents.
        '''
        bet = self._pop_bet(bet_id)
        ratio = self._to_fraction(payout_ratio)
        payout = (bet * ratio.numerator) // ratio.denominator  # floor to the cent
        credit = bet + payout
        self._chips_cents += credit

        # Update stats
        self.hands_played += 1
        self.wins += 1
        # Net reflects outcome relative to pre-bet bankroll; at placement we debited bet,
        # so the net at settlement for a win is +payout ratio * bet.
        self.net_cents += payout
        return credit

    def settle_blackjack(self, bet_id: int) -> int:
        '''Settle a natural blackjack win at 3:2 payout.'''
        return self.settle_win(bet_id, Fraction(3, 2))

    def settle_push(self, bet_id: int) -> int:
        '''Settle a push: return the original bet only.'''
        bet = self._pop_bet(bet_id)
        self._chips_cents += bet
        self.hands_played += 1
        self.pushes += 1
        # Net 0 for push
        return bet

    def settle_loss(self, bet_id: int) -> int:
        '''Settle a loss: bet remains with the house.'''
        bet = self._pop_bet(bet_id)
        self.hands_played += 1
        self.losses += 1
        self.net_cents -= bet
        # No chips credited
        return 0

    @staticmethod
    def _to_fraction(value: Union[float, Fraction]) -> Fraction:
        if isinstance(value, Fraction):
            return value
        if isinstance(value, float):
            # Support common ratios precisely: 1.0, 1.5, 2.0, etc.
            # Convert with limited denominators to avoid float noise.
            if abs(value - 1.5) < 1e-9:
                return Fraction(3, 2)
            if abs(value - 1.0) < 1e-9:
                return Fraction(1, 1)
            if abs(value - 2.0) < 1e-9:
                return Fraction(2, 1)
            # Fallback: approximate with denominator up to 100
            return Fraction.from_float(value).limit_denominator(100)
        raise TypeError('payout_ratio must be a float or Fraction')

    # -------------------- Stats & Serialization --------------------
    def reset_stats(self) -> None:
        '''Reset lifetime statistics (does not change chips or active bets).'''
        self.hands_played = 0
        self.wins = 0
        self.losses = 0
        self.pushes = 0
        self.net_cents = 0

    @property
    def stats(self) -> dict:
        '''Return a snapshot of the player's lifetime statistics.'''
        return {
            'hands': self.hands_played,
            'wins': self.wins,
            'losses': self.losses,
            'pushes': self.pushes,
            'net_cents': self.net_cents,
            'net_str': cents_to_dollars_str(self.net_cents),
        }

    def to_dict(self) -> dict:
        '''Serialize player state for external use (e.g., UI or save state).'''
        return {
            'name': self.name,
            'chips_cents': self._chips_cents,
            'chips_str': self.chips_str,
            'min_bet_cents': self.min_bet_cents,
            'max_bet_cents': self.max_bet_cents,
            'active_bets': dict(self._active_bets),
            'stats': self.stats,
        }

    def __repr__(self) -> str:
        return (
            f"Player(name='{self.name}', chips={self.chips_str}, "
            f"hands={self.hands_played}, W-L-P={self.wins}-{self.losses}-{self.pushes}, "
            f"net={cents_to_dollars_str(self.net_cents)})"
        )
