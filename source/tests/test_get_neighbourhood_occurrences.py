import datetime
import unittest

import freezegun

from todo.core import get_neighbourhood_occurrences


@freezegun.freeze_time('2023-11-20')
class TestJustAfterStart(unittest.TestCase):

    def test_just_after_start(self):
        start = datetime.datetime(2023, 11, 19)

        previous_occurrence, next_occurrence = get_neighbourhood_occurrences(
            start=start,
            period=5*24*3600,  # 5 days
        )

        self.assertEqual(previous_occurrence, start)
        self.assertEqual(next_occurrence, datetime.datetime(2023, 11, 24))


@freezegun.freeze_time('2023-03-07')
class TestLotsOfPreviousOccurrences(unittest.TestCase):

    def test_just_after_start(self):
        start = datetime.datetime(2023, 1, 1)

        previous_occurrence, next_occurrence = get_neighbourhood_occurrences(
            start=start,
            period=7*24*3600,  # 1 week
        )

        self.assertEqual(previous_occurrence, datetime.datetime(2023, 3, 5))
        self.assertEqual(next_occurrence, datetime.datetime(2023, 3, 12))
