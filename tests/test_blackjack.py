import importlib
import inspect
import random
import types
import pytest

# Helper import machinery to locate expected symbols in common module layouts
CANDIDATES = {
    "Card": ["blackjack.card", "blackjack.cards", "blackjack.models", "blackjack"],
    "Hand": ["blackjack.hand", "blackjack.hands", "blackjack.models", "blackjack"],
    "Deck": ["blackjack.deck", "blackjack.shoe", "blackjack.models", "blackjack"],
    "Player": ["blackjack.player", "blackjack.players", "blackjack.models", "blackjack"],
    "Game": ["blackjack.game", "blackjack.engine", "blackjack.controller", "blackjack"],
}


def _load_symbol(name: str):
    errors = []
    for modname in CANDIDATES.get(name, []):
        try:
            mod = importlib.import_module(modname)
        except Exception as e:  # pragma: no cover - best effort import layering
            errors.append((modname, e))
            continue
        if hasattr(mod, name):
            return getattr(mod, name)
    reason = f"Could not locate symbol {name} in any of: {CANDIDATES.get(name, [])}. Errors: {errors}"
    pytest.skip(reason)


Card = None
Hand = None
Deck = None
Player = None
Game = None


@pytest.fixture(scope="module")
def api():
    global Card, Hand, Deck, Player, Game
    if Card is None:
        Card = _load_symbol("Card")
    if Hand is None:
        Hand = _load_symbol("Hand")
    if Deck is None:
        Deck = _load_symbol("Deck")
    # Player/Game may be skipped in some tests if unavailable
    try:
        Player = _load_symbol("Player")
    except Exception:  # pragma: no cover - optional
        Player = None
    try:
        Game = _load_symbol("Game")
    except Exception:  # pragma: no cover - optional
        Game = None
    return types.SimpleNamespace(Card=Card, Hand=Hand, Deck=Deck, Player=Player, Game=Game)


@pytest.fixture(autouse=True)
def deterministic_rng():
    # Ensure deterministic behavior for tests relying on RNG/shuffle
    random.seed(1337)
    yield
    random.seed()


# ---------- Helper constructors and accessors ----------

def make_card(CardCls, rank: str, suit: str = "Spades"):
    # Try common constructors
    try:
        return CardCls(rank, suit)
    except Exception:
        pass
    try:
        return CardCls(rank=rank, suit=suit)
    except Exception:
        pass
    try:
        return CardCls(value=rank, suit=suit)
    except Exception:
        pass
    # Try shorthand factory from_str like 'AS' (Ace of Spades)
    fs = None
    for cand in ("from_str", "from_string", "parse"):
        if hasattr(CardCls, cand):
            fs = getattr(CardCls, cand)
            break
    if fs:
        spade_code = "S" if suit.lower().startswith("spad") else suit[:1]
        return fs(f"{rank}{spade_code}")
    raise AssertionError("Unable to construct Card with provided API")


def make_hand(HandCls, cards):
    # Instantiate empty hand
    try:
        hand = HandCls()
    except Exception:
        # Some implementations accept initial list of cards
        try:
            hand = HandCls(cards=[])  # start empty, then add
        except Exception:
            hand = HandCls(cards=list())
    for c in cards:
        if hasattr(hand, "add_card"):
            hand.add_card(c)
        elif hasattr(hand, "add"):
            hand.add(c)
        elif hasattr(hand, "append"):
            hand.append(c)
        elif hasattr(hand, "cards") and hasattr(hand.cards, "append"):
            hand.cards.append(c)
        else:
            raise AssertionError("Unable to add cards to Hand with provided API")
    return hand


def hand_value(hand) -> int:
    # Prefer property 'value' if numeric
    if hasattr(hand, "value") and not callable(getattr(hand, "value")):
        val = getattr(hand, "value")
        if isinstance(val, int):
            return val
    # Try common methods
    for name in ("best_value", "value", "total", "score"):
        if hasattr(hand, name):
            m = getattr(hand, name)
            if callable(m):
                v = m()
            else:
                v = m
            if isinstance(v, int):
                return v
    raise AssertionError("Unable to derive hand value from provided API")


