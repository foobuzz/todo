import unittest, sys
import os.path as op
from datetime import datetime, timedelta, timezone

from .utils import TestFunction

sys.path.insert(1, op.abspath('./todo'))

import todo.todo as todo
import todo.utils as tutils

NOW = todo.NOW


class TestDatetimeParsing(unittest.TestCase):

	input_cases = {
		'2016-02-03': datetime(2016, 2, 3),
		'2016-02-03T19:30:04': datetime(2016, 2, 3, 19, 30, 4),
		'03/02/2016': None,
		'42s': NOW + timedelta(seconds=42),
		'42m': NOW + timedelta(seconds=42*60),
		'42h': NOW + timedelta(days=1, seconds=18*3600),
		'42d': NOW + timedelta(days=42),
		'42w': NOW + timedelta(days=42*7),
		'42n': None,
		'dkfnjdfkfd': None,
		'lol42n': None,
		'-42s': None,
		'1888888s': NOW + timedelta(seconds=1888888),
		'1.25s': None,
		'20l5-01-00': None
	}

	remaining_cases = {
		timedelta(seconds=15): '15 seconds',
		timedelta(seconds=65): '65 seconds',
		timedelta(seconds=126): '2 minutes',
		timedelta(seconds=60*44): '44 minutes',
		timedelta(seconds=60*44+18): '44 minutes',
		timedelta(seconds=3600): '60 minutes',
		timedelta(seconds=2*3600): '2 hours',
		timedelta(seconds=3600*4+60*10): '4 hours',
		timedelta(days=1): '24 hours',
		timedelta(days=1, seconds=8*3600): '32 hours',
		timedelta(days=1, seconds=8*3600+450): '32 hours',
		timedelta(days=2): '2 days',
		timedelta(days=2, seconds=3600*8): '2 days',
		timedelta(days=547545): '547545 days'
	}

	def test_parse_user_date(self):
		for u_input, expected in TestDatetimeParsing.input_cases.items():
			result = tutils.get_datetime(u_input, NOW)
			if expected is not None:
				# Converting expected manually-entered datetime into UTC
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

	def test_parse_remaining(self):
		for dt, expected in TestDatetimeParsing.remaining_cases.items():
			result = tutils.parse_remaining(dt)
			self.assertEqual(result, expected)


class TestLimitStr(TestFunction, unittest.TestCase):

	cases = [
		(['hello', 5], 'hello'),
		(['hello', 6], 'hello'),
		(['hello', 4], 'h...'),
		(['hello', 3], 'hel'),
		(['hello', 0], '')
	]

	def test_limit_str(self):
		self.run_test(tutils.limit_str)


class TestGetRelativePath(TestFunction, unittest.TestCase):

	cases = [
		(['', '.test'], 'test'),
		(['', '.test.test2'], 'test.test2'),
		(['.test', '.test.test2'], 'test2')
	]

	def test_get_relative_path(self):
		self.run_test(tutils.get_relative_path)


class TestParseVersion(TestFunction, unittest.TestCase):

	cases = [
		(['1'],        ((1, 0, 0), None, 0)),
		(['1.0'],      ((1, 0, 0), None, 0)),
		(['1.0.0'],    ((1, 0, 0), None, 0)),
		(['1.0.1'],    ((1, 0, 1), None, 0)),
		(['1.2.3'],    ((1, 2, 3), None, 0)),
		(['1.2.3r'],   ((1, 2, 3), 'r', 0)),
		(['1.2.3r1'],  ((1, 2, 3), 'r', 1)),
		(['1.2.3r12'], ((1, 2, 3), 'r', 12)),
		(['1.2r1'],    ((1, 2, 0), 'r', 1)),
		(['1r1'],      ((1, 0, 0), 'r', 1)),
	]

	def test_parse_version(self):
		self.run_test(tutils.parse_version)


class TestCompareVersions(TestFunction, unittest.TestCase):

	cases = [
		(['1', '1'],            0),
		(['1', '2'],            -1),
		(['2', '1'],            1),
		(['1.1', '1'],          1),
		(['1.1.1', '1'],        1),
		(['1.0.1', '1.1'],      -1),
		(['1.0.0', '1'],        0),
		(['1.0', '1'],          0),
		(['1a', '1'],           -1),
		(['1final', '1'],       1),
		(['1.0r', '1r'],        0),
		(['1.0.1a', '1.0.1a1'], -1)
	]

	def test_compare_versions(self):
		self.run_test(tutils.compare_versions)
