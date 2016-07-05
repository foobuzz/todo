import unittest, sys
import os.path as op


sys.path.insert(1, op.abspath('./todo'))

import todo.rainbow as rainbow


class GeneralTest():

	def run_test(self, func_name):
		for args, expected in self.cases:
			result = getattr(rainbow, func_name)(*args)
			self.assertEqual(result, expected)


class TestGetColorValues(unittest.TestCase, GeneralTest):

	cases = [
		(('magenta', '8'), (5,)),
		(('magenta', 'xterm-256'), (201,)),
		(('magenta', 'rgb'), (255, 0, 255)),
		(('5', '8'), (5,)),
		(('5', 'xterm-256'), (5,)),
		(('5', 'rgb'), (205, 0, 205)),
		(('rgb(255,0,255)', '8'), (5,)),
		(('rgb(255,0,255)', 'xterm-256'), (201,)),
		(('rgb(255,0,255)', 'rgb'), (255, 0, 255)),
		(('#ff00ff', '8'), (5,)),
		(('#ff00ff', 'xterm-256'), (201,)),
		(('#ff00ff', 'rgb'), (255, 0, 255)),
	]

	def test_get_color_values(self):
		self.run_test('get_color_values')


class TestIsInPalette(unittest.TestCase, GeneralTest):

	cases = [
		(('0',), True),
		(('128',), True),
		(('255',), True),
		(('256',), False),
		(('-10',), False),
		(('1000',), False)
	]

	def test_is_in_palette(self):
		self.run_test('is_in_palette')


class TestRGBToBasic(unittest.TestCase, GeneralTest):

	cases = [
		(((255, 255, 255),), 7),
		(((0, 0, 0),), 0),
		(((255, 0, 255),), 5),
		(((255, 0, 0),), 1),
		(((210, 15, 200),), 5),
		(((210, 15, 127),), 1)
	]

	def test_rgb_to_basic(self):
		self.run_test('rgb_to_basic')


class TestXtermToRGB(unittest.TestCase, GeneralTest):

	cases = [
		((0,), (0x0, 0x0, 0x0)),
		((2,), (0x0, 0xcd, 0x0)),
		((10,), (0x0, 0xff, 0x0)),
		((15,), (0xff, 0xff, 0xff)),
		((16,), (0x0, 0x0, 0x0)),
		((42,), (0x0, 0xd7, 0x87)),
		((231,), (0xff, 0xff, 0xff)),
		((232,), (0x8, 0x8, 0x8)),
		((242,), (0x6c, 0x6c, 0x6c)),
		((255,), (0xee, 0xee, 0xee))
	]

	def test_xterm_to_rgb(self):
		self.run_test('xterm_palette_to_rgb')


class TestRGBToXterm(unittest.TestCase, GeneralTest):

	cases = [
		(((0x0, 0x0, 0x0),), 16),
		(((0x0, 0x80, 0x0),), 28),
		(((0x0, 0xff, 0x0),), 46),
		(((0xff, 0xff, 0xff),), 231),
		(((0x0, 0x0, 0x0),), 16),
		(((0x0, 0xd7, 0x87),), 42),
		(((0xff, 0xff, 0xff),), 231),
		(((0x8, 0x8, 0x8),), 16),
		(((0x66, 0x66, 0x66),), 59),
		(((0xee, 0xee, 0xee),), 231)
	]
	
	def test_rgb_to_xterm(self):
		self.run_test('rgb_to_xterm_palette')