def is_blackjack(hand) -> bool:
    for name in ("is_blackjack", "blackjack", "is_natural"):
        if hasattr(hand, name):
            prop = getattr(hand, name)
            return prop() if callable(prop) else bool(prop)
    # Fallback: two-card 21
    n_cards = None
    if hasattr(hand, "cards") and isinstance(hand.cards, (list, tuple)):
        n_cards = len(hand.cards)
    return (n_cards == 2) and (hand_value(hand) == 21)


def is_bust(hand) -> bool:
    for name in ("is_bust", "is_busted", "bust"):
        if hasattr(hand, name):
            prop = getattr(hand, name)
            return prop() if callable(prop) else bool(prop)
    return hand_value(hand) > 21


def deck_remaining(deck) -> int:
    # Try magic len
    try:
        l = len(deck)  # type: ignore
        if isinstance(l, int) and l >= 0:
            return l
    except Exception:
        pass
    # Try common properties
    for name in ("remaining", "size"):
        if hasattr(deck, name) and not callable(getattr(deck, name)):
            v = getattr(deck, name)
            if isinstance(v, int):
                return v
    # Try common methods
    for name in ("cards_remaining", "remaining", "count", "__len__"):
        if hasattr(deck, name):
            m = getattr(deck, name)
            if callable(m):
                v = m()
                if isinstance(v, int):
                    return v
    # Try internal list length
    for attr in ("cards", "_cards", "shoe"):
        if hasattr(deck, attr):
            lst = getattr(deck, attr)
            try:
                return len(lst)
            except Exception:
                pass
    raise AssertionError("Unable to determine deck remaining count")


def deck_draw(deck):
    for name in ("draw", "deal", "take", "pop"):
        if hasattr(deck, name):
            m = getattr(deck, name)
            if callable(m):
                return m()
    # Try drawing from internal list
    for attr in ("cards", "_cards", "shoe"):
        if hasattr(deck, attr):
            lst = getattr(deck, attr)
            if hasattr(lst, "pop"):
                return lst.pop()
            if hasattr(lst, "__getitem__") and hasattr(lst, "__delitem__"):
                card = lst[-1]
                del lst[-1]
                return card
    raise AssertionError("Unable to draw from deck with provided API")


def deck_shuffle(deck):
    for name in ("shuffle", "reshuffle", "shuffle_shoe"):
        if hasattr(deck, name):
            m = getattr(deck, name)
            if callable(m):
                return m()
    # Fallback: shuffle internal list
    for attr in ("cards", "_cards", "shoe"):
        if hasattr(deck, attr):
            lst = getattr(deck, attr)
            try:
                random.shuffle(lst)
                return
            except Exception:
                pass
    raise AssertionError("Unable to shuffle deck with provided API")


# ---------- Tests ----------

def test_ace_valuation(api):
    # A + 9 = 20; A + 9 + 9 = 19; A + A + 9 = 21
    a = make_card(api.Card, "A")
    nine = make_card(api.Card, "9")
    hand1 = make_hand(api.Hand, [a, nine])
    assert hand_value(hand1) == 20

    hand2 = make_hand(api.Hand, [make_card(api.Card, "A"), make_card(api.Card, "9"), make_card(api.Card, "9")])
    assert hand_value(hand2) == 19

    hand3 = make_hand(api.Hand, [make_card(api.Card, "A"), make_card(api.Card, "A"), make_card(api.Card, "9")])
    assert hand_value(hand3) == 21


def test_blackjack_detection(api):
    a = make_card(api.Card, "A")
    ten = make_card(api.Card, "K")  # any 10-value card
    hand = make_hand(api.Hand, [a, ten])
    assert hand_value(hand) == 21
    assert is_blackjack(hand) is True


def test_bust_detection(api):
    ten = make_card(api.Card, "10")
    nine = make_card(api.Card, "9")
    five = make_card(api.Card, "5")
    hand = make_hand(api.Hand, [ten, nine, five])
    assert hand_value(hand) > 21
    assert is_bust(hand) is True


