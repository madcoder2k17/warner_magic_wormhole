from twisted.trial import unittest
from .. import codes

class FakeLister:
    def __init__(self, channel_ids):
        self.channel_ids = channel_ids
        self.num_calls = 0
    def call(self):
        self.num_calls += 1
        return self.channel_ids

class Completion(unittest.TestCase):
    def test_create(self):
        fl = FakeLister([1,2,3])
        ci = codes.CodeInputter([1,2,3], fl.call, 2)

    def test_basic(self):
        fl = FakeLister([4,5,6])
        # the completer is supposed to use the initial list for the first set
        # of completion requests
        ci = codes.CodeInputter([1,2,3], fl.call, 2)
        self.assertEqual(fl.num_calls, 0)
        self.assertEqual(ci.completer("", 0), "1-")
        self.assertEqual(fl.num_calls, 0)
        self.assertEqual(ci.completer("", 1), "2-")
        self.assertEqual(fl.num_calls, 0)
        self.assertEqual(ci.completer("", 2), "3-")
        self.assertEqual(fl.num_calls, 0)
        self.assertEqual(ci.completer("", 3), None)
        self.assertEqual(fl.num_calls, 0)

        # when we prod it a second time, it should fetch a new list
        self.assertEqual(ci.completer("", 0), "4-")
        self.assertEqual(fl.num_calls, 1)
        self.assertEqual(ci.completer("", 1), "5-")
        self.assertEqual(fl.num_calls, 1)
        self.assertEqual(ci.completer("", 2), "6-")
        self.assertEqual(fl.num_calls, 1)
        self.assertEqual(ci.completer("", 3), None)
        self.assertEqual(fl.num_calls, 1)

    def test_first_word(self):
        # CodeInputter knows we have more words to go, so it will suggest a
        # trailing "-"
        fl = FakeLister([4,5,6])
        ci = codes.CodeInputter([1,2,3], fl.call, 2)
        self.assertEqual(ci.completer("2-ad", 0), "2-adroitness-")
        self.assertEqual(ci.completer("2-ad", 1), "2-adviser-")
        self.assertEqual(ci.completer("2-ad", 2), None)
        self.assertEqual(fl.num_calls, 0)

    def test_second_word(self):
        # since CodeInputter knows we're entering the last word, it won't
        # suggest the trailing "-"
        fl = FakeLister([4,5,6])
        ci = codes.CodeInputter([1,2,3], fl.call, 2)
        self.assertEqual(ci.completer("3-foo-bl", 0), "3-foo-blackjack")
        self.assertEqual(ci.completer("3-foo-bl", 1), "3-foo-blockade")
        self.assertEqual(ci.completer("3-foo-bl", 2), "3-foo-blowtorch")
        self.assertEqual(ci.completer("3-foo-bl", 3), "3-foo-bluebird")
        self.assertEqual(ci.completer("3-foo-bl", 5), None)
        self.assertEqual(fl.num_calls, 0)


