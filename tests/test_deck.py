import random
import unittest

from deck import Deck, Card, RANKS, SUITS


class TestDeck(unittest.TestCase):
    def test_build_count_single_deck(self):
        d = Deck(num_decks=1, shuffle_on_init=False)
        self.assertEqual(d.remaining(), 52)
        # Verify composition is correct
        self.assertEqual(len(d.cards), 52)
        self.assertEqual({c.suit for c in d.cards}, set(SUITS))
        self.assertEqual({c.rank for c in d.cards}, set(RANKS))

    def test_build_count_multi_deck(self):
        d = Deck(num_decks=6, shuffle_on_init=False)
        self.assertEqual(d.remaining(), 52 * 6)

    def test_draw_and_remaining(self):
        d = Deck(num_decks=1, shuffle_on_init=False)
        first = d.draw()
        self.assertIsInstance(first, Card)
        self.assertEqual(d.remaining(), 51)
        many = d.draw(3)
        self.assertEqual(len(many), 3)
        self.assertEqual(d.remaining(), 48)
        self.assertEqual(d.discard_pile_size(), 4)

    def test_draw_too_many_raises(self):
        d = Deck(num_decks=1, shuffle_on_init=False)
        with self.assertRaises(ValueError):
            d.draw(53)
        # Draw all 52, then attempt one more
        _ = d.draw(52)
        with self.assertRaises(ValueError):
            d.draw(1)

    def test_reset_rebuild(self):
        d = Deck(num_decks=2, shuffle_on_init=False)
        _ = d.draw(10)
        self.assertEqual(d.remaining(), 104 - 10)
        d.reset()
        self.assertEqual(d.remaining(), 104)
        self.assertEqual(d.discard_pile_size(), 0)

    def test_shuffle_is_deterministic_with_seed(self):
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        d1 = Deck(num_decks=1, rng=rng1, shuffle_on_init=True)
        d2 = Deck(num_decks=1, rng=rng2, shuffle_on_init=True)
        seq1 = [str(d1.draw()) for _ in range(52)]
        seq2 = [str(d2.draw()) for _ in range(52)]
        self.assertEqual(seq1, seq2)


if __name__ == "__main__":
    unittest.main()