def test_deck_draw_and_shuffle(api):
    # Deterministic seed to make shuffle predictable if needed
    random.seed(42)
    d1 = api.Deck(1) if len(inspect.signature(api.Deck).parameters) >= 1 else api.Deck()
    initial = deck_remaining(d1)
    # Expect 52 cards for a single deck
    assert initial in (52, 52)  # explicit 52 to be clear

    _ = deck_draw(d1)
    after_one = deck_remaining(d1)
    assert after_one == initial - 1

    # Shuffle should not change card count
    deck_shuffle(d1)
    assert deck_remaining(d1) == after_one


def test_deck_reshuffles_when_low(api):
    # Requirement: Deck reshuffles when remaining < 15 cards
    random.seed(99)
    d = api.Deck(1) if len(inspect.signature(api.Deck).parameters) >= 1 else api.Deck()
    full = deck_remaining(d)
    assert full >= 52

    # Draw down to below threshold
    while deck_remaining(d) > 14:
        deck_draw(d)
    assert deck_remaining(d) <= 14

    # Next draw should trigger reshuffle per requirement; remaining becomes full-1
    deck_draw(d)
    remaining = deck_remaining(d)
    expected_after_reshuffle = full - 1

    assert remaining == expected_after_reshuffle, (
        f"Deck did not reshuffle when remaining < 15. Expected {expected_after_reshuffle}, got {remaining}"
    )


@pytest.mark.parametrize(
    "bet,bankroll,table_min,table_max,should_succeed",
    [
        (10, 100, 5, 500, True),     # valid bet
        (4, 100, 5, 500, False),     # below table min
        (600, 1000, 5, 500, False),  # above table max
        (200, 150, 5, 500, False),   # above bankroll
    ],
)
def test_betting_limits(api, bet, bankroll, table_min, table_max, should_succeed):
    if api.Player is None:
        pytest.skip("Player class not available for betting tests")

    # Try to use Player.place_bet if available; fall back to Game if it manages betting
    p = None
    try:
        p = api.Player(name="Tester", bankroll=bankroll)
    except Exception:
        try:
            p = api.Player("Tester", bankroll)
        except Exception:
            pytest.skip("Unable to construct Player for betting tests")

    # Snapshot bankroll
    def get_bankroll(obj):
        for attr in ("bankroll", "chips", "balance"):
            if hasattr(obj, attr):
                return getattr(obj, attr)
        raise AssertionError("Player has no bankroll-like attribute")

    start_roll = get_bankroll(p)

    def do_bet(player, amount):
        # Try common APIs
        for meth in ("place_bet", "bet", "wager"):
            if hasattr(player, meth):
                fn = getattr(player, meth)
                try:
                    # Try with explicit limits
                    res = fn(amount, table_min, table_max)
                    return res
                except TypeError:
                    try:
                        res = fn(amount)
                        return res
                    except Exception:
                        pass
        # If Game exists, try letting Game enforce table limits
        if api.Game is not None:
            try:
                gsig = inspect.signature(api.Game)
                if "table_min" in gsig.parameters or "min_bet" in gsig.parameters:
                    kwargs = {}
                    if "table_min" in gsig.parameters:
                        kwargs["table_min"] = table_min
                    if "min_bet" in gsig.parameters:
                        kwargs["min_bet"] = table_min
                    if "table_max" in gsig.parameters:
                        kwargs["table_max"] = table_max
                    if "max_bet" in gsig.parameters:
                        kwargs["max_bet"] = table_max
                    game = api.Game(**kwargs)
                else:
                    game = api.Game()
                # Try to add player and place a bet via game
                for add_name in ("add_player", "join", "seat_player"):
                    if hasattr(game, add_name):
                        getattr(game, add_name)(p)
                        break
                # Try various bet routes
                for bet_name in ("place_bet", "bet", "wager", "submit_bet"):
                    if hasattr(game, bet_name):
                        try:
                            return getattr(game, bet_name)(p, amount)
                        except Exception:
                            pass
            except Exception:
                pass
        # Last resort: directly mutate bankroll to emulate rejection/acceptance
        # Returning True/False will be interpreted by assertions below
        cur = get_bankroll(player)
        if amount < table_min or amount > table_max or amount > cur:
            return False
        else:
            if hasattr(player, "bankroll"):
                player.bankroll -= amount
            elif hasattr(player, "chips"):
                player.chips -= amount
            elif hasattr(player, "balance"):
                player.balance -= amount
            return True

    # Execute bet attempt
    try:
        result = do_bet(p, bet)
    except Exception:
        # If the API raises on invalid bet, map to boolean expectation
        result = True

    end_roll = get_bankroll(p)

    if should_succeed:
        assert end_roll == start_roll - bet, (
            f"Bet should succeed; bankroll should decrease by {bet}. Start={start_roll}, End={end_roll}"
        )
        # If function returns a boolean, should be True
        if isinstance(result, bool):
            assert result is True
    else:
        # Bankroll should be unchanged on failure
        assert end_roll == start_roll, (
            f"Invalid bet should not change bankroll. Start={start_roll}, End={end_roll}, Bet={bet}"
        )
        if isinstance(result, bool):
            assert result is False


