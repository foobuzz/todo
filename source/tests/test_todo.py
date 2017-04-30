import unittest, sys
import os.path as op
from datetime import timedelta

from .utils import TestFunction


sys.path.insert(1, op.abspath('./todo'))

import todo.cli_parser as cli_parser


class TestParseId(TestFunction, unittest.TestCase):

	cases = [
		(([],), (True, [])),
		((['1'],), (True, [1])),
		((['11'],), (True, [17])),
		((['ae2'],), (True, [2786])),
		((['11', 'ae2'],), (True, [17, 2786])),
		((['g'],), (False, 'Invalid task ID: g')),
		((['11', 'g'],), (False, 'Invalid task ID: g')),
		((['11', 'g', 'lol'],), (False, 'Invalid tasks ID: g, lol'))
	]

	def test_parse_id(self):
		self.run_test(cli_parser.parse_id)
