""" This module deals with support of the color in the terminal through ANSI
escape codes. It defines the high level class ColoredStr which is a string
containing color escape codes ready to be printed in color to the terminal.
"""

import re


# There are three possible types of ANSI escape codes to print text in colors:
# - the first one accepts an integer in the range [0;7] which indicates one of
#   the primary colors among black, red, green, yellow, blue, magenta, cyan,
#   and white, in order. This escape code can actually be mixed with another
#   one that put the text in bold and which has the side effect of making the
#   color brighter (the normal 8 colors are quite dark). I chose not to deal
#   with this second code.
# - the second one accepts an integer in the range [0;255] indicating a color
#   among a specific palette of 256 colors. In the UNIX world, most terminals
#   work with the x-term palette. Such a palette follows a specific pattern
#   and conversions between RGB and code-point in the palette can be computed
#   without carying a whole lookup table.
# - the third one accepts three integers in the range [0;255] defining the
#   color in RGB coordinates.

# Support of these codes varies from one terminal to another. Most program
# that prints stuff in color stick to the 8 basic colors, which are widely
# supported. I prefer to let the user chose what he wants to use via a
# configuration file. Using an unsupported escape code can result in no color
# at all, a wrong color, or the escape code being printed literally.

ANSI_TEMPLATES = {
	'8':         '\33[3{}m',          # Basic 8 colors
	'xterm-256': '\33[38;5;{}m',      # 256 colors
	'rgb':       '\33[38;2;{};{};{}m' # 24-bit RGB true colors
}

# ANSI escape codes are switches, turning on a given behaviour for all the
# text following it. This escape code resets all previous things turned on,
# making the text normal again
ANSI_RESET = '\33[0m'

# The 8 basic colors for the most basic escape code
BASIC_COLORS = [
	'black',
	'red',
	'green',
	'yellow',
	'blue',
	'magenta',
	'cyan',
	'white'
]

# Their RGB equivalent. A bit of cheating is involved here. As I said, the 8
# basic colors (not mixed with bold font) are quite dark. That's because their
# equivalent RGB colors are made of coordinates set at value 128, not 255.
# Here I use 255 for convenience with the rest of the program.
BASIC_RGB = [
	(0, 0, 0),
	(205, 0, 0),
	(0, 205, 0),
	(205, 205, 0),
	(0, 0, 238),
	(205, 0, 205),
	(0, 205, 205),
	(229, 229, 229)
]

# Python's re doesn't support repeated capture :s
RGB_REGEX = 'rgb\(([0-9]{1,3}),([0-9]{1,3}),([0-9]{1,3})\)'
HEXA_REGEX = '#([a-fA-F0-9]{2})([a-fA-F0-9]{2})([a-fA-F0-9]{2})'


# The following constants deals with the nature of the x-term 256 colors
# palette:
# http://www.calmar.ws/vim/256-xterm-24bit-rgb-color-chart.html
# The x-term palette is structured as follows:
#  - Codes in [0;7] are the 8 primary colors (the same supported by the most
#    basic escape code)
#  - Codes in [9;15] are also the primary colors, but the bright version (the
#    same supported by the most basic escape code when combined with bold)
#  - Codes in [16;231] are all the various colors constructed as follows: (R,
#    G, B) coordinates are incremented by regular steps. The first step is a
#    95 increment. the 4 following steps are 40 increments. (95+4*40 = 255).
#    So, for example, 16 = (0, 0, 0), 17 = (0, 0, 95), 18 = (0, 0, 135), ...,
#    21 = (0, 0, 255), 22 = (0, 95, 0), 23 = (0, 95, 95), and so on all the
#    way up to 231 = (255, 255, 255)
#  - Codes in [232;255] are gray levels (R = G = B). It starts at (8, 8, 8)
#    and increments by steps of 10, arriving at (238, 238, 238) after 23
#    steps.

# The steps
XTERM_JUMPS = [95, 40, 40, 40, 40]

# The number of code values between an increments for each of the coordinates.
# For example, 36 code values separate (0, 0, 0) from (95, 0, 0), 6 code
# values separate (0, 0, 0) from (0, 95, 0) and, of course, 1 code value
# separate (0, 0, 0) from (0, 0, 95).
# To convert an x-term code value to RGB (after having removed the
# 16-offset), you first divide by 36. The quotient gives you the number of
# steps to apply to R. You then divide the remainder by 6, which gives you the
# number of steps to apply to G. The final remainder is the number of steps to
# apply yo B.
XTERM_COEFF = [36, 6, 1]

XTERM_GRAY_LEVELS_START = 8
XTERM_GRAY_LEVELS_OFFSET = 232
XTERM_COLORS_OFFSET = 16

DEFAULT = 'default'