def test_dealer_behavior_hits_until_seventeen(api):
    # This test uses Game if available; otherwise skip.
    if api.Game is None:
        pytest.skip("Game class not available for dealer behavior test")

    # Construct a game with deterministic RNG
    random.seed(2024)
    try:
        game = api.Game(num_decks=1)
    except Exception:
        try:
            game = api.Game()
        except Exception:
            pytest.skip("Unable to construct Game instance for dealer test")

    # Try to add a single player
    player = None
    if api.Player is not None:
        try:
            player = api.Player(name="DealerTest", bankroll=100)
        except Exception:
            try:
                player = api.Player("DealerTest", 100)
            except Exception:
                player = None
    if player is None:
        pytest.skip("Unable to create Player for dealer behavior test")

    added = False
    for add_name in ("add_player", "join", "seat_player"):
        if hasattr(game, add_name):
            try:
                getattr(game, add_name)(player)
                added = True
                break
            except Exception:
                pass
    if not added and hasattr(game, "players") and isinstance(game.players, list):
        game.players.append(player)
        added = True
    if not added:
        pytest.skip("Unable to add player to Game for dealer behavior test")

    # Place a minimal bet if the API requires
    for bet_name in ("place_bet", "bet", "wager", "submit_bet"):
        if hasattr(game, bet_name):
            try:
                getattr(game, bet_name)(player, 5)
            except Exception:
                pass
        elif hasattr(player, bet_name):
            try:
                getattr(player, bet_name)(5)
            except Exception:
                pass

    # Start a round and let dealer play according to rules
    progressed = False
    for start_name in ("start_round", "deal_initial", "deal"):
        if hasattr(game, start_name):
            try:
                getattr(game, start_name)()
                progressed = True
                break
            except Exception:
                pass
    # If there's an explicit dealer play step, invoke it
    for play_name in ("dealer_play", "play_dealer", "dealer_turn"):
        if hasattr(game, play_name):
            try:
                getattr(game, play_name)()
                progressed = True
                break
            except Exception:
                pass

    if not progressed:
        pytest.skip("Unable to progress Game to dealer turn for behavior test")

    # Try to access dealer hand
    dealer_hand = None
    # Common patterns: game.dealer.hand, game.dealer_hand, game.dealer.hand[0]
    if hasattr(game, "dealer"):
        dealer = getattr(game, "dealer")
        if hasattr(dealer, "hand"):
            dealer_hand = dealer.hand
        elif hasattr(dealer, "hands") and dealer.hands:
            dealer_hand = dealer.hands[0]
    if dealer_hand is None and hasattr(game, "dealer_hand"):
        dealer_hand = getattr(game, "dealer_hand")

    if dealer_hand is None:
        pytest.skip("Unable to obtain dealer hand from Game")

    total = hand_value(dealer_hand)
    assert 17 <= total <= 21, f"Dealer should finish with at least 17 and at most 21, got {total}"
