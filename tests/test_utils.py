#
from unittest import TestCase

from chaosaws.utils import breakup_iterable


class TestUtilities(TestCase):
    def test_breakup_iterable(self):
        iterable = []
        for i in range(0, 100):
            iterable.append("Object%s" % i)

        iteration = []
        for group in breakup_iterable(iterable, 25):
            iteration.append(group)
            self.assertEqual(len(group), 25)
        self.assertEqual(len(iteration), 4)