# The goal of this module is to allow the user to chose the palette he wants
# to use, without requiring consistency between the palette and the way the
# color is specified. For example, the user might use the x-term 256 palette
# and give a color in RGB. The module automatically makes the conversion from
# RGB to the corresponding value between 0 and 255.
# This function, given a color and a palette, returns the values to be
# inserted into the escape code corresponding to the given palette.
# It applies the following strategy: if the color is given in a format
# consistant with the palette, then it directly extracts the values from the
# color and return them. Otherwise, it converts the color to RGB and then
# converts the RGB to the format suited for the palette (or just stops at RGB
# if RGB is the format suited).
def get_color_values(color, palette):
	"""Returns a tuple of values to be inserted into the escape code
	corresponding to `palette`.

		color: a string describing a color. Accepted formats are:
		 - one of the string in `BASIC_COLORS`
		 - the decimal representation of a number between 0 and 255 (for 256
           colors palettes)
		 - a string in the form "rgb(R,G,B)" where R, G and B are integers
           between 0 and 255
		 - a string in the form "#aabbcc" where aa, bb, and cc are the
           hexadecimal representation of integers between 0 and 255

		palette: one of the keys of `PALETTES`
	"""
	rgb = None
	if color in BASIC_COLORS:
		index = BASIC_COLORS.index(color)
		if palette == '8':
			return (index,)
		else:
			rgb = tuple(255 if c > 0 else 0 for c in BASIC_RGB[index])
	elif is_in_palette(color):
		if palette == 'xterm-256':
			return (int(color),)
		else:
			rgb = xterm_palette_to_rgb(color)
	else:
		rgb_match = re.match(RGB_REGEX, color)
		if rgb_match is not None:
			rgb = rgb_match.groups()
			rgb = tuple(int(c) for c in rgb)
		else:
			hexa_match = re.match(HEXA_REGEX, color)
			if hexa_match is not None:
				rgb = hexa_match.groups()
				rgb = tuple(int(c, 16) for c in rgb)
		if (rgb_match is not None or hexa_match is not None) \
		and palette == 'rgb':
			return rgb
	if rgb is not None:
		if palette == '8':
			return (rgb_to_basic(rgb),)
		elif palette == 'xterm-256':
			return (rgb_to_xterm_palette(rgb),)
		elif palette == 'rgb':
			return rgb


def is_in_palette(color):
	try:
		value = int(color)
	except ValueError:
		return False
	return 0 <= value <= 255


def rgb_to_basic(rgb):
	bits = tuple(1 if c >= 128 else 0 for c in rgb)
	for i, color in enumerate(BASIC_RGB):
		if bits == tuple(1 if c > 0 else 0 for c in color):
			return i


def xterm_palette_to_rgb(color):
	color = int(color)
	# Basic colors
	if color <= 7:
		return BASIC_RGB[color]
	if 8 <= color <= 15:
		return tuple(255 if c > 0 else 0 for c in BASIC_RGB[color - 8])
	# Gray levels
	if XTERM_GRAY_LEVELS_OFFSET <= color <= 255:
		return (8 + 10*(color - XTERM_GRAY_LEVELS_OFFSET),) * 3
	# Other colors
	value = color - XTERM_COLORS_OFFSET
	mod = value
	rgb = []
	for c in XTERM_COEFF:
		val, mod = divmod(mod, c)
		rgb.append(sum(XTERM_JUMPS[:val]))
	return tuple(rgb)


def rgb_to_xterm_palette(rgb):
	result = None
	r, g, b = rgb
	# Gray levels
	if r == g == b:
		if r < 4:
			result = 0
		elif r > 246:
			result = 15
		elif 238 <= r <= 246:
			result = 255
		else:
			value, mod = divmod(r - XTERM_GRAY_LEVELS_START, 10)
			if mod > 4:
				value += 1
			result = XTERM_GRAY_LEVELS_OFFSET + value
	# Other colors
	total = 0
	for index, c in enumerate(rgb):
		prev_tot, tot = 0, 0
		i = 0
		while tot < c and i < len(XTERM_JUMPS):
			prev_tot = tot
			tot += XTERM_JUMPS[i]
			i += 1
		val = i if abs(tot - c) <= abs(prev_tot - c) else i-1
		total += val * XTERM_COEFF[index]
	result = XTERM_COLORS_OFFSET + total
	return result


class ColoredStr(str):

	def __new__(cls, string, color, palette='xterm-256'):
		if color == DEFAULT:
			return string
		values = get_color_values(color.lower(), palette)
		ansi_seq = get_escape(color, palette)
		literal = ansi_seq + string + ANSI_RESET
		the_string = super().__new__(cls, literal)
		setattr(the_string, 'length', len(string))
		setattr(the_string, 'true_length', len(the_string))
		setattr(the_string, 'lenesc', len(ansi_seq) + len(ANSI_RESET))
		return the_string

	def __len__(self):
		return self.length


def cstr(string, color, palette='xterm-256', no_color=False):
	if no_color:
		return string
	else:
		return ColoredStr(string, color, palette)


def get_escape(color, palette='xterm-256'):
	if color == DEFAULT:
		return None
	values = get_color_values(color.lower(), palette)
	ansi_seq = ANSI_TEMPLATES[palette].format(*values)
	return ansi_seq


if __name__ == '__main__':
	print(ColoredStr('hello, world', 'blue', 'xterm-256'))
