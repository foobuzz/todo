import unittest
import os.path as op
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(1, op.abspath('./todo'))

import todo.todo as todo
import todo.cli_parser


NOW = todo.NOW


class TestDatetimeParsing(unittest.TestCase):

    input_cases = {
        '2016-02-03': datetime(2016, 2, 3),
        '2016-02-03T19:30:04': datetime(2016, 2, 3, 19, 30, 4),
        '03/02/2016': None,
        '42m': NOW + timedelta(seconds=42*30.5*24*3600),
        '42h': NOW + timedelta(days=1, seconds=18*3600),
        '42d': NOW + timedelta(days=42),
        '42w': NOW + timedelta(days=42*7),
        '42n': None,
        'dkfnjdfkfd': None,
        'lol42n': None,
        '-42s': None,
        '1.25s': None,
        '20l5-01-00': None
    }

    def test_parse_user_date(self):
        for u_input, expected in TestDatetimeParsing.input_cases.items():
            result = todo.cli_parser.get_datetime(u_input, NOW)
            if expected is not None:
                # Converting expected manually-entered datetime into UTC
                expected = datetime.utcfromtimestamp(expected.timestamp())
                expected = expected.replace(tzinfo=timezone.utc)

                # The conversions to and back from timestamps introduce errors
                # in the range of 10-nanoseconds, but we only need a precision
                # of the second
                result = result.replace(microsecond=0)
                expected = expected.replace(microsecond=0)
                self.assertEqual(result, expected)
            else:
                self.assertEqual(result, None)
